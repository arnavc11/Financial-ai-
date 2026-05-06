from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from datetime import datetime
import yfinance as yf
from config.settings import config

router = APIRouter()
DATA_DIR = config.DATA_DIR
os.makedirs(DATA_DIR, exist_ok=True)
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolios.json")

class Holding(BaseModel):
    asset_type: str
    symbol: str
    name: str
    quantity: float
    buy_price: float
    buy_date: str
    exchange: Optional[str] = "NSE"
    notes: Optional[str] = ""

class Portfolio(BaseModel):
    portfolio_name: str
    user_id: str
    holdings: List[Holding] = []

class AddHoldingRequest(BaseModel):
    user_id: str
    portfolio_name: str
    holding: Holding

def load_portfolios() -> dict:
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    return {}

def save_portfolios(data: dict):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_portfolio_key(user_id: str, portfolio_name: str) -> str:
    return f"{user_id}::{portfolio_name}"

@router.post("/create")
async def create_portfolio(portfolio: Portfolio):
    db = load_portfolios()
    key = get_portfolio_key(portfolio.user_id, portfolio.portfolio_name)
    if key in db:
        raise HTTPException(status_code=400, detail="Portfolio already exists")
    db[key] = {
        "portfolio_name": portfolio.portfolio_name,
        "user_id": portfolio.user_id,
        "created_at": datetime.now().isoformat(),
        "holdings": []
    }
    save_portfolios(db)
    return {"message": "Portfolio created", "key": key}

@router.get("/{user_id}")
async def list_portfolios(user_id: str):
    db = load_portfolios()
    user_portfolios = {
        k: v for k, v in db.items() if v.get("user_id") == user_id
    }
    return {"user_id": user_id, "portfolios": list(user_portfolios.values())}

@router.post("/add-holding")
async def add_holding(req: AddHoldingRequest):
    db = load_portfolios()
    key = get_portfolio_key(req.user_id, req.portfolio_name)

    if key not in db:
        db[key] = {
            "portfolio_name": req.portfolio_name,
            "user_id": req.user_id,
            "created_at": datetime.now().isoformat(),
            "holdings": []
        }

    holding_dict = req.holding.dict()
    holding_dict["added_at"] = datetime.now().isoformat()
    holding_dict["id"] = f"{req.holding.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    db[key]["holdings"].append(holding_dict)
    save_portfolios(db)
    return {"message": "Holding added", "holding": holding_dict}

@router.get("/{user_id}/{portfolio_name}/summary")
async def get_portfolio_summary(user_id: str, portfolio_name: str):
    db = load_portfolios()
    key = get_portfolio_key(user_id, portfolio_name)

    if key not in db:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    portfolio = db[key]
    holdings = portfolio.get("holdings", [])

    total_invested = 0
    total_current = 0
    enriched_holdings = []

    for h in holdings:
        invested = h["quantity"] * h["buy_price"]
        total_invested += invested

        current_price = await _get_current_price(h)
        current_value = h["quantity"] * current_price if current_price else invested
        total_current += current_value

        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0

        enriched_holdings.append({
            **h,
            "invested": round(invested, 2),
            "current_price": round(current_price, 2) if current_price else None,
            "current_value": round(current_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "pnl_direction": "profit" if pnl >= 0 else "loss",
        })

    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    return {
        "portfolio_name": portfolio_name,
        "user_id": user_id,
        "summary": {
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_current, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "total_pnl_direction": "profit" if total_pnl >= 0 else "loss",
            "formatted": {
                "invested": f"₹{total_invested:,.2f}",
                "current": f"₹{total_current:,.2f}",
                "pnl": f"{'+'if total_pnl>=0 else ''}₹{total_pnl:,.2f} ({total_pnl_pct:+.2f}%)"
            }
        },
        "holdings": enriched_holdings,
        "holdings_count": len(enriched_holdings),
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/{user_id}/{portfolio_name}/holding/{holding_id}")
async def remove_holding(user_id: str, portfolio_name: str, holding_id: str):
    db = load_portfolios()
    key = get_portfolio_key(user_id, portfolio_name)
    if key not in db:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    original_count = len(db[key]["holdings"])
    db[key]["holdings"] = [h for h in db[key]["holdings"] if h.get("id") != holding_id]

    if len(db[key]["holdings"]) == original_count:
        raise HTTPException(status_code=404, detail="Holding not found")

    save_portfolios(db)
    return {"message": "Holding removed"}

@router.get("/{user_id}/{portfolio_name}/tax")
async def calculate_tax(user_id: str, portfolio_name: str):
    summary = await get_portfolio_summary(user_id, portfolio_name)
    holdings = summary["holdings"]

    stcg_amount = 0
    ltcg_amount = 0
    crypto_gains = 0

    for h in holdings:
        if h["pnl"] <= 0:
            continue

        buy_date = datetime.fromisoformat(h["buy_date"]) if "-" in h.get("buy_date","") else datetime.now()
        holding_days = (datetime.now() - buy_date).days

        if h["asset_type"] == "crypto":
            crypto_gains += h["pnl"]
        elif holding_days < 365:
            stcg_amount += h["pnl"]
        else:
            ltcg_amount += h["pnl"]

    stcg_tax = stcg_amount * 0.20
    ltcg_taxable = max(0, ltcg_amount - 125000)
    ltcg_tax = ltcg_taxable * 0.125
    crypto_tax = crypto_gains * 0.30
    total_tax = stcg_tax + ltcg_tax + crypto_tax

    return {
        "disclaimer": "Estimate only. Consult a CA for accurate tax filing.",
        "stcg": {
            "gains": round(stcg_amount, 2),
            "rate": "20%",
            "tax": round(stcg_tax, 2)
        },
        "ltcg": {
            "gains": round(ltcg_amount, 2),
            "exemption": "₹1,25,000",
            "taxable": round(ltcg_taxable, 2),
            "rate": "12.5%",
            "tax": round(ltcg_tax, 2)
        },
        "crypto": {
            "gains": round(crypto_gains, 2),
            "rate": "30% flat",
            "tax": round(crypto_tax, 2)
        },
        "total_estimated_tax": round(total_tax, 2),
        "formatted_total": f"₹{total_tax:,.2f}"
    }

async def _get_current_price(holding: dict) -> Optional[float]:
    try:
        asset_type = holding.get("asset_type", "stock")
        symbol = holding.get("symbol", "")

        if asset_type in ("stock",):
            suffix = ".NS" if holding.get("exchange", "NSE") == "NSE" else ".BO"
            yf_sym = f"{symbol}{suffix}"
            ticker = yf.Ticker(yf_sym)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])

        elif asset_type == "crypto":
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": symbol, "vs_currencies": "inr"}
                )
                data = r.json()
                return data.get(symbol, {}).get("inr")

        elif asset_type == "mutual_fund":
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"https://api.mfapi.in/mf/{symbol}/latest")
                data = r.json()
                return float(data["data"][0]["nav"])

    except Exception:
        pass

    return holding.get("buy_price")
