import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import httpx, os
from datetime import datetime

app = FastAPI(title="FinAI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FinAI - Indian Financial Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500;600&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --dark:#07101f;--card:#0d1a2d;--surface:#111f35;
  --accent:#00e5aa;--gold:#f5c842;--red:#ff4466;
  --blue:#3b82f6;--purple:#a78bfa;--orange:#fb923c;
  --text:#e8f0fe;--muted:#4a6080;--border:#1a2d45;
}
body{background:var(--dark);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;overflow:hidden;}
::-webkit-scrollbar{width:3px;}::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
.ticker{background:var(--card);border-bottom:1px solid var(--border);overflow:hidden;padding:7px 0;font-family:'Space Mono',monospace;font-size:11px;color:var(--accent);white-space:nowrap;}
.ticker-inner{display:inline-block;animation:tick 35s linear infinite;}
@keyframes tick{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
header{background:var(--card);border-bottom:1px solid var(--border);padding:10px 20px;display:flex;align-items:center;justify-content:space-between;}
.logo{font-family:'Syne',sans-serif;font-size:22px;color:#fff;letter-spacing:-1px;}
.logo span{color:var(--accent);}
.live{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--accent);font-family:'Space Mono',monospace;}
.dot{width:7px;height:7px;border-radius:50%;background:var(--accent);animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
.layout{display:grid;grid-template-columns:220px 1fr;height:calc(100vh - 76px);}
.sidebar{background:var(--card);border-right:1px solid var(--border);overflow-y:auto;display:flex;flex-direction:column;}
.sidebar-section{padding:12px 12px 0;}
.sidebar-section h4{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;font-family:'Space Mono',monospace;}
.lang-select{width:100%;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12px;margin-bottom:12px;cursor:pointer;}
.stock-item{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px 11px;margin-bottom:7px;cursor:pointer;transition:all 0.2s;}
.stock-item:hover{border-color:var(--accent);transform:translateX(2px);}
.stock-name{font-size:11px;font-weight:700;color:#fff;}
.stock-price{font-size:12px;color:var(--text);font-family:'Space Mono',monospace;margin-top:2px;}
.stock-change{font-size:10px;margin-top:2px;}
.up{color:var(--accent);}.down{color:var(--red);}
.rbi-box{background:var(--surface);border-radius:8px;padding:10px;margin-bottom:10px;}
.rbi-row{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border);font-size:11px;}
.rbi-row:last-child{border-bottom:none;}
.rbi-val{color:var(--gold);font-weight:700;font-family:'Space Mono',monospace;}
.main{display:flex;flex-direction:column;overflow:hidden;background:var(--dark);}
.tabs{display:flex;gap:3px;padding:8px 12px;background:var(--card);border-bottom:1px solid var(--border);overflow-x:auto;}
.tabs::-webkit-scrollbar{height:0;}
.tab{padding:6px 12px;border-radius:16px;font-size:11px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:transparent;color:var(--muted);transition:all 0.2s;white-space:nowrap;}
.tab.active{background:var(--accent);color:var(--dark);border-color:var(--accent);}
.content{flex:1;overflow-y:auto;padding:14px;display:none;flex-direction:column;}
.content.active{display:flex;}
/* CHAT */
.chat-wrap{display:flex;flex-direction:column;height:100%;min-height:0;}
.messages{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:10px;padding-bottom:6px;min-height:0;}
.msg{display:flex;gap:8px;animation:fadeUp 0.3s ease;}
@keyframes fadeUp{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
.msg.user{flex-direction:row-reverse;}
.avatar{width:26px;height:26px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;margin-top:2px;}
.ai-av{background:linear-gradient(135deg,var(--accent),var(--blue));}
.user-av{background:var(--border);}
.bubble{max-width:78%;padding:9px 13px;font-size:13px;line-height:1.65;white-space:pre-wrap;word-break:break-word;}
.ai-bubble{background:var(--card);border:1px solid var(--border);border-radius:4px 12px 12px 12px;}
.user-bubble{background:linear-gradient(135deg,rgba(0,229,170,0.1),rgba(59,130,246,0.1));border:1px solid rgba(0,229,170,0.2);border-radius:12px 4px 12px 12px;}
.typing{display:flex;gap:4px;align-items:center;padding:8px 12px;}
.typing span{width:6px;height:6px;border-radius:50%;background:var(--accent);animation:blink 1.2s infinite;}
.typing span:nth-child(2){animation-delay:0.2s;}.typing span:nth-child(3){animation-delay:0.4s;}
@keyframes blink{0%,100%{opacity:0.2}50%{opacity:1}}
.quick-pills{display:flex;gap:5px;flex-wrap:wrap;padding:6px 0;flex-shrink:0;}
.pill{padding:4px 10px;border-radius:12px;font-size:10px;cursor:pointer;border:1px solid var(--border);background:transparent;color:var(--muted);transition:all 0.2s;white-space:nowrap;}
.pill:hover{color:var(--accent);border-color:var(--accent);}
.input-area{display:flex;gap:7px;padding:8px 0 0;border-top:1px solid var(--border);align-items:flex-end;flex-shrink:0;}
.chat-input{flex:1;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:9px 13px;color:var(--text);font-size:13px;font-family:'DM Sans',sans-serif;resize:none;min-height:40px;max-height:90px;outline:none;transition:border-color 0.2s;}
.chat-input:focus{border-color:var(--accent);}
.btn-send{padding:9px 16px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--blue));color:var(--dark);font-weight:700;font-size:12px;border:none;cursor:pointer;flex-shrink:0;}
.btn-send:disabled{opacity:0.4;cursor:not-allowed;}
.btn-voice{width:40px;height:40px;border-radius:10px;background:var(--surface);border:1px solid var(--border);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;transition:all 0.2s;flex-shrink:0;}
.btn-voice:hover{border-color:var(--accent);}
.btn-voice.recording{background:var(--red);border-color:var(--red);}
.voice-status{font-size:10px;color:var(--muted);padding:3px 0;font-family:'Space Mono',monospace;flex-shrink:0;}
/* CARDS */
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:12px;}
.card h3{font-size:12px;font-weight:700;color:var(--text);margin-bottom:10px;}
.metric-row{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px;}
.metric{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px;text-align:center;}
.metric-val{font-size:16px;font-weight:800;color:var(--accent);font-family:'Space Mono',monospace;}
.metric-lbl{font-size:9px;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:0.5px;}
/* CRYPTO */
.crypto-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;}
.crypto-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px;}
.coin-name{font-size:12px;font-weight:700;color:#fff;}
.coin-price{font-size:15px;font-weight:800;color:var(--accent);font-family:'Space Mono',monospace;margin:4px 0;}
.coin-chg{font-size:10px;}
.tax-note{background:rgba(245,200,66,0.07);border-left:2px solid var(--gold);padding:6px 8px;border-radius:0 5px 5px 0;margin-top:7px;font-size:10px;color:var(--muted);line-height:1.5;}
/* SIP */
.sip-form{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:12px;}
.form-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px;}
.form-group label{display:block;font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px;}
.form-group input,.form-group textarea{width:100%;background:var(--surface);border:1px solid var(--border);border-radius:7px;padding:7px 10px;color:var(--text);font-size:12px;outline:none;font-family:'DM Sans',sans-serif;}
.form-group input:focus,.form-group textarea:focus{border-color:var(--accent);}
.btn-calc{padding:9px 20px;background:linear-gradient(135deg,var(--accent),var(--blue));color:var(--dark);font-weight:700;border:none;border-radius:8px;cursor:pointer;font-size:12px;}
.sip-result{background:var(--surface);border-radius:10px;padding:12px;margin-top:10px;display:none;}
.sip-result.show{display:block;}
.result-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);font-size:12px;}
.result-row:last-child{border-bottom:none;}
.result-val{color:var(--gold);font-weight:700;font-family:'Space Mono',monospace;}
/* HEALTH SCORE */
.score-ring{width:130px;height:130px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;margin:0 auto 14px;border:8px solid var(--border);}
.score-num{font-size:34px;font-weight:800;font-family:'Space Mono',monospace;}
.score-lbl{font-size:9px;color:var(--muted);text-transform:uppercase;}
.breakdown-row{display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid var(--border);}
.breakdown-row:last-child{border-bottom:none;}
.breakdown-bar{flex:1;height:7px;background:var(--surface);border-radius:4px;overflow:hidden;}
.breakdown-fill{height:100%;border-radius:4px;transition:width 0.5s;}
.breakdown-name{font-size:10px;color:var(--muted);min-width:95px;}
.breakdown-score{font-size:10px;font-family:'Space Mono',monospace;color:var(--text);min-width:40px;text-align:right;}
.tip-item{background:var(--surface);border-left:3px solid var(--gold);padding:8px 10px;border-radius:0 7px 7px 0;margin-bottom:7px;font-size:11px;color:var(--text);line-height:1.7;}
/* UPI */
.upi-cat{display:flex;align-items:center;gap:7px;padding:7px 0;border-bottom:1px solid var(--border);}
.upi-cat:last-child{border-bottom:none;}
.upi-bar-wrap{flex:1;height:7px;background:var(--surface);border-radius:4px;overflow:hidden;}
.upi-bar{height:100%;border-radius:4px;}
.upi-catname{font-size:11px;color:var(--text);min-width:105px;}
.upi-amt{font-size:10px;font-family:'Space Mono',monospace;color:var(--gold);min-width:75px;text-align:right;}
.upi-pct{font-size:9px;color:var(--muted);min-width:32px;text-align:right;}
.waste-card{background:rgba(255,68,102,0.08);border:1px solid rgba(255,68,102,0.2);border-radius:9px;padding:10px;margin-bottom:7px;}
.invest-card{background:rgba(0,229,170,0.07);border:1px solid rgba(0,229,170,0.2);border-radius:9px;padding:10px;margin-bottom:7px;}
/* LANG */
.lang-row{background:var(--card);border:1px solid var(--border);border-radius:9px;padding:10px 12px;margin-bottom:7px;display:flex;gap:10px;}
.lang-name{font-size:9px;font-weight:700;color:var(--accent);margin-bottom:2px;font-family:'Space Mono',monospace;}
.lang-text{font-size:11px;color:var(--text);line-height:1.5;}
/* MOOD */
.mood-bar{height:9px;background:var(--surface);border-radius:5px;overflow:hidden;margin:7px 0;}
.mood-fill{height:100%;border-radius:5px;transition:width 0.5s;}
.headline-item{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid var(--border);font-size:11px;gap:7px;}
.headline-item:last-child{border-bottom:none;}
.badge{padding:2px 7px;border-radius:9px;font-size:9px;font-weight:700;white-space:nowrap;}
.badge-bull{background:rgba(0,229,170,0.12);color:var(--accent);}
.badge-bear{background:rgba(255,68,102,0.12);color:var(--red);}
.badge-neut{background:rgba(245,200,66,0.12);color:var(--gold);}
/* CHECKBOX */
.check-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;}
.check-label{display:flex;align-items:center;gap:7px;font-size:12px;cursor:pointer;background:var(--surface);padding:9px 10px;border-radius:7px;border:1px solid var(--border);}
.check-label input{width:15px;height:15px;accent-color:var(--accent);}
button{cursor:pointer;font-family:'DM Sans',sans-serif;}
</style>
</head>
<body>

