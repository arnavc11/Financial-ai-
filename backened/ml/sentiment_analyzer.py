import numpy as np
import re
from datetime import datetime
from typing import List, Dict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

INDIAN_FINANCE_LEXICON = {

    "rate cut": 2.0, "repo cut": 2.0, "stimulus": 1.8,
    "record high": 1.8, "bull run": 1.8, "rally": 1.5,
    "gdp growth": 1.5, "profit surge": 1.5, "dividend": 1.2,
    "buyback": 1.2, "fdi inflow": 1.5, "foreign inflow": 1.3,
    "all time high": 2.0, "nifty record": 1.8, "sensex record": 1.8,
    "upgrade": 1.3, "outperform": 1.3, "beat estimates": 1.5,
    "strong results": 1.5, "bumper harvest": 1.2,
    "mudra": 0.8, "msme boost": 1.0, "infrastructure push": 1.0,

    "rate hike": -2.0, "repo hike": -2.0, "inflation surge": -1.8,
    "crash": -2.0, "crisis": -1.8, "recession": -2.0,
    "npa": -1.5, "bad loan": -1.5, "fraud": -1.8,
    "default": -1.8, "downgrade": -1.5, "underperform": -1.3,
    "miss estimates": -1.5, "profit warning": -1.5,
    "fii outflow": -1.5, "foreign outflow": -1.3,
    "geopolitical": -1.0, "war": -1.5, "sanctions": -1.3,
    "global slowdown": -1.5, "us recession": -1.8,
    "rupee fall": -1.0, "rupee crash": -1.5,
    "sebi action": -1.2, "rbi penalty": -1.2,

    "recovery": 1.0, "rebound": 1.0, "positive": 0.8,
    "growth": 0.8, "expansion": 0.8, "robust": 0.8,
    "strong": 0.6, "gains": 0.8, "rises": 0.6,

    "concern": -0.6, "worry": -0.6, "uncertain": -0.5,
    "volatile": -0.5, "pressure": -0.6, "weak": -0.6,
    "falls": -0.6, "decline": -0.7, "slump": -0.8,
}

DARK   = "#0a1628"
CARD   = "#111827"
ACCENT = "#00d4aa"
GOLD   = "#f5c842"
RED    = "#ff4d6a"
BLUE   = "#3b82f6"
TEXT   = "#e2e8f0"
GRID   = "#1e2d45"

