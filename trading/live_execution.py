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

import time
import traceback
from datetime import datetime

from config import (
    PRODUCT_TYPE,
    ORDER_TYPE,
    ENABLE_TELEGRAM_CONFIRMATION,
    ORDER_RETRY_COUNT,
)

from trading.dhan_client import dhan
from trading.execution_quality import ExecutionQuality

# Import your telegram notifier later
# from notifications.telegram_notifier import send_message


class LiveExecution:

    def __init__(self):
        self.execution_quality = ExecutionQuality()
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

    def _confirm_fill(self, order_id):
        """
        Post-placement confirmation: fetch the order and
        read status + average traded price. Returns
        (status, fill_price) — (None, None) on failure.
        """
        try:
            detail = dhan.get_order_by_id(order_id)

            data = (
                detail.get("data")
                if isinstance(detail, dict) else None
            )

            if isinstance(data, list) and data:
                data = data[0]

            if not isinstance(data, dict):
                return None, None

            status = data.get("orderStatus", "")

            fill_price = (
                data.get("averageTradedPrice")
                or data.get("average_traded_price")
                or data.get("tradedPrice")
            )

            return status, (
                float(fill_price) if fill_price else None
            )

        except Exception:
            return None, None

    # ---------------------------------------------------------

    def _execute(
        self,
        transaction_type,
        side_label,
        security_id,
        symbol,
        qty,
        price=0
    ):
        """
        Consolidated order wrapper handling SDK
        handshakes, retries, price mapping, fill
        confirmation, and slippage capture.
        """
        try:
            self._validate_order(
                security_id,
                symbol,
                qty
            )

            order_type = self._get_order_type()

            # Price mapping: MARKET ignores price;
            # LIMIT uses it; STOP_LIMIT uses it as
            # trigger + limit.
            order_price = 0
            trigger_price = 0

            if order_type == dhan.LIMIT:
                order_price = float(price or 0)
            elif order_type == dhan.SL:
                order_price = float(price or 0)
                trigger_price = float(price or 0)

            response = None
            last_error = "Order not attempted."

            for attempt in range(
                1, max(1, ORDER_RETRY_COUNT) + 1
            ):
                try:
                    response = dhan.place_order(
                        security_id=str(security_id),
                        exchange_segment=dhan.NSE,
                        transaction_type=transaction_type,
                        quantity=int(qty),
                        order_type=order_type,
                        product_type=self._get_product_type(),
                        price=order_price,
                        trigger_price=trigger_price,
                        validity="DAY"
                    )

                    if (
                        isinstance(response, dict)
                        and response.get("status") == "success"
                    ):
                        break

                    last_error = (
                        response.get("remarks", "rejected")
                        if isinstance(response, dict)
                        else str(response)
                    )

                except Exception as e:
                    last_error = str(e)
                    response = None

                if attempt < ORDER_RETRY_COUNT:
                    print(
                        f"[EXEC] Retry {attempt}/"
                        f"{ORDER_RETRY_COUNT}: {symbol} "
                        f"({str(last_error)[:80]})"
                    )
                    time.sleep(1)

            self._log_execution(
                side_label,
                symbol,
                qty,
                response
            )

            if ENABLE_TELEGRAM_CONFIRMATION:
                pass

            if (
                isinstance(response, dict)
                and response.get("status") == "success"
            ):
                # ------------------------------------
                # Fill confirmation + slippage capture
                # ------------------------------------
                order_id = ""
                try:
                    order_id = str(
                        response.get("data", {}).get(
                            "orderId", ""
                        )
                    )
                except Exception:
                    pass

                fill_status, fill_price = (None, None)

                if order_id:
                    fill_status, fill_price = (
                        self._confirm_fill(order_id)
                    )

                self.execution_quality.record(
                    mode="LIVE",
                    side=side_label,
                    symbol=symbol,
                    qty=qty,
                    intended_price=float(price or 0),
                    fill_price=fill_price,
                    order_id=order_id,
                    status=fill_status or "PLACED",
                )

                return self._success(response)

            # All attempts failed
            self.execution_quality.record(
                mode="LIVE",
                side=side_label,
                symbol=symbol,
                qty=qty,
                intended_price=float(price or 0),
                fill_price=None,
                status=f"FAILED: {str(last_error)[:60]}",
            )

            return self._failure(last_error)

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
            qty=qty,
            price=price
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
            qty=qty,
            price=price
        )