<header>
  <div class="logo">Fin<span>AI</span> 🇮🇳</div>
  <div style="font-size:11px;color:var(--muted)">Indian Financial Intelligence</div>
  <div class="live"><span class="dot"></span>LIVE</div>
</header>

<div class="ticker">
  <div class="ticker-inner" id="tickerText">Loading...</div>
</div>

<div class="layout">
  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sidebar-section">
      <h4>Language / भाषा</h4>
      <select class="lang-select" id="langSelect" onchange="onLangChange(this.value)">
        <option value="english">🇬🇧 English</option>
        <option value="hindi">🇮🇳 हिंदी Hindi</option>
        <option value="tamil">🇮🇳 தமிழ் Tamil</option>
        <option value="telugu">🇮🇳 తెలుగు Telugu</option>
        <option value="bengali">🇮🇳 বাংলা Bengali</option>
        <option value="marathi">🇮🇳 मराठी Marathi</option>
        <option value="gujarati">🇮🇳 ગુજરાતી Gujarati</option>
        <option value="kannada">🇮🇳 ಕನ್ನಡ Kannada</option>
      </select>
    </div>
    <div class="sidebar-section">
      <h4>NSE Stocks</h4>
      <div class="stock-item" onclick="stockChat('RELIANCE')"><div class="stock-name">RELIANCE</div><div class="stock-price">₹2,847.30</div><div class="stock-change up">▲ +1.24%</div></div>
      <div class="stock-item" onclick="stockChat('TCS')"><div class="stock-name">TCS</div><div class="stock-price">₹3,612.15</div><div class="stock-change up">▲ +0.87%</div></div>
      <div class="stock-item" onclick="stockChat('HDFCBANK')"><div class="stock-name">HDFC BANK</div><div class="stock-price">₹1,589.40</div><div class="stock-change down">▼ -0.32%</div></div>
      <div class="stock-item" onclick="stockChat('INFY')"><div class="stock-name">INFOSYS</div><div class="stock-price">₹1,421.70</div><div class="stock-change up">▲ +2.11%</div></div>
      <div class="stock-item" onclick="stockChat('SBIN')"><div class="stock-name">SBI</div><div class="stock-price">₹812.45</div><div class="stock-change up">▲ +0.56%</div></div>
      <div class="stock-item" onclick="stockChat('WIPRO')"><div class="stock-name">WIPRO</div><div class="stock-price">₹487.25</div><div class="stock-change down">▼ -0.67%</div></div>
    </div>
    <div class="sidebar-section" style="padding-bottom:12px;">
      <h4>RBI Rates</h4>
      <div class="rbi-box">
        <div class="rbi-row"><span>Repo Rate</span><span class="rbi-val">6.00%</span></div>
        <div class="rbi-row"><span>Reverse Repo</span><span class="rbi-val">3.35%</span></div>
        <div class="rbi-row"><span>CRR</span><span class="rbi-val">4.00%</span></div>
        <div class="rbi-row"><span>SLR</span><span class="rbi-val">18.00%</span></div>
        <div class="rbi-row"><span>USD/INR</span><span class="rbi-val">₹83.47</span></div>
      </div>
    </div>
  </div>

  <!-- MAIN -->
  <div class="main">
    <div class="tabs">
      <button class="tab active" onclick="switchTab('chat',this)">💬 AI Chat</button>
      <button class="tab" onclick="switchTab('crypto',this)">₿ Crypto</button>
      <button class="tab" onclick="switchTab('stocks',this)">📈 Stocks</button>
      <button class="tab" onclick="switchTab('sip',this)">💰 SIP</button>
      <button class="tab" onclick="switchTab('sentiment',this)">😊 Sentiment</button>
      <button class="tab" onclick="switchTab('health',this)">🏥 Health Score</button>
      <button class="tab" onclick="switchTab('upi',this)">💳 UPI Analyzer</button>
      <button class="tab" onclick="switchTab('languages',this)">🌐 Languages</button>
    </div>

    <!-- AI CHAT TAB -->
    <div class="content active" id="tab-chat">
      <div class="chat-wrap">
        <div class="messages" id="messages">
          <div class="msg"><div class="avatar ai-av">₹</div>
            <div class="bubble ai-bubble">Namaste! 🙏 I am FinAI — your Indian financial companion.

I can help with stocks, crypto, SIP, RBI rates, budget analysis and more. You can also use the 🎤 voice button to speak your question!

