import uvicorn
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import httpx, os
from datetime import datetime

app = FastAPI(title="FinAI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

@app.get("/", include_in_schema=False)
async def root():
    with open("frontend/index.html", "r") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Surrogate-Control": "no-store",
        }
    )

@app.get("/health")
async def health():
    return {"status": "ok", "app": "FinAI", "version": "3.0.0"}

# Serve static files with cache busting
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/api/crypto/prices")
async def crypto_prices():
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://api.coingecko.com/api/v3/simple/price",
                params={"ids":"bitcoin,ethereum,binancecoin,solana","vs_currencies":"inr,usd","include_24hr_change":"true"})
            data = r.json()
        names = {"bitcoin":"Bitcoin","ethereum":"Ethereum","binancecoin":"BNB","solana":"Solana"}
        coins = []
        for cid, info in data.items():
            inr = info.get("inr",0); chg = info.get("inr_24h_change",0)
            fmt = f"Rs.{inr/10000000:.2f} Cr" if inr>10000000 else f"Rs.{inr/100000:.2f} L" if inr>100000 else f"Rs.{inr:,.2f}"
            coins.append({"id":cid,"name":names.get(cid,cid),"price_inr":round(inr,2),"formatted_inr":fmt,"change_24h_pct":round(chg,2),"direction":"up" if chg>=0 else "down"})
        return {"coins":coins,"timestamp":datetime.now().isoformat()}
    except Exception as e:
        return JSONResponse(status_code=503,content={"error":str(e)})

@app.get("/api/rbi/rates")
async def rbi_rates():
    return {"rates":{"repo_rate":{"value":6.00,"unit":"%"},"reverse_repo":{"value":3.35,"unit":"%"},"crr":{"value":4.00,"unit":"%"},"slr":{"value":18.00,"unit":"%"}},"last_updated":"April 2026","usd_inr":83.47}

@app.get("/api/stocks/indices")
async def stock_indices():
    try:
        results = {}
        async with httpx.AsyncClient(timeout=10) as c:
            for name,sym in [("NIFTY50","^NSEI"),("SENSEX","^BSESN"),("BANKNIFTY","^NSEBANK")]:
                try:
                    r = await c.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                        params={"interval":"1d","range":"2d"},headers={"User-Agent":"Mozilla/5.0"})
                    closes = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                    curr=closes[-1]; prev=closes[-2]; chg=((curr-prev)/prev)*100
                    results[name]={"value":round(curr,2),"change_pct":round(chg,2),"direction":"up" if chg>=0 else "down","formatted":f"{curr:,.2f}"}
                except:
                    results[name]={"error":"unavailable"}
        return {"indices":results,"timestamp":datetime.now().isoformat()}
    except Exception as e:
        return JSONResponse(status_code=503,content={"error":str(e)})

@app.get("/api/stocks/quote/{symbol}")
async def stock_quote(symbol:str):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}.NS",
                params={"interval":"1d","range":"5d"},headers={"User-Agent":"Mozilla/5.0"})
        d = r.json()["chart"]["result"][0]
        closes = d["indicators"]["quote"][0]["close"]
        curr=closes[-1]; prev=closes[-2]; chg=((curr-prev)/prev)*100
        meta = d["meta"]
        return {
            "symbol":symbol.upper(),
            "current_price":round(curr,2),
            "formatted":f"Rs.{curr:,.2f}",
            "change_pct":round(chg,2),
            "direction":"up" if chg>=0 else "down",
            "52w_high":round(meta.get("fiftyTwoWeekHigh",0),2),
            "52w_low":round(meta.get("fiftyTwoWeekLow",0),2),
            "currency":"INR"
        }
    except Exception as e:
        return JSONResponse(status_code=503,content={"error":str(e)})

@app.get("/api/mf/sip-calculator")
async def sip_calculator(monthly_amount:float=5000,annual_return_pct:float=12.0,years:int=10):
    r=(annual_return_pct/100)/12; n=years*12
    fv=monthly_amount*(((1+r)**n-1)/r)*(1+r); inv=monthly_amount*n; gain=fv-inv
    def fmt(v): return f"Rs.{v/10000000:.2f} Crore" if v>=10000000 else f"Rs.{v/100000:.2f} Lakh" if v>=100000 else f"Rs.{v:,.2f}"
    return {"monthly_sip":monthly_amount,"years":years,"total_invested":round(inv,2),"future_value":round(fv,2),"total_gain":round(gain,2),"wealth_ratio":round(fv/inv,2),"formatted":{"invested":fmt(inv),"wealth":fmt(fv),"gain":fmt(gain)}}

