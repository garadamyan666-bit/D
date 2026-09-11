"""Database entities."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Signal(Base):
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(8), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    price: Mapped[float] = mapped_column(Float)
    signal: Mapped[str] = mapped_column(String(24), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    trend: Mapped[str] = mapped_column(String(16))
    rsi: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema20: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema50: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema200: Mapped[float | None] = mapped_column(Float, nullable=True)
    support: Mapped[float | None] = mapped_column(Float, nullable=True)
    resistance: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasons: Mapped[str] = mapped_column(Text, default="[]")
    warnings: Mapped[str] = mapped_column(Text, default="[]")
    payload: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"
    __table_args__ = (UniqueConstraint("source", "symbol", "timeframe", name="uq_alert_market"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(16), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(8), index=True)
    min_confidence: Mapped[float] = mapped_column(Float, default=70)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_signal: Mapped[str | None] = mapped_column(String(24), nullable=True)
    last_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))


class ForecastCheck(Base):
    __tablename__ = 'forecast_checks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32))
    timeframe: Mapped[str] = mapped_column(String(8))
    signal: Mapped[str] = mapped_column(String(24))
    confidence: Mapped[float] = mapped_column(Float)
    start_price: Mapped[float] = mapped_column(Float)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    target_ms: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    end_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(2), default='hy')
    telegram_chat_id: Mapped[str | None] = mapped_column(String(40), nullable=True, unique=True)
    telegram_link_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    telegram_link_expires: Mapped[float | None] = mapped_column(Float, nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=100)
    risk_percent: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserSession(Base):
    __tablename__ = 'user_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    expires_at: Mapped[float] = mapped_column(Float)


class UserAlert(Base):
    __tablename__ = 'user_alerts'
    __table_args__ = (UniqueConstraint('user_id', 'symbol', 'timeframe', name='uq_user_alert'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    symbol: Mapped[str] = mapped_column(String(32))
    timeframe: Mapped[str] = mapped_column(String(8))
    min_confidence: Mapped[float] = mapped_column(Float, default=70)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_signal: Mapped[str | None] = mapped_column(String(24), nullable=True)
    last_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
