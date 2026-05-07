"""
Enhanced Stocks Router — REAL NSE Data (No broker account needed!)
Uses nsetools + nsepython + yfinance as fallback.
100% free, no API keys, no Zerodha/Angel One account required.

Install: pip install nsetools nsepython yfinance
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import yfinance as yf
from datetime import datetime
from backened.cache import cache

router = APIRouter()

try:
    from nsetools import Nse
    nse_client = Nse()
    NSE_TOOLS_AVAILABLE = True
    print("✅ nsetools loaded — real NSE data active")
except ImportError:
    NSE_TOOLS_AVAILABLE = False
    print("⚠️  nsetools not installed. Run: pip install nsetools")

try:
    from nsepython import nsefetch, nse_eq, nse_index
    NSEPYTHON_AVAILABLE = True
    print("✅ nsepython loaded")
except ImportError:
    NSEPYTHON_AVAILABLE = False
    print("⚠️  nsepython not installed. Run: pip install nsepython")


NIFTY50_YF = {
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
}


@router.get("/quote/{symbol}")
async def get_quote(symbol: str, exchange: str = Query("NSE")):
    """
    Real-time stock quote using nsetools (direct NSE feed).
    Falls back to yfinance if nsetools unavailable.
    """
    symbol = symbol.upper()
    cache_key = f"quote_nse_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached
      
    if NSE_TOOLS_AVAILABLE:
        try:
            quote = nse_client.get_quote(symbol)
            if quote:
                ltp = quote.get("lastPrice", 0)
                prev = quote.get("previousClose", ltp)
                change = ltp - prev
                change_pct = (change / prev * 100) if prev else 0

                result = {
                    "source": "NSE Direct (nsetools)",
                    "symbol": symbol,
                    "name": quote.get("companyName", symbol),
                    "current_price": ltp,
                    "formatted_price": f"₹{ltp:,.2f}",
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "direction": "up" if change >= 0 else "down",
                    "open": quote.get("open", 0),
                    "high": quote.get("dayHigh", 0),
                    "low": quote.get("dayLow", 0),
                    "prev_close": prev,
                    "volume": quote.get("totalTradedVolume", 0),
                    "52w_high": quote.get("high52", 0),
                    "52w_low": quote.get("low52", 0),
                    "pe_ratio": quote.get("pe", "N/A"),
                    "sector_pe": quote.get("sectorPe", "N/A"),
                    "delivery_pct": quote.get("deliveryToTradedQuantity", "N/A"),
                    "timestamp": datetime.now().isoformat(),
                }
                cache.set(cache_key, result, ttl=30)  # 30s cache for live quotes
                return result
        except Exception as e:
            print(f"nsetools error for {symbol}: {e}")

    if NSEPYTHON_AVAILABLE:
        try:
            data = nse_eq(symbol)
            price_info = data.get("priceInfo", {})
            ltp = price_info.get("lastPrice", 0)
            prev = price_info.get("previousClose", ltp)
            change = ltp - prev
            change_pct = (change / prev * 100) if prev else 0

            result = {
                "source": "NSE API (nsepython)",
                "symbol": symbol,
                "name": data.get("info", {}).get("companyName", symbol),
                "current_price": ltp,
                "formatted_price": f"₹{ltp:,.2f}",
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "direction": "up" if change >= 0 else "down",
                "open": price_info.get("open", 0),
                "high": price_info.get("intraDayHighLow", {}).get("max", 0),
                "low": price_info.get("intraDayHighLow", {}).get("min", 0),
                "prev_close": prev,
                "52w_high": price_info.get("weekHighLow", {}).get("max", 0),
                "52w_low": price_info.get("weekHighLow", {}).get("min", 0),
                "timestamp": datetime.now().isoformat(),
            }
            cache.set(cache_key, result, ttl=30)
            return result
        except Exception as e:
            print(f"nsepython error for {symbol}: {e}")

    yf_sym = NIFTY50_YF.get(symbol, f"{symbol}.NS")
    try:
        ticker = yf.Ticker(yf_sym)
        hist = ticker.history(period="2d")
        info = ticker.info
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")

        current = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
        change = current - prev
        change_pct = (change / prev * 100) if prev else 0

        result = {
            "source": "Yahoo Finance (fallback)",
            "symbol": symbol,
            "name": info.get("longName", symbol),
            "current_price": round(current, 2),
            "formatted_price": f"₹{current:,.2f}",
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "direction": "up" if change >= 0 else "down",
            "open": round(float(hist["Open"].iloc[-1]), 2),
            "high": round(float(hist["High"].iloc[-1]), 2),
            "low": round(float(hist["Low"].iloc[-1]), 2),
            "prev_close": round(prev, 2),
            "volume": int(hist["Volume"].iloc[-1]),
            "52w_high": round(info.get("fiftyTwoWeekHigh", 0), 2),
            "52w_low": round(info.get("fiftyTwoWeekLow", 0), 2),
            "pe_ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else "N/A",
            "market_cap": info.get("marketCap", 0),
            "timestamp": datetime.now().isoformat(),
        }
        cache.set(cache_key, result, ttl=60)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices")
async def get_indices():
    """NSE indices using nsetools (direct feed)."""
    cached = cache.get("indices_nse")
    if cached:
        return cached

    results = {}
    index_names = ["NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY AUTO",
                   "NIFTY PHARMA", "NIFTY FMCG", "NIFTY MIDCAP 50"]

    if NSE_TOOLS_AVAILABLE:
        for idx_name in index_names:
            try:
                data = nse_client.get_index_quote(idx_name)
                if data:
                    results[idx_name] = {
                        "name": idx_name,
                        "value": data.get("last", 0),
                        "change": data.get("variation", 0),
                        "change_pct": data.get("percentChange", 0),
                        "open": data.get("open", 0),
                        "high": data.get("high", 0),
                        "low": data.get("low", 0),
                        "advances": data.get("advances", 0),
                        "declines": data.get("declines", 0),
                        "pe": data.get("pe", "N/A"),
                        "pb": data.get("pb", "N/A"),
                        "year_high": data.get("yearHigh", 0),
                        "year_low": data.get("yearLow", 0),
                        "direction": "up" if data.get("variation", 0) >= 0 else "down",
                    }
            except Exception:
                pass
              
    yf_fallback = {
        "NIFTY 50": "^NSEI", "NIFTY BANK": "^NSEBANK",
        "NIFTY IT": "^CNXIT", "SENSEX": "^BSESN"
    }
    for name, sym in yf_fallback.items():
        if name not in results:
            try:
                t = yf.Ticker(sym)
                h = t.history(period="2d")
                if not h.empty:
                    curr = float(h["Close"].iloc[-1])
                    prev = float(h["Close"].iloc[-2]) if len(h) > 1 else curr
                    results[name] = {
                        "name": name,
                        "value": round(curr, 2),
                        "change": round(curr - prev, 2),
                        "change_pct": round((curr - prev) / prev * 100, 2) if prev else 0,
                        "direction": "up" if curr >= prev else "down",
                    }
            except:
                pass

    cache.set("indices_nse", results, ttl=60)
    return {"indices": results, "timestamp": datetime.now().isoformat()}


@router.get("/52-week-highs")
async def get_52_week_highs():
    """Stocks hitting 52-week highs today on NSE."""
    if not NSE_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Install nsetools: pip install nsetools")
    cached = cache.get("52w_highs")
    if cached:
        return cached
    try:
        data = nse_client.get_52_week_high()
        cache.set("52w_highs", data, ttl=600)
        return {"stocks": data, "count": len(data), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/52-week-lows")
async def get_52_week_lows():
    """Stocks hitting 52-week lows today on NSE."""
    if not NSE_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Install nsetools: pip install nsetools")
    cached = cache.get("52w_lows")
    if cached:
        return cached
    try:
        data = nse_client.get_52_week_low()
        cache.set("52w_lows", data, ttl=600)
        return {"stocks": data, "count": len(data), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-gainers")
async def get_top_gainers():
    """Top gaining stocks on NSE today."""
    if not NSE_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Install nsetools: pip install nsetools")
    cached = cache.get("top_gainers")
    if cached:
        return cached
    try:
        data = nse_client.get_top_gainers()
        cache.set("top_gainers", data, ttl=300)
        return {"gainers": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-losers")
async def get_top_losers():
    """Top losing stocks on NSE today."""
    if not NSE_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Install nsetools: pip install nsetools")
    cached = cache.get("top_losers")
    if cached:
        return cached
    try:
        data = nse_client.get_top_losers()
        cache.set("top_losers", data, ttl=300)
        return {"losers": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index-stocks/{index_name}")
async def get_stocks_in_index(index_name: str = "NIFTY BANK"):
    """Get all stock symbols in a given NSE index."""
    if not NSE_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Install nsetools: pip install nsetools")
    try:
        stocks = nse_client.get_stocks_in_index(index_name.upper())
        return {"index": index_name, "stocks": stocks, "count": len(stocks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{symbol}")
async def get_history(
    symbol: str,
    period: str = Query("3mo", description="1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y"),
    exchange: str = Query("NSE")
):
    """Historical OHLCV data via yfinance."""
    symbol = symbol.upper()
    suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
    yf_sym = NIFTY50_YF.get(symbol, f"{symbol}{suffix}")

    try:
        hist = yf.Ticker(yf_sym).history(period=period)
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No history for {symbol}")
        return {
            "symbol": symbol,
            "period": period,
            "data": [
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "open": round(float(r["Open"]), 2),
                    "high": round(float(r["High"]), 2),
                    "low": round(float(r["Low"]), 2),
                    "close": round(float(r["Close"]), 2),
                    "volume": int(r["Volume"]),
                }
                for d, r in hist.iterrows()
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/{symbol}")
async def get_options_chain(symbol: str):
    """
    Options chain for a stock or index.
    Uses nsetools for real options data.
    """
    if not NSE_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Install nsetools: pip install nsetools")
    symbol = symbol.upper()
    try:
        # nsetools can fetch F&O data
        futures = nse_client.get_future_quote(symbol)
        return {
            "symbol": symbol,
            "futures": futures,
            "note": "For full options chain use nsepython.nse_optionchain_scrapper(symbol)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