@app.get("/api/ml/sentiment")
async def market_sentiment():
    LEXICON={"record high":1.8,"rally":1.5,"profit":1.2,"growth":0.8,"gains":0.9,"strong":0.7,"surge":0.8,"beat":1.2,"crash":-1.8,"recession":-2.0,"npa":-1.5,"outflow":-1.3,"selloff":-1.5,"warning":-1.5,"concerns":-0.8,"inflation":-0.8,"fears":-1.0}
    try:
        import feedparser
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",headers={"User-Agent":"FinAI/2.0"})
        feed = feedparser.parse(r.text)
        headlines = [e.get("title","") for e in feed.entries[:15] if e.get("title")]
    except:
        headlines = ["Nifty hits record high on FII inflows","Market rallies on strong results","RBI holds rates steady"]
    scored = []
    for h in headlines:
        s = sum(v for t,v in LEXICON.items() if t in h.lower()); s=max(-1.0,min(1.0,s/3.0))
        scored.append({"headline":h,"score":round(s,3),"label":"BULLISH" if s>=0.15 else("BEARISH" if s<=-0.15 else "NEUTRAL")})
    mood = sum(s["score"] for s in scored)/len(scored) if scored else 0
    bull=sum(1 for s in scored if s["label"]=="BULLISH")
    bear=sum(1 for s in scored if s["label"]=="BEARISH")
    neut=sum(1 for s in scored if s["label"]=="NEUTRAL")
    return {"mood_score":round(mood,3),"mood_label":"BULLISH 📈" if mood>0.1 else("BEARISH 📉" if mood<-0.1 else "NEUTRAL ➡"),"prediction":"Nifty likely to open HIGHER" if mood>0.1 else("Nifty likely LOWER" if mood<-0.1 else "Direction uncertain"),"breakdown":{"bullish":bull,"bearish":bear,"neutral":neut},"top_headlines":sorted(scored,key=lambda x:abs(x["score"]),reverse=True)[:5],"timestamp":datetime.now().isoformat()}

