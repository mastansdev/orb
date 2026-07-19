"""
Broker Synchronization Engine

Purpose
-------
Keeps the bot synchronized with the broker.

Detects:
- Manual exits
- Broker square-offs
- Missing positions

This module NEVER places orders.
It ONLY reads broker positions.
"""

from datetime import datetime

from trading.dhan_client import dhan


class BrokerSync:

    def __init__(self):
        print("✓ Broker Sync Initialized")

    # --------------------------------------------------

    def get_open_positions(self):
        """
        Returns broker open positions.

        Returns:
            list
        """

        try:

            response = dhan.get_positions()

            if response.get("status") != "success":
                return []

            return response.get("data", [])

        except Exception as e:

            print("\n========== BROKER SYNC ERROR ==========")
            print(datetime.now())
            print(e)
            print("=======================================\n")

            return []

    # --------------------------------------------------

    def has_position(
        self,
        security_id
    ):
        """
        Returns True if broker still has the position.
        """

        positions = self.get_open_positions()

        for position in positions:

            if str(position.get("securityId")) == str(security_id):
                return True

        return False