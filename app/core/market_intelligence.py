"""Read-only Binance market breadth, order-flow, and multi-timeframe analytics."""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.analyzer import binance_analyzer
from app.core.binance_client import BinanceClient, binance_client


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_order_book_metrics(book: dict[str, Any], levels: int = 20) -> dict[str, float | str]:
    bids = [(_float(price), _float(quantity)) for price, quantity in book.get("bids", [])[:levels]]
    asks = [(_float(price), _float(quantity)) for price, quantity in book.get("asks", [])[:levels]]
    if not bids or not asks:
        raise ValueError("Order book must contain bids and asks")
    bid_notional = sum(price * quantity for price, quantity in bids)
    ask_notional = sum(price * quantity for price, quantity in asks)
    total = bid_notional + ask_notional
    imbalance = (bid_notional - ask_notional) / total * 100 if total else 0.0
    midpoint = (bids[0][0] + asks[0][0]) / 2
    spread_bps = (asks[0][0] - bids[0][0]) / midpoint * 10_000 if midpoint else 0.0
    pressure = "BUY" if imbalance >= 10 else "SELL" if imbalance <= -10 else "BALANCED"
    return {
        "bid_notional": round(bid_notional, 2), "ask_notional": round(ask_notional, 2),
        "order_book_imbalance_pct": round(imbalance, 2), "spread_bps": round(spread_bps, 3),
        "order_book_pressure": pressure,
    }


def calculate_trade_flow(trades: list[dict[str, Any]]) -> dict[str, float | str | int]:
    """Estimate aggressive flow using Binance's buyer-is-maker flag."""
    buy_notional = 0.0
    sell_notional = 0.0
    for trade in trades:
        notional = _float(trade.get("p")) * _float(trade.get("q"))
        if trade.get("m") is True:  # buyer is maker => aggressive seller
            sell_notional += notional
        else:
            buy_notional += notional
    total = buy_notional + sell_notional
    buy_ratio = buy_notional / total * 100 if total else 50.0
    delta = buy_notional - sell_notional
    pressure = "BUY" if buy_ratio >= 55 else "SELL" if buy_ratio <= 45 else "BALANCED"
    return {
        "sample_trades": len(trades), "aggressive_buy_notional": round(buy_notional, 2),
        "aggressive_sell_notional": round(sell_notional, 2), "taker_buy_ratio_pct": round(buy_ratio, 2),
        "trade_flow_delta": round(delta, 2), "trade_flow_pressure": pressure,
    }


def multi_timeframe_consensus(symbol: str, timeframes: tuple[str, ...] = ("M15", "H1", "H4")) -> dict[str, Any]:
    analyses = [binance_analyzer.analyze(symbol, timeframe, persist=False) for timeframe in timeframes]
    average_score = sum(item["score"] for item in analyses) / len(analyses)
    aligned_buy = all(item["score"] >= 35 for item in analyses)
    aligned_sell = all(item["score"] <= -35 for item in analyses)
    direction = "BUY" if aligned_buy else "SELL" if aligned_sell else "MIXED"
    return {
        "consensus": direction, "average_score": round(average_score, 1),
        "aligned": aligned_buy or aligned_sell,
        "timeframes": [{"timeframe": item["timeframe"], "signal": item["signal"], "score": item["score"], "confidence": item["confidence"], "trend": item["trend"]} for item in analyses],
    }


def build_market_intelligence(symbol: str, client: BinanceClient = binance_client) -> dict[str, Any]:
    ticker = client.get_24h_ticker(symbol)
    if not isinstance(ticker, dict):
        raise ValueError("Expected a single-symbol ticker")
    order_book = calculate_order_book_metrics(client.get_order_book(symbol, 100))
    trade_flow = calculate_trade_flow(client.get_aggregate_trades(symbol, 500))
    consensus = multi_timeframe_consensus(symbol)
    warnings = [
        "Order-book orders can be cancelled and do not guarantee future trades.",
        "Trade-flow and volume are aggregate market activity, not individual buyer identities.",
        "Multi-timeframe consensus is not a probability of profit.",
    ]
    return {
        "source": "BINANCE", "symbol": symbol.upper(),
        "price_change_24h_pct": _float(ticker.get("priceChangePercent")),
        "quote_volume_24h": _float(ticker.get("quoteVolume")), "base_volume_24h": _float(ticker.get("volume")),
        "trade_count_24h": int(ticker.get("count", 0)), "weighted_average_price_24h": _float(ticker.get("weightedAvgPrice")),
        **order_book, **trade_flow, "multi_timeframe": consensus, "warnings": warnings,
    }


def market_leaders(client: BinanceClient = binance_client, limit: int = 10, minimum_quote_volume: float = 5_000_000) -> dict[str, list[dict[str, Any]]]:
    payload = client.get_24h_ticker()
    if not isinstance(payload, list):
        raise ValueError("Expected all-symbol ticker data")
    excluded_suffixes = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")
    rows = []
    for item in payload:
        symbol = str(item.get("symbol", ""))
        quote_volume = _float(item.get("quoteVolume"))
        if not symbol.endswith("USDT") or symbol.endswith(excluded_suffixes) or quote_volume < minimum_quote_volume:
            continue
        rows.append({
            "symbol": symbol, "last_price": _float(item.get("lastPrice")),
            "price_change_pct": _float(item.get("priceChangePercent")), "quote_volume": quote_volume,
            "trade_count": int(item.get("count", 0)),
        })
    by_volume = sorted(rows, key=lambda item: item["quote_volume"], reverse=True)[:limit]
    gainers = sorted(rows, key=lambda item: item["price_change_pct"], reverse=True)[:limit]
    losers = sorted(rows, key=lambda item: item["price_change_pct"])[:limit]
    return {"top_volume": by_volume, "top_gainers": gainers, "top_losers": losers}
