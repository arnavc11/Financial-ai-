from fastapi import APIRouter, HTTPException, Query
import httpx
from datetime import datetime
from backened.cache import cache

router = APIRouter()
BASE_URL = "https://api.mfapi.in/mf"

async def mfapi_get(path: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{BASE_URL}{path}")
        r.raise_for_status()
        return r.json()

POPULAR_FUNDS = {

    "100033": "SBI Bluechip Fund — Direct Growth",
    "120503": "Mirae Asset Large Cap Fund — Direct Growth",

    "100270": "HDFC Mid-Cap Opportunities — Direct Growth",
    "119598": "Axis Midcap Fund — Direct Growth",

    "120828": "SBI Small Cap Fund — Direct Growth",
    "135781": "Nippon India Small Cap Fund — Direct Growth",

    "120503": "Mirae Asset Tax Saver — Direct Growth",
    "125354": "Axis Long Term Equity — Direct Growth",

    "120716": "UTI Nifty 50 Index Fund — Direct Growth",
    "120684": "HDFC Index Fund Nifty 50 — Direct Growth",

    "100122": "HDFC Short Term Debt Fund — Direct Growth",
    "101305": "SBI Magnum Medium Duration — Direct Growth",
}

@router.get("/search")
async def search_mutual_funds(q: str = Query(..., description="Fund name or keyword")):
    cache_key = f"mf_search_{q.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{BASE_URL}/search?q={q}")
            r.raise_for_status()
            data = r.json()

        results = [
            {"scheme_code": str(f.get("schemeCode")), "name": f.get("schemeName")}
            for f in data[:20]
        ]
        result = {"query": q, "results": results, "count": len(results)}
        cache.set(cache_key, result, ttl=3600)
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/nav/{scheme_code}")
async def get_fund_nav(scheme_code: str):
    cache_key = f"mf_nav_{scheme_code}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        data = await mfapi_get(f"/{scheme_code}/latest")
        meta = data.get("meta", {})
        nav_data = data.get("data", [{}])[0]

        result = {
            "scheme_code": scheme_code,
            "fund_house": meta.get("fund_house"),
            "scheme_name": meta.get("scheme_name"),
            "scheme_category": meta.get("scheme_category"),
            "scheme_type": meta.get("scheme_type"),
            "nav": float(nav_data.get("nav", 0)),
            "nav_formatted": f"₹{float(nav_data.get('nav', 0)):,.4f}",
            "date": nav_data.get("date"),
            "isin_growth": meta.get("isin_growth"),
            "isin_div_reinvestment": meta.get("isin_div_reinvestment"),
        }
        cache.set(cache_key, result, ttl=3600)
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/history/{scheme_code}")
async def get_fund_nav_history(
    scheme_code: str,
    days: int = Query(365, description="Number of days of history")
):
    cache_key = f"mf_hist_{scheme_code}_{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        data = await mfapi_get(f"/{scheme_code}")
        all_nav = data.get("data", [])

        recent = all_nav[:days]

        if len(recent) >= 2:
            current_nav = float(recent[0]["nav"])
            old_nav = float(recent[-1]["nav"])
            total_return = ((current_nav - old_nav) / old_nav) * 100
        else:
            total_return = 0

        def calc_return(n_days):
            if len(all_nav) > n_days:
                curr = float(all_nav[0]["nav"])
                past = float(all_nav[n_days]["nav"])
                return round(((curr - past) / past) * 100, 2)
            return None

        result = {
            "scheme_code": scheme_code,
            "fund_name": data.get("meta", {}).get("scheme_name"),
            "returns": {
                "1_month": calc_return(30),
                "3_month": calc_return(90),
                "6_month": calc_return(180),
                "1_year": calc_return(365),
                "3_year": calc_return(1095),
            },
            "nav_history": [
                {"date": d["date"], "nav": float(d["nav"])}
                for d in recent
            ],
            "data_points": len(recent)
        }
        cache.set(cache_key, result, ttl=3600)
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/popular")
async def get_popular_funds():
    results = []
    for code, name in list(POPULAR_FUNDS.items())[:8]:
        try:
            nav_data = await get_fund_nav(code)
            results.append(nav_data)
        except:
            results.append({"scheme_code": code, "scheme_name": name, "error": "unavailable"})
    return {"funds": results, "count": len(results)}

@router.get("/sip-calculator")
async def sip_calculator(
    monthly_amount: float = Query(..., description="Monthly SIP amount in ₹"),
    annual_return_pct: float = Query(12.0, description="Expected annual return %"),
    years: int = Query(10, description="Investment period in years")
):
    r = (annual_return_pct / 100) / 12
    n = years * 12

    future_value = monthly_amount * (((1 + r) ** n - 1) / r) * (1 + r)
    total_invested = monthly_amount * n
    total_gain = future_value - total_invested
    wealth_ratio = future_value / total_invested

    breakdown = []
    for y in range(1, years + 1):
        n_y = y * 12
        fv_y = monthly_amount * (((1 + r) ** n_y - 1) / r) * (1 + r)
        breakdown.append({
            "year": y,
            "invested": round(monthly_amount * n_y, 2),
            "value": round(fv_y, 2),
            "gain": round(fv_y - monthly_amount * n_y, 2),
        })

    return {
        "monthly_sip": monthly_amount,
        "annual_return_pct": annual_return_pct,
        "years": years,
        "total_invested": round(total_invested, 2),
        "future_value": round(future_value, 2),
        "total_gain": round(total_gain, 2),
        "wealth_ratio": round(wealth_ratio, 2),
        "formatted": {
            "invested": f"₹{total_invested:,.0f}",
            "value": f"₹{future_value:,.0f}",
            "gain": f"₹{total_gain:,.0f}"
        },
        "year_wise": breakdown
          }