What would you like to know today?</div></div>
        </div>
        <div class="quick-pills">
          <button class="pill" onclick="ask('What is RBI repo rate?')">RBI Rate</button>
          <button class="pill" onclick="ask('Should I buy RELIANCE stock?')">RELIANCE?</button>
          <button class="pill" onclick="ask('Bitcoin price in rupees today')">Bitcoin ₹</button>
          <button class="pill" onclick="ask('Best SIP for beginners India')">Best SIP</button>
          <button class="pill" onclick="ask('Explain Nifty 50 simply')">Nifty 50?</button>
          <button class="pill" onclick="ask('Crypto tax rules India 2025')">Crypto Tax</button>
          <button class="pill" onclick="ask('How to start investing with Rs.1000 per month?')">Start Investing</button>
          <button class="pill" onclick="ask('ELSS vs PPF which is better?')">ELSS vs PPF</button>
        </div>
        <div class="input-area">
          <button class="btn-voice" id="voiceBtn" onclick="toggleVoice()" title="Click to speak">🎤</button>
          <textarea class="chat-input" id="chatInput" rows="1" placeholder="Type or speak your financial question..." onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
          <button class="btn-send" id="sendBtn" onclick="sendMsg('chat')">Send</button>
        </div>
        <div class="voice-status" id="voiceStatus"></div>
      </div>
    </div>

    <!-- CRYPTO TAB -->
    <div class="content" id="tab-crypto">
      <div class="crypto-grid" id="cryptoGrid">
        <div class="crypto-card"><div class="coin-name">₿ Bitcoin</div><div class="coin-price" id="btcPrice">Loading...</div><div class="coin-chg" id="btcChg"></div><div class="tax-note">🇮🇳 30% tax on profits + 1% TDS above ₹10,000</div></div>
        <div class="crypto-card"><div class="coin-name">Ξ Ethereum</div><div class="coin-price" id="ethPrice">Loading...</div><div class="coin-chg" id="ethChg"></div><div class="tax-note">🇮🇳 30% tax on profits + 1% TDS above ₹10,000</div></div>
        <div class="crypto-card"><div class="coin-name">BNB</div><div class="coin-price" id="bnbPrice">Loading...</div><div class="coin-chg" id="bnbChg"></div><div class="tax-note">🇮🇳 30% tax on profits + 1% TDS above ₹10,000</div></div>
        <div class="crypto-card"><div class="coin-name">◎ Solana</div><div class="coin-price" id="solPrice">Loading...</div><div class="coin-chg" id="solChg"></div><div class="tax-note">🇮🇳 30% tax on profits + 1% TDS above ₹10,000</div></div>
      </div>
       <div class="card">
        <h3>💬 Chat about Crypto — Type or Speak!</h3>
        <div class="messages" id="cryptoMessages" style="max-height:180px;overflow-y:auto;margin-bottom:8px;gap:8px;display:flex;flex-direction:column;">
          <div class="msg"><div class="avatar ai-av">₹</div>
            <div class="bubble ai-bubble" id="cryptoGreeting">Hey! Live crypto prices loaded above 🚀 Ask me anything about Bitcoin, Ethereum, crypto tax in India, or which crypto to invest in!</div></div>
        </div>
        <div class="quick-pills">
          <button class="pill" onclick="askInTab('Is Bitcoin a good investment in India?','crypto')">Bitcoin good buy?</button>
          <button class="pill" onclick="askInTab('Crypto tax rules India 2025 explained simply','crypto')">Crypto Tax</button>
          <button class="pill" onclick="askInTab('Difference between Bitcoin and Ethereum','crypto')">BTC vs ETH</button>
          <button class="pill" onclick="askInTab('Best Indian crypto exchanges like WazirX CoinDCX','crypto')">Best Exchanges</button>
          <button class="pill" onclick="askInTab('Should I invest in Solana?','crypto')">Solana?</button>
        </div>
        <div class="input-area" style="padding-top:8px;">
          <button class="btn-voice" id="cryptoVoiceBtn" onclick="toggleVoiceForTab('crypto')" title="Speak">🎤</button>
          <textarea class="chat-input" id="cryptoInput" rows="1" placeholder="Ask anything about crypto..." onkeydown="handleTabKey(event,'crypto')" oninput="autoResize(this)"></textarea>
          <button class="btn-send" id="cryptoSendBtn" onclick="sendMsg('crypto')">Send</button>
        </div>
        <div class="voice-status" id="cryptoVoiceStatus"></div>
      </div>
    </div>

    <!-- STOCKS TAB -->
    <div class="content" id="tab-stocks">
      <div class="metric-row">
        <div class="metric"><div class="metric-val" id="niftyVal">--</div><div class="metric-lbl">NIFTY 50</div></div>
        <div class="metric"><div class="metric-val" id="sensexVal">--</div><div class="metric-lbl">SENSEX</div></div>
        <div class="metric"><div class="metric-val" id="bankVal">--</div><div class="metric-lbl">BANK NIFTY</div></div>
      </div>
      <div class="card">
        <h3>Search & Analyse Any NSE Stock</h3>
        <div style="display:flex;gap:8px;margin-bottom:10px;">
          <input id="stockSearch" placeholder="e.g. RELIANCE, TCS, HDFCBANK..." style="flex:1;background:var(--surface);border:1px solid var(--border);border-radius:7px;padding:8px 10px;color:var(--text);font-size:12px;outline:none;">
          <button class="btn-calc" onclick="analyseStock()">Analyse</button>
        </div>
        <div id="stockResult" style="display:none;background:var(--surface);border-radius:8px;padding:10px;font-size:12px;line-height:1.7;"></div>
      </div>
      <div class="card">
        <h3>💬 Chat about Stocks</h3>
        <div class="messages" id="stocksMessages" style="max-height:160px;overflow-y:auto;margin-bottom:8px;gap:8px;display:flex;flex-direction:column;">
          <div class="msg"><div class="avatar ai-av">₹</div>
            <div class="bubble ai-bubble">Hey! 📈 I can analyse any NSE/BSE stock for you. Search above or ask me anything about the Indian stock market!</div></div>
        </div>
        <div class="quick-pills">
          <button class="pill" onclick="askInTab('What are top gainers on NSE today?','stocks')">Top Gainers</button>
          <button class="pill" onclick="askInTab('What is Nifty 50 explained simply','stocks')">What is Nifty?</button>
          <button class="pill" onclick="askInTab('How to start investing in stocks India beginner','stocks')">How to Start</button>
          <button class="pill" onclick="askInTab('What is PE ratio and how to use it?','stocks')">PE Ratio?</button>
        </div>
        <div class="input-area" style="padding-top:8px;">
          <button class="btn-voice" id="stocksVoiceBtn" onclick="toggleVoiceForTab('stocks')" title="Speak">🎤</button>
          <textarea class="chat-input" id="stocksInput" rows="1" placeholder="Ask about any stock or the market..." onkeydown="handleTabKey(event,'stocks')" oninput="autoResize(this)"></textarea>
          <button class="btn-send" id="stocksSendBtn" onclick="sendMsg('stocks')">Send</button>
        </div>
        <div class="voice-status" id="stocksVoiceStatus"></div>
      </div>
    </div>

    <!-- SIP TAB -->
    <div class="content" id="tab-sip">
      <div class="sip-form">
        <h3 style="margin-bottom:10px;">💰 SIP Wealth Calculator</h3>
        <div class="form-row">
          <div class="form-group"><label>Monthly SIP (₹)</label><input type="number" id="sipAmt" value="5000" min="100"></div>
          <div class="form-group"><label>Annual Return (%)</label><input type="number" id="sipRate" value="12" min="1" max="30"></div>
          <div class="form-group"><label>Years</label><input type="number" id="sipYrs" value="20" min="1" max="40"></div>
        </div>
        <button class="btn-calc" onclick="calcSIP()" style="width:100%;">Calculate Wealth 🚀</button>
        <div class="sip-result" id="sipResult">
          <div class="result-row"><span>Total Invested</span><span class="result-val" id="sipInv">-</span></div>
          <div class="result-row"><span>Expected Wealth</span><span class="result-val" id="sipWealth">-</span></div>
          <div class="result-row"><span>Total Gains</span><span class="result-val" id="sipGain">-</span></div>
          <div class="result-row"><span>Wealth Multiplier</span><span class="result-val" id="sipMult">-</span></div>
          <div id="sipComment" style="margin-top:8px;padding:9px;background:var(--card);border-radius:7px;font-size:11px;color:var(--muted);line-height:1.7;border-left:3px solid var(--accent);"></div>
        </div>
      </div>
      <div class="card">
        <h3>💬 Ask About Investing</h3>
        <div class="messages" id="sipMessages" style="max-height:140px;overflow-y:auto;margin-bottom:8px;gap:8px;display:flex;flex-direction:column;">
          <div class="msg"><div class="avatar ai-av">₹</div>
            <div class="bubble ai-bubble">Hey! 💰 Calculate your SIP above or ask me anything about mutual funds, SIP, and growing wealth in India!</div></div>
        </div>
        <div class="quick-pills">
          <button class="pill" onclick="askInTab('What is SIP and how does it work?','sip')">What is SIP?</button>
          <button class="pill" onclick="askInTab('Best mutual funds for SIP in India 2025','sip')">Best MF</button>
          <button class="pill" onclick="askInTab('What is ELSS mutual fund?','sip')">What is ELSS?</button>
          <button class="pill" onclick="askInTab('Direct vs regular mutual fund difference','sip')">Direct vs Regular</button>
        </div>
        <div class="input-area" style="padding-top:8px;">
          <button class="btn-voice" id="sipVoiceBtn" onclick="toggleVoiceForTab('sip')" title="Speak">🎤</button>
          <textarea class="chat-input" id="sipInput" rows="1" placeholder="Ask about SIP, mutual funds..." onkeydown="handleTabKey(event,'sip')" oninput="autoResize(this)"></textarea>
          <button class="btn-send" id="sipSendBtn" onclick="sendMsg('sip')">Send</button>
        </div>
        <div class="voice-status" id="sipVoiceStatus"></div>
      </div>
    </div>

    <!-- SENTIMENT TAB -->
    <div class="content" id="tab-sentiment">
      <div class="card">
        <h3>Today's Market Mood</h3>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
          <span style="font-size:13px;" id="moodLabel">Analysing headlines...</span>
          <span style="font-size:18px;font-weight:800;font-family:'Space Mono',monospace;" id="moodScore">--</span>
        </div>
        <div class="mood-bar"><div class="mood-fill" id="moodFill" style="width:50%;background:var(--gold);"></div></div>
        <div style="display:flex;justify-content:space-between;font-size:9px;color:var(--muted);margin-top:3px;"><span>BEARISH 📉</span><span>NEUTRAL</span><span>BULLISH 📈</span></div>
        <div style="margin-top:8px;font-size:11px;color:var(--muted);" id="moodPrediction"></div>
      </div>
      <div class="card">
        <h3>Headlines Scored by AI</h3>
        <div id="headlineList"><div style="color:var(--muted);font-size:12px;">Loading headlines...</div></div>
      </div>
    </div>

    <!-- HEALTH SCORE TAB -->
    <div class="content" id="tab-health">
      <div class="card">
        <h3>🏥 Financial Health Score — Like CIBIL but Complete</h3>
        <div class="form-row">
          <div class="form-group"><label>Monthly Income (₹)</label><input type="number" id="hIncome" placeholder="e.g. 50000"></div>
          <div class="form-group"><label>Monthly Savings (₹)</label><input type="number" id="hSavings" placeholder="e.g. 10000"></div>
          <div class="form-group"><label>Monthly Investments (₹)</label><input type="number" id="hInvest" placeholder="e.g. 5000"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>Monthly EMI (₹)</label><input type="number" id="hEmi" placeholder="0 if none"></div>
          <div class="form-group"><label>Emergency Fund (months)</label><input type="number" id="hEmFund" placeholder="0 if none"></div>
          <div class="form-group"><label>Your Age</label><input type="number" id="hAge" placeholder="e.g. 22"></div>
        </div>
        <div class="check-grid">
          <label class="check-label"><input type="checkbox" id="hHealth"> Health Insurance</label>
          <label class="check-label"><input type="checkbox" id="hTerm"> Term Insurance</label>
          <label class="check-label"><input type="checkbox" id="hEmergency"> Emergency Fund</label>
          <label class="check-label"><input type="checkbox" id="hRetire"> Retirement Plan (NPS/PPF)</label>
        </div>
        <button class="btn-calc" onclick="calcHealth()" style="width:100%;">Calculate My Health Score 🏥</button>
      </div>
      <div id="healthResult" style="display:none;">
        <div class="card" style="text-align:center;">
          <div class="score-ring" id="scoreRing">
            <div class="score-num" id="scoreNum">--</div>
            <div class="score-lbl">out of 100</div>
          </div>
          <div style="font-size:17px;font-weight:800;margin-bottom:5px;" id="scoreRating"></div>
          <div style="font-size:11px;color:var(--muted);margin-bottom:7px;" id="scorePercentile"></div>
          <div style="font-size:12px;line-height:1.7;" id="scoreSummary"></div>
        </div>
        <div class="card">
          <h3>Score Breakdown</h3>
          <div id="breakdownList"></div>
        </div>
        <div class="card">
          <h3>🎯 Your Action Plan</h3>
          <div id="tipsList"></div>
          <div id="aiPlan" style="display:none;margin-top:8px;padding:10px;background:var(--surface);border-radius:7px;font-size:11px;color:var(--text);line-height:1.8;border-left:3px solid var(--accent);"></div>
        </div>
      </div>
    </div>

     <!-- UPI ANALYZER TAB -->
    <div class="content" id="tab-upi">
      <div class="card">
        <h3>💳 UPI Budget Analyzer — Find Where Your Money Goes</h3>
        <p style="font-size:11px;color:var(--muted);margin-bottom:8px;">Paste your UPI/bank transactions below. Works with PhonePe, GPay, Paytm, or any bank statement. Each transaction on a new line.</p>
        <textarea id="upiText" rows="7" style="width:100%;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:9px;color:var(--text);font-size:11px;resize:vertical;outline:none;font-family:'DM Sans',sans-serif;margin-bottom:8px;" placeholder="Paste transactions here. Example:
