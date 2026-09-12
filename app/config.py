"""Environment-backed application configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _csv(name: str, default: str) -> list[str]:
    return [value.strip().upper() for value in os.getenv(name, default).split(",") if value.strip()]


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = field(default_factory=lambda: os.getenv('GEMINI_API_KEY', '').strip())
    gemini_vision_model: str = field(default_factory=lambda: os.getenv('GEMINI_VISION_MODEL', 'gemini-3.8-flash').strip())
    active_workspace: str = field(default_factory=lambda: os.getenv('ACTIVE_WORKSPACE', 'POCKET_OPTION').upper())
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_vision_model: str = field(default_factory=lambda: os.getenv("OPENAI_VISION_MODEL", "gpt-5.6-luna"))
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    telegram_bot_username: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_USERNAME", "").lstrip("@"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data/trading.db"))
    binance_symbols: list[str] = field(default_factory=lambda: _csv("BINANCE_SYMBOLS", "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT"))
    binance_enabled: bool = field(default_factory=lambda: os.getenv("BINANCE_ENABLED", "true").lower() in {"1", "true", "yes"})
    binance_base_urls: list[str] = field(default_factory=lambda: [value.strip().rstrip("/") for value in os.getenv("BINANCE_BASE_URLS", "https://data-api.binance.vision,https://api.binance.com").split(",") if value.strip()])
    timeframes: list[str] = field(default_factory=lambda: _csv("TIMEFRAMES", "M15,H1"))
    default_timeframe: str = field(default_factory=lambda: os.getenv("DEFAULT_TIMEFRAME", "M15").upper())
    scan_interval_minutes: int = field(default_factory=lambda: max(1, int(os.getenv("SCAN_INTERVAL_MINUTES", "5"))))
    min_signal_confidence: float = field(default_factory=lambda: float(os.getenv("MIN_SIGNAL_CONFIDENCE", "70")))
    telegram_cooldown_minutes: int = field(default_factory=lambda: max(0, int(os.getenv("TELEGRAM_COOLDOWN_MINUTES", "30"))))
    account_balance: float = field(default_factory=lambda: float(os.getenv("ACCOUNT_BALANCE", "1000")))
    risk_percent: float = field(default_factory=lambda: float(os.getenv("RISK_PERCENT", "1")))
    max_daily_risk: float = field(default_factory=lambda: float(os.getenv("MAX_DAILY_RISK", "50")))
    atr_multiplier: float = field(default_factory=lambda: float(os.getenv("ATR_MULTIPLIER", "1.5")))
    risk_reward: float = field(default_factory=lambda: float(os.getenv("RISK_REWARD", "2")))
    buy_threshold: int = field(default_factory=lambda: int(os.getenv("BUY_THRESHOLD", "35")))
    strong_buy_threshold: int = field(default_factory=lambda: int(os.getenv("STRONG_BUY_THRESHOLD", "60")))
    sell_threshold: int = field(default_factory=lambda: int(os.getenv("SELL_THRESHOLD", "-35")))
    strong_sell_threshold: int = field(default_factory=lambda: int(os.getenv("STRONG_SELL_THRESHOLD", "-60")))
    scheduler_enabled: bool = field(default_factory=lambda: os.getenv("SCHEDULER_ENABLED", "true").lower() in {"1", "true", "yes"})
    public_url: str = field(default_factory=lambda: os.getenv(
        "PUBLIC_URL", os.getenv("RENDER_EXTERNAL_URL", "http://127.0.0.1:8000")
    ).rstrip("/"))
    admin_username: str = field(default_factory=lambda: os.getenv("ADMIN_USERNAME", "admin").strip().lower())
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", ""))


settings = Settings()
