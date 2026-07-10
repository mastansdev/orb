import os
import time
from datetime import date

from dotenv import load_dotenv
from dhanhq import DhanContext, dhanhq


class HistoricalData:

    def __init__(self):

        load_dotenv()

        context = DhanContext(
            os.getenv("DHAN_CLIENT_ID"), os.getenv("DHAN_ACCESS_TOKEN")
        )

        self.dhan = dhanhq(context)

        # ORB Cache
        self.orb_cache = {}
        self.last_request_time = 0
        self.request_delay = 0.35

    def get_orb(self, security_id):

        today = date.today().strftime("%Y-%m-%d")

        response = self.dhan.intraday_minute_data(
            security_id=security_id,
            exchange_segment="NSE_EQ",
            instrument_type="EQUITY",
            from_date=today,
            to_date=today,
            interval=15,
        )

        

        if response["status"] != "success":

            print("\n========== ORB LOAD FAILED ==========")
            print(f"Security ID : {security_id}")
            print(f"Status      : {response.get('status')}")
            print(f"Remarks     : {response.get('remarks', 'N/A')}")

            if "data" in response:
                print(f"Data        : {response['data']}")

            print("=====================================\n")

            return None

        data = response["data"]

        if len(data["high"]) == 0:
            return None

        return {
            "high": float(data["high"][0]),
            "low": float(data["low"][0]),
            "completed": True,
            "entry_taken": False,
        }

    def preload_orb(self, security_ids):

        print("\nLoading Historical ORB...")

        loaded = 0
        failed = 0

        for security_id in security_ids:

            now = time.time()
            elapsed = now - self.last_request_time

            if elapsed < self.request_delay:
                time.sleep(self.request_delay - elapsed)

            orb = self.get_orb(security_id)

            self.last_request_time = time.time()

            if orb:

                self.orb_cache[str(security_id)] = orb
                loaded += 1

            else:

                failed += 1

            if loaded % 25 == 0 and loaded > 0:
                print(f"Loaded {loaded} ORBs...")

        print(f"\nHistorical ORB Loaded : {loaded}")
        print(f"Historical ORB Failed : {failed}")

    def get_cached_orb(self, security_id):
        """
        Return cached ORB for the given security.
        
        Uses the same key type that preload_orb()
        uses while storing the cache.
        """

        return self.orb_cache.get(security_id)