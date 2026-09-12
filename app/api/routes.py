"""FastAPI JSON routes."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select

from app.config import settings
from app.core.analyzer import binance_analyzer
from app.core.analyzer import closed_candles, CONFIRMATION_TIMEFRAME
from datetime import datetime, timezone
from app.core.binance_client import BinanceError, binance_client
from app.core.backtester import backtest_frame
from app.core.market_intelligence import build_market_intelligence, market_leaders
from app.core.binance_client import TIMEFRAMES
from app.database.database import session_scope
from app.database.models import Signal, User, UserAlert
from app.api.schemas import AlertCreate, AlertLanguageUpdate
from app.services.telegram import format_test_message, send_message
from app.services.alerts import scan_alert_subscriptions
from app.services.accounts import current_user, same_origin
from app.services.accounts import limit as rate_limit
from app.services.chart_vision import ChartVisionError, analyze_chart

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", dependencies=[Depends(current_user)])


class ChartAnalysisRequest(BaseModel):
    image_data: str = Field(min_length=100, max_length=7_500_000)
    symbol: str = Field(default="", max_length=32)
    timeframe: str = Field(default="", max_length=8)


def _validate(symbol: str, timeframe: str, source: str = "BINANCE") -> tuple[str, str, str]:
    symbol, timeframe = symbol.upper(), timeframe.upper()
    source = source.upper()
    if source != "BINANCE":
        raise HTTPException(400, f"Unsupported market source: {source}")
    allowed = settings.binance_symbols
    if symbol not in allowed:
        raise HTTPException(404, f"Unsupported configured symbol: {symbol}")
    if timeframe not in settings.timeframes or timeframe not in TIMEFRAMES:
        raise HTTPException(400, f"Unsupported timeframe: {timeframe}")
    return source, symbol, timeframe


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "binance_connected": binance_client.is_connected(),
            "retry_after_seconds": binance_client.retry_after_seconds(), "analysis_only": True}


@router.get("/symbols")
def symbols() -> dict:
    return {"symbols": settings.binance_symbols, "sources": {"BINANCE": settings.binance_symbols}, "timeframes": settings.timeframes, "default_timeframe": settings.default_timeframe}


@router.get("/analyze/{symbol}")
def analyze_default(symbol: str, user: User = Depends(current_user)) -> dict:
    return analyze_source("BINANCE", symbol, settings.default_timeframe, user)


@router.get("/analyze/{symbol}/{timeframe}")
def analyze(symbol: str, timeframe: str, user: User = Depends(current_user)) -> dict:
    return analyze_source("BINANCE", symbol, timeframe, user)


@router.get("/analyze/{source}/{symbol}/{timeframe}")
def analyze_source(source: str, symbol: str, timeframe: str, user: User = Depends(current_user)) -> dict:
    source, symbol, timeframe = _validate(symbol, timeframe, source)
    try:
        return binance_analyzer.analyze(symbol, timeframe, user_id=user.id,
                                        account_balance=user.balance, risk_percent=user.risk_percent)
    except (BinanceError, ValueError) as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.exception("%s analysis endpoint failed", source)
        raise HTTPException(500, "Analysis failed; consult logs/app.log") from exc


@router.get("/intelligence/binance/{symbol}")
def binance_intelligence(symbol: str) -> dict:
    _, symbol, _ = _validate(symbol, "M15", "BINANCE")
    try:
        return build_market_intelligence(symbol)
    except (BinanceError, ValueError) as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/markets/binance/leaders")
def binance_market_leaders(limit: int = Query(10, ge=3, le=25)) -> dict:
    try:
        return market_leaders(limit=limit)
    except (BinanceError, ValueError) as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/backtest/binance/{symbol}/{timeframe}")
def binance_backtest(symbol: str, timeframe: str, horizon_bars: int = Query(12, ge=1, le=100), max_trades: int = Query(80, ge=10, le=200), cost_bps: float = Query(25, ge=0, le=100)) -> dict:
    _, symbol, timeframe = _validate(symbol, timeframe, "BINANCE")
    try:
        now = datetime.now(timezone.utc)
        candles = closed_candles(binance_client.get_candles(symbol, timeframe, 1000), now)
        higher_tf = CONFIRMATION_TIMEFRAME.get(timeframe)
        higher = closed_candles(binance_client.get_candles(symbol, higher_tf, 1000), now) if higher_tf else None
        return backtest_frame(candles, symbol, timeframe, horizon_bars, max_trades, cost_bps, higher_frame=higher)
    except (BinanceError, ValueError) as exc:
        raise HTTPException(503, str(exc)) from exc


@router.post("/chart-analysis")
def chart_analysis(payload: ChartAnalysisRequest, request: Request) -> dict:
    same_origin(request)
    rate_limit(request, "chart-analysis", 10, 3600)
    symbol = payload.symbol.strip().upper()
    timeframe = payload.timeframe.strip().upper()
    if timeframe and timeframe not in {"M15", "H1", "H4", "D1"}:
        raise HTTPException(400, "Ընտրեք M15, H1, H4 կամ D1 ժամանակահատված։")
    try:
        return {"analysis": analyze_chart(payload.image_data, symbol, timeframe), "stored": False}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except ChartVisionError as exc:
        raise HTTPException(503, str(exc)) from exc


def _payload(row: Signal) -> dict:
    try:
        return json.loads(row.payload)
    except (TypeError, json.JSONDecodeError):
        return {"id": row.id, "symbol": row.symbol, "timeframe": row.timeframe, "timestamp": row.timestamp.isoformat(), "current_price": row.price, "signal": row.signal, "confidence": row.confidence, "trend": row.trend}


@router.get("/signals")
def signals(limit: int = Query(50, ge=1, le=500), symbol: str | None = None, user: User = Depends(current_user)) -> list[dict]:
    with session_scope() as session:
        query = select(Signal).where(Signal.user_id == user.id).order_by(desc(Signal.timestamp)).limit(limit)
        if symbol:
            query = query.where(Signal.symbol == symbol.upper())
        return [_payload(row) for row in session.scalars(query).all()]


@router.get("/signals/latest")
def latest(user: User = Depends(current_user)) -> dict:
    with session_scope() as session:
        row = session.scalar(select(Signal).where(Signal.user_id == user.id).order_by(desc(Signal.timestamp)).limit(1))
        if not row:
            raise HTTPException(404, "No analyses have been stored yet")
        return _payload(row)


@router.get("/stats")
def stats(user: User = Depends(current_user)) -> dict:
    with session_scope() as session:
        total = session.scalar(select(func.count()).select_from(Signal).where(Signal.user_id == user.id)) or 0
        groups = session.execute(select(Signal.signal, func.count()).where(Signal.user_id == user.id).group_by(Signal.signal)).all()
        average = session.scalar(select(func.avg(Signal.confidence)).where(Signal.user_id == user.id)) or 0
        return {"total_analyses": total, "by_signal": dict(groups), "average_confidence": round(float(average), 1), "analysis_only": True}


def _alert_payload(row: UserAlert) -> dict:
    return {
        "id": row.id,
        "source": "BINANCE",
        "symbol": row.symbol,
        "timeframe": row.timeframe,
        "min_confidence": row.min_confidence,
        "active": row.active,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "last_checked_at": row.last_checked_at.isoformat() if row.last_checked_at else None,
        "last_notified_at": row.last_notified_at.isoformat() if row.last_notified_at else None,
        "last_signal": row.last_signal,
        "last_confidence": row.last_confidence,
    }


@router.get("/alerts/status")
def alert_status(user: User = Depends(current_user)) -> dict:
    return {
        "telegram_configured": bool(settings.telegram_bot_token and user.telegram_chat_id),
        "scheduler_enabled": settings.scheduler_enabled,
        "scan_interval_minutes": settings.scan_interval_minutes,
        "cooldown_minutes": settings.telegram_cooldown_minutes,
        "language": user.language,
    }


@router.put("/alerts/language")
def update_alert_language(payload: AlertLanguageUpdate, request: Request, user: User = Depends(current_user)) -> dict:
    same_origin(request)
    if payload.language not in {"hy", "ru", "en"}:
        raise HTTPException(400, "Unsupported language")
    with session_scope() as session:
        row = session.get(User, user.id); row.language = payload.language
    return {"language": payload.language}


@router.get("/alerts")
def list_alerts(user: User = Depends(current_user)) -> list[dict]:
    with session_scope() as session:
        rows = session.scalars(select(UserAlert).where(UserAlert.user_id == user.id).order_by(desc(UserAlert.created_at))).all()
        return [_alert_payload(row) for row in rows]


@router.post("/alerts")
def save_alert(payload: AlertCreate, background_tasks: BackgroundTasks, request: Request, user: User = Depends(current_user)) -> dict:
    same_origin(request)
    source, symbol, timeframe = _validate(payload.symbol, payload.timeframe, payload.source)
    with session_scope() as session:
        row = session.scalar(select(UserAlert).where(
            UserAlert.user_id == user.id,
            UserAlert.symbol == symbol,
            UserAlert.timeframe == timeframe,
        ))
        if row is None:
            row = UserAlert(user_id=user.id, symbol=symbol, timeframe=timeframe, min_confidence=payload.min_confidence)
            session.add(row)
        else:
            row.min_confidence = payload.min_confidence
            row.active = True
        session.flush()
        result = _alert_payload(row)
        alert_id = row.id
    background_tasks.add_task(scan_alert_subscriptions, alert_id)
    return result


@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int, request: Request, user: User = Depends(current_user)) -> dict:
    same_origin(request)
    with session_scope() as session:
        row = session.get(UserAlert, alert_id)
        if row is None or row.user_id != user.id:
            raise HTTPException(404, "Alert subscription not found")
        session.delete(row)
    return {"deleted": True, "id": alert_id}


@router.post("/alerts/test")
def test_alert(request: Request, user: User = Depends(current_user)) -> dict:
    same_origin(request)
    if not settings.telegram_bot_token or not user.telegram_chat_id:
        raise HTTPException(400, "Միացրեք Telegram-ը ձեր հաշվին")
    if not send_message(format_test_message(user.language), user.telegram_chat_id):
        raise HTTPException(502, "Telegram rejected the notification; check token, chat ID, and internet connection")
    return {"sent": True}
