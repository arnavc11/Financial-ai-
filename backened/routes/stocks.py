from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import yfinance as yf
import httpx
import json
from datetime import datetime, timedelta
from config.settings import config
from backened.cache import cache

router = APIRouter()

NIFTY50_SYMBOLS = {
    "RELIANCE": "RELIANCE.NS",   "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS",   "INFY": "INFY.NS",
    "ICICIBANK": "ICICIBANK.NS", "HINDUNILVR": "HINDUNILVR.NS",
    "ITC": "ITC.NS",             "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS", "KOTAKBANK": "KOTAKBANK.NS",
    "WIPRO": "WIPRO.NS",         "LT": "LT.NS",
    "AXISBANK": "AXISBANK.NS",   "MARUTI": "MARUTI.NS",
    "SUNPHARMA": "SUNPHARMA.NS", "BAJFINANCE": "BAJFINANCE.NS",
    "TITAN": "TITAN.NS",         "NESTLEIND": "NESTLEIND.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS", "POWERGRID": "POWERGRID.NS",
}

INDICES = {
    "NIFTY50":   "^NSEI",
    "SENSEX":    "^BSESN",
    "BANKNIFTY": "^NSEBANK",
    "NIFTYIT":   "^CNXIT",
    "NIFTYMID":  "^NSEMDCP50",
}

def format_inr(value: float) -> str:
    if value >= 1_00_00_000:
        return f"₹{value/1_00_00_000:.2f} Cr"
    elif value >= 1_00_000:
        return f"₹{value/1_00_000:.2f} L"
    else:
        return f"₹{value:,.2f}"

@router.get("/indices")
async def get_indices():
    cached = cache.get("indices")
    if cached:
        return cached

    results = {}
    for name, symbol in INDICES.items():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            hist = ticker.history(period="2d")

            if not hist.empty:
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
                change = current - prev
                change_pct = (change / prev) * 100 if prev else 0

                results[name] = {
                    "symbol": symbol,
                    "name": name,
                    "current": round(current, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "formatted": f"{current:,.2f}",
                    "direction": "up" if change >= 0 else "down",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            results[name] = {"name": name, "error": str(e)}

    cache.set("indices", results, ttl=300)
    return results

@router.get("/quote/{symbol}")
async def get_stock_quote(
    symbol: str,
    exchange: str = Query("NSE", description="NSE or BSE")
):
    symbol = symbol.upper()
    suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
    yf_symbol = NIFTY50_SYMBOLS.get(symbol, f"{symbol}{suffix}")

    cache_key = f"quote_{yf_symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        hist = ticker.history(period="5d")

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        current = float(hist["Close"].iloc[-1])
        prev_close = float(info.get("previousClose", hist["Close"].iloc[-2] if len(hist) > 1 else current))
        change = current - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        result = {
            "symbol": symbol,
            "exchange": exchange.upper(),
            "name": info.get("longName", info.get("shortName", symbol)),
            "sector": info.get("sector", "N/A"),
            "current_price": round(current, 2),
            "formatted_price": f"₹{current:,.2f}",
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "direction": "up" if change >= 0 else "down",
            "open": round(float(hist["Open"].iloc[-1]), 2),
            "high": round(float(hist["High"].iloc[-1]), 2),
            "low": round(float(hist["Low"].iloc[-1]), 2),
            "prev_close": round(prev_close, 2),
            "volume": int(hist["Volume"].iloc[-1]),
            "market_cap": format_inr(info.get("marketCap", 0)) if info.get("marketCap") else "N/A",
            "pe_ratio": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else "N/A",
            "pb_ratio": round(info.get("priceToBook", 0), 2) if info.get("priceToBook") else "N/A",
            "52w_high": round(info.get("fiftyTwoWeekHigh", 0), 2),
            "52w_low": round(info.get("fiftyTwoWeekLow", 0), 2),
            "dividend_yield": f"{info.get('dividendYield', 0)*100:.2f}%" if info.get("dividendYield") else "N/A",
            "timestamp": datetime.now().isoformat(),
        }

        cache.set(cache_key, result, ttl=60)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching {symbol}: {str(e)}")

@router.get("/history/{symbol}")
async def get_stock_history(
    symbol: str,
    period: str = Query("1mo", description="Valid: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y"),
    exchange: str = Query("NSE")
):
    symbol = symbol.upper()
    suffix = ".NS" if exchange.upper() == "NSE" else ".BO"
    yf_symbol = NIFTY50_SYMBOLS.get(symbol, f"{symbol}{suffix}")

    try:
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No history for {symbol}")

        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        return {
            "symbol": symbol,
            "exchange": exchange,
            "period": period,
            "count": len(data),
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nifty50")
async def get_nifty50_overview():
    cached = cache.get("nifty50_overview")
    if cached:
        return cached

    results = []

    symbols_str = " ".join(NIFTY50_SYMBOLS.values())
    try:
        import yfinance as yf
        data = yf.download(
            tickers=symbols_str,
            period="2d",
            group_by="ticker",
            auto_adjust=True,
            threads=True,
            progress=False
        )

        for name, yf_sym in NIFTY50_SYMBOLS.items():
            try:
                if yf_sym in data.columns.get_level_values(0):
                    close = data[yf_sym]["Close"]
                    current = float(close.iloc[-1])
                    prev = float(close.iloc[-2]) if len(close) > 1 else current
                    change_pct = ((current - prev) / prev) * 100 if prev else 0
                    results.append({
                        "symbol": name,
                        "price": round(current, 2),
                        "change_pct": round(change_pct, 2),
                        "direction": "up" if change_pct >= 0 else "down"
                    })
            except:
                pass

        cache.set("nifty50_overview", results, ttl=300)
        return {"stocks": results, "count": len(results), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_stocks(q: str = Query(..., description="Search term")):
    q = q.upper()
    matches = [
        {"symbol": sym, "yf_symbol": yf_sym, "exchange": "NSE"}
        for sym, yf_sym in NIFTY50_SYMBOLS.items()
        if q in sym
    ]
    return {"query": q, "results": matches}