class SentimentAnalyzer:

    def __init__(self):
        self.vader = None
        if VADER_AVAILABLE:
            self.vader = SentimentIntensityAnalyzer()

            self.vader.lexicon.update(INDIAN_FINANCE_LEXICON)

    def score_headline(self, headline: str) -> Dict:
        headline_lower = headline.lower()
        custom_score = 0.0
        matched_words = []

        for term, score in INDIAN_FINANCE_LEXICON.items():
            if term in headline_lower:
                custom_score += score
                matched_words.append(term)

        custom_score = max(-1.0, min(1.0, custom_score / 3.0))

        vader_score = 0.0
        if self.vader:
            vs = self.vader.polarity_scores(headline)
            vader_score = vs["compound"]

        if matched_words:

            final_score = 0.7 * custom_score + 0.3 * vader_score
        else:

            final_score = vader_score if self.vader else 0.0

        if final_score >= 0.35:
            label = "BULLISH"
            color = ACCENT
        elif final_score <= -0.35:
            label = "BEARISH"
            color = RED
        else:
            label = "NEUTRAL"
            color = GOLD

        return {
            "headline": headline,
            "score": round(final_score, 3),
            "label": label,
            "color": color,
            "matched_terms": matched_words[:3],
        }

    async def fetch_headlines(self) -> List[str]:
        headlines = []
        feeds = [
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "https://www.moneycontrol.com/rss/buzzingstocks.xml",
        ]

        try:
            import httpx, feedparser
            async with httpx.AsyncClient(timeout=10) as client:
                for url in feeds:
                    try:
                        r = await client.get(
                            url, headers={"User-Agent": "ArthAI/2.0"})
                        feed = feedparser.parse(r.text)
                        for entry in feed.entries[:15]:
                            title = entry.get("title", "")
                            if title and len(title) > 10:
                                headlines.append(title)
                    except Exception:
                        pass
        except Exception:
            pass

        if not headlines:
            headlines = [
                "Nifty 50 hits record high as FII inflows surge",
                "RBI holds repo rate at 6%, policy stance neutral",
                "Sensex gains 500 points on strong Q4 results",
                "Rupee strengthens against dollar on positive macro data",
                "HDFC Bank reports record profit, beats estimates",
                "Global markets cautious amid US Fed uncertainty",
                "India GDP growth forecast revised upward to 7%",
            ]

        return list(set(headlines))

    async def analyze_market_mood(self) -> Dict:
        headlines = await self.fetch_headlines()
        scored = [self.score_headline(h) for h in headlines if h.strip()]

        if not scored:
            return {"error": "Could not fetch headlines"}

        scores = [s["score"] for s in scored]
        mood_score = float(np.mean(scores))

        bullish_count = sum(1 for s in scored if s["label"] == "BULLISH")
        bearish_count = sum(1 for s in scored if s["label"] == "BEARISH")
        neutral_count = sum(1 for s in scored if s["label"] == "NEUTRAL")

        if mood_score >= 0.35:
            mood_label   = "VERY BULLISH"
            prediction   = "Nifty likely to OPEN HIGHER and trend upward"
            color        = ACCENT
            confidence   = min(95, 60 + abs(mood_score) * 50)
        elif mood_score >= 0.10:
            mood_label   = "BULLISH"
            prediction   = "Nifty likely to open positive, watch for continuation"
            color        = ACCENT
            confidence   = min(80, 50 + abs(mood_score) * 50)
        elif mood_score <= -0.35:
            mood_label   = "VERY BEARISH"
            prediction   = "Nifty likely to OPEN LOWER and face selling pressure"
            color        = RED
            confidence   = min(95, 60 + abs(mood_score) * 50)
        elif mood_score <= -0.10:
            mood_label   = "BEARISH"
            prediction   = "Nifty likely to open negative, caution advised"
            color        = RED
            confidence   = min(80, 50 + abs(mood_score) * 50)
        else:
            mood_label   = "NEUTRAL"
            prediction   = "Mixed signals — market direction uncertain today"
            color        = GOLD
            confidence   = 40

        chart_b64 = self._generate_sentiment_chart(scored, mood_score)

        top_headlines = sorted(
            scored, key=lambda x: abs(x["score"]), reverse=True)[:5]

        return {
            "mood_score":      round(mood_score, 3),
            "mood_label":      mood_label,
            "prediction":      prediction,
            "confidence_pct":  round(float(confidence), 1),
            "headlines_analyzed": len(scored),
            "breakdown": {
                "bullish": bullish_count,
                "bearish": bearish_count,
                "neutral": neutral_count,
            },
            "top_headlines":   top_headlines,
            "all_scores":      sorted(scored, key=lambda x: x["score"], reverse=True),
            "chart_base64":    chart_b64,
            "timestamp":       datetime.now().isoformat(),
            "disclaimer": (
                "Sentiment analysis is one indicator. Markets are influenced "
                "by many factors beyond news headlines. Not investment advice."
            )
        }

    def _generate_sentiment_chart(self, scored: List[Dict],
                                   mood_score: float) -> str:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
        fig.patch.set_facecolor(DARK)
        for ax in [ax1, ax2]:
            ax.set_facecolor(CARD)
            ax.tick_params(colors=TEXT, labelsize=8)
            for sp in ax.spines.values():
                sp.set_color(GRID)
            ax.grid(True, color=GRID, alpha=0.4, linewidth=0.5)

        fig.suptitle(
            f"Market Sentiment Analysis — Mood Score: {mood_score:+.2f}",
            color=TEXT, fontsize=13, fontweight="bold")

        scores = [s["score"] for s in scored]
        colors_list = [
            ACCENT if s >= 0.1 else (RED if s <= -0.1 else GOLD)
            for s in scores
        ]
        ax1.bar(range(len(scores)), sorted(scores),
                color=sorted(colors_list), alpha=0.8, edgecolor=DARK)
        ax1.axhline(0, color=TEXT, linewidth=1, alpha=0.5)
        ax1.axhline(mood_score, color=GOLD, linewidth=2,
                    linestyle="--", label=f"Avg: {mood_score:+.2f}")
        ax1.set_ylabel("Sentiment Score", color=TEXT)
        ax1.set_xlabel("Headlines (sorted)", color=TEXT)
        ax1.set_title("Headline Sentiment Distribution", color=TEXT)
        ax1.set_ylim(-1.1, 1.1)
        ax1.legend(facecolor=CARD, labelcolor=TEXT, fontsize=8)
        ax1.set_xticks([])

        bullish = sum(1 for s in scored if s["label"] == "BULLISH")
        bearish = sum(1 for s in scored if s["label"] == "BEARISH")
        neutral = sum(1 for s in scored if s["label"] == "NEUTRAL")
        total = len(scored)

        if total > 0:
            sizes  = [bullish, neutral, bearish]
            labels = [f"Bullish\n{bullish}", f"Neutral\n{neutral}",
                      f"Bearish\n{bearish}"]
            clrs   = [ACCENT, GOLD, RED]
            non_zero = [(s, l, c) for s, l, c in zip(sizes, labels, clrs) if s > 0]
            if non_zero:
                sz, lb, cl = zip(*non_zero)
                wedges, texts, autotexts = ax2.pie(
                    sz, labels=lb, colors=cl, autopct="%1.0f%%",
                    startangle=90,
                    wedgeprops=dict(edgecolor=DARK, linewidth=2))
                for t in texts:
                    t.set_color(TEXT)
                    t.set_fontsize(9)
                for at in autotexts:
                    at.set_color(DARK)
                    at.set_fontweight("bold")
        ax2.set_title("Sentiment Breakdown", color=TEXT)

        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150,
                    bbox_inches="tight", facecolor=DARK)
        buf.seek(0)
        plt.close(fig)
        return base64.b64encode(buf.read()).decode("utf-8")
