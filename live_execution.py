"""
Live Execution Engine

Responsible ONLY for placing live orders.

No trading logic.
No quantity calculations.
No strategy.

Input
    ↓
Validate
    ↓
Dhan Order
    ↓
Return Response
"""

import traceback
from datetime import datetime

from config import (
    PRODUCT_TYPE,
    ORDER_TYPE,
    ENABLE_TELEGRAM_CONFIRMATION
)

from dhan_client import dhan

# Import your telegram notifier later
# from telegram_notifier import send_message


class LiveExecution:

    def __init__(self):
        print("✓ Live Execution Engine Initialized")

    # ---------------------------------------------------------
    # PRIVATE HELPERS
    # ---------------------------------------------------------

    def _get_product_type(self):
        p_type = PRODUCT_TYPE.upper() if isinstance(PRODUCT_TYPE, str) else PRODUCT_TYPE
        
        if p_type == "MIS":
            return dhan.INTRA

        if p_type == "CNC":
            return dhan.CNC

        raise ValueError(f"Unsupported PRODUCT_TYPE: {PRODUCT_TYPE}")

    # ---------------------------------------------------------

    def _get_order_type(self):
        o_type = ORDER_TYPE.upper() if isinstance(ORDER_TYPE, str) else ORDER_TYPE

        if o_type == "MARKET":
            return dhan.MARKET

        if o_type == "LIMIT":
            return dhan.LIMIT

        if o_type == "STOP_LIMIT":
            return dhan.SL

        raise ValueError(f"Unsupported ORDER_TYPE: {ORDER_TYPE}")

    # ---------------------------------------------------------

    def _validate_order(
        self,
        security_id,
        symbol,
        qty
    ):
        if not security_id:
            raise ValueError("Security ID missing.")

        if not symbol:
            raise ValueError("Symbol missing.")

        if qty <= 0:
            raise ValueError("Quantity must be greater than zero.")

    # ---------------------------------------------------------

    def _log_execution(
        self,
        side,
        symbol,
        qty,
        response
    ):
        print("\n==============================")
        print("LIVE ORDER")
        print("==============================")
        print(f"Time     : {datetime.now()}")
        print(f"Side     : {side}")
        print(f"Symbol   : {symbol}")
        print(f"Qty      : {qty}")
        print(f"Response : {response}")
        print("==============================\n")

    # ---------------------------------------------------------

    def _success(
        self,
        response
    ):
        return {
            "success": True,
            "response": response
        }

    # ---------------------------------------------------------

    def _failure(
        self,
        error
    ):
        return {
            "success": False,
            "error": str(error)
        }

    # ---------------------------------------------------------

    def _execute(
        self,
        transaction_type,
        side_label,
        security_id,
        symbol,
        qty
    ):
        """
        Consolidated order wrapper handling SDK handshakes and execution safety.
        """
        try:
            self._validate_order(
                security_id,
                symbol,
                qty
            )

            response = dhan.place_order(
                security_id=str(security_id),
                exchange_segment=dhan.NSE,
                transaction_type=transaction_type,
                quantity=int(qty),
                order_type=self._get_order_type(),
                product_type=self._get_product_type(),
                # Note: Defaulting to 0 because MARKET orders ignore the supplied price.
                # If LIMIT/STOP_LIMIT are supported later, map the price argument here.
                price=0,
                trigger_price=0,
                validity="DAY"
            )

            self._log_execution(
                side_label,
                symbol,
                qty,
                response
            )

            if ENABLE_TELEGRAM_CONFIRMATION:
                pass

            # Broker accepted the order
            if response.get("status") == "success":
                return self._success(response)

            # Broker rejected the order
            return self._failure(
                response.get(
                    "remarks",
                    "Broker rejected order."
                )
            )

        except Exception as e:
            traceback.print_exc()
            return self._failure(e)

    # ---------------------------------------------------------
    # PUBLIC INTERFACE
    # ---------------------------------------------------------

    def buy(
        self,
        security_id,
        symbol,
        price,
        qty
    ):
        return self._execute(
            transaction_type=dhan.BUY,
            side_label="BUY",
            security_id=security_id,
            symbol=symbol,
            qty=qty
        )

    # ---------------------------------------------------------

    def sell(
        self,
        security_id,
        symbol,
        price,
        qty
    ):
        return self._execute(
            transaction_type=dhan.SELL,
            side_label="SELL",
            security_id=security_id,
            symbol=symbol,
            qty=qty
        )