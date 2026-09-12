"""Read-only Binance Spot public market-data adapter.

No API key is used and no account or order endpoint is implemented.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import requests
import time
import copy
from threading import RLock

from app.config import settings


class BinanceError(RuntimeError):
    """Raised when Binance public market data cannot be retrieved."""


TIMEFRAMES = {
    "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
    "H1": "1h", "H4": "4h", "D1": "1d",
}


class BinanceClient:
    """Small failover client for Binance Spot public REST endpoints."""
    _lock = RLock()
    _cache = {}
    _blocked_until = 0.0
    _last_request = 0.0

    @staticmethod
    def _saved_pause(value=None):
        # Persist the exchange's deadline across worker restarts. One worker is
        # configured in render.yaml; this is not a distributed rate limiter.
        from app.database.database import session_scope
        from app.database.models import AppSetting
        try:
            with session_scope() as session:
                row = session.get(AppSetting, 'binance_pause_until')
                if value is not None:
                    session.merge(AppSetting(key='binance_pause_until', value=str(max(value, float(row.value) if row else 0))))
                return float(row.value) if row else 0
        except Exception:
            return 0

    @classmethod
    def retry_after_seconds(cls):
        return max(0, int(cls._blocked_until - time.time()) + 1) if cls._blocked_until else 0

    def __init__(self, base_urls: list[str] | None = None, timeout: float = 12) -> None:
        self.base_urls = base_urls or settings.binance_base_urls
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "TradeAnalysisBot/1.0 (market-data-only)"})

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if settings.active_workspace == 'POCKET_OPTION' or not settings.binance_enabled:
            raise BinanceError('Binance is paused while Pocket Option workspace is active')
        with self._lock:
            BinanceClient._blocked_until = max(BinanceClient._blocked_until, self._saved_pause())
            if self.retry_after_seconds():
                raise BinanceError(f"Binance temporarily paused; retry in {self.retry_after_seconds()} seconds")
            key = (tuple(self.base_urls), path, tuple(sorted((params or {}).items())))
            cached = self._cache.get(key)
            if cached and cached[0] > time.time():
                return copy.deepcopy(cached[1])
            delay = 0.25 - (time.monotonic() - BinanceClient._last_request)
            if delay > 0:
                time.sleep(delay)
            BinanceClient._last_request = time.monotonic()
            payload = self._request(path, params)
            ttl = 3600 if path.endswith('exchangeInfo') else 30 if path.endswith(('klines', 'ping')) else 5
            self._cache[key] = (time.time() + ttl, copy.deepcopy(payload))
            if len(self._cache) > 512:
                self._cache.pop(next(iter(self._cache)))
            return payload

    def _request(self, path, params):
        errors: list[str] = []
        for base_url in self.base_urls:
            try:
                response = self.session.get(f"{base_url}{path}", params=params, timeout=self.timeout)
                if response.status_code in (418, 429):
                    try:
                        wait = max(1, int(response.headers.get('Retry-After', '300')))
                    except (ValueError, TypeError, AttributeError):
                        wait = 300
                    BinanceClient._blocked_until = time.time() + wait
                    self._saved_pause(BinanceClient._blocked_until)
                    break
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict) and "code" in payload and int(payload["code"]) < 0:
                    raise BinanceError(str(payload.get("msg", payload)))
                return payload
            except (requests.RequestException, ValueError, BinanceError) as exc:
                errors.append(f"{base_url}: {exc}")
        if self.retry_after_seconds():
            raise BinanceError(f"Binance temporarily paused; retry in {self.retry_after_seconds()} seconds")
        raise BinanceError("Binance market data is unavailable: " + " | ".join(errors))

    def is_connected(self) -> bool:
        try:
            self._get('/api/v3/ping')
            return True
        except BinanceError:
            return False

    def get_symbols(self) -> list[str]:
        payload = self._get("/api/v3/exchangeInfo", {"permissions": "SPOT"})
        return [item["symbol"] for item in payload.get("symbols", []) if item.get("status") == "TRADING"]

    def resolve_symbol(self, configured: str) -> str:
        symbol = configured.upper().replace("/", "").replace("-", "")
        if symbol not in settings.binance_symbols:
            raise BinanceError(f"Binance symbol '{symbol}' is not configured")
        return symbol

    def get_candles(self, symbol: str, timeframe: str, count: int = 300) -> pd.DataFrame:
        key = timeframe.upper()
        if key not in TIMEFRAMES:
            raise ValueError(f"Unsupported Binance timeframe: {timeframe}")
        resolved = self.resolve_symbol(symbol)
        payload = self._get("/api/v3/klines", {"symbol": resolved, "interval": TIMEFRAMES[key], "limit": min(max(count, 1), 1000)})
        if not isinstance(payload, list) or not payload:
            raise BinanceError(f"No Binance candles returned for {resolved} {key}")
        columns = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"]
        frame = pd.DataFrame(payload, columns=columns)
        for column in ("open", "high", "low", "close", "volume", "quote_volume"):
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame["time"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
        frame.attrs["resolved_symbol"] = resolved
        return frame

    def get_current_price(self, symbol: str) -> float:
        resolved = self.resolve_symbol(symbol)
        payload = self._get("/api/v3/ticker/price", {"symbol": resolved})
        try:
            return float(payload["price"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BinanceError(f"Invalid current-price response for {resolved}") from exc

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        resolved = self.resolve_symbol(symbol)
        payload = self._get("/api/v3/exchangeInfo", {"symbol": resolved})
        items = payload.get("symbols", [])
        if not items:
            raise BinanceError(f"No Binance symbol information for {resolved}")
        return items[0]

    def get_order_book(self, symbol: str, limit: int = 100) -> dict[str, Any]:
        """Return public bid/ask depth. Open orders may be cancelled at any time."""
        resolved = self.resolve_symbol(symbol)
        allowed_limits = (5, 10, 20, 50, 100, 500, 1000, 5000)
        selected_limit = min(allowed_limits, key=lambda value: abs(value - limit))
        payload = self._get("/api/v3/depth", {"symbol": resolved, "limit": selected_limit})
        if not isinstance(payload, dict) or "bids" not in payload or "asks" not in payload:
            raise BinanceError(f"Invalid order-book response for {resolved}")
        return payload

    def get_24h_ticker(self, symbol: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        """Return public rolling 24-hour price and volume statistics."""
        params = {"symbol": self.resolve_symbol(symbol)} if symbol else None
        payload = self._get("/api/v3/ticker/24hr", params)
        if not isinstance(payload, (dict, list)):
            raise BinanceError("Invalid Binance 24-hour ticker response")
        return payload

    def get_aggregate_trades(self, symbol: str, limit: int = 500) -> list[dict[str, Any]]:
        """Return recent public aggregate trades; buyer identities are not exposed."""
        resolved = self.resolve_symbol(symbol)
        payload = self._get("/api/v3/aggTrades", {"symbol": resolved, "limit": min(max(limit, 1), 1000)})
        if not isinstance(payload, list):
            raise BinanceError(f"Invalid aggregate-trades response for {resolved}")
        return payload


binance_client = BinanceClient()
