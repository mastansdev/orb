"""
==========================================================
ORB Strategy Backtest
==========================================================

Replays real historical price bars through the ACTUAL live
Strategy (core/strategy.py) and DynamicTradeManager
(trading/dynamic_trade_manager.py) classes -- not a
reimplementation of the entry/exit logic, the real thing --
so results reflect what the CURRENT live code would actually
have done, not a guess at what it might do.

SCOPE -- read this before trusting a single number out of it
--------------------------------------------------------------
This tests ONLY the price-structural half of the bot: ORB
breakout detection + the exit/risk-management framework. It
does NOT test the news/evidence/conviction entry-filtering
half (10 evidence sources, CONVICTION_MIN_SCORE=55, etc.) --
there is no historical news archive to replay against, so
that half can only be judged from live paper trading. Every
entry here fires purely on "did price break the opening range
with a closed-candle confirmation," which is a looser filter
than production's real entry bar. Treat this as "how good is
the EXIT framework, given a reasonable entry," not "how many
trades would the live bot actually take."

Also bar-based, not tick-by-tick: stop/target levels are
checked against each bar's low/high, not a live tick stream.
When a bar's low would hit the stop AND its high would hit a
target in the same bar, the stop is assumed to fire first --
the conservative assumption, standard practice, but not proof
of exactly what a live tick sequence would have done.

THREE EXIT MODES COMPARED
--------------------------------------------------------------
Every detected entry is run through all three, in parallel,
against the identical subsequent price path -- an apples-to-
apples comparison:

    OLD_1_1       Retired 2026-07-22. Full position closes the
                  instant price hits entry + 1x risk. This is
                  what the live bot did before last night --
                  reimplemented here ONLY for comparison, the
                  live trading/risk_manager.py no longer has
                  this behavior.
    HARD_2_1_CAP  Never was live. Partial-books at 1R like the
                  real DynamicTradeManager, trails the
                  remainder, but force-closes everything the
                  instant price hits entry + 2x risk.
    TRAILING_RUNNER  What's actually live today. Partial-books
                  at 1R, trails the remainder with NO fixed
                  cap -- exits only via the ratcheting trail,
                  the stop, or the hard 15:15 time exit.

Position sizing: RISK_PER_TRADE (1% of CAPITAL) / (entry -
stop), the same formula PositionManager uses live -- but
without the live portfolio-heat/sector-cap/replacement
machinery, since this tests one symbol's price action in
isolation, not portfolio-level capital competition.

Charges: the exact real rate table from
trading/charges_calculator.py (brokerage, STT, exchange, SEBI,
stamp duty, GST) -- every "net" number below is genuinely
after-charges, not gross.

Usage:
    py backtest/orb_strategy_backtest.py

Author : H&M ORB AUTO TRADER
==========================================================
"""

import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from config import (
    CAPITAL,
    RISK_PER_TRADE,
    ORB_BUFFER,
    MIN_ORB_RANGE_PERCENT,
    MIN_PRICE,
    HARD_EXIT_TIME,
)
from core.historical_fetcher import HistoricalFetcher
from core.strategy import Strategy
from trading.risk_manager import RiskManager
from trading.dynamic_trade_manager import DynamicTradeManager
from trading.charges_calculator import ChargesCalculator


# Liquid, F&O-active NSE names confirmed present in the real
# master database (Masterdata/master_database.xlsx) -- not a
# guess, looked each one up before including it.
DEFAULT_UNIVERSE = {
    "RELIANCE": "2885", "TCS": "11536", "HDFCBANK": "1333",
    "INFY": "1594", "ICICIBANK": "4963", "SBIN": "3045",
    "AXISBANK": "5900", "KOTAKBANK": "1922", "LT": "11483",
    "BAJFINANCE": "317", "HINDUNILVR": "1394", "ITC": "1660",
    "MARUTI": "10999", "SUNPHARMA": "3351", "WIPRO": "3787",
    "ONGC": "2475", "TITAN": "3506", "ULTRACEMCO": "11532",
}

