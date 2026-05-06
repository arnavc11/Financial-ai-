from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
import io
import base64
from datetime import datetime, timedelta
from typing import List, Optional
import httpx

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates

import yfinance as yf
import pandas as pd
import numpy as np

from backend.cache import cache

router = APIRouter()

DARK_BG    = "#0a1628"
CARD_BG    = "#111827"
ACCENT     = "#00d4aa"
GOLD       = "#f5c842"
RED        = "#ff4d6a"
TEXT       = "#e2e8f0"
GRID_COLOR = "#1e2d45"
BLUE       = "#3b82f6"
PURPLE     = "#8b5cf6"
ORANGE     = "#f97316"

def apply_arthiai_style(fig, axes):
    fig.patch.set_facecolor(DARK_BG)
    for ax in (axes if isinstance(axes, (list, np.ndarray)) else [axes]):
        ax.set_facecolor(CARD_BG)
        ax.tick_params(colors=TEXT, labelsize=8)
        ax.xaxis.label.set_color(TEXT)
        ax.yaxis.label.set_color(TEXT)
        ax.title.set_color(TEXT)
        for spine in ax.spines.values():
            spine.set_color(GRID_COLOR)
        ax.grid(True, color=GRID_COLOR, alpha=0.5, linewidth=0.5)

def fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=DARK_BG, edgecolor="none")
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode("utf-8")

def fetch_stock_data(symbol: str, period: str = "6mo") -> pd.DataFrame:
    suffix = ".NS"
    yf_sym = f"{symbol}{suffix}"
    df = yf.download(yf_sym, period=period, auto_adjust=True, progress=False)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_macd(close: pd.Series):
    ema12  = close.ewm(span=12, adjust=False).mean()
    ema26  = close.ewm(span=26, adjust=False).mean()
    macd   = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist   = macd - signal
    return macd, signal, hist

def calc_bollinger_bands(close: pd.Series, period: int = 20):
    ma     = close.rolling(period).mean()
    std    = close.rolling(period).std()
    upper  = ma + 2 * std
    lower  = ma - 2 * std
    return upper, ma, lower

