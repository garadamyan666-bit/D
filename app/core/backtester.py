"""Conservative historical replay for analysis signals.

Results are hypothetical, use only candles available at each decision point,
enter on the next candle open, and count a same-candle SL/TP collision as a loss.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.config import settings
from app.core.indicators import calculate_indicators, detect_trend
from app.core.price_action import detect_price_action
from app.core.risk_manager import calculate_trade_levels
from app.core.signal_engine import score_signal
from app.core.support_resistance import find_levels


def _outcome(direction: str, entry: float, stop: float, target: float, future: pd.DataFrame, cost_bps: float) -> tuple[str, float, int]:
    risk = abs(entry - stop)
    cost_r = (entry * cost_bps / 10_000) / risk if risk else 0.0
    for bars, (_, candle) in enumerate(future.iterrows(), start=1):
        if direction == "LONG":
            stop_hit, target_hit = candle.low <= stop, candle.high >= target
        else:
            stop_hit, target_hit = candle.high >= stop, candle.low <= target
        if stop_hit:  # conservative when both levels occur inside one candle
            return "LOSS", round(-1.0 - cost_r, 3), bars
        if target_hit:
            gross_r = abs(target - entry) / risk
            return "WIN", round(gross_r - cost_r, 3), bars
    final_price = float(future.close.iloc[-1])
    gross_r = (final_price - entry) / risk if direction == "LONG" else (entry - final_price) / risk
    return "TIMEOUT", round(gross_r - cost_r, 3), len(future)


def backtest_frame(frame: pd.DataFrame, symbol: str, timeframe: str, horizon_bars: int = 12, max_trades: int = 100, cost_bps: float = 25.0, higher_frame: pd.DataFrame | None = None) -> dict[str, Any]:
    if len(frame) < 240:
        raise ValueError("At least 240 candles are required for backtesting")
    if horizon_bars < 1 or max_trades < 1 or cost_bps < 0:
        raise ValueError("Backtest horizon/trades must be positive and costs cannot be negative")
    # The first 70% is warm-up/development history, never reported as holdout.
    split = max(220, int(len(frame) * .7))
    candidate_indices = list(range(split, len(frame) - horizon_bars - 1))
    # Bound CPU while favoring recent history and preserving chronological order.
    candidate_indices = candidate_indices[-max_trades * 5:]
    trades: list[dict[str, Any]] = []
    next_index = 0
    for index in candidate_indices:
        if index < next_index:
            continue
        history = frame.iloc[max(0, index - 349):index + 1]
        indicators = calculate_indicators(history)
        signal_price = float(history.close.iloc[-1])
        trend = detect_trend(indicators, signal_price)
        patterns = detect_price_action(history)
        levels = find_levels(history, signal_price)
        scoring = score_signal(indicators, trend, patterns, levels, signal_price)
        if timeframe in {'M15', 'H1'}:
            if higher_frame is None or 'close_time' not in frame or 'close_time' not in higher_frame:
                continue  # Do not present an unconfirmed strategy as the live one.
            higher = higher_frame[higher_frame.close_time <= frame.close_time.iloc[index]].tail(350)
            if len(higher) < 220:
                continue
            from app.core.analyzer import confirm_direction
            higher_trend = detect_trend(calculate_indicators(higher), float(higher.close.iloc[-1]))['trend']
            scoring['signal'] = confirm_direction(scoring['signal'], higher_trend, scoring['warnings'])
        if scoring["signal"] not in {"BUY", "STRONG BUY", "SELL", "STRONG SELL"}:
            continue
        direction = "LONG" if "BUY" in scoring["signal"] else "SHORT"
        entry = float(frame.open.iloc[index + 1])
        setup = calculate_trade_levels(direction, entry, indicators["atr"], levels["nearest_support"], levels["nearest_resistance"], settings.atr_multiplier, settings.risk_reward)
        stop, target = float(setup["stop_loss"]), float(setup["take_profit"])
        future = frame.iloc[index + 1:index + 1 + horizon_bars]
        outcome, r_multiple, bars_held = _outcome(direction, entry, stop, target, future, cost_bps)
        next_index = index + 1 + bars_held
        timestamp = history.time.iloc[-1] if "time" in history else history.index[-1]
        trades.append({
            "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp),
            "signal": scoring["signal"], "score": scoring["score"], "entry": entry,
            "stop_loss": stop, "take_profit": target, "outcome": outcome,
            "r_multiple": r_multiple, "bars_held": bars_held,
        })
        if len(trades) >= max_trades:
            break
    wins = [trade for trade in trades if trade["outcome"] == "WIN"]
    losses = [trade for trade in trades if trade["outcome"] == "LOSS"]
    returns = [trade["r_multiple"] for trade in trades]
    positive = sum(value for value in returns if value > 0)
    negative = abs(sum(value for value in returns if value < 0))
    equity = peak = drawdown = 0.0
    for value in returns:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    resolved = len(wins) + len(losses)
    return {
        "symbol": symbol.upper(), "timeframe": timeframe.upper(), "hypothetical": True,
        "candles": len(frame), "trades": len(trades), "wins": len(wins), "losses": len(losses),
        "timeouts": len(trades) - resolved, "win_rate_pct": round(len(wins) / resolved * 100, 2) if resolved else 0.0,
        "net_r": round(sum(returns), 3), "expectancy_r": round(sum(returns) / len(returns), 3) if returns else 0.0,
        "profit_factor": round(positive / negative, 3) if negative else None,
        "max_drawdown_r": round(drawdown, 3), "assumed_round_trip_cost_bps": cost_bps,
        "horizon_bars": horizon_bars, "recent_trades": trades[-20:],
        "evaluation": "chronological_holdout", "holdout_start_index": split,
        "higher_timeframe_data_present": higher_frame is not None,
        "non_overlapping": True,
        "warnings": [
            "Hypothetical backtest; it does not represent actual trading.",
            "Past results do not predict future performance.",
            "Holdout is not certified unseen if these historical dates were previously used to tune rules; prospective admin results are the independent check.",
            "Missing higher-timeframe warm-up skips signals, not confirmation. Zero trades is not proof of accuracy.",
            "Candle data cannot reveal intrabar execution order; simultaneous SL/TP is counted as a loss.",
            "Funding, taxes, market impact, latency, and changing liquidity are not modeled.",
        ],
    }