# Fix (2026-07-22): DEFAULT_UNIVERSE above is safe, liquid
# blue chips -- convenient for a first pass, but the WRONG
# sample to test the bot's real thesis. Large-cap index names
# move mostly on broad flows, not single-stock catalysts.
# This is the high-news-conviction / thematic-momentum
# universe the user actually asked to test: AI/semiconductor/
# electronics manufacturing, defense, and power/T&D names --
# every symbol below confirmed present in the real master
# database (not guessed).
THEMATIC_UNIVERSE = {
    "NETWEB": "17433",      # AI/data-center servers
    "GVT&D": "16783",       # power transmission & distribution
    "POWERINDIA": "18457",  # Hitachi Energy India, power equipment
    "CGPOWER": "760",       # CG Power, capital goods/power
    "BEL": "383",           # defense electronics
    "HAL": "2303",          # defense aerospace
    "MAZDOCK": "509",       # defense shipbuilding
    "DIXON": "21690",       # electronics manufacturing (EMS)
    "KAYNES": "12092",      # electronics manufacturing (EMS)
    "SUZLON": "12018",      # renewables/wind power
    "TATAPOWER": "3426",    # power/renewables
    "TATAELXSI": "3411",    # design/tech, EV & semiconductor-adjacent
    "SIEMENS": "3150",      # capital goods/power equipment
    "ABB": "13",            # capital goods/automation
}

MODES = ("OLD_1_1", "HARD_2_1_CAP", "TRAILING_RUNNER")


# ==========================================================
# Bar / candle helpers
# ==========================================================

def _bars_to_days(minute_data):
    """
    Dhan's minute payload is parallel arrays; group into a
    dict of {date_str: [bar, ...]} sorted chronologically,
    each bar a dict with open/high/low/close/volume/time.
    """
    days = defaultdict(list)
    timestamps = minute_data.get("timestamp", [])

    for i, ts in enumerate(timestamps):
        dt = datetime.fromtimestamp(ts)
        day_key = dt.strftime("%Y-%m-%d")
        days[day_key].append({
            "time": dt.strftime("%H:%M:%S"),
            "open": minute_data["open"][i],
            "high": minute_data["high"][i],
            "low": minute_data["low"][i],
            "close": minute_data["close"][i],
        })

    for day_key in days:
        days[day_key].sort(key=lambda b: b["time"])

    return days


def _build_orb(day_bars):
    """
    Opening range from bars in [09:15, 09:30) -- bar high/low
    as a proxy for the tick-level high/low a live ORB builder
    would see. Returns (orb_high, orb_low) or (None, None) if
    there's no data in that window.
    """
    orb_high = orb_low = None
    for bar in day_bars:
        if bar["time"] >= "09:30:00":
            break
        orb_high = bar["high"] if orb_high is None else max(orb_high, bar["high"])
        orb_low = bar["low"] if orb_low is None else min(orb_low, bar["low"])
    return orb_high, orb_low


# ==========================================================
# Entry detection -- the REAL Strategy class, not a copy
# ==========================================================

def find_entry(day_bars, strategy):
    """
    Walks the day's bars using the actual live
    Strategy.is_buy_signal(). Returns an entry dict or None.

    Fix (2026-07-22): a bar isn't "closed" until the NEXT bar
    starts -- checking is_buy_signal() using a bar's own close
    at that same bar's own start time is a lookahead bug (it
    would mean knowing a candle's close before that candle has
    even finished forming). Walk PAIRS instead: at curr_bar's
    start ("now"), the most recently CLOSED candle is prev_bar.
    Entry price is curr_bar's open -- the closest honest proxy
    for "price right as we notice the just-closed confirmation",
    since live entry price is whatever ltp is at that moment,
    not the already-closed candle's own price.
    """
    orb_high, orb_low = _build_orb(day_bars)
    if orb_high is None or orb_low <= 0:
        return None

    orb_range_pct = ((orb_high - orb_low) / orb_low) * 100
    if orb_range_pct < MIN_ORB_RANGE_PERCENT:
        return None  # same gate trade_selection_engine.py applies live

    post_orb_bars = [b for b in day_bars if b["time"] >= "09:30:00"]
    if len(post_orb_bars) < 2:
        return None  # need at least one closed post-ORB candle

    orb = {
        "completed": True,
        "entry_taken": False,
        "high": orb_high,
        "low": orb_low,
    }

    for i in range(1, len(post_orb_bars)):
        prev_bar = post_orb_bars[i - 1]
        curr_bar = post_orb_bars[i]

        last_closed_candle = {"close": prev_bar["close"]}

        if strategy.is_buy_signal(orb, curr_bar["time"], last_closed_candle):
            entry_price = curr_bar["open"]
            if entry_price < MIN_PRICE:
                return None
            return {
                "entry_price": entry_price,
                "entry_time": curr_bar["time"],
                "orb_high": orb_high,
                "orb_low": orb_low,
            }

    return None


# ==========================================================
# Trade simulation -- the REAL RiskManager + DynamicTradeManager
# ==========================================================