@router.get("/technical/{symbol}")
async def technical_chart(
    symbol: str,
    period: str = Query("6mo", description="1mo, 3mo, 6mo, 1y, 2y"),
):
    symbol = symbol.upper()
    cache_key = f"chart_tech_{symbol}_{period}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    df = fetch_stock_data(symbol, period)
    close = df["Close"].squeeze()
    dates = df.index

    df["MA20"]  = close.rolling(20).mean()
    df["MA50"]  = close.rolling(50).mean()
    df["MA200"] = close.rolling(200).mean()
    df["RSI"]   = calc_rsi(close)
    bb_upper, bb_mid, bb_lower = calc_bollinger_bands(close)
    macd, signal, hist = calc_macd(close)

    fig = plt.figure(figsize=(14, 10))
    gs  = GridSpec(4, 1, figure=fig, height_ratios=[3, 1, 1, 1], hspace=0.05)

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax4 = fig.add_subplot(gs[3], sharex=ax1)

    apply_arthiai_style(fig, [ax1, ax2, ax3, ax4])
    fig.suptitle(f"{symbol} — Technical Analysis ({period})",
                 color=TEXT, fontsize=14, fontweight="bold", y=0.98)

    width  = (dates[1] - dates[0]).days * 0.6 if len(dates) > 1 else 0.6
    for i, (date, row) in enumerate(df.iterrows()):
        o, h, l, c = float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"])
        color = ACCENT if c >= o else RED

        ax1.bar(date, abs(c - o), bottom=min(o, c), color=color, width=timedelta(days=width*0.8), alpha=0.8)

        ax1.plot([date, date], [l, h], color=color, linewidth=0.5)

    ax1.plot(dates, df["MA20"],  color=GOLD,   linewidth=1.0, label="MA20",  alpha=0.9)
    ax1.plot(dates, df["MA50"],  color=BLUE,   linewidth=1.0, label="MA50",  alpha=0.9)
    ax1.plot(dates, df["MA200"], color=PURPLE, linewidth=1.0, label="MA200", alpha=0.7)

    ax1.plot(dates, bb_upper, color=TEXT, linewidth=0.5, linestyle="--", alpha=0.4, label="BB Upper")
    ax1.plot(dates, bb_lower, color=TEXT, linewidth=0.5, linestyle="--", alpha=0.4, label="BB Lower")
    ax1.fill_between(dates, bb_upper, bb_lower, alpha=0.05, color=TEXT)

    ax1.set_ylabel("Price (Rs.)", color=TEXT, fontsize=9)
    ax1.legend(loc="upper left", fontsize=7, facecolor=CARD_BG,
               labelcolor=TEXT, framealpha=0.8)
    ax1.tick_params(labelbottom=False)

    volume = df["Volume"].squeeze()
    vol_colors = [ACCENT if float(df["Close"].iloc[i]) >= float(df["Open"].iloc[i]) else RED
                  for i in range(len(df))]
    ax2.bar(dates, volume, color=vol_colors, width=timedelta(days=width*0.8), alpha=0.7)
    ax2.set_ylabel("Volume", color=TEXT, fontsize=8)
    ax2.tick_params(labelbottom=False)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1e6:.1f}M"))

    rsi_vals = df["RSI"]
    ax3.plot(dates, rsi_vals, color=GOLD, linewidth=1.2)
    ax3.axhline(70, color=RED,    linestyle="--", linewidth=0.8, alpha=0.7, label="Overbought (70)")
    ax3.axhline(30, color=ACCENT, linestyle="--", linewidth=0.8, alpha=0.7, label="Oversold (30)")
    ax3.fill_between(dates, rsi_vals, 70, where=(rsi_vals >= 70), alpha=0.2, color=RED)
    ax3.fill_between(dates, rsi_vals, 30, where=(rsi_vals <= 30), alpha=0.2, color=ACCENT)
    ax3.set_ylim(0, 100)
    ax3.set_ylabel("RSI", color=TEXT, fontsize=8)
    ax3.legend(loc="upper left", fontsize=6, facecolor=CARD_BG, labelcolor=TEXT)
    ax3.tick_params(labelbottom=False)

    hist_colors = [ACCENT if float(v) >= 0 else RED for v in hist]
    ax4.bar(dates, hist, color=hist_colors, width=timedelta(days=width*0.8), alpha=0.7)
    ax4.plot(dates, macd,   color=BLUE,   linewidth=1.0, label="MACD")
    ax4.plot(dates, signal, color=ORANGE, linewidth=1.0, label="Signal")
    ax4.axhline(0, color=TEXT, linewidth=0.5, alpha=0.4)
    ax4.set_ylabel("MACD", color=TEXT, fontsize=8)
    ax4.legend(loc="upper left", fontsize=6, facecolor=CARD_BG, labelcolor=TEXT)
    ax4.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax4.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=30, ha="right")

    chart_b64 = fig_to_base64(fig)

    latest_close = float(close.iloc[-1])
    latest_rsi   = float(df["RSI"].iloc[-1]) if not pd.isna(df["RSI"].iloc[-1]) else 50
    ma20_val     = float(df["MA20"].iloc[-1]) if not pd.isna(df["MA20"].iloc[-1]) else latest_close
    ma50_val     = float(df["MA50"].iloc[-1]) if not pd.isna(df["MA50"].iloc[-1]) else latest_close
    macd_val     = float(macd.iloc[-1])
    signal_val   = float(signal.iloc[-1])

    price_vs_ma20  = "above" if latest_close > ma20_val else "below"
    price_vs_ma50  = "above" if latest_close > ma50_val else "below"
    rsi_signal     = "overbought" if latest_rsi > 70 else ("oversold" if latest_rsi < 30 else "neutral")
    macd_signal    = "bullish (MACD above signal)" if macd_val > signal_val else "bearish (MACD below signal)"

    period_return = float(((close.iloc[-1] - close.iloc[0]) / close.iloc[0]) * 100)

    ai_analysis = {
        "symbol": symbol,
        "period": period,
        "price": f"Rs.{latest_close:,.2f}",
        "period_return": f"{period_return:+.2f}%",
        "indicators": {
            "rsi": {
                "value": round(latest_rsi, 1),
                "signal": rsi_signal,
                "interpretation": (
                    f"RSI at {latest_rsi:.1f} — stock is {rsi_signal}. "
                    + ("Consider waiting for a pullback before buying." if latest_rsi > 70
                       else "Potential buying opportunity — but verify with other signals." if latest_rsi < 30
                       else "Momentum is balanced — no extreme signal.")
                ),
            },
            "moving_averages": {
                "ma20": f"Rs.{ma20_val:,.2f}",
                "ma50": f"Rs.{ma50_val:,.2f}",
                "signal": (
                    f"Price is {price_vs_ma20} 20-day MA and {price_vs_ma50} 50-day MA. "
                    + ("Short-term and medium-term trend is UP (bullish)." if price_vs_ma20 == "above" and price_vs_ma50 == "above"
                       else "Short-term and medium-term trend is DOWN (bearish)." if price_vs_ma20 == "below" and price_vs_ma50 == "below"
                       else "Mixed signals — price is between moving averages. Watch for breakout direction.")
                ),
            },
            "macd": {
                "value": round(macd_val, 2),
                "signal_value": round(signal_val, 2),
                "signal": macd_signal,
                "interpretation": (
                    "MACD crossing above signal line — bullish momentum building." if macd_val > signal_val and macd_val - signal_val < 0.5
                    else "Strong upward momentum — MACD well above signal." if macd_val > signal_val
                    else "MACD below signal line — downward pressure on price."
                ),
            },
        },
        "overall_signal": (
            "BULLISH" if (latest_rsi < 70 and price_vs_ma20 == "above" and macd_val > signal_val)
            else "BEARISH" if (latest_rsi > 50 and price_vs_ma50 == "below" and macd_val < signal_val)
            else "NEUTRAL — mixed signals, wait for clearer direction"
        ),
        "disclaimer": "Technical analysis is one tool. Always check company fundamentals and news. Not SEBI-registered advice.",
    }

    result = {
        "symbol": symbol,
        "chart_base64": chart_b64,
        "chart_format": "PNG",
        "chart_usage": "In HTML: <img src='data:image/png;base64,{chart_base64}'>",
        "analysis": ai_analysis,
        "generated_at": datetime.now().isoformat(),
    }

    cache.set(cache_key, result, ttl=300)
    return result

