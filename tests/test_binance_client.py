import pytest

from app.core.binance_client import BinanceClient, BinanceError


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch):
    monkeypatch.setattr(BinanceClient, '_cache', {})
    monkeypatch.setattr(BinanceClient, '_blocked_until', 0)
    monkeypatch.setattr(BinanceClient, '_last_request', 0)
    monkeypatch.setattr(BinanceClient, '_saved_pause', staticmethod(lambda value=None: 0))


@pytest.mark.parametrize('status', [418, 429])
def test_exchange_pause_stops_all_clients_and_failover(monkeypatch, status):
    calls = []
    def request(*args, **kwargs):
        calls.append(args)
        response = FakeResponse({}, status)
        response.headers = {'Retry-After': '120'}
        return response
    first = BinanceClient(['https://one.test', 'https://two.test'])
    monkeypatch.setattr(first.session, 'get', request)
    with pytest.raises(BinanceError, match='paused'):
        first._get('/api/v3/ping')
    second = BinanceClient(['https://three.test'])
    monkeypatch.setattr(second.session, 'get', lambda *a, **k: pytest.fail('Must not retry'))
    with pytest.raises(BinanceError, match='paused'):
        second._get('/api/v3/ping')
    assert len(calls) == 1
    assert 119 <= first.retry_after_seconds() <= 121


def test_cache_shared_and_copied(monkeypatch):
    first = BinanceClient(['https://cache.test'])
    monkeypatch.setattr(first.session, 'get', lambda *a, **k: FakeResponse({'price':'100'}))
    first._get('/api/v3/ticker/price')['price'] = 'wrong'
    second = BinanceClient(['https://cache.test'])
    monkeypatch.setattr(second.session, 'get', lambda *a, **k: pytest.fail('Cache expected'))
    assert second._get('/api/v3/ticker/price')['price'] == '100'


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        key = (url.rsplit("/api", 1)[-1], tuple(sorted((params or {}).items())))
        return FakeResponse(self.responses[key])


def make_kline(index):
    price = 100 + index * 0.1
    return [index * 60_000, str(price), str(price + 1), str(price - 1), str(price + .5), str(1000 + index), index * 60_000 + 59_999, "100000", 10, "500", "50000", "0"]


def test_binance_candles_and_price_are_normalized():
    responses = {
        ("/v3/klines", (("interval", "15m"), ("limit", 350), ("symbol", "BTCUSDT"))): [make_kline(i) for i in range(350)],
        ("/v3/ticker/price", (("symbol", "BTCUSDT"),)): {"symbol": "BTCUSDT", "price": "65432.10"},
    }
    client = BinanceClient(["https://example.test"])
    client.session = FakeSession(responses)
    candles = client.get_candles("BTCUSDT", "M15", 350)
    assert len(candles) == 350
    assert candles.attrs["resolved_symbol"] == "BTCUSDT"
    assert candles.close.dtype.kind == "f"
    assert client.get_current_price("BTCUSDT") == pytest.approx(65432.1)


def test_binance_rejects_unconfigured_symbol_and_timeframe():
    client = BinanceClient(["https://example.test"])
    with pytest.raises(BinanceError, match="not configured"):
        client.resolve_symbol("DOGEUSDT")
    with pytest.raises(ValueError, match="Unsupported Binance timeframe"):
        client.get_candles("BTCUSDT", "W1")
