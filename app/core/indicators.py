"""Technical indicators implemented with pandas for deterministic testing."""
from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {"open", "high", "low", "close"}


def validate_ohlcv(frame: pd.DataFrame, minimum: int = 2) -> None:
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing OHLC columns: {', '.join(sorted(missing))}")
    if len(frame) < minimum:
        raise ValueError(f"At least {minimum} candles are required")
    if frame[list(REQUIRED_COLUMNS)].isnull().any().any():
        raise ValueError("OHLC data contains null values")


def ema(series: pd.Series, period: int) -> pd.Series:
    if period <= 0:
        raise ValueError("EMA period must be positive")
    return series.astype(float).ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.astype(float).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result = 100 - (100 / (1 + rs))
    result = result.where(avg_loss != 0, 100.0).where(avg_gain != 0, 0.0)
    return result


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    line = ema(series, fast) - ema(series, slow)
    signal_line = line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return line, signal_line, line - signal_line


def atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    previous = frame["close"].shift(1)
    ranges = pd.concat([(frame["high"] - frame["low"]), (frame["high"] - previous).abs(), (frame["low"] - previous).abs()], axis=1)
    return ranges.max(axis=1).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def calculate_indicators(frame: pd.DataFrame) -> dict[str, float]:
    validate_ohlcv(frame, 200)
    close = frame["close"].astype(float)
    middle = close.rolling(20).mean()
    deviation = close.rolling(20).std(ddof=0)
    macd_line, signal_line, histogram = macd(close)
    volume_col = "tick_volume" if "tick_volume" in frame else "volume" if "volume" in frame else None
    volume = float(frame[volume_col].iloc[-1]) if volume_col else 0.0
    average_volume = float(frame[volume_col].rolling(20).mean().iloc[-1]) if volume_col else 0.0
    values = {
        "ema20": ema(close, 20).iloc[-1], "ema50": ema(close, 50).iloc[-1], "ema200": ema(close, 200).iloc[-1],
        "rsi": rsi(close, 14).iloc[-1], "macd": macd_line.iloc[-1], "macd_signal": signal_line.iloc[-1],
        "macd_histogram": histogram.iloc[-1], "atr": atr(frame, 14).iloc[-1], "bb_upper": (middle + 2 * deviation).iloc[-1],
        "bb_middle": middle.iloc[-1], "bb_lower": (middle - 2 * deviation).iloc[-1], "volume": volume, "average_volume": average_volume,
    }
    if any(pd.isna(value) for value in values.values()):
        raise ValueError("Insufficient candle history for complete indicator calculation")
    return {key: float(value) for key, value in values.items()}


def detect_trend(indicators: dict[str, float], price: float) -> dict[str, str | float]:
    e20, e50, e200 = indicators["ema20"], indicators["ema50"], indicators["ema200"]
    trend = "BULLISH" if e20 > e50 > e200 else "BEARISH" if e20 < e50 < e200 else "NEUTRAL"
    separation = (abs(e20 - e50) + abs(e50 - e200)) / max(abs(price), 1e-12) * 100
    strength = min(100.0, separation * 100)
    return {"trend": trend, "trend_strength": round(strength, 2), "price_vs_ema200": "ABOVE" if price > e200 else "BELOW"}
