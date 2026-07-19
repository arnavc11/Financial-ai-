"""
Stocks service — single source of truth for live NSE stock/index data.

Design goals:
  - No hardcoded prices. Every number comes from a live fetch.
  - Resilient: retries with backoff, short timeouts, and an in-memory
    TTL cache. If a fresh fetch fails, we serve the last known-good
    cached value (marked "stale") instead of showing nothing.
  - Every function returns a consistent shape with a "status" field
    so the frontend can render loading / ok / stale / error states.
"""

import asyncio
import time
from typing import Optional

import httpx

# ── Symbol registry (the only place tickers are defined) ────────────
NIFTY50_SYMBOLS = {
    "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS", "INFY": "INFY.NS",
    "ICICIBANK": "ICICIBANK.NS", "HINDUNILVR": "HINDUNILVR.NS",
    "ITC": "ITC.NS", "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS", "KOTAKBANK": "KOTAKBANK.NS",
    "WIPRO": "WIPRO.NS", "LT": "LT.NS",
    "AXISBANK": "AXISBANK.NS", "MARUTI": "MARUTI.NS",
    "SUNPHARMA": "SUNPHARMA.NS", "BAJFINANCE": "BAJFINANCE.NS",
    "TITAN": "TITAN.NS", "NESTLEIND": "NESTLEIND.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS", "POWERGRID": "POWERGRID.NS",
    "TATAMOTORS": "TATAMOTORS.NS", "ONGC": "ONGC.NS",
    "NTPC": "NTPC.NS", "ADANIPORTS": "ADANIPORTS.NS",
}

INDICES = {
    "NIFTY50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANKNIFTY": "^NSEBANK",
}

# Default watchlist shown in the sidebar
DEFAULT_WATCHLIST = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "SBIN", "WIPRO"]

_YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FinAI/1.0)"}


# ── Tiny in-memory TTL cache with stale fallback ─────────────────────
class _TTLCache:
    def __init__(self):
        self._store: dict[str, tuple[float, dict]] = {}

    def get_fresh(self, key: str, ttl: float) -> Optional[dict]:
        entry = self._store.get(key)
        if entry and (time.time() - entry[0]) < ttl:
            return entry[1]
        return None

    def get_stale(self, key: str) -> Optional[dict]:
        entry = self._store.get(key)
        return entry[1] if entry else None

    def set(self, key: str, value: dict):
        self._store[key] = (time.time(), value)


_cache = _TTLCache()

QUOTE_TTL = 60      # seconds
INDEX_TTL = 30       # seconds


def resolve_symbol(symbol: str, exchange: str = "NSE") -> str:
    symbol = symbol.upper()
    if symbol in NIFTY50_SYMBOLS:
        return NIFTY50_SYMBOLS[symbol]
    suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
    return f"{symbol}{suffix}"


async def _fetch_chart(yf_symbol: str, range_: str = "5d", retries: int = 2) -> dict:
    """Fetch raw chart data from Yahoo Finance with retry + backoff."""
    last_error: Optional[Exception] = None
    async with httpx.AsyncClient(timeout=6, headers=_HEADERS) as client:
        for attempt in range(retries + 1):
            try:
                resp = await client.get(
                    _YAHOO_CHART_URL.format(symbol=yf_symbol),
                    params={"interval": "1d", "range": range_},
                )
                resp.raise_for_status()
                payload = resp.json()
                result = payload.get("chart", {}).get("result")
                if not result:
                    raise ValueError(f"No data returned for {yf_symbol}")
                return result[0]
            except Exception as e:
                last_error = e
                if attempt < retries:
                    await asyncio.sleep(0.4 * (attempt + 1))  # backoff
    raise RuntimeError(f"Failed to fetch {yf_symbol}: {last_error}")


def _extract_quote(chart_result: dict) -> dict:
    closes = [c for c in chart_result["indicators"]["quote"][0]["close"] if c is not None]
    if len(closes) < 1:
        raise ValueError("No close price data available")
    current = closes[-1]
    prev = closes[-2] if len(closes) > 1 else chart_result["meta"].get("previousClose", current)
    change = current - prev
    change_pct = (change / prev * 100) if prev else 0
    meta = chart_result.get("meta", {})
    return {
        "current_price": round(current, 2),
        "prev_close": round(prev, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "direction": "up" if change >= 0 else "down",
        "52w_high": round(meta.get("fiftyTwoWeekHigh", 0), 2),
        "52w_low": round(meta.get("fiftyTwoWeekLow", 0), 2),
        "currency": meta.get("currency", "INR"),
    }


async def get_quote(symbol: str, exchange: str = "NSE") -> dict:
    symbol = symbol.upper()
    yf_symbol = resolve_symbol(symbol, exchange)
    cache_key = f"quote:{yf_symbol}"

    fresh = _cache.get_fresh(cache_key, QUOTE_TTL)
    if fresh:
        return {**fresh, "status": "ok"}

    try:
        chart = await _fetch_chart(yf_symbol, range_="5d")
        data = _extract_quote(chart)
        result = {
            "symbol": symbol,
            "exchange": exchange.upper(),
            "formatted_price": f"₹{data['current_price']:,.2f}",
            **data,
            "timestamp": time.time(),
        }
        _cache.set(cache_key, result)
        return {**result, "status": "ok"}
    except Exception as e:
        stale = _cache.get_stale(cache_key)
        if stale:
            return {**stale, "status": "stale", "error": str(e)}
        return {
            "symbol": symbol,
            "exchange": exchange.upper(),
            "status": "error",
            "error": f"Could not fetch live price for {symbol}: {e}",
        }


async def get_index(name: str) -> dict:
    name = name.upper()
    yf_symbol = INDICES.get(name)
    if not yf_symbol:
        return {"name": name, "status": "error", "error": f"Unknown index {name}"}

    cache_key = f"index:{yf_symbol}"
    fresh = _cache.get_fresh(cache_key, INDEX_TTL)
    if fresh:
        return {**fresh, "status": "ok"}

    try:
        chart = await _fetch_chart(yf_symbol, range_="2d")
        data = _extract_quote(chart)
        result = {
            "name": name,
            "value": data["current_price"],
            "formatted": f"{data['current_price']:,.2f}",
            "change_pct": data["change_pct"],
            "direction": data["direction"],
            "timestamp": time.time(),
        }
        _cache.set(cache_key, result)
        return {**result, "status": "ok"}
    except Exception as e:
        stale = _cache.get_stale(cache_key)
        if stale:
            return {**stale, "status": "stale", "error": str(e)}
        return {"name": name, "status": "error", "error": f"Could not fetch {name}: {e}"}


async def get_indices() -> dict:
    names = list(INDICES.keys())
    results = await asyncio.gather(*(get_index(n) for n in names))
    return {name: result for name, result in zip(names, results)}


async def get_watchlist(symbols: Optional[list[str]] = None) -> dict:
    symbols = symbols or DEFAULT_WATCHLIST
    results = await asyncio.gather(*(get_quote(s) for s in symbols))
    return {sym: result for sym, result in zip(symbols, results)}
