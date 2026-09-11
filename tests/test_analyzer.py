from datetime import datetime, timezone

import pandas as pd

from app.core.analyzer import closed_candles, confirm_direction


def test_open_candle_is_excluded_without_losing_metadata():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    frame = pd.DataFrame({"close": [100, 101], "close_time": [int(now.timestamp() * 1000) - 1, int(now.timestamp() * 1000) + 59_999]})
    frame.attrs["resolved_symbol"] = "BTCUSDT"
    result = closed_candles(frame, now)
    assert result["close"].tolist() == [100]
    assert result.attrs["resolved_symbol"] == "BTCUSDT"


def test_higher_timeframe_must_confirm_direction():
    warnings = []
    assert confirm_direction("STRONG BUY", "BEARISH", warnings) == "WAIT"
    assert warnings
    assert confirm_direction("SELL", "BEARISH", []) == "SELL"
    assert confirm_direction("WAIT", "NEUTRAL", []) == "WAIT"
