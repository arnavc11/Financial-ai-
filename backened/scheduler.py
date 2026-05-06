from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config.settings import config
import asyncio
import logging

logger = logging.getLogger("arthiai.scheduler")
scheduler = AsyncIOScheduler()

def start_scheduler():

    @scheduler.scheduled_job(IntervalTrigger(seconds=config.ALERT_CHECK_INTERVAL_SECONDS))
    async def check_alerts_job():
        try:
            from backend.routes.alerts import check_all_alerts
            await check_all_alerts()
        except Exception as e:
            logger.error(f"Alert check failed: {e}")

    @scheduler.scheduled_job(IntervalTrigger(seconds=config.DATA_REFRESH_INTERVAL_SECONDS))
    async def refresh_indices_cache():
        try:
            from backend.routes.stocks import get_indices
            await get_indices()
            logger.info("✅ Market indices cache refreshed")
        except Exception as e:
            logger.error(f"Index cache refresh failed: {e}")

    @scheduler.scheduled_job(IntervalTrigger(seconds=120))
    async def refresh_crypto_cache():
        try:
            from backend.routes.crypto import get_crypto_prices
            await get_crypto_prices("bitcoin,ethereum,binancecoin,solana,ripple")
            logger.info("✅ Crypto cache refreshed")
        except Exception as e:
            logger.error(f"Crypto cache refresh failed: {e}")

    scheduler.start()
    logger.info("🕐 Background scheduler started (alerts, cache refresh)")
    print("🕐 Background jobs started: price alerts ✓ | market cache ✓ | crypto cache ✓")
