from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.verification import make_check, result_for


def test_horizon_never_before_full_timeframe():
    now = datetime(2026, 9, 6, 12, 0, 25, tzinfo=timezone.utc)
    item = dict(market_source='BINANCE', symbol='BTCUSDT', timeframe='M15', signal='BUY', confidence=70, current_price=100)
    row = make_check(item, now)
    assert row.target_ms == int(datetime(2026,9,6,12,16,tzinfo=timezone.utc).timestamp()*1000)-1
    assert row.status == 'PENDING'
    item['signal'] = 'WAIT'
    assert make_check(item, now).status == 'EXCLUDED'
    item['market_source'] = 'OTHER'
    assert make_check(item, now) is None


def test_direction_and_flat():
    assert result_for('BUY',100,101)[1] == 'CORRECT'
    assert result_for('STRONG SELL',100,101)[1] == 'INCORRECT'
    assert result_for('SELL',100,99)[1] == 'CORRECT'
    assert result_for('BUY',100,100)[1] == 'FLAT'
    assert result_for('BUY',100,100.01)[1] == 'FLAT'
    with pytest.raises(ValueError):
        result_for('BUY',0,100)


def test_admin_routes_require_authentication(monkeypatch):
    monkeypatch.setattr('app.main.scheduler.start', lambda: None)
    monkeypatch.setattr('app.main.scheduler.stop', lambda: None)
    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get('/admin', follow_redirects=False).status_code == 303
        assert client.get('/admin/login', follow_redirects=False).status_code == 303
        assert client.get('/api/admin/verification').status_code == 401
        assert client.get('/static/admin/index.html').status_code == 404


def test_verification_persists_and_retries(tmp_path, monkeypatch):
    from contextlib import contextmanager
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.database.models import ForecastCheck
    import app.services.verification as service
    engine = create_engine('sqlite:///' + str(tmp_path / 'checks.db'))
    ForecastCheck.__table__.create(engine)
    @contextmanager
    def scope():
        with Session(engine) as s:
            yield s
            s.commit()
    monkeypatch.setattr(service, 'session_scope', scope)
    item = dict(market_source='BINANCE',symbol='BTCUSDT',timeframe='M1',signal='BUY',confidence=80,current_price=100)
    with scope() as s:
        row = make_check(item,datetime(2026,1,1,tzinfo=timezone.utc))
        end = row.target_ms
        s.add(row)
    monkeypatch.setattr(service.client,'_get',lambda *a,**kw: [])
    service.verify_pending()
    with scope() as s:
        assert s.get(ForecastCheck,1).status == 'PENDING'
        assert s.get(ForecastCheck,1).error
    monkeypatch.setattr(service.client,'_get',lambda *a,**kw: [[end-59999,0,0,0,'101',0,end]])
    service.verify_pending()
    with scope() as s:
        row=s.get(ForecastCheck,1)
        assert row.status == 'CORRECT' and row.end_price == 101 and row.error is None
    monkeypatch.setattr(service.client,'_get',lambda *a,**kw: pytest.fail('Already evaluated'))
    service.verify_pending()


def test_admin_role_check():
    import app.api.admin as module
    from fastapi import HTTPException
    from app.database.models import User
    admin = User(username='admin-test', password_hash='unused', is_admin=True)
    ordinary = User(username='ordinary-test', password_hash='unused', is_admin=False)
    assert module.require_admin(admin) is admin
    with pytest.raises(HTTPException):
        module.require_admin(ordinary)
    with TestClient(app) as client:
        assert client.get('/api/admin/verification').status_code == 401
        assert client.delete('/api/admin/verification?confirm=RESET').status_code == 401


def test_admin_can_reset_verification_history():
    from sqlalchemy import select
    from app.database.database import session_scope
    from app.database.models import ForecastCheck, User
    with TestClient(app) as client:
        credentials = {'username': 'reset-admin', 'password': 'safe-password-123'}
        assert client.post('/api/auth/register', json=credentials).status_code in {200, 409}
        with session_scope() as session:
            user = session.scalar(select(User).where(User.username == 'reset-admin'))
            user.is_admin = True
            session.add(make_check(dict(market_source='BINANCE', symbol='BTCUSDT', timeframe='M1', signal='BUY', confidence=70, current_price=100), datetime.now(timezone.utc), user.id))
        assert client.delete('/api/admin/verification').status_code == 400
        response = client.delete('/api/admin/verification?confirm=RESET')
        assert response.status_code == 200 and response.json()['deleted'] >= 1
        assert client.get('/api/admin/verification').json()['rows'] == []