Swiggy food order Rs.450
Ola cab 180
Amazon Rs.1250
Netflix 499
Electricity bill 850
Zerodha SIP 3000
BigBasket 1200
Zomato 320"></textarea>
        <div style="display:flex;gap:8px;align-items:flex-end;">
          <div class="form-group" style="flex:1;margin:0;"><label>Monthly Income ₹ (optional)</label><input type="number" id="upiIncome" placeholder="e.g. 50000"></div>
          <button class="btn-calc" onclick="analyzeUPI()">Analyse 🔍</button>
        </div>
      </div>
      <div id="upiResult" style="display:none;">
        <div class="metric-row">
          <div class="metric"><div class="metric-val" id="upiTotal">-</div><div class="metric-lbl">Total Spent</div></div>
          <div class="metric"><div class="metric-val" id="upiTxns">-</div><div class="metric-lbl">Transactions</div></div>
          <div class="metric"><div class="metric-val" id="upiTop" style="font-size:12px;">-</div><div class="metric-lbl">Top Category</div></div>
        </div>
        <div class="card"><h3>Spending Breakdown</h3><div id="upiBreakdown"></div></div>
        <div id="upiWaste" style="display:none;" class="card"><h3>⚠️ Wasteful Spending</h3><div id="upiWasteList"></div></div>
        <div id="upiInvestSection" style="display:none;" class="card"><h3>🚀 What If You Invested Instead?</h3><div id="upiInvestList"></div></div>
        <div id="upiAiTips" style="display:none;" class="card"><h3>💡 AI Money Tips</h3><div id="upiAiContent" style="font-size:12px;line-height:1.8;color:var(--text);"></div></div>
      </div>
    </div>

    <!-- LANGUAGES TAB -->
    <div class="content" id="tab-languages">
      <div class="card" style="margin-bottom:12px;">
        <h3>🌐 Same Signal — 8 Indian Languages</h3>
        <p style="font-size:11px;color:var(--muted);margin-bottom:10px;">RSI is 72 for RELIANCE — what does this mean?</p>
        <div id="langGrid"></div>
      </div>
      <div class="card">
        <h3>Ask in Your Language</h3>
        <div class="quick-pills">
          <button class="pill" onclick="ask('RELIANCE ka stock khareedna chahiye? Hindi mein batao')">हिंदी में पूछो</button>
          <button class="pill" onclick="ask('Bitcoin invest karna sahi hai? Simple Hindi mein')">Bitcoin Hindi</button>
          <button class="pill" onclick="ask('SIP kya hota hai beginners ke liye explain karo')">SIP Hindi</button>
        </div>
      </div>
    </div>

  </div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────
let currentLang = 'english';
let chatHistories = { chat:[], crypto:[], stocks:[], sip:[] };
let isRecording = false;
let recognition = null;
let activeVoiceTab = 'chat';

// ── LIVE TICKER ────────────────────────────────────────────────────
async function loadLiveTicker() {

  try {

    const stockRes =
      await fetch('/api/stocks/indices');

    const stockData =
      await stockRes.json();

    const cryptoRes =
      await fetch('/api/crypto/prices');

    const cryptoData =
      await cryptoRes.json();

    const nifty =
      stockData.indices?.NIFTY50 || {};

    const sensex =
      stockData.indices?.SENSEX || {};

    const bank =
      stockData.indices?.BANKNIFTY || {};

    const btc =
      cryptoData.coins?.find(
        c => c.id === 'bitcoin'
      ) || {};

    const eth =
      cryptoData.coins?.find(
        c => c.id === 'ethereum'
      ) || {};

    const ticker = `
      NIFTY 50: ${nifty.formatted || '--'}
      ${nifty.direction === 'up' ? '▲' : '▼'}
      ${nifty.change_pct || 0}%  •

      SENSEX: ${sensex.formatted || '--'}
      ${sensex.direction === 'up' ? '▲' : '▼'}
      ${sensex.change_pct || 0}%  •

      BANK NIFTY: ${bank.formatted || '--'}
      ${bank.direction === 'up' ? '▲' : '▼'}
      ${bank.change_pct || 0}%  •

      BTC/INR: ${btc.formatted_inr || '--'}
      ${btc.change_24h_pct >= 0 ? '▲' : '▼'}
      ${btc.change_24h_pct || 0}%  •

      ETH/INR: ${eth.formatted_inr || '--'}
      ${eth.change_24h_pct >= 0 ? '▲' : '▼'}
      ${eth.change_24h_pct || 0}%  •
    `;

    document.getElementById(
      'tickerText'
    ).textContent = ticker + ticker;

  } catch(err) {

    console.error(
      'LIVE TICKER ERROR:',
      err
    );

  }
}

loadLiveTicker();

setInterval(loadLiveTicker, 30000);

// ── Tab switching ──────────────────────────────────────────────────
function switchTab(tab, btn) {
  document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  btn.classList.add('active');
  if (tab === 'crypto') loadCrypto();
  if (tab === 'stocks') loadIndices();
  if (tab === 'sentiment') loadSentiment();
  if (tab === 'languages') renderLangs();
}

// ── Language ───────────────────────────────────────────────────────
function onLangChange(lang) {
  currentLang = lang;
  const g = {english:"Language set to English!",hindi:"भाषा हिंदी में बदल दी!",tamil:"மொழி தமிழாக மாற்றப்பட்டது!",telugu:"భాష తెలుగులో మార్చబడింది!",bengali:"ভাষা বাংলায় পরিবর্তিত হয়েছে!",marathi:"भाषा मराठीत बदलली!",gujarati:"ભાષા ગુજરાતીમાં બદલાઈ!",kannada:"ಭಾಷೆ ಕನ್ನಡಕ್ಕೆ ಬದಲಾಯಿತು!"};
  addBubble('messages', g[lang] || g.english);
}

// ── Chat ───────────────────────────────────────────────────────────
function addBubble(containerId, text, isUser=false) {
  const c = document.getElementById(containerId);
  if (!c) return;
  const d = document.createElement('div');
  d.className = 'msg' + (isUser ? ' user' : '');
  d.innerHTML = `<div class="avatar ${isUser?'user-av':'ai-av'}">${isUser?'👤':'₹'}</div><div class="bubble ${isUser?'user-bubble':'ai-bubble'}"></div>`;
  c.appendChild(d);
  const bubble = d.querySelector('.bubble');
  if (!isUser) {
    let i = 0;
    const iv = setInterval(() => { bubble.textContent += text[i]; i++; if (i >= text.length) clearInterval(iv); }, 12);
  } else {
    bubble.textContent = text;
  }
  c.scrollTop = c.scrollHeight;
}