@app.post("/api/ai/chat")
async def ai_chat(request:dict):
    messages = request.get("messages",[])
    language = request.get("language","english")

    # Fetch live market data to inject into AI context
    market_context = ""
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            # Get crypto prices
            r = await c.get("https://api.coingecko.com/api/v3/simple/price",
                params={"ids":"bitcoin,ethereum","vs_currencies":"inr","include_24hr_change":"true"})
            cd = r.json()
            btc = cd.get("bitcoin",{}).get("inr",0)
            eth = cd.get("ethereum",{}).get("inr",0)
            btc_chg = cd.get("bitcoin",{}).get("inr_24h_change",0)
            market_context += f"Bitcoin: Rs.{btc:,.0f} ({btc_chg:+.1f}% today). Ethereum: Rs.{eth:,.0f}. "
    except:
        pass

    try:
        async with httpx.AsyncClient(timeout=8) as c:
            # Get Nifty
            r = await c.get("https://query1.finance.yahoo.com/v8/finance/chart/^NSEI",
                params={"interval":"1d","range":"2d"},headers={"User-Agent":"Mozilla/5.0"})
            closes = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            curr=closes[-1]; prev=closes[-2]; chg=((curr-prev)/prev)*100
            market_context += f"Nifty 50: {curr:,.2f} ({chg:+.1f}% today). "
    except:
        pass

    market_context += "RBI Repo Rate: 6.00%. USD/INR: Rs.83.47. "
    market_context += f"Date: {datetime.now().strftime('%d %B %Y')}."

    # Check if user is asking about a specific stock price
    last_msg = messages[-1]["content"].lower() if messages else ""
    stock_data = ""
    stock_keywords = ["price","share","stock","quote","rate","value","worth","trading","nse","bse"]
    if any(kw in last_msg for kw in stock_keywords):
        # Extract possible stock symbol
        common_stocks = {
            "reliance":"RELIANCE","tcs":"TCS","infosys":"INFY","infy":"INFY",
            "hdfc":"HDFCBANK","hdfcbank":"HDFCBANK","icici":"ICICIBANK",
            "sbi":"SBIN","wipro":"WIPRO","bajaj":"BAJFINANCE",
            "kotak":"KOTAKBANK","axis":"AXISBANK","maruti":"MARUTI",
            "tatamotors":"TATAMOTORS","tata motors":"TATAMOTORS",
            "sunpharma":"SUNPHARMA","itc":"ITC","lt":"LT","ongc":"ONGC",
            "bharti":"BHARTIARTL","airtel":"BHARTIARTL","ntpc":"NTPC",
            "adani":"ADANIPORTS","titan":"TITAN","nestle":"NESTLEIND",
            "nifty":"^NSEI","sensex":"^BSESN"
        }
        for name, sym in common_stocks.items():
            if name in last_msg:
                try:
                    async with httpx.AsyncClient(timeout=8) as c:
                        suffix = "" if sym.startswith("^") else ".NS"
                        r = await c.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suffix}",
                            params={"interval":"1d","range":"2d"},headers={"User-Agent":"Mozilla/5.0"})
                        closes = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                        curr=closes[-1]; prev=closes[-2]; chg=((curr-prev)/prev)*100
                        stock_data = f"LIVE DATA for {sym}: Current price Rs.{curr:,.2f}, change {chg:+.2f}% today. 52W High: Rs.{r.json()['chart']['result'][0]['meta'].get('fiftyTwoWeekHigh',0):,.2f}, 52W Low: Rs.{r.json()['chart']['result'][0]['meta'].get('fiftyTwoWeekLow',0):,.2f}. "
                except:
                    pass
                break

    system_prompt = f"""You are FinAI, an intelligent Indian financial assistant. You have access to LIVE market data.

LIVE MARKET DATA RIGHT NOW:
{market_context}
{stock_data}

YOUR RULES:
1. ALWAYS answer the question directly — never say "check elsewhere" or "I don't have access"
2. If asked about a stock price and you have live data above, give the exact price
3. If asked about a stock not in your live data, give your best analysis based on recent trends and say it may vary slightly
4. Use Rs. for Indian Rupee prices
5. Be conversational, friendly and helpful like a knowledgeable friend
6. Give specific numbers and actionable advice
7. Keep responses concise — 3-5 sentences unless detailed analysis is needed
8. Always add a brief risk disclaimer for investment advice
9. Reply in {language}
10. You are NOT just a chatbot — you are a financial expert with live data access

NEVER say: "I don't have real-time data", "check a financial website", "I cannot provide", "please consult"
ALWAYS say: Give the actual answer with the data you have"""

    if not GROQ_KEY:
        return {
            "reply": f"FinAI is live! I have access to live market data. {market_context} Add your GROQ_API_KEY in Render Environment to enable full AI responses!",
            "engine": "no key"
        }

    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
                json={
                    "model":"llama3-8b-8192",
                    "messages":[
                        {"role":"system","content":system_prompt},
                        *messages[-8:]
                    ],
                    "max_tokens":800,
                    "temperature":0.7
                }
            )
            reply = r.json()["choices"][0]["message"]["content"]
            return {"reply":reply,"engine":"Groq/Llama3","cost":"Rs.0"}
    except Exception as e:
        return {"reply":f"Sorry, AI error: {str(e)[:80]}. Please try again!","engine":"error"}

@app.post("/api/financial-health-score")
async def financial_health_score(request:dict):
    return {"message":"Client-side scoring active"}

@app.post("/api/upi-analyzer")
async def upi_analyzer(request:dict):
    return {"message":"Client-side analysis active"}

@app.get("/api/rbi/msme-schemes")
async def msme_schemes():
    return {"schemes":[{"name":"MUDRA Shishu","max_loan":"Rs.50,000","portal":"mudra.org.in"},{"name":"MUDRA Kishore","max_loan":"Rs.5 Lakh","portal":"mudra.org.in"},{"name":"MUDRA Tarun","max_loan":"Rs.20 Lakh","portal":"mudra.org.in"},{"name":"CGTMSE","max_loan":"Rs.5 Crore","portal":"cgtmse.in"},{"name":"Stand-Up India","max_loan":"Rs.1 Crore","portal":"standupmitra.in"}]}

@app.get("/api/crypto/india-tax-guide")
async def crypto_tax():
    return {"flat_tax":"30% on ALL crypto gains","tds":"1% TDS above Rs.10,000","loss_setoff":"Cannot offset losses","itr":"Report in ITR-2/ITR-3 under VDA"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    uvicorn.run("main:app",host="0.0.0.0",port=port)
