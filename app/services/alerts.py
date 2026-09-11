"""Persisted Telegram alert subscriptions and background evaluation."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select

from app.config import settings
from app.core.analyzer import binance_analyzer
from app.database.database import session_scope
from app.database.models import User, UserAlert
from app.services.telegram import send_analysis

logger = logging.getLogger(__name__)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def should_notify(item: dict[str, Any], threshold: float, last_notified_at: datetime | None, previous_signal: str | None, now: datetime) -> bool:
    if float(item.get("confidence", 0)) < threshold:
        return False
    last = _utc(last_notified_at)
    signal_changed = bool(previous_signal and previous_signal != item.get("signal"))
    cooldown_ok = last is None or now - last >= timedelta(minutes=settings.telegram_cooldown_minutes)
    return signal_changed or cooldown_ok


def scan_alert_subscriptions(subscription_id: int | None = None) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    with session_scope() as session:
        query = select(UserAlert).where(UserAlert.active.is_(True))
        if subscription_id is not None:
            query = query.where(UserAlert.id == subscription_id)
        subscriptions = session.scalars(query).all()
        for subscription in subscriptions:
            now = datetime.now(timezone.utc)
            previous_signal = subscription.last_signal
            try:
                if subscription.timeframe not in settings.timeframes:
                    subscription.active = False
                    outcomes.append({"id": subscription.id, "disabled": True, "reason": "timeframe disabled"})
                    continue
                user = session.get(User, subscription.user_id)
                if not user:
                    continue
                item = binance_analyzer.analyze(subscription.symbol, subscription.timeframe, user_id=user.id,
                                                account_balance=user.balance, risk_percent=user.risk_percent)
                notify = should_notify(item, subscription.min_confidence, subscription.last_notified_at, previous_signal, now)
                sent = bool(notify and user.telegram_chat_id and send_analysis(item, user.language, user.telegram_chat_id))
                subscription.last_checked_at = now
                subscription.last_signal = str(item.get("signal"))
                subscription.last_confidence = float(item.get("confidence", 0))
                if sent:
                    subscription.last_notified_at = now
                outcomes.append({"id": subscription.id, "qualified": notify, "sent": sent, "signal": subscription.last_signal, "confidence": subscription.last_confidence})
            except Exception as exc:
                subscription.last_checked_at = now
                outcomes.append({"id": subscription.id, "error": str(exc)})
                logger.warning("Alert scan failed for user %s %s %s: %s", subscription.user_id, subscription.symbol, subscription.timeframe, exc)
    return outcomes
