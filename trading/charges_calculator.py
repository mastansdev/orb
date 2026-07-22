import csv


class ChargesCalculator:

    BROKERAGE_PER_ORDER = 20.00

    STT_RATE = 0.00025                 # 0.025% Sell Side
    EXCHANGE_RATE = 0.000030699        # NSE
    SEBI_RATE = 0.000001               # ₹10 / Crore
    STAMP_RATE = 0.00003               # 0.003% Buy Side
    GST_RATE = 0.18

    # --------------------------------------------------
    # Fix (2026-07-22): single-trade version of the exact
    # same charge model above, for the historical backtester
    # (core/historical_fetcher.py and whatever consumes it) --
    # so a backtested trade's "net" P&L is computed with the
    # SAME real rates the live/paper engine already uses, not
    # a separately-invented estimate. calculate()/todays_trades()
    # below are untouched.
    # --------------------------------------------------

    def charge_for_trade(self, entry, exit_price, qty):
        buy_turnover = entry * qty
        sell_turnover = exit_price * qty
        total_turnover = buy_turnover + sell_turnover

        brokerage = 2 * self.BROKERAGE_PER_ORDER  # one buy + one sell order
        stt = sell_turnover * self.STT_RATE
        exchange = total_turnover * self.EXCHANGE_RATE
        sebi = total_turnover * self.SEBI_RATE
        stamp = buy_turnover * self.STAMP_RATE
        gst = (brokerage + exchange + sebi) * self.GST_RATE

        total_charges = (
            brokerage + stt + exchange + sebi + stamp + gst
        )

        gross_pnl = sell_turnover - buy_turnover

        return {
            "gross_pnl": round(gross_pnl, 2),
            "total_charges": round(total_charges, 2),
            "net_pnl": round(gross_pnl - total_charges, 2),
        }

    # --------------------------------------------------
    # Fix (2026-07-22): a partial-booked trade is really ONE
    # buy order + TWO sell orders (the partial exit, then the
    # final exit) -- calling charge_for_trade() twice would
    # double-charge a phantom second buy order. This computes
    # brokerage as (1 buy + N sells), same rate table, so the
    # backtester's numbers for the true-trailing-runner mode
    # (which always partial-books) are accurate, not inflated.
    # --------------------------------------------------

    def charge_for_multi_exit_trade(self, entry, qty, exits):
        """
        exits: list of (exit_price, exit_qty) tuples that sum
        to qty -- one entry (buy) order, N exit (sell) orders.
        """
        buy_turnover = entry * qty
        sell_turnover = sum(price * q for price, q in exits)
        total_turnover = buy_turnover + sell_turnover

        num_orders = 1 + len(exits)
        brokerage = num_orders * self.BROKERAGE_PER_ORDER
        stt = sell_turnover * self.STT_RATE
        exchange = total_turnover * self.EXCHANGE_RATE
        sebi = total_turnover * self.SEBI_RATE
        stamp = buy_turnover * self.STAMP_RATE
        gst = (brokerage + exchange + sebi) * self.GST_RATE

        total_charges = (
            brokerage + stt + exchange + sebi + stamp + gst
        )

        gross_pnl = sell_turnover - buy_turnover

        return {
            "gross_pnl": round(gross_pnl, 2),
            "total_charges": round(total_charges, 2),
            "net_pnl": round(gross_pnl - total_charges, 2),
        }

    # --------------------------------------------------

    def load_trades(self):

        try:

            with open(
                "trade_log.csv",
                newline="",
                encoding="utf-8"
            ) as file:

                return list(csv.DictReader(file))

        except FileNotFoundError:

            return []

    # --------------------------------------------------

    def todays_trades(self):

        trades = self.load_trades()

        if not trades:
            return []

        latest_date = max(
            trade["Date"]
            for trade in trades
        )

        return [
            trade
            for trade in trades
            if trade["Date"] == latest_date
        ]

    # --------------------------------------------------

    def calculate(self):

        trades = self.todays_trades()

        buy_turnover = 0.0
        sell_turnover = 0.0
        gross_pnl = 0.0

        for trade in trades:

            entry = float(trade["Entry"])
            exit = float(trade["Exit"])
            qty = int(trade["Qty"])

            buy_turnover += entry * qty
            sell_turnover += exit * qty
            gross_pnl += float(trade["PnL"])

        total_turnover = buy_turnover + sell_turnover

        brokerage = len(trades) * 2 * self.BROKERAGE_PER_ORDER

        stt = sell_turnover * self.STT_RATE

        exchange = total_turnover * self.EXCHANGE_RATE

        sebi = total_turnover * self.SEBI_RATE

        stamp = buy_turnover * self.STAMP_RATE

        gst = (
            brokerage +
            exchange +
            sebi
        ) * self.GST_RATE

        total_charges = (
            brokerage +
            stt +
            exchange +
            sebi +
            stamp +
            gst
        )

        net_pnl = gross_pnl - total_charges

        return {

            "trades": len(trades),

            "buy_turnover": round(buy_turnover, 2),
            "sell_turnover": round(sell_turnover, 2),
            "total_turnover": round(total_turnover, 2),

            "gross_pnl": round(gross_pnl, 2),

            "brokerage": round(brokerage, 2),
            "stt": round(stt, 2),
            "exchange": round(exchange, 2),
            "sebi": round(sebi, 2),
            "stamp": round(stamp, 2),
            "gst": round(gst, 2),

            "total_charges": round(total_charges, 2),

            "net_pnl": round(net_pnl, 2)

        }


# ------------------------------------------------------

if __name__ == "__main__":

    c = ChargesCalculator()

    r = c.calculate()

    print()
    print("=" * 65)
    print("               CHARGES CALCULATOR")
    print("=" * 65)

    print(f"Trades            : {r['trades']}")

    print()

    print(f"Buy Turnover      : ₹{r['buy_turnover']:,.2f}")
    print(f"Sell Turnover     : ₹{r['sell_turnover']:,.2f}")
    print(f"Total Turnover    : ₹{r['total_turnover']:,.2f}")

    print()

    print(f"Gross P&L         : ₹{r['gross_pnl']:,.2f}")

    print()

    print(f"Brokerage         : ₹{r['brokerage']:,.2f}")
    print(f"STT               : ₹{r['stt']:,.2f}")
    print(f"Exchange          : ₹{r['exchange']:,.2f}")
    print(f"SEBI              : ₹{r['sebi']:,.2f}")
    print(f"Stamp Duty        : ₹{r['stamp']:,.2f}")
    print(f"GST               : ₹{r['gst']:,.2f}")

    print("-" * 65)

    print(f"Total Charges     : ₹{r['total_charges']:,.2f}")

    print()

    print(f"NET P&L           : ₹{r['net_pnl']:,.2f}")

    print("=" * 65)