@router.post("/portfolio-allocation")
async def portfolio_allocation_chart(holdings: List[dict]):
    if not holdings:
        raise HTTPException(status_code=400, detail="No holdings provided")

    allocation: Dict[str, float] = {}
    for h in holdings:
        atype = h.get("asset_type", "other").capitalize()
        allocation[atype] = allocation.get(atype, 0) + float(h.get("current_value", 0))

    labels = list(allocation.keys())
    values = list(allocation.values())
    colors_list = [ACCENT, GOLD, BLUE, PURPLE, ORANGE, RED][:len(labels)]
    total = sum(values)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    apply_arthiai_style(fig, [ax1, ax2])
    fig.suptitle("Portfolio Asset Allocation", color=TEXT, fontsize=14, fontweight="bold")

    wedges, texts, autotexts = ax1.pie(
        values,
        labels=labels,
        colors=colors_list,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.8,
        wedgeprops=dict(width=0.6, edgecolor=DARK_BG, linewidth=2),
    )
    for t in texts:
        t.set_color(TEXT)
        t.set_fontsize(10)
    for at in autotexts:
        at.set_color(DARK_BG)
        at.set_fontsize(9)
        at.set_fontweight("bold")

    ax1.text(0, 0, f"Rs.{total/100000:.1f}L\nTotal", ha="center", va="center",
             color=TEXT, fontsize=11, fontweight="bold")

    bars = ax2.barh(labels, values, color=colors_list, edgecolor=DARK_BG, linewidth=1)
    ax2.set_xlabel("Value (Rs.)", color=TEXT)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs.{x/100000:.1f}L"))
    for bar, val in zip(bars, values):
        ax2.text(bar.get_width() * 1.01, bar.get_y() + bar.get_height() / 2,
                 f"Rs.{val/100000:.2f}L ({val/total*100:.1f}%)",
                 va="center", color=TEXT, fontsize=8)
    ax2.set_xlim(0, max(values) * 1.3)

    return {"chart_base64": fig_to_base64(fig), "allocation": allocation, "total_value": round(total, 2)}

