from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
from datetime import datetime
from groq import Groq
from backened.config.settings import config

router = APIRouter()

client = Groq(api_key=config.GROQ_API_KEY)
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    
FIN_AI_SYSTEM = """You are FinAI, an expert AI financial assistant for Indian markets.
You help users understand NSE/BSE stocks, RBI policy, bonds, MSME schemes, crypto (30% tax), 
mutual funds, and the Indian economy.

Always use Rs. for prices, Indian numbering (Lakh/Crore), and warn that this is educational only."""

@router.post("/chat")
async def handle_chat(request: ChatRequest):
    """
    Main chat endpoint updated to use Groq for near-instant responses.
    """
    try:
        messages = [{"role": "system", "content": FIN_AI_SYSTEM}]
        for m in request.messages:
            messages.append({"role": m.role, "content": m.content})

        completion = client.chat.completions.create(
            model=DEFAULT_GROQ_MODEL,
            messages=messages,
            temperature=0.7,
        )

        return {
            "reply": completion.choices[0].message.content,
            "engine": f"Groq/{DEFAULT_GROQ_MODEL}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-stock")
async def analyze_stock(symbol: str, exchange: str = "NSE"):
    """
    Combines Real-time Yahoo Finance data with Groq AI analysis.
    """
    import yfinance as yf
    symbol = symbol.upper()
    try:
        ticker_symbol = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
        ticker = yf.Ticker(ticker_symbol)
        
        hist = ticker.history(period="3mo")
        info = ticker.info
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol} on {exchange}")

        curr = float(hist["Close"].iloc[-1])
        start = float(hist["Close"].iloc[0])
        ret_3m = ((curr - start) / start) * 100
        
        summary = (
            f"Stock: {symbol} | Price: Rs.{curr:.2f} | "
            f"3M Return: {ret_3m:.1f}% | PE: {info.get('trailingPE','N/A')} | "
            f"52W High: Rs.{info.get('fiftyTwoWeekHigh','N/A')} | "
            f"Sector: {info.get('sector','N/A')}"
        )

        analysis_completion = client.chat.completions.create(
            model=DEFAULT_GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are FinAI, an expert Indian stock market analyst. Provide a brief, high-level insight."},
                {"role": "user", "content": f"Analyze this data for {symbol}: {summary}"}
            ]
        )
        
        return {
            "symbol": symbol,
            "data": summary,
            "analysis": analysis_completion.choices[0].message.content,
            "engine": f"Groq/{DEFAULT_GROQ_MODEL}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/token-explainer")
async def explain_tokens():
    """
    Educational endpoint explaining AI costs.
    """
    return {
        "simple_explanation": "A TOKEN is a small piece of text - roughly one word or part of a word.",
        "examples": {
            "Hello": "1 token",
            "Nifty 50": "2 tokens",
            "What is the current RBI repo rate?": "8 tokens"
        },
        "comparison": {
            "Groq API": "Fastest inference, affordable for high-speed apps.",
            "Legacy APIs": "Slower and more expensive per million tokens."
        }
    }
