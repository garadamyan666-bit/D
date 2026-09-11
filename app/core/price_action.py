"""Conservative candle-pattern heuristics."""
from __future__ import annotations

import pandas as pd


def detect_price_action(frame: pd.DataFrame) -> list[str]:
    if len(frame) < 2:
        raise ValueError("At least two candles are required for price-action analysis")
    previous, candle = frame.iloc[-2], frame.iloc[-1]
    body = abs(candle.close - candle.open)
    full_range = max(candle.high - candle.low, 1e-12)
    upper = candle.high - max(candle.open, candle.close)
    lower = min(candle.open, candle.close) - candle.low
    patterns: list[str] = []
    if body / full_range <= 0.1:
        patterns.append("DOJI")
    if lower >= body * 2 and upper <= max(body, full_range * 0.1) and candle.close >= candle.open:
        patterns.append("HAMMER")
    if upper >= body * 2 and lower <= max(body, full_range * 0.1) and candle.close <= candle.open:
        patterns.append("SHOOTING_STAR")
    if previous.close < previous.open and candle.close > candle.open and candle.open <= previous.close and candle.close >= previous.open:
        patterns.append("BULLISH_ENGULFING")
    if previous.close > previous.open and candle.close < candle.open and candle.open >= previous.close and candle.close <= previous.open:
        patterns.append("BEARISH_ENGULFING")
    average_body = (frame["close"] - frame["open"]).abs().tail(20).mean()
    if body >= average_body * 1.5 and body / full_range >= 0.65:
        patterns.append("STRONG_BULLISH_CANDLE" if candle.close > candle.open else "STRONG_BEARISH_CANDLE")
    return patterns or ["NONE"]
