"""
==========================================================
Price History Provider  (optional jugaad-data backfill)
==========================================================

Deeper historical prices for proper event studies:
multi-day windows and market-adjusted abnormal returns
computed against real NIFTY history.

Uses jugaad-data (github.com/jugaad-py/jugaad-data) when
installed; degrades GRACEFULLY to None when it is not —
the live reaction-decay path never depends on it, because
that path already computes abnormal returns from the
bot's own intraday data (stock change − breadth avg).

    pip install jugaad-data

This module NEVER trades.

Author : H&M ORB AUTO TRADER
==========================================================
"""

from datetime import date, timedelta


class PriceHistory:

    def __init__(self):
        self.available = False
        self._stock_fn = None
        self._index_fn = None

        try:
            from jugaad_data.nse import stock_df, index_df
            self._stock_fn = stock_df
            self._index_fn = index_df
            self.available = True
            print("[HISTORY] jugaad-data available")
        except Exception:
            print(
                "[HISTORY] jugaad-data not installed — "
                "deep backfill disabled (live decay model "
                "still works from own data). "
                "pip install jugaad-data to enable."
            )

    # --------------------------------------------------

    def daily_returns(self, symbol, days=90):
        """
        Recent daily % returns for a symbol, or None.
        """
        if not self.available:
            return None

        try:
            end = date.today()
            start = end - timedelta(days=int(days * 1.6))

            df = self._stock_fn(
                symbol=symbol,
                from_date=start,
                to_date=end,
                series="EQ",
            )
            if df is None or df.empty:
                return None

            closes = df["CLOSE"].astype(float).tolist()
            returns = [
                round(
                    (closes[i] - closes[i - 1])
                    / closes[i - 1] * 100, 2
                )
                for i in range(1, len(closes))
            ]
            return returns
        except Exception as e:
            print(f"[HISTORY] {symbol} failed: {str(e)[:80]}")
            return None

    # --------------------------------------------------

    def index_returns(self, index="NIFTY 50", days=90):
        """
        Recent daily % returns for the market index —
        the benchmark for abnormal-return calculation.
        """
        if not self.available:
            return None

        try:
            end = date.today()
            start = end - timedelta(days=int(days * 1.6))

            df = self._index_fn(
                symbol=index,
                from_date=start,
                to_date=end,
            )
            if df is None or df.empty:
                return None

            col = (
                "CLOSE" if "CLOSE" in df.columns
                else df.columns[-1]
            )
            closes = df[col].astype(float).tolist()
            return [
                round(
                    (closes[i] - closes[i - 1])
                    / closes[i - 1] * 100, 2
                )
                for i in range(1, len(closes))
            ]
        except Exception:
            return None

    # --------------------------------------------------

    def abnormal_return(self, symbol, event_date):
        """
        Event-study abnormal return on the event day:
        stock return − index return. None if unavailable.
        (Deep/historical path; the live path uses breadth.)
        """
        if not self.available:
            return None

        try:
            from jugaad_data.nse import stock_df, index_df

            d = event_date
            if isinstance(d, str):
                from datetime import datetime as _dt
                d = _dt.strptime(d, "%Y-%m-%d").date()

            window_start = d - timedelta(days=4)
            window_end = d + timedelta(days=1)

            sdf = stock_df(
                symbol=symbol,
                from_date=window_start,
                to_date=window_end,
                series="EQ",
            )
            idf = index_df(
                symbol="NIFTY 50",
                from_date=window_start,
                to_date=window_end,
            )
            if sdf is None or sdf.empty:
                return None

            def day_return(df):
                closes = df["CLOSE"].astype(float).tolist() \
                    if "CLOSE" in df.columns \
                    else df[df.columns[-1]].astype(float).tolist()
                if len(closes) < 2:
                    return None
                return (closes[-1] - closes[-2]) / closes[-2] * 100

            stock_r = day_return(sdf)
            index_r = day_return(idf) if idf is not None else 0.0

            if stock_r is None:
                return None

            return round(stock_r - (index_r or 0.0), 2)
        except Exception:
            return None


price_history = PriceHistory()
