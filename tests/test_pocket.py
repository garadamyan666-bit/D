from dataclasses import replace
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.config import settings
def _login(client, username):
    payload = {'username': username, 'password': 'safe-password-123'}
    response = client.post('/api/auth/register', json=payload)
    if response.status_code == 409:
        response = client.post('/api/auth/login', json=payload)
    assert response.status_code == 200


def test_pocket_workspace_pauses_binance_without_requests(monkeypatch):
    pocket = replace(settings, active_workspace='POCKET_OPTION')
    for module in ['app.main', 'app.api.routes', 'app.core.binance_client', 'app.services.alerts', 'app.config']:
        monkeypatch.setattr(module + '.settings', pocket)
    from app.core.binance_client import BinanceClient, BinanceError
    client = BinanceClient()
    monkeypatch.setattr(client.session, 'get', lambda *a, **k: pytest.fail('Binance must sleep'))
    with pytest.raises(BinanceError, match='paused'):
        client._get('/api/v3/ping')
    from app.services.alerts import scan_alert_subscriptions
    assert scan_alert_subscriptions() == []
    from app.services.verification import verify_pending
    assert verify_pending() is None
    with TestClient(app) as browser:
        _login(browser, 'pocket-test')
        assert 'pocket.js' in browser.get('/').text
        assert browser.get('/api/workspace').json()['binance_paused']
        assert browser.get('/api/health').json()['binance_connected'] is False


def test_chart_requires_consent_and_separates_expiry(monkeypatch):
    captured = []
    monkeypatch.setattr('app.api.routes.analyze_chart', lambda *args: captured.append(args) or 'WAIT')
    with TestClient(app) as browser:
        _login(browser, 'pocket-image')
        payload = dict(image_data='x'*120, symbol='EUR/USD', timeframe='M1', expiry_minutes=5, language='ru', market_type='OTC')
        assert browser.post('/api/chart-analysis', json=payload).status_code == 400
        payload['consent'] = True
        result = browser.post('/api/chart-analysis', json=payload)
        assert result.status_code == 200
        assert captured[0][2:] == ('M1', 5, 'ru', 'OTC')
        assert result.json()['live_data'] is False
        assert browser.post('/api/chart-analysis', json={**payload,'expiry_minutes':0}).status_code == 422
        assert browser.post('/api/chart-analysis', json={**payload,'language':'unknown'}).status_code == 422
