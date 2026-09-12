import numpy as np
import pandas as pd

from app.core.backtester import backtest_frame


def trending_frame(count=420):
    close = pd.Series(100 + np.arange(count, dtype=float))
    volume = np.where(np.arange(count) % 2 == 0, 2000.0, 500.0)
    return pd.DataFrame({
        "time": pd.date_range("2025-01-01", periods=count, freq="15min", tz="UTC"),
        "open": close - .2, "high": close + .8, "low": close - .8, "close": close,
        "volume": volume,
    })


def test_backtest_is_hypothetical_and_reports_metrics():
    result = backtest_frame(trending_frame(), "BTCUSDT", "M15", horizon_bars=12, max_trades=20, cost_bps=10)
    assert result["hypothetical"] is True
    assert 0 <= result["trades"] <= 20
    assert result["wins"] >= 0
    assert result["win_rate_pct"] <= 100
    assert "expectancy_r" in result
    assert result["assumed_round_trip_cost_bps"] == 10


def test_backtest_rejects_short_history():
    try:
        backtest_frame(trending_frame(100), "BTCUSDT", "M15")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "240 candles" in str(exc)


def test_missing_confirmation_never_fakes_live_strategy():
    result = backtest_frame(trending_frame(), 'BTCUSDT', 'M15')
    assert result['trades'] == 0
    assert result['evaluation'] == 'chronological_holdout'
    assert result['holdout_start_index'] == 294
    assert result['non_overlapping']