@router.post("/portfolio-pnl")
async def portfolio_pnl_chart(holdings: List[dict]):
    if not holdings:
        raise HTTPException(status_code=400, detail="No holdings provided")

    symbols = [h.get("symbol", "?") for h in holdings]
    pnl_vals = [float(h.get("pnl", 0)) for h in holdings]
    pnl_pcts = [float(h.get("pnl_pct", 0)) for h in holdings]
    colors_list = [ACCENT if p >= 0 else RED for p in pnl_vals]

    sorted_data = sorted(zip(symbols, pnl_vals, pnl_pcts, colors_list),
                         key=lambda x: x[2], reverse=True)
    symbols, pnl_vals, pnl_pcts, colors_list = zip(*sorted_data) if sorted_data else ([], [], [], [])

    fig, ax = plt.subplots(figsize=(12, max(5, len(symbols) * 0.5 + 2)))
    apply_arthiai_style(fig, ax)
    fig.suptitle("Portfolio P&L by Holding", color=TEXT, fontsize=13, fontweight="bold")

    bars = ax.barh(symbols, pnl_pcts, color=colors_list, edgecolor=DARK_BG, linewidth=1, height=0.6)
    ax.axvline(0, color=TEXT, linewidth=1, alpha=0.5)
    ax.set_xlabel("Return (%)", color=TEXT)

    for bar, val, pct in zip(bars, pnl_vals, pnl_pcts):
        xpos = bar.get_width() + (0.3 if bar.get_width() >= 0 else -0.3)
        sign = "+" if val >= 0 else ""
        ax.text(xpos, bar.get_y() + bar.get_height() / 2,
                f"{sign}Rs.{abs(val):,.0f} ({sign}{pct:.1f}%)",
                va="center", ha="left" if val >= 0 else "right",
                color=TEXT, fontsize=8)

    ax.set_xlim(min(pnl_pcts) * 1.4 - 1, max(pnl_pcts) * 1.4 + 1)
    return {"chart_base64": fig_to_base64(fig)}