def _qty_for(entry_price, stop_loss):
    risk_per_share = entry_price - stop_loss
    if risk_per_share <= 0:
        return 0
    budget = CAPITAL * RISK_PER_TRADE
    qty = int(budget // risk_per_share)
    return max(qty, 0)


def simulate_trade(entry, bars_after_entry, mode, charges):
    """
    Runs ONE detected entry forward through the rest of the
    day's bars under the given exit `mode`. Returns a result
    dict, or None if quantity sizing failed (stop too close /
    zero risk).
    """
    entry_price = entry["entry_price"]
    stop_loss = entry["orb_low"] - ORB_BUFFER

    qty = _qty_for(entry_price, stop_loss)
    if qty <= 0:
        return None

    risk_mgr = RiskManager()
    dyn_mgr = DynamicTradeManager()  # no news/fno wiring -> catalyst exit never fires here (honest: this backtest can't see news)

    trade = risk_mgr.create_trade(entry_price, stop_loss)
    trade["qty"] = qty
    original_qty = qty

    exits = []  # (price, qty) sell fills
    remaining_qty = qty

    for bar in bars_after_entry:
        if remaining_qty <= 0:
            break

        # Conservative bar-based fill check: test the LOW
        # first (stop side) before the HIGH (upside side),
        # since we don't know the true intra-bar tick order.
        for probe_price in (bar["low"], bar["high"], bar["close"]):
            if remaining_qty <= 0:
                break

            result = risk_mgr.update(trade, probe_price, bar["time"])

            if result == "STOPLOSS":
                exits.append((probe_price, remaining_qty))
                remaining_qty = 0
                trade["active"] = False
                break

            if result == "TIME_EXIT":
                exits.append((probe_price, remaining_qty))
                remaining_qty = 0
                trade["active"] = False
                break

            if result != "ACTIVE":
                continue

            # -- retired hard-target modes, comparison only --
            # Fill AT the target, not at the (coarser) bar
            # probe price that crossed it -- using the probe
            # price would let a hard-capped trade "overshoot"
            # its own cap whenever a bar's high jumps past the
            # target, which flatters OLD_1_1/HARD_2_1_CAP
            # against TRAILING_RUNNER and isn't how a real
            # target order behaves.
            if mode == "OLD_1_1":
                target = trade["entry"] + trade["risk"] * 1.0
                if probe_price >= target:
                    exits.append((target, remaining_qty))
                    remaining_qty = 0
                    trade["active"] = False
                    break
                continue  # OLD_1_1 never partial-books/trails

            if mode == "HARD_2_1_CAP":
                target = trade["entry"] + trade["risk"] * 2.0
                if probe_price >= target:
                    exits.append((target, remaining_qty))
                    remaining_qty = 0
                    trade["active"] = False
                    break

            # TRAILING_RUNNER and HARD_2_1_CAP (below its cap)
            # both use the real DynamicTradeManager.
            advice = dyn_mgr.advise("BT", trade, probe_price)

            if advice["action"] == "PARTIAL_BOOK":
                book_qty = min(advice["qty"], remaining_qty)
                if book_qty > 0:
                    exits.append((probe_price, book_qty))
                    remaining_qty -= book_qty
                    trade["qty"] = remaining_qty
                    trade["partial_done"] = True

            elif advice["action"] == "TIGHTEN":
                trade["trail_sl"] = advice["new_trail"]
                trade["trail_active"] = True

            elif advice["action"] == "EXIT":
                # velocity/catalyst -- catalyst can't fire here
                # (no live news feed in a backtest); velocity can.
                exits.append((probe_price, remaining_qty))
                remaining_qty = 0
                trade["active"] = False
                break

        if not trade.get("active", True):
            break

    # Hard time exit -- anything still open at HARD_EXIT_TIME
    # closes at the last bar's close, matching the live 15:15
    # MIS square-off rule.
    if remaining_qty > 0 and bars_after_entry:
        last_close = bars_after_entry[-1]["close"]
        exits.append((last_close, remaining_qty))
        remaining_qty = 0

    if not exits:
        return None

    charge_result = charges.charge_for_multi_exit_trade(
        entry_price, original_qty, exits
    )

    return {
        "mode": mode,
        "qty": original_qty,
        "num_exits": len(exits),
        **charge_result,
    }


# ==========================================================
# Aggregation / reporting
# ==========================================================

def summarize(results_by_mode):
    print("\n" + "=" * 72)
    print("ORB STRATEGY BACKTEST -- RESULTS")
    print("=" * 72)

    for mode in MODES:
        trades = results_by_mode[mode]
        if not trades:
            print(f"\n{mode}: no trades")
            continue

        n = len(trades)
        wins = [t for t in trades if t["net_pnl"] > 0]
        total_net = sum(t["net_pnl"] for t in trades)
        avg_net = total_net / n
        win_rate = 100 * len(wins) / n
        best = max(trades, key=lambda t: t["net_pnl"])
        worst = min(trades, key=lambda t: t["net_pnl"])

        print(f"\n{mode}")
        print(f"  Trades       : {n}")
        print(f"  Win rate     : {win_rate:.1f}%")
        print(f"  Avg net P&L  : Rs {avg_net:,.0f} / trade")
        print(f"  Total net    : Rs {total_net:,.0f}")
        print(f"  Best trade   : Rs {best['net_pnl']:,.0f}")
        print(f"  Worst trade  : Rs {worst['net_pnl']:,.0f}")

    # --------------------------------------------------
    # Per-symbol breakdown (2026-07-22) -- lets you line
    # this up directly against a simple buy-and-hold return
    # table per stock, to check whether losses concentrate
    # in stocks that were actually declining over the period,
    # or whether they're spread evenly regardless of trend.
    # Reported for TRAILING_RUNNER only, since that's what's
    # actually live today.
    # --------------------------------------------------
    print("\nPER-SYMBOL BREAKDOWN (TRAILING_RUNNER -- the live mode)")
    print("-" * 72)

    by_symbol = defaultdict(list)
    for t in results_by_mode["TRAILING_RUNNER"]:
        by_symbol[t["symbol"]].append(t)

    symbol_rows = []
    for symbol, trades in by_symbol.items():
        n = len(trades)
        total_net = sum(t["net_pnl"] for t in trades)
        wins = sum(1 for t in trades if t["net_pnl"] > 0)
        symbol_rows.append((symbol, n, total_net, 100 * wins / n))

    symbol_rows.sort(key=lambda r: r[2], reverse=True)

    print(f"{'Symbol':<12}{'Trades':>8}{'Win %':>10}{'Total Net':>16}")
    for symbol, n, total_net, win_pct in symbol_rows:
        print(f"{symbol:<12}{n:>8}{win_pct:>9.1f}%{total_net:>16,.0f}")

    print("\n" + "=" * 72)
    print("Reminder: this tests ENTRY-ON-BREAKOUT + EXIT MANAGEMENT only.")
    print("It does NOT validate the news/evidence conviction filter --")
    print("that side can only be judged from live paper trading.")
    print("=" * 72 + "\n")


# ==========================================================
# Main
# ==========================================================

def run_backtest(universe=None, years=1.0, interval=15):
    universe = universe or DEFAULT_UNIVERSE
    fetcher = HistoricalFetcher()
    strategy = Strategy()
    charges = ChargesCalculator()

    results_by_mode = {mode: [] for mode in MODES}

    to_d = date.today()
    from_d = to_d - timedelta(days=int(years * 365.25))

    for symbol, security_id in universe.items():
        print(f"\nFetching {symbol} ({security_id})...")
        minute_data = fetcher.get_minute_history(
            security_id=security_id,
            from_date=from_d.strftime("%Y-%m-%d"),
            to_date=to_d.strftime("%Y-%m-%d"),
            interval=interval,
        )

        if minute_data is None:
            print(f"  no data -- skipped")
            continue

        days = _bars_to_days(minute_data)
        print(f"  {len(days)} trading days, simulating breakouts...")

        symbol_entries = 0
        for day_key in sorted(days.keys()):
            day_bars = days[day_key]

            entry = find_entry(day_bars, strategy)
            if entry is None:
                continue

            bars_after = [
                b for b in day_bars
                if b["time"] > entry["entry_time"]
                and b["time"] <= HARD_EXIT_TIME + ":00"
            ]
            if not bars_after:
                continue

            symbol_entries += 1
            for mode in MODES:
                result = simulate_trade(entry, bars_after, mode, charges)
                if result is not None:
                    result["symbol"] = symbol
                    result["date"] = day_key
                    results_by_mode[mode].append(result)

        print(f"  {symbol_entries} breakout entries found")

    summarize(results_by_mode)
    return results_by_mode


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--universe",
        choices=["default", "thematic"],
        default="default",
        help=(
            "default = 18 liquid blue chips. "
            "thematic = AI/semiconductor/EMS/defense/power "
            "high-news-conviction names."
        ),
    )
    parser.add_argument(
        "--years", type=float, default=1.0,
        help="how many years back to test (default 1.0)",
    )
    args = parser.parse_args()

    chosen_universe = (
        THEMATIC_UNIVERSE if args.universe == "thematic"
        else DEFAULT_UNIVERSE
    )

    run_backtest(universe=chosen_universe, years=args.years)
