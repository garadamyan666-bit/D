"""Forward evaluation of saved Binance forecasts at a fixed, recorded horizon."""
from datetime import datetime, timedelta, timezone
import logging
import math
from sqlalchemy import select
from app.core.binance_client import BinanceClient
from app.database.database import session_scope
from app.database.models import ForecastCheck

MINUTES = {'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30, 'H1': 60, 'H4': 240, 'D1': 1440}
MIN_MEANINGFUL_MOVE_PCT = 0.02
client = BinanceClient(timeout=8)
logger = logging.getLogger(__name__)


def make_check(item, now, user_id=None):
    if item.get('market_source') != 'BINANCE' or item['timeframe'] not in MINUTES:
        return None
    # First minute boundary at or after the full forecast horizon has elapsed.
    target = now + timedelta(minutes=MINUTES[item['timeframe']])
    end_ms = (math.floor(target.timestamp() / 60) + 1) * 60000 - 1
    return ForecastCheck(user_id=user_id, symbol=item['symbol'], timeframe=item['timeframe'],
        signal=item['signal'], confidence=item['confidence'], start_price=item['current_price'],
        issued_at=now, target_ms=end_ms,
        status='EXCLUDED' if item['signal'] == 'WAIT' else 'PENDING')


def result_for(signal, start, end):
    if not all(math.isfinite(x) and x > 0 for x in (start, end)):
        raise ValueError('Invalid price')
    change = (end / start - 1) * 100
    directed = change if 'BUY' in signal else -change
    return change, ('FLAT' if abs(change) < MIN_MEANINGFUL_MOVE_PCT else 'CORRECT' if directed > 0 else 'INCORRECT')


def verify_pending():
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    with session_scope() as session:
        rows = session.scalars(select(ForecastCheck).where(ForecastCheck.status == 'PENDING',
            ForecastCheck.target_ms < now_ms - 2000).order_by(ForecastCheck.id).limit(30)).all()
        work = [(r.id, r.symbol, r.target_ms) for r in rows]
    cache = {}
    for row_id, symbol, end_ms in work:
        try:
            key = (symbol, end_ms)
            if key not in cache:
                candles = client._get('/api/v3/klines', {'symbol': symbol, 'interval': '1m',
                    'startTime': end_ms - 59999, 'endTime': end_ms, 'limit': 1})
                if not candles or int(candles[0][0]) != end_ms - 59999 or int(candles[0][6]) != end_ms:
                    raise ValueError('Target closed candle unavailable')
                cache[key] = float(candles[0][4])
            with session_scope() as session:
                row = session.get(ForecastCheck, row_id)
                if row is None or row.status != 'PENDING':
                    continue
                row.change_pct, row.status = result_for(row.signal, row.start_price, cache[key])
                row.end_price = cache[key]
                row.checked_at = datetime.now(timezone.utc)
                row.error = None
        except Exception:
            logger.warning('Forecast verification unavailable for record %s; will retry', row_id)
            with session_scope() as session:
                row = session.get(ForecastCheck, row_id)
                if row:
                    row.error = 'Binance տվյալները անհասանելի են․ կփորձենք կրկին։'
