import numpy as np
import pandas as pd
import pytest

from app.core.indicators import calculate_indicators, detect_trend, ema, macd, rsi


def frame(count=300):
    close = pd.Series(np.linspace(100, 150, count) + np.sin(np.arange(count) / 4))
    return pd.DataFrame({"open": close - .2, "high": close + .8, "low": close - .8, "close": close, "tick_volume": np.linspace(100, 200, count)})


def test_ema_matches_pandas_definition():
    values = pd.Series(range(1, 31), dtype=float)
    expected = values.ewm(span=20, adjust=False, min_periods=20).mean()
    pd.testing.assert_series_equal(ema(values, 20), expected)


def test_rsi_for_rising_series_is_100():
    result = rsi(pd.Series(range(1, 40), dtype=float))
    assert result.iloc[-1] == pytest.approx(100)


def test_macd_line_is_positive_for_uptrend():
    line, signal, histogram = macd(pd.Series(range(1, 100), dtype=float))
    assert line.iloc[-1] > 0
    assert not np.isnan(signal.iloc[-1])
    assert not np.isnan(histogram.iloc[-1])


def test_indicator_bundle_and_bullish_trend():
    data = calculate_indicators(frame())
    trend = detect_trend(data, float(frame().close.iloc[-1]))
    assert set(("ema20", "ema50", "ema200", "rsi", "atr")) <= data.keys()
    assert trend["trend"] == "BULLISH"
    assert trend["trend_strength"] >= 0


def test_invalid_and_insufficient_data():
    with pytest.raises(ValueError, match="Missing OHLC"):
        calculate_indicators(pd.DataFrame({"close": [1] * 300}))
    with pytest.raises(ValueError, match="At least 200"):
        calculate_indicators(frame(50))
