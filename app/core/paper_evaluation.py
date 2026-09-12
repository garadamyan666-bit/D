"""Frozen, prospective paper protocol, not an execution or profit guarantee.

Entry is the next FULL minute's open; existing SL/TP are never moved.
One OHLC bar touching both levels is ambiguous, not a fabricated win.
Costs are an explicit 25bps round-trip assumption (fees plus slippage).
"""
import math

VERSION = 'confirmed-v1'
CANDIDATE = 'cost-filter-v2'
COST_BPS = 25.0


def snapshot(item):
    stop, target, entry = item.get('stop_loss'), item.get('take_profit'), item['current_price']
    if item['signal'] == 'WAIT' or not stop or not target:
        return None
    reward = abs(target - entry) / entry * 10000
    risk = abs(entry - stop)
    # Fixed before future outcomes are known; shadow-only, not auto-promoted.
    accepted = reward >= 3 * COST_BPS and risk > 0 and abs(target - entry) / risk >= 1.5
    return {'version': VERSION, 'candidate': CANDIDATE, 'candidate_accepted': accepted,
            'stop': stop, 'target': target, 'cost_bps': COST_BPS, 'paper_status': 'PENDING'}


def evaluate(signal, frozen, candles):
    entry = float(candles[0][1])
    stop, target = frozen['stop'], frozen['target']
    long = 'BUY' in signal
    if not all(math.isfinite(v) and v > 0 for v in (entry, stop, target)):
        raise ValueError('Invalid paper prices')
    if not (stop < entry < target if long else target < entry < stop):
        return {'paper_status': 'ENTRY_OUTSIDE_LEVELS', 'paper_entry': entry}
    exit_price, status = float(candles[-1][4]), 'HORIZON'
    for candle in candles:
        opened, high, low, close = map(float, candle[1:5])
        if not all(math.isfinite(v) and v > 0 for v in (opened, high, low, close)) or not low <= min(opened, close) <= max(opened, close) <= high:
            raise ValueError('Invalid OHLC')
        # Gaps through a stop fill at the open, not the better stop price.
        if (opened <= stop if long else opened >= stop):
            exit_price, status = opened, 'SL'
            break
        if (opened >= target if long else opened <= target):
            exit_price, status = target, 'TP'
            break
        sl = low <= stop if long else high >= stop
        tp = high >= target if long else low <= target
        if sl and tp:
            return {'paper_status': 'AMBIGUOUS', 'paper_entry': entry}
        if sl or tp:
            exit_price, status = (stop, 'SL') if sl else (target, 'TP')
            break
    gross = (exit_price / entry - 1) * (1 if long else -1) * 100
    net = gross - frozen['cost_bps'] / 100
    return {'paper_status': status, 'paper_entry': entry, 'paper_exit': exit_price,
            'net_pct': round(net, 6), 'profitable': net > 0}
