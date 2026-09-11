"""Theoretical risk and position sizing; never executes orders."""
from __future__ import annotations


def calculate_trade_levels(direction: str, entry: float, atr: float, support: float | None = None, resistance: float | None = None, atr_multiplier: float = 1.5, risk_reward: float = 2.0) -> dict[str, float | None]:
    if entry <= 0 or atr <= 0 or atr_multiplier <= 0 or risk_reward <= 0:
        raise ValueError("Entry, ATR, ATR multiplier, and risk/reward must be positive")
    if direction not in {"LONG", "SHORT"}:
        return {"entry": entry, "stop_loss": None, "take_profit": None, "risk_reward": risk_reward}
    atr_distance = atr * atr_multiplier
    if direction == "LONG":
        stop = min(entry - atr_distance, support - atr * 0.15) if support and support < entry else entry - atr_distance
        risk = entry - stop
        target = entry + risk * risk_reward
        if resistance and resistance > entry and resistance >= entry + risk:
            target = min(target, resistance - atr * 0.1)
    else:
        stop = max(entry + atr_distance, resistance + atr * 0.15) if resistance and resistance > entry else entry + atr_distance
        risk = stop - entry
        target = entry - risk * risk_reward
        if support and support < entry and support <= entry - risk:
            target = max(target, support + atr * 0.1)
    actual_rr = abs(target - entry) / risk
    return {"entry": entry, "stop_loss": stop, "take_profit": target, "risk_reward": round(actual_rr, 2)}


def calculate_risk(account_balance: float, risk_percent: float, entry: float, stop_loss: float | None, take_profit: float | None, max_daily_risk: float | None = None, value_per_price_unit: float = 1.0) -> dict[str, float]:
    if account_balance <= 0 or not 0 < risk_percent <= 100:
        raise ValueError("Account balance must be positive and risk percent must be between 0 and 100")
    risk_amount = account_balance * risk_percent / 100
    if max_daily_risk is not None:
        risk_amount = min(risk_amount, max_daily_risk)
    stop_distance = abs(entry - stop_loss) if stop_loss is not None else 0.0
    position_size = risk_amount / (stop_distance * value_per_price_unit) if stop_distance > 0 else 0.0
    profit_distance = abs(take_profit - entry) if take_profit is not None else 0.0
    return {"risk_amount": risk_amount, "position_size": position_size, "stop_distance": stop_distance, "potential_profit": position_size * profit_distance * value_per_price_unit, "potential_loss": risk_amount if stop_distance else 0.0}
