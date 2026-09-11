"""Multi-factor deterministic signal scoring."""
from __future__ import annotations

from app.config import settings

BULLISH_PATTERNS = {"BULLISH_ENGULFING", "HAMMER", "STRONG_BULLISH_CANDLE"}
BEARISH_PATTERNS = {"BEARISH_ENGULFING", "SHOOTING_STAR", "STRONG_BEARISH_CANDLE"}


def classify_signal(score: int) -> str:
    if score >= settings.strong_buy_threshold: return "STRONG BUY"
    if score >= settings.buy_threshold: return "BUY"
    if score <= settings.strong_sell_threshold: return "STRONG SELL"
    if score <= settings.sell_threshold: return "SELL"
    return "WAIT"


def calculate_confidence(score: int, confirmations: int, factors: int = 7) -> float:
    magnitude = min(100.0, abs(score))
    breadth = min(100.0, confirmations / max(factors, 1) * 100)
    return round(magnitude * 0.75 + breadth * 0.25, 1)


def score_signal(indicators: dict[str, float], trend: dict, patterns: list[str], levels: dict, price: float) -> dict:
    score, confirmations = 0, 0
    reasons, warnings = [], []
    direction = 1 if trend["trend"] == "BULLISH" else -1 if trend["trend"] == "BEARISH" else 0
    if direction:
        score += 25 * direction; confirmations += 1; reasons.append(f"{trend['trend'].title()} multi-EMA trend")
    ema_direction = 1 if indicators["ema20"] > indicators["ema50"] else -1
    score += 15 * ema_direction; confirmations += int(ema_direction == direction or direction == 0)
    reasons.append("EMA20 is above EMA50" if ema_direction > 0 else "EMA20 is below EMA50")
    macd_direction = 1 if indicators["macd"] > indicators["macd_signal"] else -1
    score += 15 * macd_direction; confirmations += int(macd_direction == direction or direction == 0)
    reasons.append("MACD momentum is bullish" if macd_direction > 0 else "MACD momentum is bearish")
    rsi_value = indicators["rsi"]
    rsi_direction = 1 if 50 <= rsi_value < 70 else -1 if 30 < rsi_value < 50 else 0
    if rsi_value <= 30: rsi_direction = 1; warnings.append("RSI is oversold; reversal is not guaranteed")
    if rsi_value >= 70: rsi_direction = -1; warnings.append("RSI is overbought; trend may persist")
    score += 10 * rsi_direction; confirmations += int(rsi_direction == direction and direction != 0)
    volume_strong = indicators["average_volume"] > 0 and indicators["volume"] >= indicators["average_volume"] * 1.1
    if volume_strong and direction:
        score += 10 * direction; confirmations += 1; reasons.append("Above-average tick volume confirms direction")
    elif indicators["average_volume"] > 0:
        score += -10 * direction if direction else 0; warnings.append("Tick volume is below confirmation threshold")
    pattern_direction = 1 if any(p in BULLISH_PATTERNS for p in patterns) else -1 if any(p in BEARISH_PATTERNS for p in patterns) else 0
    score += 10 * pattern_direction; confirmations += int(pattern_direction == direction and direction != 0)
    if pattern_direction: reasons.append("Bullish price-action pattern" if pattern_direction > 0 else "Bearish price-action pattern")
    support_distance, resistance_distance = levels.get("support_distance"), levels.get("resistance_distance")
    atr_value = indicators["atr"]
    if direction > 0 and support_distance is not None and support_distance <= atr_value * 2:
        score += 15; confirmations += 1; reasons.append("Nearby support favors the long setup")
    elif direction < 0 and resistance_distance is not None and resistance_distance <= atr_value * 2:
        score -= 15; confirmations += 1; reasons.append("Nearby resistance favors the short setup")
    if direction > 0 and resistance_distance is not None and resistance_distance < atr_value:
        score -= 15; warnings.append("Resistance is less than one ATR away")
    if direction < 0 and support_distance is not None and support_distance < atr_value:
        score += 15; warnings.append("Support is less than one ATR away")
    score = max(-100, min(100, int(score)))
    signal = classify_signal(score)
    # Only publish a direction when independent factors strongly agree.
    high_quality = abs(score) >= 60 and confirmations >= 5 and trend.get("trend_strength", 0) >= 50 and volume_strong
    if signal != "WAIT" and not high_quality:
        signal = "WAIT"
        warnings.append("Directional setup rejected: trend, volume and confirmations do not agree strongly enough")
    return {"score": score, "signal": signal, "confidence": calculate_confidence(score, confirmations), "confirmations": confirmations, "reasons": reasons, "warnings": warnings}
