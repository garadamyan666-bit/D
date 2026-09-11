import pytest

from app.core.market_intelligence import calculate_order_book_metrics, calculate_trade_flow


def test_order_book_imbalance_and_spread():
    book = {"bids": [["100", "10"], ["99", "10"]], "asks": [["101", "5"], ["102", "5"]]}
    metrics = calculate_order_book_metrics(book)
    assert metrics["bid_notional"] == 1990
    assert metrics["ask_notional"] == 1015
    assert metrics["order_book_imbalance_pct"] > 30
    assert metrics["order_book_pressure"] == "BUY"
    assert metrics["spread_bps"] == pytest.approx(99.502, abs=.001)


def test_trade_flow_uses_aggressor_side():
    trades = [
        {"p": "100", "q": "2", "m": False},
        {"p": "100", "q": "1", "m": True},
    ]
    flow = calculate_trade_flow(trades)
    assert flow["aggressive_buy_notional"] == 200
    assert flow["aggressive_sell_notional"] == 100
    assert flow["taker_buy_ratio_pct"] == pytest.approx(66.67, abs=.01)
    assert flow["trade_flow_pressure"] == "BUY"


def test_empty_order_book_is_invalid():
    with pytest.raises(ValueError):
        calculate_order_book_metrics({"bids": [], "asks": []})
