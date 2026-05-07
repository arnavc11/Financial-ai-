from fastapi import APIRouter, HTTPException, Query
import httpx
import feedparser
from datetime import datetime
from config.settings import config
from backened.cache import cache

router = APIRouter()

RSS_FEEDS = {
    "economic_times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "moneycontrol":   "https://www.moneycontrol.com/rss/buzzingstocks.xml",
    "livemint":       "https://www.livemint.com/rss/markets",
    "business_standard": "https://www.business-standard.com/rss/markets-106.rss",
    "rbi_press":      "https://www.rbi.org.in/rssnews.aspx",
}

NEWSAPI_QUERIES = {
    "stocks":  "NSE BSE Nifty Sensex India stock market",
    "crypto":  "cryptocurrency Bitcoin India RBI crypto regulation",
    "rbi":     "RBI Reserve Bank India monetary policy repo rate",
    "msme":    "MSME India small business loan government scheme",
    "economy": "India economy GDP inflation budget",
}

async def fetch_rss_news(feed_url: str, max_items: int = 10) -> list:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(feed_url, headers={"User-Agent": "ArthAI/1.0"})
            feed = feedparser.parse(r.text)
            items = []
            for entry in feed.entries[:max_items]:
                items.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", ""))[:300],
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "source": feed.feed.get("title", "Unknown"),
                })
            return items
    except Exception as e:
        return []

async def fetch_newsapi(query: str, max_items: int = 10) -> list:
    if not config.NEWS_API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{config.NEWS_API_BASE_URL}/everything",
                params={
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": max_items,
                    "apiKey": config.NEWS_API_KEY,
                }
            )
            data = r.json()
            return [
                {
                    "title": a.get("title", ""),
                    "summary": (a.get("description") or "")[:300],
                    "url": a.get("url", ""),
                    "published": a.get("publishedAt", ""),
                    "source": a.get("source", {}).get("name", ""),
                    "image": a.get("urlToImage"),
                }
                for a in data.get("articles", [])
                if a.get("title") and "[Removed]" not in a.get("title", "")
            ]
    except Exception:
        return []

@router.get("/")
async def get_financial_news(
    category: str = Query(
        "stocks",
        description="Category: stocks, crypto, rbi, msme, economy"
    ),
    limit: int = Query(15, description="Number of news items to return")
):
    cache_key = f"news_{category}_{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    articles = []

    if config.NEWS_API_KEY:
        query = NEWSAPI_QUERIES.get(category, NEWSAPI_QUERIES["stocks"])
        articles = await fetch_newsapi(query, limit)

    if not articles:
        feed_urls = list(RSS_FEEDS.values())[:3]
        for url in feed_urls:
            rss_items = await fetch_rss_news(url, 5)
            articles.extend(rss_items)
            if len(articles) >= limit:
                break
        articles = articles[:limit]

    result = {
        "category": category,
        "articles": articles,
        "count": len(articles),
        "timestamp": datetime.now().isoformat(),
        "source": "NewsAPI" if config.NEWS_API_KEY else "RSS Feeds"
    }

    cache.set(cache_key, result, ttl=900)
    return result

@router.get("/rbi-press-releases")
async def get_rbi_press_releases():
    cache_key = "rbi_press"
    cached = cache.get(cache_key)
    if cached:
        return cached

    items = await fetch_rss_news(RSS_FEEDS["rbi_press"], 20)
    result = {
        "source": "RBI Official Press Releases",
        "url": "https://www.rbi.org.in",
        "items": items,
        "timestamp": datetime.now().isoformat()
    }
    cache.set(cache_key, result, ttl=3600)
    return result

@router.get("/market-summary")
async def get_market_summary():
    cache_key = "market_summary_news"
    cached = cache.get(cache_key)
    if cached:
        return cached

    import asyncio
    tasks = [
        fetch_rss_news(RSS_FEEDS["economic_times"], 5),
        fetch_rss_news(RSS_FEEDS["moneycontrol"], 5),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles = []
    for r in results:
        if isinstance(r, list):
            all_articles.extend(r)

    result = {
        "articles": all_articles[:15],
        "count": len(all_articles[:15]),
        "timestamp": datetime.now().isoformat()
    }
    cache.set(cache_key, result, ttl=900)
    return result
