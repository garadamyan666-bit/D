from app.core.signal_engine import calculate_confidence, classify_signal, score_signal


def bullish_inputs():
    indicators = {"ema20": 110, "ema50": 105, "ema200": 100, "rsi": 58, "macd": 2, "macd_signal": 1, "volume": 150, "average_volume": 100, "atr": 2}
    trend = {"trend": "BULLISH", "trend_strength": 80}
    levels = {"support_distance": 1, "resistance_distance": 10}
    return indicators, trend, levels


def test_strong_bullish_confluence_scores_strong_buy():
    indicators, trend, levels = bullish_inputs()
    result = score_signal(indicators, trend, ["BULLISH_ENGULFING"], levels, 111)
    assert result["score"] == 100
    assert result["signal"] == "STRONG BUY"
    assert result["confidence"] > 80
    assert len(result["reasons"]) >= 5


def test_classification_boundaries():
    assert classify_signal(60) == "STRONG BUY"
    assert classify_signal(35) == "BUY"
    assert classify_signal(34) == "WAIT"
    assert classify_signal(-35) == "SELL"
    assert classify_signal(-60) == "STRONG SELL"


def test_confidence_is_derived_and_bounded():
    assert calculate_confidence(0, 0) == 0
    assert calculate_confidence(100, 7) == 100
    assert calculate_confidence(50, 4) == calculate_confidence(-50, 4)


def test_direction_is_rejected_without_volume_confirmation():
    indicators, trend, levels = bullish_inputs()
    indicators["volume"] = 50
    result = score_signal(indicators, trend, ["BULLISH_ENGULFING"], levels, 111)
    assert result["signal"] == "WAIT"
