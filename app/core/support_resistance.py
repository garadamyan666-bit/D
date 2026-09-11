"""Swing-based support and resistance detection."""
from __future__ import annotations

import pandas as pd


def _cluster(levels: list[float], tolerance: float, limit: int, reverse: bool = False) -> list[float]:
    clusters: list[list[float]] = []
    for level in sorted(levels):
        target = next((group for group in clusters if abs(level - sum(group) / len(group)) <= tolerance), None)
        (target if target is not None else clusters.append([level]))
        if target is not None:
            target.append(level)
    ranked = sorted(clusters, key=lambda group: (len(group), max(group) if reverse else -min(group)), reverse=True)
    return sorted([sum(group) / len(group) for group in ranked[:limit]], reverse=reverse)


def find_levels(frame: pd.DataFrame, current_price: float, window: int = 3, max_levels: int = 5) -> dict:
    recent = frame.tail(200).reset_index(drop=True)
    highs, lows = [], []
    for index in range(window, len(recent) - window):
        if recent.high.iloc[index] >= recent.high.iloc[index-window:index+window+1].max():
            highs.append(float(recent.high.iloc[index]))
        if recent.low.iloc[index] <= recent.low.iloc[index-window:index+window+1].min():
            lows.append(float(recent.low.iloc[index]))
    tolerance = max(float((recent.high - recent.low).tail(14).mean()) * 0.5, abs(current_price) * 0.0001)
    supports = [level for level in _cluster(lows, tolerance, max_levels) if level < current_price]
    resistances = [level for level in _cluster(highs, tolerance, max_levels, True) if level > current_price]
    nearest_support = max(supports, default=None)
    nearest_resistance = min(resistances, default=None)
    return {
        "support_levels": supports, "resistance_levels": sorted(resistances),
        "nearest_support": nearest_support, "nearest_resistance": nearest_resistance,
        "support_distance": current_price - nearest_support if nearest_support else None,
        "resistance_distance": nearest_resistance - current_price if nearest_resistance else None,
    }
