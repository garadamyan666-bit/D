# Evaluation protocol

All results are paper analysis, never orders. Confidence is a rule score,
not a calibrated win probability. No target accuracy is promised.

## Prospective admin comparison

New signals freeze their stop, target, 25 bps assumed round-trip fee/slippage,
and two version labels before future candles arrive. `confirmed-v1` is the
existing strategy. `cost-filter-v2` is shadow-only: reward must cover three
times assumed costs and reward/risk must be at least 1.5. No automatic
promotion or live signal changes occur.

The paper entry is the next full one-minute candle open. Stop and target
remain fixed. Invalid entry levels skip the trade; missing bars retry.
Both levels touched in one bar is ambiguous and excluded from net metrics.
The horizon close supplies the exit if neither level is hit. Stop gaps use
the opening price. Direction accuracy uses the original price separately.
Short results are hypothetical and do not imply Spot shorting is available.

Admin comparison is grouped by symbol, timeframe and version, ordered by
issue time, excluding overlapping horizons and duplicate user copies.
It reports sample count, profitable share and mean net percentage, not
portfolio returns. Fewer than 100 samples is explicitly insufficient;
100 samples alone does not prove an edge. Inspect exclusions as well.
Old rows without frozen levels are not backfilled with invented values.

## Historical diagnostic

Only the last 30% is scored; previous bars are indicator warm-up. M15/H1
must have already-closed H1/H4 confirmation data. Positions do not overlap.
This is not certified unseen if prior tuning used those dates. Its bar
horizon, next-bar execution and conservative same-bar stop-first assumption
differ from the prospective minute-resolution protocol; do not pool them.

## Hosting and exchange limits

One Render worker shares a bounded market-data cache and request pacing.
418/429 stops all fallback endpoints until Retry-After (300s if missing),
with the deadline saved in the database across restarts. Other programs on
the same outbound IP are outside this limiter's control. Never rotate IPs
to bypass exchange restrictions. The pause is not a guaranteed recovery ETA.
Multiple workers require a distributed limiter before scaling.

Render free hosting sleeps; it cannot guarantee continuous Telegram checks.
Changing the paid web/database plan requires owner approval. No keep-awake
workaround is configured.
