"""End-to-end market analysis orchestration."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Protocol

import pandas as pd
from sqlalchemy import select

from app.config import settings
from app.core.indicators import calculate_indicators, detect_trend
from app.core.binance_client import binance_client
from app.core.price_action import detect_price_action
from app.core.risk_manager import calculate_risk, calculate_trade_levels
from app.core.signal_engine import score_signal
from app.core.support_resistance import find_levels
from app.database.database import session_scope
from app.database.models import ForecastCheck, Signal

logger = logging.getLogger(__name__)

CONFIRMATION_TIMEFRAME = {"M15": "H1", "H1": "H4"}


def closed_candles(frame: pd.DataFrame, now: datetime) -> pd.DataFrame:
    """Exclude Binance's still-forming last candle so signals never repaint."""
    if "close_time" not in frame or frame.empty:
        return frame
    cutoff_ms = int(now.timestamp() * 1000)
    if int(frame["close_time"].iloc[-1]) <= cutoff_ms:
        return frame
    attrs = dict(frame.attrs)
    result = frame.iloc[:-1].copy()
    result.attrs.update(attrs)
    return result


def confirm_direction(signal: str, higher_trend: str, warnings: list[str]) -> str:
    expected = "BULLISH" if "BUY" in signal else "BEARISH" if "SELL" in signal else None
    if expected and higher_trend != expected:
        warnings.append("Higher-timeframe trend does not confirm this direction")
        return "WAIT"
    return signal


class MarketDataClient(Protocol):
    def get_candles(self, symbol: str, timeframe: str, count: int = 300): ...
    def get_current_price(self, symbol: str) -> float: ...


class Analyzer:
    def __init__(self, client: MarketDataClient = binance_client, source: str = "BINANCE") -> None:
        self.client = client
        self.source = source.upper()

    def analyze(self, symbol: str, timeframe: str, persist: bool = True, user_id: int | None = None,
                account_balance: float | None = None, risk_percent: float | None = None) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        frame = closed_candles(self.client.get_candles(symbol, timeframe, 350), now)
        price = self.client.get_current_price(symbol)
        indicators = calculate_indicators(frame)
        trend = detect_trend(indicators, price)
        patterns = detect_price_action(frame)
        levels = find_levels(frame, price)
        scoring = score_signal(indicators, trend, patterns, levels, price)
        confirmation_timeframe = CONFIRMATION_TIMEFRAME.get(timeframe.upper())
        confirmation_trend = "NOT_REQUIRED"
        if confirmation_timeframe:
            higher = closed_candles(self.client.get_candles(symbol, confirmation_timeframe, 350), now)
            higher_indicators = calculate_indicators(higher)
            confirmation_trend = str(detect_trend(higher_indicators, float(higher["close"].iloc[-1]))["trend"])
            scoring["signal"] = confirm_direction(scoring["signal"], confirmation_trend, scoring["warnings"])
        direction = "LONG" if scoring["signal"] in {"BUY", "STRONG BUY"} else "SHORT" if scoring["signal"] in {"SELL", "STRONG SELL"} else "WAIT"
        setup = calculate_trade_levels(direction, price, indicators["atr"], levels["nearest_support"], levels["nearest_resistance"], settings.atr_multiplier, settings.risk_reward)
        risk = calculate_risk(account_balance or settings.account_balance, risk_percent or settings.risk_percent,
                              price, setup["stop_loss"], setup["take_profit"], settings.max_daily_risk)
        # Forecast starts after data retrieval, never before a slow request.
        now = datetime.now(timezone.utc)
        result: dict[str, Any] = {
            "symbol": symbol.upper(), "broker_symbol": frame.attrs.get("resolved_symbol", symbol), "market_source": self.source, "timeframe": timeframe.upper(), "timestamp": now.isoformat(),
            "current_price": price, "signal": scoring["signal"], "score": scoring["score"], "confidence": scoring["confidence"],
            "trend": trend["trend"], "trend_strength": trend["trend_strength"], "rsi": indicators["rsi"], "macd": indicators["macd"],
            "macd_signal": indicators["macd_signal"], "ema20": indicators["ema20"], "ema50": indicators["ema50"], "ema200": indicators["ema200"],
            "atr": indicators["atr"], "bb_upper": indicators["bb_upper"], "bb_middle": indicators["bb_middle"], "bb_lower": indicators["bb_lower"],
            "support": levels["nearest_support"], "resistance": levels["nearest_resistance"], "support_levels": levels["support_levels"], "resistance_levels": levels["resistance_levels"],
            "volume_status": "STRONG" if indicators["average_volume"] and indicators["volume"] >= indicators["average_volume"] * 1.1 else "NORMAL/WEAK",
            "volume": indicators["volume"], "average_volume": indicators["average_volume"], "price_action": patterns,
            "confirmation_timeframe": confirmation_timeframe, "confirmation_trend": confirmation_trend,
            **setup, "risk": risk, "reasons": scoring["reasons"], "warnings": scoring["warnings"], "analysis_only": True,
        }
        if persist and not self.save(result, now, user_id):
            result["warnings"].append("Analysis completed, but database persistence failed; consult logs/app.log")
        return result

    @staticmethod
    def save(result: dict[str, Any], timestamp: datetime, user_id: int | None = None) -> bool:
        try:
            with session_scope() as session:
                from app.services.verification import make_check
                check = make_check(result, timestamp, user_id)
                if check is not None:
                    duplicate = session.scalar(select(ForecastCheck.id).where(
                        ForecastCheck.user_id == user_id,
                        ForecastCheck.symbol == check.symbol,
                        ForecastCheck.timeframe == check.timeframe,
                        ForecastCheck.target_ms == check.target_ms,
                    ).limit(1))
                    if duplicate is None:
                        session.add(check)
                session.add(Signal(
                    user_id=user_id,
                    symbol=result["symbol"], timeframe=result["timeframe"], timestamp=timestamp, price=result["current_price"], signal=result["signal"], confidence=result["confidence"],
                    trend=result["trend"], rsi=result["rsi"], macd=result["macd"], ema20=result["ema20"], ema50=result["ema50"], ema200=result["ema200"],
                    support=result["support"], resistance=result["resistance"], entry=result["entry"], stop_loss=result["stop_loss"], take_profit=result["take_profit"],
                    risk_reward=result["risk_reward"], reasons=json.dumps(result["reasons"]), warnings=json.dumps(result["warnings"]), payload=json.dumps(result),
                ))
            return True
        except Exception:
            logger.exception("Failed to persist analysis for %s %s", result["symbol"], result["timeframe"])
            return False


binance_analyzer = Analyzer(binance_client, "BINANCE")
