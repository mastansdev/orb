"""
Railway Intelligence Service

Runs 24/7 on Railway.

Responsibilities
----------------
- Collect market news
- Build Market Stories
- Store institutional intelligence
- Update PostgreSQL

This service NEVER:
- Connects to Dhan
- Loads Master Database
- Starts Trading
- Executes Orders
"""

import logging
import signal
import sys
import time
from railway_news_engine import RailwayNewsEngine

# 1. Setup explicit, unbuffered logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)] # Ensures logs stream instantly
)
logger = logging.getLogger(__name__)

class RailwayIntelligenceService:

    def __init__(self):
        # Updated to use RailwayNewsEngine
        self.news_engine = RailwayNewsEngine()
        self.running = True
        
        # 2. Capture shutdown signals from Railway
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Triggered when Railway stops or redeploys the service."""
        logger.info(f"Received signal {signum}. Commencing graceful shutdown...")
        self.running = False

    def run(self):
        logger.info("=" * 60)
        logger.info("H&M Railway Intelligence Service Started")
        logger.info("=" * 60)

        # Main loop checking the shutdown flag
        while self.running:
            try:
                logger.info("Collecting Market Intelligence...")
                self.news_engine.run()
                
            except Exception as e:
                # 3. Prevent transient errors from killing the 24/7 service
                logger.error(f"Error during intelligence collection: {e}", exc_info=True)

                # 3b. SELF-HEAL (2026-07-21): Railway's Postgres
                # proxy drops long-lived connections. Once dead,
                # every cycle fails on the same broken connection
                # forever — the service looks alive but produces
                # nothing (observed: feed silent from 06:15).
                # Rebuild the engine (fresh DB connection) so the
                # next cycle starts clean.
                try:
                    logger.info("Rebuilding news engine (fresh DB connection)...")
                    self.news_engine = RailwayNewsEngine()
                    logger.info("News engine rebuilt OK.")
                except Exception as rebuild_error:
                    logger.error(
                        f"Rebuild failed (will retry next cycle): {rebuild_error}"
                    )

                logger.info("Retrying in the next cycle...")

            # 4. Responsive sleep: checks for shutdown every second instead of blocking for 60s
            for _ in range(60):
                if not self.running:
                    break
                time.sleep(1)

        logger.info("Service has successfully shut down clean. Goodbye!")

if __name__ == "__main__":
    RailwayIntelligenceService().run()