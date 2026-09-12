from app.core.paper_evaluation import evaluate, snapshot
from app.api.admin import comparison
from app.services.verification import make_check
from datetime import datetime, timezone
import json
import pytest

def test_costs_and_ambiguous_path():
    frozen = {'stop': 99, 'target': 102, 'cost_bps': 25}
    assert evaluate('BUY', frozen, [[0, 100, 101, 99.5, 100.1]])['net_pct'] == pytest.approx(-0.15)
    assert evaluate('BUY', frozen, [[0, 100, 103, 98, 100]])['paper_status'] == 'AMBIGUOUS'
    assert evaluate('BUY', frozen, [[0, 100, 103, 99.5, 102]])['net_pct'] == pytest.approx(1.75)
    assert evaluate('BUY', frozen, [[0, 98, 99, 97, 98]])['paper_status'] == 'ENTRY_OUTSIDE_LEVELS'
    assert evaluate('SELL', {'stop':101,'target':98,'cost_bps':25}, [[0,100,100.5,97,98]])['net_pct'] == pytest.approx(1.75)

def test_snapshot_and_nonoverlapping_holdout():
    item = dict(market_source='BINANCE', symbol='BTCUSDT', timeframe='M15', signal='BUY', confidence=80, current_price=100, stop_loss=99, take_profit=102)
    rows = []
    for minute in (0, 1, 17):
        row = make_check(item, datetime(2026,1,1,0,minute,tzinfo=timezone.utc))
        frozen = json.loads(row.evaluation)
        assert frozen['candidate_accepted']
        frozen['net_pct'] = 1
        row.evaluation = json.dumps(frozen)
        rows.append(row)
    assert all(r['samples'] == 2 for r in comparison(rows))
    assert not snapshot({**item, 'signal':'WAIT'})

def test_invalid_ohlc_rejected():
    with pytest.raises(ValueError):
        evaluate('BUY', {'stop':99,'target':102,'cost_bps':25}, [[0,100,99,101,100]])
