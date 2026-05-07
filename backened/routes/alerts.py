from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from config.settings import config

router = APIRouter()
ALERTS_FILE = os.path.join(config.DATA_DIR, "alerts.json")
os.makedirs(config.DATA_DIR, exist_ok=True)

class Alert(BaseModel):
    user_id: str
    asset_type: str
    symbol: str
    alert_type: str
    target_value: float
    exchange: Optional[str] = "NSE"
    email: Optional[str] = None
    note: Optional[str] = ""

def load_alerts() -> list:
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_alerts(alerts: list):
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=2)

@router.get("/")
async def list_alerts(user_id: str):
    alerts = load_alerts()
    user_alerts = [a for a in alerts if a.get("user_id") == user_id]
    return {
        "user_id": user_id,
        "alerts": user_alerts,
        "count": len(user_alerts)
    }

@router.post("/create")
async def create_alert(alert: Alert):
    alerts = load_alerts()

    alert_dict = alert.dict()
    alert_dict["id"] = f"alert_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    alert_dict["created_at"] = datetime.now().isoformat()
    alert_dict["status"] = "active"
    alert_dict["triggered_at"] = None
    alert_dict["triggered_price"] = None

    alerts.append(alert_dict)
    save_alerts(alerts)

    return {
        "message": "Alert created successfully",
        "alert_id": alert_dict["id"],
        "description": _describe_alert(alert_dict),
        "alert": alert_dict
    }

@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, user_id: str):
    alerts = load_alerts()
    original = len(alerts)
    alerts = [a for a in alerts if not (a["id"] == alert_id and a["user_id"] == user_id)]
    if len(alerts) == original:
        raise HTTPException(status_code=404, detail="Alert not found")
    save_alerts(alerts)
    return {"message": "Alert deleted"}

@router.get("/history")
async def get_triggered_alerts(user_id: str):
    alerts = load_alerts()
    triggered = [
        a for a in alerts
        if a.get("user_id") == user_id and a.get("status") == "triggered"
    ]
    return {"user_id": user_id, "triggered_alerts": triggered}

@router.post("/{alert_id}/snooze")
async def snooze_alert(alert_id: str, user_id: str):
    alerts = load_alerts()
    for a in alerts:
        if a["id"] == alert_id and a["user_id"] == user_id:
            a["status"] = "active"
            a["triggered_at"] = None
            save_alerts(alerts)
            return {"message": "Alert re-activated"}
    raise HTTPException(status_code=404, detail="Alert not found")

async def check_all_alerts():
    alerts = load_alerts()
    active = [a for a in alerts if a.get("status") == "active"]

    if not active:
        return

    changed = False
    for alert in active:
        try:
            current_price = await _fetch_price_for_alert(alert)
            if current_price is None:
                continue

            triggered = False
            if alert["alert_type"] == "above" and current_price >= alert["target_value"]:
                triggered = True
            elif alert["alert_type"] == "below" and current_price <= alert["target_value"]:
                triggered = True

            if triggered:
                alert["status"] = "triggered"
                alert["triggered_at"] = datetime.now().isoformat()
                alert["triggered_price"] = current_price
                changed = True

                await _send_alert_notification(alert, current_price)
                print(f"🔔 ALERT TRIGGERED: {_describe_alert(alert)} | Current: ₹{current_price:,.2f}")

        except Exception as e:
            print(f"Alert check error for {alert.get('symbol')}: {e}")

    if changed:
        save_alerts(alerts)

async def _fetch_price_for_alert(alert: dict) -> Optional[float]:
    try:
        if alert["asset_type"] == "stock":
            import yfinance as yf
            suffix = ".NS" if alert.get("exchange", "NSE") == "NSE" else ".BO"
            ticker = yf.Ticker(f"{alert['symbol']}{suffix}")
            hist = ticker.history(period="1d")
            if not hist.empty:
                return float(hist["Close"].iloc[-1])

        elif alert["asset_type"] == "crypto":
            import httpx
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": alert["symbol"], "vs_currencies": "inr"}
                )
                return r.json().get(alert["symbol"], {}).get("inr")

    except Exception:
        pass
    return None

async def _send_alert_notification(alert: dict, current_price: float):
    if not alert.get("email") or not config.SMTP_USER:
        return

    try:
        subject = f"🔔 FinAI Alert: {alert['symbol']} {alert['alert_type']} ₹{alert['target_value']:,.2f}"
        body = f"""
FinAI Price Alert Triggered!

Asset: {alert['symbol']} ({alert['asset_type']})
Alert: {_describe_alert(alert)}
Current Price: {current_price:,.2f}
Triggered At: {alert['triggered_at']}
Your Note: {alert.get('note', '-')}"""

— FinAI Financial Intelligence Platform
    direction = "rises above" if alert["alert_type"] == "above" else "falls below"
    return f"{alert['symbol']} {direction} ₹{alert['target_value']:,.2f}"