@router.get("/sip-growth")
async def sip_growth_chart(
    monthly_sip: float = Query(5000,  description="Monthly SIP amount in Rs."),
    annual_return: float = Query(12.0, description="Expected annual return %"),
    years: int           = Query(20,   description="Investment period in years"),
):
    r = (annual_return / 100) / 12
    months = list(range(1, years * 12 + 1))

    invested = [monthly_sip * m for m in months]
    fv       = [monthly_sip * (((1 + r) ** m - 1) / r) * (1 + r) for m in months]
    gain     = [f - i for f, i in zip(fv, invested)]

    fig, ax = plt.subplots(figsize=(12, 6))
    apply_arthiai_style(fig, ax)
    fig.suptitle(f"SIP Growth Projection — Rs.{monthly_sip:,.0f}/month @ {annual_return}% for {years} years",
                 color=TEXT, fontsize=12, fontweight="bold")

    years_axis = [m / 12 for m in months]
    ax.fill_between(years_axis, invested, alpha=0.6, color=BLUE,   label="Amount Invested")
    ax.fill_between(years_axis, fv,       alpha=0.4, color=ACCENT, label="Total Wealth")
    ax.fill_between(years_axis, invested, fv, alpha=0.5, color=GOLD, label="Gains (Compounding)")

    ax.plot(years_axis, fv,       color=ACCENT, linewidth=2)
    ax.plot(years_axis, invested, color=BLUE,   linewidth=1.5, linestyle="--")

    for y in range(5, years + 1, 5):
        m_idx = y * 12 - 1
        if m_idx < len(fv):
            fv_val  = fv[m_idx] / 100000
            inv_val = invested[m_idx] / 100000
            ax.annotate(f"Yr {y}\nRs.{fv_val:.1f}L",
                        xy=(y, fv[m_idx]),
                        xytext=(y, fv[m_idx] * 1.05),
                        color=TEXT, fontsize=7, ha="center",
                        arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.8))

    ax.set_xlabel("Years", color=TEXT)
    ax.set_ylabel("Amount (Rs.)", color=TEXT)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"Rs.{x/100000:.0f}L"))
    ax.legend(facecolor=CARD_BG, labelcolor=TEXT, fontsize=9)

    final_invested = invested[-1]
    final_wealth   = fv[-1]
    final_gain     = gain[-1]
    summary = (f"Total Invested: Rs.{final_invested/100000:.1f}L  |  "
               f"Final Value: Rs.{final_wealth/100000:.1f}L  |  "
               f"Total Gain: Rs.{final_gain/100000:.1f}L  |  "
               f"Wealth Ratio: {final_wealth/final_invested:.1f}x")
    ax.set_title(summary, color=GOLD, fontsize=8, pad=4)

    return {
        "chart_base64": fig_to_base64(fig),
        "summary": {
            "total_invested": round(final_invested, 2),
            "final_wealth":   round(final_wealth, 2),
            "total_gain":     round(final_gain, 2),
            "wealth_ratio":   round(final_wealth / final_invested, 2),
            "formatted": {
                "invested": f"Rs.{final_invested/100000:.2f} Lakh",
                "wealth":   f"Rs.{final_wealth/100000:.2f} Lakh",
                "gain":     f"Rs.{final_gain/100000:.2f} Lakh",
            }
        }
    }

@router.get("/compare")
async def compare_stocks_chart(
    symbols: str = Query("RELIANCE,TCS,INFY", description="Comma-separated NSE symbols"),
    period:  str = Query("1y", description="1mo, 3mo, 6mo, 1y, 2y"),
):
    sym_list = [s.strip().upper() for s in symbols.split(",")][:6]

    fig, ax = plt.subplots(figsize=(13, 6))
    apply_arthiai_style(fig, ax)
    fig.suptitle(f"Stock Comparison (Normalised to 100) — {period}",
                 color=TEXT, fontsize=13, fontweight="bold")

    line_colors = [ACCENT, GOLD, BLUE, PURPLE, ORANGE, RED]
    final_returns = {}

    for sym, color in zip(sym_list, line_colors):
        try:
            df = fetch_stock_data(sym, period)
            close = df["Close"].squeeze()
            normalised = (close / float(close.iloc[0])) * 100
            ax.plot(df.index, normalised, color=color, linewidth=1.8,
                    label=f"{sym} ({(float(close.iloc[-1])/float(close.iloc[0])-1)*100:+.1f}%)")
            final_returns[sym] = round((float(close.iloc[-1]) / float(close.iloc[0]) - 1) * 100, 2)
        except Exception:
            pass

    ax.axhline(100, color=TEXT, linewidth=0.8, linestyle="--", alpha=0.4, label="Baseline")
    ax.set_ylabel("Normalised Price (start = 100)", color=TEXT, fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.legend(facecolor=CARD_BG, labelcolor=TEXT, fontsize=9, loc="upper left")
    fig.autofmt_xdate(rotation=25)

    winner = max(final_returns, key=final_returns.get) if final_returns else "N/A"

    return {
        "chart_base64": fig_to_base64(fig),
        "returns": final_returns,
        "winner": winner,
        "analysis": f"{winner} outperformed over {period} with {final_returns.get(winner, 0):+.1f}% return."
  }
