from fastapi.testclient import TestClient

from app.main import app


def _offline_connections(monkeypatch):
    monkeypatch.setattr("app.api.routes.binance_client.is_connected", lambda: False)


def _login(client, username="api-user"):
    response = client.post("/api/auth/register", json={"username": username, "password": "safe-password-123"})
    if response.status_code == 409:
        response = client.post("/api/auth/login", json={"username": username, "password": "safe-password-123"})
    assert response.status_code == 200


def test_health_and_dashboard(monkeypatch):
    _offline_connections(monkeypatch)
    with TestClient(app) as client:
        assert client.get("/", follow_redirects=False).status_code == 303
        _login(client)
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["analysis_only"] is True
        alert_status = client.get("/api/alerts/status")
        assert alert_status.status_code == 200
        assert "telegram_configured" in alert_status.json()
        assert client.get("/api/symbols").json()["timeframes"] == ["M15", "H1"]
        dashboard = client.get("/")
        assert dashboard.status_code == 200
        assert "ՄԻԱՅՆ ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ" in dashboard.text


def test_invalid_symbol_and_timeframe_are_clear(monkeypatch):
    _offline_connections(monkeypatch)
    with TestClient(app) as client:
        _login(client)
        assert client.get("/api/analyze/NOTREAL/M15").status_code == 404
        assert client.get("/api/analyze/BTCUSDT/M1").status_code == 400
        response = client.get("/api/analyze/BTCUSDT/W1")
        assert response.status_code == 400
        assert "Unsupported timeframe" in response.json()["detail"]


def test_empty_stats_and_signals_work(monkeypatch):
    _offline_connections(monkeypatch)
    with TestClient(app) as client:
        _login(client)
        assert client.get("/api/signals").status_code == 200
        assert client.get("/api/stats").status_code == 200


def test_frontend_assets_and_source_selector(monkeypatch):
    _offline_connections(monkeypatch)
    with TestClient(app) as client:
        _login(client)
        page = client.get("/")
        css = client.get("/static/css/style.css?v=test")
        javascript = client.get("/static/js/app.js?v=test")
        assert client.get("/static/index.html").status_code == 404
        assert client.get("/static/account.html").status_code == 404
        assert client.get("/taxes").status_code == 404
        assert 'id="source"' in page.text
        assert 'id="saveAlert"' in page.text
        assert 'data-lang="hy"' in page.text
        assert 'data-lang="ru"' in page.text
        assert 'data-lang="en"' in page.text
        assert "style.css?v=" in page.text and "app.js?v=" in page.text
        assert css.status_code == 200 and css.headers["content-type"].startswith("text/css")
        assert javascript.status_code == 200 and "sourceSymbols" in javascript.text
        assert "loadAlerts" in javascript.text
        assert 'id="chartImage"' in page.text
        assert client.get("/static/js/chart-analysis.js").status_code == 200
        manifest = client.get("/manifest.webmanifest")
        worker = client.get("/sw.js")
        assert manifest.status_code == 200 and manifest.json()["display"] == "standalone"
        assert worker.status_code == 200 and worker.headers["service-worker-allowed"] == "/"
        assert "no-store" in css.headers["cache-control"]


def test_accounts_are_isolated(monkeypatch):
    _offline_connections(monkeypatch)
    with TestClient(app) as first, TestClient(app) as second:
        _login(first, "isolated-one")
        _login(second, "isolated-two")
        created = first.post("/api/alerts", json={"source": "BINANCE", "symbol": "BTCUSDT", "timeframe": "M15", "min_confidence": 99})
        assert created.status_code == 200
        assert len(first.get("/api/alerts").json()) == 1
        assert second.get("/api/alerts").json() == []
