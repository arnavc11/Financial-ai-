import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
print("--- STAGE 1: BASIC IMPORTS ---", flush=True)
from fastapi import FastAPI
import os

print("--- STAGE 2: ROUTE IMPORTS ---", flush=True)
print("Loading stocks...", flush=True)
from backened.routes import stocks
print("Loading alerts...", flush=True)
from backened.routes import alerts 

print("--- STAGE 3: APP INITIALIZATION ---", flush=True)
app = FastAPI()

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backened.routes import stocks, crypto, rbi, mutualfunds, portfolio, alerts, news, ai_chat
from backened.routes import charts, voice, stocks_enhanced
from backened.scheduler import start_scheduler
from backened.database import init_db

app = FastAPI(title="FinAI", description="Indian Financial Intelligence Platform", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(stocks.router,          prefix="/api/stocks",    tags=["Stocks"])
app.include_router(stocks_enhanced.router, prefix="/api/nse",       tags=["NSE Direct"])
app.include_router(crypto.router,          prefix="/api/crypto",    tags=["Crypto"])
app.include_router(rbi.router,             prefix="/api/rbi",       tags=["RBI"])
app.include_router(mutualfunds.router,     prefix="/api/mf",        tags=["Mutual Funds"])
app.include_router(portfolio.router,       prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(alerts.router,          prefix="/api/alerts",    tags=["Alerts"])
app.include_router(news.router,            prefix="/api/news",      tags=["News"])
app.include_router(ai_chat.router,         prefix="/api/ai",        tags=["AI Chat"])
app.include_router(charts.router,          prefix="/api/charts",    tags=["Charts"])
app.include_router(voice.router,           prefix="/api/voice",     tags=["Voice"])

if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/app", include_in_schema=False)
async def app_page():
    return FileResponse("frontend/index.html")

#@app.on_event("startup")
#async def startup():
#    init_db()
   # start_scheduler()
    print("FinAI v2.0 started!")

@app.get("/health")
async def health():
    return {"status": "ok", "app": "ArthAI", "version": "2.0.0"}

@app.get("/", include_in_schema=False)
async def root():
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    return {"app": "FinAI", "docs": "/docs"}
    
@app.post("/api/financial-health-score")
async def financial_health_score(request: dict):
    return {"message": "Use the client-side scoring built into index.html"}

@app.post("/api/upi-analyzer")  
async def upi_analyzer(request: dict):
    return {"message": "Use the client-side analysis built into index.html"}
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