function showTypingIn(containerId) {
  const c = document.getElementById(containerId);
  if (!c) return;
  const d = document.createElement('div');
  d.className = 'msg'; d.id = containerId + '-typing';
  d.innerHTML = `<div class="avatar ai-av">₹</div><div class="bubble ai-bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
  c.appendChild(d); c.scrollTop = c.scrollHeight;
}

function removeTypingFrom(containerId) {
  const t = document.getElementById(containerId + '-typing');
  if (t) t.remove();
}

function getTabContext(tab) {
  const contexts = {
    chat:   "You are FinAI, an expert Indian financial assistant. Answer in " + currentLang + ". Use Rs. for prices. Educational only, not SEBI advice.",
    crypto: "You are FinAI, a crypto expert for Indian markets. Focus on crypto topics — Bitcoin, Ethereum, altcoins, Indian crypto tax (30% flat), exchanges like WazirX/CoinDCX. Answer in " + currentLang + ". Keep it simple for beginners.",
    stocks: "You are FinAI, an NSE/BSE stock market expert. Focus on Indian stocks, Nifty, Sensex, sector analysis. Answer in " + currentLang + ". Use Rs. for prices. Educational only.",
    sip:    "You are FinAI, a mutual fund and SIP expert for India. Focus on SIP, mutual funds, ELSS, index funds, compounding. Answer in " + currentLang + ". Educational only."
  };
  return contexts[tab] || contexts.chat;
}

async function sendMsg(tab) {
  const inputId = tab === 'chat' ? 'chatInput' : tab + 'Input';
  const msgId   = tab === 'chat' ? 'messages'  : tab + 'Messages';
  const input = document.getElementById(inputId);
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;
  input.value = ''; input.style.height = 'auto';
  addBubble(msgId, text, true);

  // Try to fetch live stock price if user asked about one
  let liveData = '';
  const textLower = text.toLowerCase();
  const stockMap = {
    'reliance':'RELIANCE','tcs':'TCS','infosys':'INFY','infy':'INFY',
    'hdfc':'HDFCBANK','hdfcbank':'HDFCBANK','icici':'ICICIBANK',
    'sbi':'SBIN','wipro':'WIPRO','bajaj':'BAJFINANCE','kotak':'KOTAKBANK',
    'axis':'AXISBANK','maruti':'MARUTI','itc':'ITC','airtel':'BHARTIARTL',
    'titan':'TITAN','nestle':'NESTLEIND','lt':'LT','ongc':'ONGC',
    'tatamotors':'TATAMOTORS','tata motors':'TATAMOTORS','ntpc':'NTPC',
    'adani':'ADANIPORTS','bajajfinance':'BAJFINANCE','sunpharma':'SUNPHARMA'
  };
  for (const [name, sym] of Object.entries(stockMap)) {
    if (textLower.includes(name)) {
      try {
        const r = await fetch('/api/stocks/quote/' + sym);
        const d = await r.json();
        if (d.current_price) {
          liveData = 'LIVE NSE DATA: ' + sym + ' is trading at Rs.' + d.current_price.toLocaleString('en-IN') + ' (' + (d.change_pct >= 0 ? '+' : '') + d.change_pct + '% today). 52W High: Rs.' + d['52w_high'].toLocaleString('en-IN') + ', 52W Low: Rs.' + d['52w_low'].toLocaleString('en-IN') + '.';
        }
      } catch(e) {}
      break;
    }
  }

  // Also fetch crypto if asked
  const cryptoMap = {'bitcoin':'bitcoin','btc':'bitcoin','ethereum':'ethereum','eth':'ethereum','bnb':'binancecoin','solana':'solana','sol':'solana'};
  for (const [name, id] of Object.entries(cryptoMap)) {
    if (textLower.includes(name)) {
      try {
        const r = await fetch('/api/crypto/prices');
        const d = await r.json();
        const coin = d.coins.find(c => c.id === id);
        if (coin) liveData += ' LIVE CRYPTO: ' + coin.name + ' = ' + coin.formatted_inr + ' (' + (coin.change_24h_pct >= 0 ? '+' : '') + coin.change_24h_pct + '% today).';
      } catch(e) {}
      break;
    }
  }

  const contextMsg = liveData ? {role:'system', content: getTabContext(tab) + ' ' + liveData} : {role:'system', content: getTabContext(tab)};

  chatHistories[tab].push({role:'user', content:text});
  showTypingIn(msgId);
  const btnMap = {
    chat: 'sendBtn',
    crypto: 'cryptoSendBtn',
    stocks: 'stocksSendBtn',
    sip: 'sipSendBtn'
  };

  const btnId = btnMap[tab];
  if (btnId) document.getElementById(btnId).disabled = true;

  try {
    const res = await fetch(window.location.origin + '/api/ai/chat', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        messages: [contextMsg, ...chatHistories[tab].slice(-8)],
        language: currentLang
      })
    });
    if (!res.ok) {
      throw new Error('Server returned ' + res.status);
    }

    const data = await res.json();
    removeTypingFrom(msgId);
    const reply = data.reply || 'Sorry, could not process that. Try again!';
    addBubble(msgId, reply);
    chatHistories[tab].push({role:'assistant', content:reply});
    if (chatHistories[tab].length > 16) chatHistories[tab] = chatHistories[tab].slice(-16);
  } catch(e) {
    removeTypingFrom(msgId);
    console.error('AI FETCH ERROR:', e);
    addBubble(msgId, 'Connection/API error: ' + e.message);
  }
  if (btnId) document.getElementById(btnId).disabled = false;
}

function ask(q) {
  document.getElementById('chatInput').value = q;
  sendMsg('chat');
}

function askInTab(q, tab) {
  const inputId = tab + 'Input';
  const el = document.getElementById(inputId);
  if (el) { el.value = q; sendMsg(tab); }
}

function stockChat(sym) { ask('Analyse ' + sym + ' NSE stock. Should I buy sell or hold? Explain simply.'); }
function handleKey(e) { if (e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg('chat');} }
function handleTabKey(e, tab) { if (e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg(tab);} }
function autoResize(el) { el.style.height='auto'; el.style.height=Math.min(el.scrollHeight,90)+'px'; }

// ── Voice ──────────────────────────────────────────────────────────
const LANG_CODES = {english:'en-IN',hindi:'hi-IN',tamil:'ta-IN',telugu:'te-IN',bengali:'bn-IN',marathi:'mr-IN',gujarati:'gu-IN',kannada:'kn-IN'};

function startRecognition(inputId, statusId, tab) {
  const statusEl = document.getElementById(statusId);
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    statusEl.textContent = '⚠️ Voice needs Chrome browser.'; return;
  }
  if (isRecording) { stopVoice(); return; }
  // Request microphone permission explicitly first
  navigator.mediaDevices.getUserMedia({audio: true})
    .then(stream => {
      stream.getTracks().forEach(track => track.stop()); // stop preview stream
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition = new SR();
      recognition.lang = LANG_CODES[currentLang] || 'en-IN';
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;
      recognition.onstart = () => {
        isRecording = true; activeVoiceTab = tab;
        statusEl.textContent = '🎤 Listening... Speak now!';
        const voiceBtnMap = {
          chat: 'voiceBtn',
          crypto: 'cryptoVoiceBtn',
          stocks: 'stocksVoiceBtn',
          sip: 'sipVoiceBtn'
        };

        const vBtn = document.getElementById(voiceBtnMap[tab]);
        if(vBtn) { vBtn.textContent = '⏹️'; vBtn.classList.add('recording'); }
      };
      recognition.onresult = (e) => {
        try {
          let transcript = '';
          for (let i = e.resultIndex; i < e.results.length; i++) {
            transcript += e.results[i][0].transcript;
          }

          console.log("VOICE HEARD:", transcript);

          const input = document.getElementById(inputId);

          if (!input) return;

          input.value = transcript;
          input.dispatchEvent(new Event('input'));

          statusEl.textContent =
            '✅ Heard: "' + transcript + '"';

          setTimeout(() => {
            sendMsg(tab);
          }, 500);

        } catch(err) {
          console.error(err);
        }
      };

      recognition.onerror = (e) => {

    console.error("VOICE ERROR:", e);

    isRecording = false;

    const statusEl = document.getElementById(tab + 'VoiceStatus');

    if (statusEl) {
        statusEl.textContent =
            '❌ Voice error: ' + e.error;
    }

};
        
      recognition.onend = () => {

    console.log("VOICE ENDED");

    isRecording = false;
    activeVoiceTab = null;

    const btns = ['voiceBtn','cryptoVoiceBtn','stocksVoiceBtn','sipVoiceBtn'];

    btns.forEach(id => {
        const btn = document.getElementById(id);

        if (btn) {
            btn.classList.remove('recording');
            btn.textContent = '🎤';
        }
    });
 };
 recognition.start();
 }) 
      .catch(err => {
      statusEl.textContent = '❌ Microphone blocked! Go to browser Settings → Site Settings → Microphone → Allow for this site.';
    });
}

function toggleVoice() { startRecognition('chatInput','voiceStatus','chat'); }
function toggleVoiceForTab(tab) {
  const inputId = tab + 'Input';
  const statusId = tab + 'VoiceStatus';
  startRecognition(inputId, statusId, tab);
}

function stopVoice() {

  if (recognition) {
    try {
      recognition.stop();
    } catch(e) {}
  }

  isRecording = false;
  const btns = ['voiceBtn','cryptoVoiceBtn','stocksVoiceBtn','sipVoiceBtn'];

  btns.forEach(id => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.classList.remove('recording');
      btn.textContent = '🎤';
    }
  });
  setTimeout(() => {
    ['voiceStatus','cryptoVoiceStatus','stocksVoiceStatus','sipVoiceStatus'].forEach(id => {
      const el = document.getElementById(id); if (el) el.textContent = '';
    });
  }, 3000);
}

// ── Crypto ─────────────────────────────────────────────────────────
async function loadCrypto() {
  try {
    const res = await fetch('/api/crypto/prices');
    const data = await res.json();
    const map = {bitcoin:['btcPrice','btcChg'],ethereum:['ethPrice','ethChg'],binancecoin:['bnbPrice','bnbChg'],solana:['solPrice','solChg']};
    data.coins.forEach(coin => {
      if (!map[coin.id]) return;
      const [pId,cId] = map[coin.id];
      document.getElementById(pId).textContent =
        coin.formatted_inr ||
        ('₹' + Number(
          coin.price_inr || 0
        ).toLocaleString('en-IN'));

      const chg =
        Number(
          coin.change_24h_pct || 0
        ).toFixed(2);

      const el = document.getElementById(cId);

      el.textContent =
        (chg >= 0 ? '▲ +' : '▼ ') +
        chg +
        '% today';

      el.className =
        'coin-chg ' +
        (chg >= 0 ? 'up' : 'down');
    });
    const btc = data.coins.find(c=>c.id==='bitcoin');
    if (btc) {
      const g = document.getElementById('cryptoGreeting');
      if (g) {
        const msg = `Hey! 🚀 Live prices loaded! Bitcoin is at ${btc.formatted_inr} (${btc.change_24h_pct>=0?'+':''}${btc.change_24h_pct}% today). Ask me anything about crypto or use the 🎤 voice button!`;
        g.textContent=''; let i=0;
        const iv=setInterval(()=>{g.textContent+=msg[i];i++;if(i>=msg.length)clearInterval(iv);},12);
      }
    }
  } catch(e) { document.getElementById('btcPrice').textContent='Error loading'; }
}

// ── Indices ────────────────────────────────────────────────────────
async function loadIndices() {
  try {
    const res = await fetch('/api/stocks/indices');
    const data = await res.json();
    if (!data.indices) return;
    const pairs = [['NIFTY50','niftyVal'],['SENSEX','sensexVal'],['BANKNIFTY','bankVal']];
    pairs.forEach(([k,id]) => {
      const idx = data.indices[k];
      if (idx && idx.value) {
        const el = document.getElementById(id);
        el.textContent = idx.formatted || idx.value;
        el.style.color = idx.direction==='up'?'var(--accent)':'var(--red)';
      }
    });
  } catch(e) {}
}

async function analyseStock() {
  const sym = document.getElementById('stockSearch').value.trim().toUpperCase();
  if (!sym) return;
  const res = document.getElementById('stockResult');
  res.style.display='block';
  res.innerHTML='<span style="color:var(--muted)">⏳ Fetching '+sym+'...</span>';
  try {
    const r = await fetch('/api/stocks/quote/'+sym);
    const d = await r.json();
    if (d.error) { res.innerHTML='<span style="color:var(--red)">Not found. Try NSE symbol like RELIANCE, TCS, HDFCBANK</span>'; return; }
    res.innerHTML = `<b style="color:var(--accent)">${sym}</b> — ₹${d.current_price?.toLocaleString('en-IN')} <span class="${d.direction==='up'?'up':'down'}">${d.direction==='up'?'▲ +':'▼ '}${d.change_pct}%</span><br><span style="color:var(--muted);font-size:11px;">52W High: ₹${d['52w_high']?.toLocaleString('en-IN')} | 52W Low: ₹${d['52w_low']?.toLocaleString('en-IN')}</span>`;
    askInTab('Analyse '+sym+' NSE stock at Rs.'+d.current_price+'. Should I buy sell or hold? Explain simply.','stocks');
  } catch(e) { res.innerHTML='<span style="color:var(--red)">Error. Try again.</span>'; }
}

// ── SIP ────────────────────────────────────────────────────────────
function calcSIP() {
  const M=parseFloat(document.getElementById('sipAmt').value);
  const r=parseFloat(document.getElementById('sipRate').value)/100/12;
  const n=parseFloat(document.getElementById('sipYrs').value)*12;
  const fv=M*(((1+r)**n-1)/r)*(1+r); const inv=M*n; const gain=fv-inv; const mult=fv/inv;
  function fmt(v){return v>=10000000?`₹${(v/10000000).toFixed(2)} Cr`:v>=100000?`₹${(v/100000).toFixed(2)} L`:`₹${v.toFixed(0)}`;}
  document.getElementById('sipInv').textContent=fmt(inv);
  document.getElementById('sipWealth').textContent=fmt(fv);
  document.getElementById('sipGain').textContent=fmt(gain);
  document.getElementById('sipMult').textContent=mult.toFixed(2)+'x';
  document.getElementById('sipResult').classList.add('show');
  document.getElementById('sipComment').textContent=`💡 By investing just ${fmt(M)}/month for ${document.getElementById('sipYrs').value} years, your money grows ${mult.toFixed(1)}x! You invest ${fmt(inv)} and get back ${fmt(fv)}. The extra ${fmt(gain)} is FREE money from compounding!`;
}

// ── Sentiment ──────────────────────────────────────────────────────
async function loadSentiment() {
  try {
    const res = await fetch('/api/ml/sentiment');
    const data = await res.json();
    const score = data.mood_score||0;
    document.getElementById('moodLabel').textContent = data.mood_label||'NEUTRAL';
    document.getElementById('moodScore').textContent = (score>=0?'+':'')+score.toFixed(2);
    const pct = Math.round(((score+1)/2)*100);
    const fill = document.getElementById('moodFill');
    fill.style.width=pct+'%';
    fill.style.background=score>0.1?'var(--accent)':score<-0.1?'var(--red)':'var(--gold)';
    document.getElementById('moodPrediction').textContent = data.prediction||'';
    const list = document.getElementById('headlineList');
    list.innerHTML = (data.top_headlines||[]).map(h=>`
      <div class="headline-item">
        <span style="color:var(--text);flex:1;font-size:11px;">${h.headline}</span>
        <span class="badge ${h.label==='BULLISH'?'badge-bull':h.label==='BEARISH'?'badge-bear':'badge-neut'}">${h.label==='BULLISH'?'📈':h.label==='BEARISH'?'📉':'➡️'} ${h.label}</span>
      </div>`).join('');
  } catch(e) { document.getElementById('moodLabel').textContent='Could not load'; }
}

// ── Health Score ───────────────────────────────────────────────────
async function calcHealth() {
  const income=parseFloat(document.getElementById('hIncome').value)||0;
  if (!income) { alert('Please enter monthly income!'); return; }
  const savings=parseFloat(document.getElementById('hSavings').value)||0;
  const invest=parseFloat(document.getElementById('hInvest').value)||0;
  const emi=parseFloat(document.getElementById('hEmi').value)||0;
  const emFund=parseFloat(document.getElementById('hEmFund').value)||0;
  const age=parseInt(document.getElementById('hAge').value)||25;
  const hasHealth=document.getElementById('hHealth').checked;
  const hasTerm=document.getElementById('hTerm').checked;
  const hasEmergency=document.getElementById('hEmergency').checked;
  const hasRetire=document.getElementById('hRetire').checked;

  // Client-side scoring (fallback if API not connected)
  let score=0; const breakdown={}; const tips=[];
  const savRate=(savings/income)*100;
  const sScore=savRate>=30?25:savRate>=20?20:savRate>=10?12:savRate>=5?6:0;
  score+=sScore; breakdown.Savings={score:sScore,max:25,detail:`${savRate.toFixed(1)}% savings rate`};
  if(savRate<20) tips.push(`Save at least 20% of income. Currently ${savRate.toFixed(1)}%. Try saving Rs.${(income*0.20-savings).toFixed(0)} more.`);

  const invRate=(invest/income)*100;
  const iScore=invRate>=20?20:invRate>=10?15:invRate>=5?8:invest>0?4:0;
  score+=iScore; breakdown.Investments={score:iScore,max:20,detail:`${invRate.toFixed(1)}% investment rate`};
  if(invRate<10) tips.push(`Start SIP of at least Rs.${(income*0.10).toFixed(0)}/month (10% of salary).`);

  const emiRate=(emi/income)*100;
  const eScore=emiRate===0?20:emiRate<=20?18:emiRate<=30?12:emiRate<=40?6:0;
  score+=eScore; breakdown['EMI Burden']={score:eScore,max:20,detail:`${emiRate.toFixed(1)}% EMI burden`};
  if(emiRate>30) tips.push(`EMI is ${emiRate.toFixed(1)}% of income — too high. Try to prepay loans.`);

  const efScore=hasEmergency&&emFund>=6?15:hasEmergency&&emFund>=3?10:hasEmergency?5:0;
  score+=efScore; breakdown['Emergency Fund']={score:efScore,max:15,detail:hasEmergency?`${emFund} months covered`:'No emergency fund'};
  if(!hasEmergency||emFund<6) tips.push(`Build emergency fund of Rs.${(income*6).toLocaleString('en-IN')} (6 months income).`);

  const insScore=(hasHealth?5:0)+(hasTerm?5:0);
  score+=insScore; breakdown.Insurance={score:insScore,max:10,detail:`Health:${hasHealth?'✅':'❌'} Term:${hasTerm?'✅':'❌'}`};
  if(!hasHealth) tips.push('Get health insurance immediately! Rs.5-10L cover costs ~Rs.6,000/year.');
  if(!hasTerm&&age<50) tips.push('Get term life insurance of 15x annual income. Very cheap when young.');

  const retScore=hasRetire?10:0;
  score+=retScore; breakdown.Retirement={score:retScore,max:10,detail:hasRetire?'Has plan':'No plan'};
  if(!hasRetire) tips.push('Start NPS or PPF for retirement. Every year of delay costs lakhs.');

  const color=score>=80?'var(--accent)':score>=65?'var(--blue)':score>=50?'var(--gold)':score>=35?'var(--orange)':'var(--red)';
  const rating=score>=80?'EXCELLENT 🌟':score>=65?'GOOD 👍':score>=50?'AVERAGE 😐':score>=35?'NEEDS WORK ⚠️':'CRITICAL 🚨';
  const percentile=score>=80?'Top 5%':score>=65?'Top 20%':score>=50?'Top 50%':score>=35?'Bottom 40%':'Bottom 20%';
  const summary=score>=65?'Good financial health! Follow the tips to make it excellent.':'Take action on the tips below to improve your financial health significantly.';

  document.getElementById('healthResult').style.display='block';
  document.getElementById('scoreNum').textContent=score;
  document.getElementById('scoreNum').style.color=color;
  document.getElementById('scoreRing').style.borderColor=color;
  document.getElementById('scoreRating').textContent=rating;
  document.getElementById('scoreRating').style.color=color;
  document.getElementById('scorePercentile').textContent=percentile+' of Indians';
  document.getElementById('scoreSummary').textContent=summary;

  const bl=document.getElementById('breakdownList');
  bl.innerHTML=Object.entries(breakdown).map(([name,val])=>{
    const pct=(val.score/val.max)*100;
    const bc=pct>=70?'var(--accent)':pct>=40?'var(--gold)':'var(--red)';
    return `<div class="breakdown-row"><div class="breakdown-name">${name}</div><div class="breakdown-bar"><div class="breakdown-fill" style="width:${pct}%;background:${bc}"></div></div><div class="breakdown-score">${val.score}/${val.max}</div></div>`;
  }).join('');

  const tl=document.getElementById('tipsList');
  tl.innerHTML=tips.length?tips.map(t=>`<div class="tip-item">💡 ${t}</div>`).join(''):'<div style="color:var(--accent);font-size:12px;">✅ Great! No major issues found.</div>';

  document.getElementById('healthResult').scrollIntoView({behavior:'smooth'});

  // Also ask AI for personalised plan
  try {
    const r = await fetch('/api/ai/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({messages:[{role:'user',content:`Indian person age ${age}, income Rs.${income}, savings ${savRate.toFixed(0)}%, financial health score ${score}/100. Give 3 specific actionable tips in simple English. Be concise.`}],language:currentLang})});
    const d = await r.json();
    if (d.reply) {
      const ap=document.getElementById('aiPlan');
      ap.style.display='block';
      ap.innerHTML='<b style="color:var(--accent)">🤖 AI Action Plan:</b><br>'+d.reply;
    }
  } catch(e) {}
}

// ── UPI Analyzer ───────────────────────────────────────────────────
async function analyzeUPI() {
  const text=document.getElementById('upiText').value.trim();
  const income=parseFloat(document.getElementById('upiIncome').value)||0;
  if (!text) { alert('Please paste your transactions!'); return; }

  // Client-side parsing
  const CATS={
    'Food & Dining':['swiggy','zomato','food','restaurant','cafe','dominos','kfc','pizza','burger','hotel','mess','chai'],
    'Transport':['ola','uber','rapido','metro','petrol','fuel','cab','auto','irctc','railway'],
    'Shopping':['amazon','flipkart','myntra','mall','shop','meesho','ajio','nykaa'],
    'Entertainment':['netflix','hotstar','prime','spotify','movie','cinema','pvr','bookmyshow','game'],
    'Groceries':['bigbasket','grofers','blinkit','zepto','grocery','vegetable','milk','kirana','dmart'],
    'Health':['pharmacy','medical','doctor','hospital','medicine','chemist','apollo'],
    'Utilities':['electricity','water','gas','jio','airtel','recharge','dth','internet','wifi'],
    'Investment':['zerodha','groww','sip','mutual','nps','ppf','insurance','upstox','coin'],
    'Rent/EMI':['rent','emi','loan','housing','pg','hostel'],
    'Transfer':['transfer','sent','received','credited','debited'],
  };

  const lines=text.split('\\n').filter(l=>l.trim());
  const txns=[]; let total=0;
  const catTotals={};

  lines.forEach(line => {
    const amtMatch=line.match(/(?:rs\\.?|₹|inr)?\\s*(\\d+(?:,\\d+)*(?:\\.\\d+)?)/i);
    if (!amtMatch) return;
    const amt=parseFloat(amtMatch[1].replace(/,/g,''));
    if (amt<10||amt>500000) return;
    let cat='Others';
    const low=line.toLowerCase();
    for (const [c,kws] of Object.entries(CATS)) {
      if (kws.some(k=>low.includes(k))) { cat=c; break; }
    }
    txns.push({line:line.slice(0,60),amt,cat});
    catTotals[cat]=(catTotals[cat]||0)+amt;
    total+=amt;
  });

  if (!txns.length) { alert('No transactions found. Make sure each line has an amount like Rs.450 or 450.'); return; }

  document.getElementById('upiResult').style.display='block';
  document.getElementById('upiTotal').textContent=total>=100000?`₹${(total/100000).toFixed(1)}L`:`₹${total.toLocaleString('en-IN')}`;
  document.getElementById('upiTxns').textContent=txns.length;
  const sorted=Object.entries(catTotals).sort((a,b)=>b[1]-a[1]);
  document.getElementById('upiTop').textContent=sorted[0]?.[0]||'-';

  const maxAmt=sorted[0]?.[1]||1;
  document.getElementById('upiBreakdown').innerHTML=sorted.map(([cat,amt])=>{
    const pct=Math.round((amt/total)*100);
    const bc=pct>25?'var(--red)':pct>15?'var(--gold)':'var(--accent)';
    return `<div class="upi-cat"><div class="upi-catname">${cat}</div><div class="upi-bar-wrap"><div class="upi-bar" style="width:${(amt/maxAmt)*100}%;background:${bc}"></div></div><div class="upi-amt">₹${amt.toLocaleString('en-IN')}</div><div class="upi-pct">${pct}%</div></div>`;
  }).join('');

  // Wasteful spending
  const WASTEFUL=['Food & Dining','Entertainment','Shopping'];
  const waste=sorted.filter(([cat,amt])=>WASTEFUL.includes(cat)&&(amt/total)>0.15);
  if (waste.length) {
    document.getElementById('upiWaste').style.display='block';
    document.getElementById('upiWasteList').innerHTML=waste.map(([cat,amt])=>{
      const pct=Math.round((amt/total)*100);
      const save=Math.round(amt*0.3);
      return `<div class="waste-card"><b style="color:var(--red)">${cat}</b> — ₹${amt.toLocaleString('en-IN')} (${pct}% of spending)<br><span style="font-size:11px;color:var(--muted)">Reducing by 30% saves ₹${save.toLocaleString('en-IN')}/month!</span></div>`;
    }).join('');
  }

  // Investment insight
  const foodAmt=catTotals['Food & Dining']||0;
  if (foodAmt>1000) {
    document.getElementById('upiInvestSection').style.display='block';
    const sip20=(foodAmt*(((1.01)**240-1)/0.01)*1.01)/100000;
    document.getElementById('upiInvestList').innerHTML=`<div class="invest-card" style="font-size:12px;line-height:1.8;">🚀 If you invested your monthly food budget of ₹${foodAmt.toLocaleString('en-IN')} instead of spending it, at 12% annual return over 20 years you would have <b style="color:var(--accent)">₹${sip20.toFixed(1)} Lakh!</b></div>`;
  }

  // Ask AI for tips
  try {
    const top3=sorted.slice(0,3).map(([c,a])=>`${c}: Rs.${a.toLocaleString('en-IN')}`).join(', ');
    const r=await fetch('/api/ai/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({messages:[{role:'user',content:`Indian person spent Rs.${total.toLocaleString('en-IN')} total. Top categories: ${top3}. Give 3 specific money saving tips for India. Be practical with Rs. amounts. Under 80 words.`}],language:currentLang})});
    const d=await r.json();
    if (d.reply) {
      document.getElementById('upiAiTips').style.display='block';
      document.getElementById('upiAiContent').textContent=d.reply;
    }
  } catch(e) {}

  document.getElementById('upiResult').scrollIntoView({behavior:'smooth'});
}

// ── Languages ──────────────────────────────────────────────────────
const LANGS={
  english:{name:'🇬🇧 English',text:'RSI is 72 for RELIANCE. Stock looks overpriced — wait before buying. Price may fall soon.',color:'var(--accent)'},
  hindi:{name:'🇮🇳 हिंदी',text:'RELIANCE का RSI 72 है। यह शेयर महंगा लग रहा है — अभी मत खरीदो। दाम नीचे आ सकता है।',color:'var(--gold)'},
  tamil:{name:'🇮🇳 தமிழ்',text:'RELIANCE RSI 72. பங்கு விலை அதிகம் — இப்போது வாங்காதே. விலை குறையலாம்.',color:'var(--blue)'},
  telugu:{name:'🇮🇳 తెలుగు',text:'RELIANCE RSI 72. స్టాక్ ధర ఎక్కువ — ఇప్పుడు కొనకు. ధర తగ్గవచ్చు.',color:'var(--purple)'},
  bengali:{name:'🇮🇳 বাংলা',text:'RELIANCE RSI 72। শেয়ার দামী — এখন কিনো না। দাম কমতে পারে।',color:'var(--orange)'},
  marathi:{name:'🇮🇳 मराठी',text:'RELIANCE RSI 72. हा शेअर महाग आहे — आत्ता विकत घेऊ नका.',color:'var(--red)'},
  gujarati:{name:'🇮🇳 ગુજરાતી',text:'RELIANCE RSI 72. સ્ટૉક મોઘો છે — અત્યારે ખરીદશો નહીં.',color:'#22d3ee'},
  kannada:{name:'🇮🇳 ಕನ್ನಡ',text:'RELIANCE RSI 72. ಸ್ಟಾಕ್ ದುಬಾರಿ — ಈಗ ಕೊಳ್ಳಬೇಡ.',color:'#a78bfa'},
};

function renderLangs() {
  document.getElementById('langGrid').innerHTML=Object.values(LANGS).map(l=>`
    <div class="lang-row">
      <div><div class="lang-name" style="color:${l.color}">${l.name}</div><div class="lang-text">${l.text}</div></div>
    </div>`).join('');
}

// ── Init ───────────────────────────────────────────────────────────
calcSIP();
</script>
</body>
</html>
"""

@app.get("/", include_in_schema=False)
async def root():
    return HTMLResponse(content=HTML_PAGE, headers={
        "Cache-Control":"no-cache, no-store, must-revalidate, max-age=0",
        "Pragma":"no-cache","Expires":"0"})

@app.get("/health")
async def health():
    return {"status":"ok","app":"FinAI","version":"7.0.0"}

@app.get("/api/crypto/prices")
async def crypto_prices():
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://api.coingecko.com/api/v3/simple/price",
                params={"ids":"bitcoin,ethereum,binancecoin,solana","vs_currencies":"inr,usd","include_24hr_change":"true"})
            data = r.json()

if not isinstance(data, dict) or not data:

    return {
        "coins": [
            {
                "id": "bitcoin",
                "name": "Bitcoin",
                "price_inr": 7420000,
                "formatted_inr": "₹74.2L",
                "change_24h_pct": 2.4,
                "direction": "up"
            },
            {
                "id": "ethereum",
                "name": "Ethereum",
                "price_inr": 219000,
                "formatted_inr": "₹2.19L",
                "change_24h_pct": 1.2,
                "direction": "up"
            }
        ]
    }

        names = {"bitcoin":"Bitcoin","ethereum":"Ethereum","binancecoin":"BNB","solana":"Solana"}
        coins = []
        for cid, info in data.items():
            inr = info.get("inr",0); chg = info.get("inr_24h_change",0)
            if inr > 10000000: fmt = f"Rs.{inr/10000000:.2f} Cr"
            elif inr > 100000: fmt = f"Rs.{inr/100000:.2f} L"
            else: fmt = f"Rs.{inr:,.2f}"
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
                    r = await c.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",params={"interval":"1d","range":"2d"},headers={"User-Agent":"Mozilla/5.0"})
                    closes = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                    curr=closes[-1]; prev=closes[-2]; chg=((curr-prev)/prev)*100
                    results[name]={"value":round(curr,2),"change_pct":round(chg,2),"direction":"up" if chg>=0 else "down","formatted":f"{curr:,.2f}"}
                except: results[name]={"error":"unavailable"}
        return {"indices":results,"timestamp":datetime.now().isoformat()}
    except Exception as e:
        return JSONResponse(status_code=503,content={"error":str(e)})

@app.get("/api/stocks/quote/{symbol}")
async def stock_quote(symbol:str):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}.NS",params={"interval":"1d","range":"5d"},headers={"User-Agent":"Mozilla/5.0"})
        d = r.json()["chart"]["result"][0]
        closes = d["indicators"]["quote"][0]["close"]
        curr=closes[-1]; prev=closes[-2]; chg=((curr-prev)/prev)*100
        return {"symbol":symbol.upper(),"current_price":round(curr,2),"formatted":f"Rs.{curr:,.2f}","change_pct":round(chg,2),"direction":"up" if chg>=0 else "down","52w_high":round(d["meta"].get("fiftyTwoWeekHigh",0),2),"52w_low":round(d["meta"].get("fiftyTwoWeekLow",0),2)}
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
    bull=sum(1 for s in scored if s["label"]=="BULLISH"); bear=sum(1 for s in scored if s["label"]=="BEARISH"); neut=sum(1 for s in scored if s["label"]=="NEUTRAL")
    return {"mood_score":round(mood,3),"mood_label":"BULLISH 📈" if mood>0.1 else("BEARISH 📉" if mood<-0.1 else "NEUTRAL ➡"),"prediction":"Nifty likely to open HIGHER" if mood>0.1 else("Nifty likely LOWER" if mood<-0.1 else "Direction uncertain"),"breakdown":{"bullish":bull,"bearish":bear,"neutral":neut},"top_headlines":sorted(scored,key=lambda x:abs(x["score"]),reverse=True)[:5],"timestamp":datetime.now().isoformat()}

@app.post("/api/ai/chat")
async def ai_chat(request:dict):
    messages = request.get("messages",[]); language = request.get("language","english")
    market_context = ""
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get("https://api.coingecko.com/api/v3/simple/price",params={"ids":"bitcoin,ethereum","vs_currencies":"inr","include_24hr_change":"true"})
            cd = r.json()
            btc=cd.get("bitcoin",{}).get("inr",0); eth=cd.get("ethereum",{}).get("inr",0); btc_chg=cd.get("bitcoin",{}).get("inr_24h_change",0)
            market_context += f"Bitcoin: Rs.{btc:,.0f} ({btc_chg:+.1f}% today). Ethereum: Rs.{eth:,.0f}. "
    except: pass
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get("https://query1.finance.yahoo.com/v8/finance/chart/^NSEI",params={"interval":"1d","range":"2d"},headers={"User-Agent":"Mozilla/5.0"})
            closes = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            curr=closes[-1]; prev=closes[-2]; chg=((curr-prev)/prev)*100
            market_context += f"Nifty 50: {curr:,.2f} ({chg:+.1f}% today). "
    except: pass
    market_context += f"RBI Repo Rate: 6.00%. USD/INR: Rs.83.47. Date: {datetime.now().strftime('%d %B %Y')}."
    last_msg = messages[-1]["content"].lower() if messages else ""
    stock_data = ""
    stocks = {"reliance":"RELIANCE","tcs":"TCS","infosys":"INFY","infy":"INFY","hdfc":"HDFCBANK","hdfcbank":"HDFCBANK","icici":"ICICIBANK","sbi":"SBIN","wipro":"WIPRO","bajaj":"BAJFINANCE","kotak":"KOTAKBANK","axis":"AXISBANK","maruti":"MARUTI","tatamotors":"TATAMOTORS","itc":"ITC","lt":"LT","ongc":"ONGC","airtel":"BHARTIARTL","titan":"TITAN","nestle":"NESTLEIND","sunpharma":"SUNPHARMA","ntpc":"NTPC","adani":"ADANIPORTS"}
    for name, sym in stocks.items():
        if name in last_msg:
            try:
                async with httpx.AsyncClient(timeout=8) as c:
                    r = await c.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}.NS",params={"interval":"1d","range":"2d"},headers={"User-Agent":"Mozilla/5.0"})
                    result = r.json()["chart"]["result"][0]
                    closes = result["indicators"]["quote"][0]["close"]
                    curr=closes[-1]; prev=closes[-2]; chg=((curr-prev)/prev)*100
                    meta = result["meta"]
                    stock_data = f"LIVE NSE: {sym} = Rs.{curr:,.2f} ({chg:+.2f}% today). 52W High: Rs.{meta.get('fiftyTwoWeekHigh',0):,.2f}, 52W Low: Rs.{meta.get('fiftyTwoWeekLow',0):,.2f}."
            except: pass
            break
    system = f"""You are FinAI, an intelligent Indian financial AI with LIVE market data.

LIVE DATA:
{market_context}
{stock_data}

RULES:
1. Always answer directly using live data above
2. Never say check elsewhere or I dont have access
3. Be friendly like a knowledgeable friend
4. Use Rs. Lakh Crore for Indian numbers
5. Keep answers 3-5 sentences
6. Add brief risk disclaimer for investment advice
7. Reply in {language}"""

    if not GROQ_KEY:
        return {"reply":f"FinAI here! Live: {market_context} Add GROQ_API_KEY in Render Environment for full AI!","engine":"no key"}
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
                json={"model":"llama-3.3-70b-versatile","messages":[{"role":"system","content":system},*messages[-8:]],"max_tokens":800,"temperature":0.7})
            response_data = r.json()
            if "choices" not in response_data:
                error_msg = response_data.get("error",{}).get("message","Unknown error")
                return {"reply":f"AI error: {error_msg}","engine":"error"}
            return {"reply":response_data["choices"][0]["message"]["content"],"engine":"Groq/Llama3","cost":"Rs.0"}
    except httpx.TimeoutException:
        return {"reply":"Request timed out. Please try again!","engine":"timeout"}
    except Exception as e:
        return {"reply":f"Error: {str(e)[:100]}. Try again!","engine":"error"}

@app.post("/api/financial-health-score")
async def fhs(request:dict): return {"message":"ok"}

@app.post("/api/upi-analyzer")
async def upia(request:dict): return {"message":"ok"}

@app.get("/api/rbi/msme-schemes")
async def msme():
    return {"schemes":[{"name":"MUDRA Shishu","max_loan":"Rs.50,000","portal":"mudra.org.in"},{"name":"MUDRA Kishore","max_loan":"Rs.5 Lakh","portal":"mudra.org.in"},{"name":"MUDRA Tarun","max_loan":"Rs.20 Lakh","portal":"mudra.org.in"},{"name":"CGTMSE","max_loan":"Rs.5 Crore","portal":"cgtmse.in"}]}

@app.get("/api/crypto/india-tax-guide")
async def tax():
    return {"flat_tax":"30%","tds":"1% above Rs.10,000","itr":"ITR-2/ITR-3 VDA"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    uvicorn.run("main:app",host="0.0.0.0",port=port)
      
