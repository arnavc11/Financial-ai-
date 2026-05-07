from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
from datetime import datetime
from config.settings import config

router = APIRouter()

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2"

Fin_AI_SYSTEM = """You are FinAI, an expert AI financial assistant for Indian markets.
You help users understand NSE/BSE stocks, RBI policy, bonds, MSME schemes, crypto (30% tax),
mutual funds, and the Indian economy.

CURRENT MARKET CONTEXT:
{market_context}

Always use Rs. for prices, Indian numbering (Lakh/Crore), and warn that this is educational only."""

@router.post("/chat")
async def handle_chat(request: ChatRequest):
    
    market_context = await get_market_context()
    system = FIN_AI_SYSTEM.format(market_context=market_context)
    messages = [{"role": m.role, "content": m.content} for m in request.messages]


    if request.use_anthropic and config.ANTHROPIC_API_KEY:
        reply = await chat_with_anthropic(messages, system)
        engine = "Anthropic Claude (paid)"
    else:
        model = request.model or DEFAULT_OLLAMA_MODEL
        reply = await chat_with_ollama(messages, model, system)
        engine = f"Ollama/{model} (free)"

    return {"reply": reply, "engine": engine, "market_context": market_context,
            "timestamp": datetime.now().isoformat()}

@router.get("/ollama-models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{OLLAMA_BASE_URL}/api/tags")
            models = [m["name"] for m in r.json().get("models", [])]
            return {"installed": models, "install_more": "ollama pull <model-name>",
                    "recommended": ["llama3.2", "mistral", "qwen2.5:7b"]}
    except Exception:
        return {"error": "Ollama not running", "fix": "ollama serve"}

@router.get("/token-explainer")
async def explain_tokens():
    return {
        "simple_explanation": (
            "A TOKEN is a small piece of text — roughly one word or part of a word. "
            "AI companies like Anthropic and OpenAI charge you money for every token "
            "you send AND receive. It is like paying per SMS but for AI messages."
        ),
        "examples": {
            "Hello": "1 token",
            "Nifty 50": "2 tokens",
            "What is the current RBI repo rate?": "8 tokens",
            "One full paragraph (100 words)": "approx 130 tokens"
        },
        "cost_comparison": {
            "Anthropic Claude": "Rs. 0.25 per 1000 words sent+received",
            "OpenAI GPT-4": "Rs. 2.50 per 1000 words — very expensive",
            "Ollama on your laptop": "Rs. 0 — completely free, unlimited",
            "Groq API": "Free tier — fast cloud option, no credit card"
        },
        "recommendation": (
            "For your college project, use Ollama. "
            "It runs Llama 4 or Mistral on your own laptop. "
            "No billing. No API key. No internet required once downloaded."
        ),
        "setup_steps": [
            "Step 1: Download Ollama from https://ollama.com/download",
            "Step 2: Install it like a normal Windows/Mac app",
            "Step 3: Open a terminal and type: ollama pull llama3.2",
            "Step 4: Run FinAI: python main.py",
            "Step 5: Chat for free forever!"
        ]
    }

@router.post("/analyze-stock")
async def analyze_stock(symbol: str, exchange: str = "NSE"):
    import yfinance as yf
    symbol = symbol.upper()
    try:
        hist = yf.Ticker(f"{symbol}.NS").history(period="3mo")
        info = yf.Ticker(f"{symbol}.NS").info
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")
        curr = float(hist["Close"].iloc[-1])
        start = float(hist["Close"].iloc[0])
        ret_3m = ((curr - start) / start) * 100
        summary = (f"Stock: {symbol} | Price: Rs.{curr:,.2f} | "
                   f"3M Return: {ret_3m:.1f}% | PE: {info.get('trailingPE','N/A')} | "
                   f"52W High: Rs.{info.get('fiftyTwoWeekHigh','N/A')} | "
                   f"Sector: {info.get('sector','N/A')}")
        reply = await chat_with_ollama(
            messages=[{"role": "user", "content": f"Briefly analyse this Indian stock (under 150 words, include risk disclaimer): {summary}"}],
            model=DEFAULT_OLLAMA_MODEL,
            system="You are FinAI, Indian stock market analyst."
        )
        return {"symbol": symbol, "data": summary, "analysis": reply,
                "engine": f"Ollama/{DEFAULT_OLLAMA_MODEL} (free)"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
