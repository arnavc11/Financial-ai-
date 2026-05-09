import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

print("--- STAGE 1: BASIC IMPORTS ---", flush=True)


from backened.routes import (
    stocks, crypto, rbi, mutualfunds, portfolio, 
    alerts, news, ai_chat, charts, voice, stocks_enhanced
)
from backened.scheduler import start_scheduler
from backened.database import init_db


print("--- STAGE 2: APP INITIALIZATION ---", flush=True)

app = FastAPI(
    title="FinAI", 
    description="Indian Financial Intelligence Platform", 
    version="2.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(stocks.router,           prefix="/api/stocks",    tags=["Stocks"])
app.include_router(stocks_enhanced.router,  prefix="/api/nse",       tags=["NSE Direct"])
app.include_router(crypto.router,           prefix="/api/crypto",    tags=["Crypto"])
app.include_router(rbi.router,              prefix="/api/rbi",       tags=["RBI"])
app.include_router(mutualfunds.router,      prefix="/api/mf",        tags=["Mutual Funds"])
app.include_router(portfolio.router,        prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(alerts.router,           prefix="/api/alerts",    tags=["Alerts"])
app.include_router(news.router,             prefix="/api/news",      tags=["News"])
app.include_router(ai_chat.router,          prefix="/api/ai",        tags=["AI Chat"])
app.include_router(charts.router,           prefix="/api/charts",    tags=["Charts"])
app.include_router(voice.router,            prefix="/api/voice",     tags=["Voice"])


if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.on_event("startup")
async def startup():
    print("Initializing Database...", flush=True)
    init_db()
    print("Starting Scheduler...", flush=True)
    start_scheduler()
    print("ArthAI v2.0 started!", flush=True)

@app.get("/health")
async def health():
    return {"status": "ok", "app": "ArthAI", "version": "2.0.0"}

@app.get("/", include_in_schema=False)
async def root():
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    return {"app": "FinAI", "docs": "/docs"}
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
