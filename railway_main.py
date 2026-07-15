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

import time

from news_engine import NewsEngine

class RailwayIntelligenceService:

    def __init__(self):

        self.news_engine = NewsEngine()

    def run(self):

        print("=" * 60)
        print("H&M Railway Intelligence Service")
        print("=" * 60)

        while True:
            print("Collecting Market Intelligence...")
            self.news_engine.run()
            time.sleep(60)    

if __name__ == "__main__":

    RailwayIntelligenceService().run()


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
from news_engine import NewsEngine

# 1. Setup explicit, unbuffered logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)] # Ensures logs stream instantly
)
logger = logging.getLogger(__name__)

class RailwayIntelligenceService:

    def __init__(self):
        self.news_engine = NewsEngine()
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
                logger.info("Retrying in the next cycle...")

            # 4. Responsive sleep: checks for shutdown every second instead of blocking for 60s
            for _ in range(60):
                if not self.running:
                    break
                time.sleep(1)

        logger.info("Service has successfully shut down clean. Goodbye!")

if __name__ == "__main__":
    RailwayIntelligenceService().run()