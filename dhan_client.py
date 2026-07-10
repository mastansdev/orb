import os

from dotenv import load_dotenv
from dhanhq import DhanContext, dhanhq

load_dotenv()


class DhanClient:

    def __init__(self):

        self.client_id = os.getenv("DHAN_CLIENT_ID")
        self.access_token = os.getenv("DHAN_ACCESS_TOKEN")

        self.context = None
        self.client = None

        self.connect()

    # -------------------------------------------------

    def connect(self):

        self.context = DhanContext(
            self.client_id,
            self.access_token
        )

        self.client = dhanhq(self.context)

        print("✅ Dhan Connected")

    # -------------------------------------------------

    def health_check(self):

        try:

            response = self.client.get_fund_limits()

            return response["status"] == "success"

        except Exception:

            return False

    # -------------------------------------------------

    def get_funds(self):

        return self.client.get_fund_limits()

    # -------------------------------------------------

    def get_positions(self):

        return self.client.get_positions()

    # -------------------------------------------------

    def get_orders(self):

        return self.client.get_order_list()

    # -------------------------------------------------

    def buy(self, **kwargs):

        return self.client.place_order(**kwargs)

    # -------------------------------------------------

    def sell(self, **kwargs):

        return self.client.place_order(**kwargs)


dhan_client = DhanClient()

dhan = dhan_client.client