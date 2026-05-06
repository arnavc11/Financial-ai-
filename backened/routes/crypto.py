from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import httpx
from datetime import datetime
from config.settings import config
from backend.cache import cache

router = APIRouter()

BASE_URL = config.COINGECKO_BASE_URL

POPULAR_COINS = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "binancecoin": "BNB",
    "solana": "Solana",
    "ripple": "XRP",
    "cardano": "Cardano",
    "dogecoin": "Dogecoin",
    "polkadot": "Polkadot",
    "matic-network": "Polygon (MATIC)",
    "chainlink": "Chainlink",
}

async def coingecko_get(endpoint: str, params: dict = {}) -> dict:
    headers = {}
    if config.COINGECKO_API_KEY:
        headers["x-cg-pro-api-key"] = config.COINGECKO_API_KEY

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"{BASE_URL}{endpoint}",
            params=params,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

@router.get("/prices")
async def get_crypto_prices(
    coins: str = Query(
        "bitcoin,ethereum,binancecoin,solana,ripple",
        description="Comma-separated CoinGecko coin IDs"
    )
):
    cache_key = f"crypto_prices_{coins}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    coin_list = [c.strip() for c in coins.split(",")]

    try:
        data = await coingecko_get("/simple/price", {
            "ids": ",".join(coin_list),
            "vs_currencies": "inr,usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
        })

        results = []
        for coin_id in coin_list:
            if coin_id in data:
                d = data[coin_id]
                inr_price = d.get("inr", 0)
                change_24h = d.get("inr_24h_change", 0)

                if inr_price >= 1_00_00_000:
                    formatted_inr = f"₹{inr_price/1_00_00_000:.2f} Cr"
                elif inr_price >= 1_00_000:
                    formatted_inr = f"₹{inr_price/1_00_000:.2f} L"
                else:
                    formatted_inr = f"₹{inr_price:,.2f}"

                results.append({
                    "id": coin_id,
                    "name": POPULAR_COINS.get(coin_id, coin_id.capitalize()),
                    "price_inr": round(inr_price, 2),
                    "price_usd": round(d.get("usd", 0), 2),
                    "formatted_inr": formatted_inr,
                    "change_24h_pct": round(change_24h, 2),
                    "direction": "up" if change_24h >= 0 else "down",
                    "market_cap_inr": d.get("inr_market_cap", 0),
                    "volume_24h_inr": d.get("inr_24h_vol", 0),
                })

        result = {
            "coins": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }

        cache.set(cache_key, result, ttl=60)
        return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"CoinGecko API error: {str(e)}")

@router.get("/coin/{coin_id}")
async def get_coin_detail(coin_id: str):
    cache_key = f"coin_detail_{coin_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        data = await coingecko_get(f"/coins/{coin_id}", {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false",
        })

        market = data.get("market_data", {})
        inr_price = market.get("current_price", {}).get("inr", 0)

        result = {
            "id": coin_id,
            "name": data.get("name"),
            "symbol": data.get("symbol", "").upper(),
            "description": data.get("description", {}).get("en", "")[:500],
            "price_inr": round(inr_price, 2),
            "price_usd": round(market.get("current_price", {}).get("usd", 0), 2),
            "formatted_inr": f"₹{inr_price:,.2f}",
            "market_cap_rank": data.get("market_cap_rank"),
            "change_24h": round(market.get("price_change_percentage_24h", 0), 2),
            "change_7d": round(market.get("price_change_percentage_7d", 0), 2),
            "change_30d": round(market.get("price_change_percentage_30d", 0), 2),
            "ath_inr": market.get("ath", {}).get("inr", 0),
            "atl_inr": market.get("atl", {}).get("inr", 0),
            "circulating_supply": market.get("circulating_supply"),
            "total_supply": market.get("total_supply"),
            "image": data.get("image", {}).get("small"),
            "india_regulations": _get_india_crypto_note(coin_id),
        }

        cache.set(cache_key, result, ttl=300)
        return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/history/{coin_id}")
async def get_crypto_history(
    coin_id: str,
    days: int = Query(30, description="Number of days of history (1, 7, 30, 90, 365)")
):
    cache_key = f"crypto_hist_{coin_id}_{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        data = await coingecko_get(f"/coins/{coin_id}/market_chart", {
            "vs_currency": "inr",
            "days": days,
            "interval": "daily" if days > 7 else "hourly"
        })

        prices = [
            {"timestamp": p[0], "price": round(p[1], 2)}
            for p in data.get("prices", [])
        ]

        result = {"coin_id": coin_id, "days": days, "currency": "INR", "prices": prices}
        cache.set(cache_key, result, ttl=300)
        return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/india-tax-guide")
async def get_india_crypto_tax():
    return {
        "title": "Crypto Tax Rules in India (FY 2025-26)",
        "flat_tax_rate": "30% flat tax on crypto gains (no slab benefit)",
        "tds": "1% TDS on crypto transactions above ₹10,000 per transaction (₹50,000 for specified persons)",
        "loss_setoff": "Losses from one crypto CANNOT be set off against gains from another",
        "carry_forward": "Crypto losses CANNOT be carried forward to next year",
        "gifts": "Crypto received as gifts taxable as 'Income from Other Sources'",
        "itr_form": "Report in ITR-2 or ITR-3 under 'Virtual Digital Assets (VDA)'",
        "legal_status": "Crypto is legal to hold and trade in India but not legal tender",
        "regulated_by": "SEBI (partial oversight) and RBI (banking transactions)",
        "exchanges": ["WazirX", "CoinDCX", "ZebPay", "Bitbns", "Mudrex"],
        "note": "Tax rules subject to change. Consult a CA for accurate filing.",
    }

def _get_india_crypto_note(coin_id: str) -> str:
    notes = {
        "bitcoin": "Most widely traded crypto in India. Available on all major Indian exchanges. Subject to 30% tax on gains.",
        "ethereum": "Popular for DeFi and NFTs. Available on Indian exchanges. Staking rewards taxable at 30%.",
        "ripple": "XRP has ongoing legal clarity issues globally; trade with caution.",
    }
    return notes.get(coin_id, "Available on major Indian exchanges. Subject to 30% flat tax on gains under VDA rules.")
