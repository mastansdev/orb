"""
greeks_check.py

Read-only F&O decision-support tool for the ORB Auto Trader repo.
Does NOT place orders, does NOT touch OwnershipRegistry, brain.py, or the
execution pipeline. Pure lookup/calculator, meant to be run manually or
wired into a Telegram command later.

Usage:
    python greeks_check.py BHEL 450 CE
    python greeks_check.py NIFTY 24500 PE --expiry 2026-07-23

Env vars required (same as your existing Dhan wrapper):
    DHAN_CLIENT_ID
    DHAN_ACCESS_TOKEN

Dependencies:
    pip install requests --break-system-packages
"""

import os
import sys
import argparse
import requests
from datetime import datetime, date, timedelta
from instrument_loader import InstrumentLoader

try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(dotenv_path=_env_path)
except ImportError:
    print("NOTE: python-dotenv not installed — run: py -m pip install python-dotenv")

BASE_URL = "https://api.dhan.co/v2"

_loader = InstrumentLoader()

# Known indices trade under IDX_I, not NSE_EQ. Extend this set as needed.
INDEX_SYMBOLS = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"}

# NSE trading holidays 2026 (source: NSE official circulars, via exchange holiday calendar)
NSE_HOLIDAYS_2026 = {
    date(2026, 1, 15), date(2026, 1, 26), date(2026, 3, 3), date(2026, 3, 26),
    date(2026, 3, 31), date(2026, 4, 3), date(2026, 4, 14), date(2026, 5, 1),
    date(2026, 5, 28), date(2026, 6, 26), date(2026, 9, 14), date(2026, 10, 2),
    date(2026, 10, 20), date(2026, 11, 10), date(2026, 11, 24), date(2026, 12, 25),
}


def trading_days_left(from_date: date, to_date: date) -> int:
    """Counts trading days strictly between from_date and to_date (exclusive of
    from_date, inclusive of to_date), skipping Sat/Sun and NSE_HOLIDAYS_2026."""
    if to_date <= from_date:
        return 0
    count = 0
    d = from_date + timedelta(days=1)
    while d <= to_date:
        if d.weekday() < 5 and d not in NSE_HOLIDAYS_2026:  # Mon=0 ... Fri=4
            count += 1
        d += timedelta(days=1)
    return count


def get_headers():
    client_id = os.environ.get("DHAN_CLIENT_ID")
    access_token = os.environ.get("DHAN_ACCESS_TOKEN")
    if not client_id or not access_token:
        print("ERROR: Set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN env vars.")
        sys.exit(1)
    return {
        "Content-Type": "application/json",
        "access-token": access_token,
        "client-id": client_id,
    }


def get_security_id(symbol: str) -> tuple[str, str]:
    """
    Resolves a symbol (e.g. "BHEL", "NIFTY") to (security_id, exchange_segment)
    using the repo's existing InstrumentLoader / master_loader.
    """
    symbol = symbol.upper()
    security_id = _loader.get_security_id(symbol)

    if security_id is None:
        print(f"ERROR: '{symbol}' not found in instrument master. "
              f"Check spelling or confirm it's in MASTER_STOCKS_v2.")
        sys.exit(1)

    exchange_segment = "IDX_I" if symbol in INDEX_SYMBOLS else "NSE_EQ"
    return int(security_id), exchange_segment


def get_expiry_list(security_id: str, exchange_segment: str) -> list[str]:
    resp = requests.post(
        f"{BASE_URL}/optionchain/expirylist",
        headers=get_headers(),
        json={
            "UnderlyingScrip": security_id,
            "UnderlyingSeg": exchange_segment,
        },
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"\nDhan API error {resp.status_code}: {resp.text}\n")
    resp.raise_for_status()
    return resp.json().get("data", [])


def get_option_chain(security_id: str, exchange_segment: str, expiry: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/optionchain",
        headers=get_headers(),
        json={
            "UnderlyingScrip": security_id,
            "UnderlyingSeg": exchange_segment,
            "Expiry": expiry,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("data", {})


def analyze(symbol: str, strike: float, option_type: str, expiry: str | None, days_forward: int = 0):
    security_id, exchange_segment = get_security_id(symbol)

    if not expiry:
        expiries = get_expiry_list(security_id, exchange_segment)
        if not expiries:
            print("No expiries found.")
            return
        expiry = expiries[0]  # nearest expiry

    chain = get_option_chain(security_id, exchange_segment, expiry)

    spot = chain.get("last_price")
    strikes_data = chain.get("oc", {})
    strike_key = f"{strike:.6f}"  # Dhan keys strikes as strings

    if strike_key not in strikes_data:
        print(f"Strike {strike} not found in chain for {symbol} {expiry}.")
        return

    leg = strikes_data[strike_key].get(option_type.lower())
    if not leg:
        print(f"No {option_type} data for strike {strike}.")
        return

    ltp = leg.get("last_price")
    delta = leg.get("greeks", {}).get("delta")
    theta = leg.get("greeks", {}).get("theta")
    gamma = leg.get("greeks", {}).get("gamma")
    iv = leg.get("implied_volatility")

    today = date.today()
    expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
    days_left = trading_days_left(today, expiry_date)

    print(f"\n=== {symbol} {int(strike)}{option_type.upper()} ===")
    print(f"Date: {today.strftime('%d-%b-%Y')} ({today.strftime('%A')})")
    print(f"Expiry: {expiry_date.strftime('%d-%b-%Y')} ({expiry_date.strftime('%A')})")
    print(f"Trading days left (excl. weekends & NSE holidays): {days_left}")

    print(f"\nStock price now: Rs.{spot}")
    print(f"Option price now: Rs.{ltp}")

    print("\n--- Quick Read ---")

    is_itm = (option_type.upper() == "CE" and spot > strike) or \
             (option_type.upper() == "PE" and spot < strike)

    if delta:
        pts_per_rupee = round(1 / delta) if delta else None
        tightening = " (tightens more as price nears strike)" if not is_itm else ""
        print(f"Stock UP Rs.{pts_per_rupee} = Premium UP ~Rs.1{tightening}")

    if theta is not None:
        print(f"No movement / slow day = lose ~Rs.{abs(theta):.2f}/day (decay)")

    if iv is not None:
        iv_label = "High risk of premium drop even if right on direction" if iv > 35 \
            else "Normal risk" if iv > 20 else "Low volatility priced in"
        print(f"Volatility: {iv_label} ({iv:.0f}%)")

    if delta and ltp:
        breakeven_points = abs(ltp / delta)
        print(f"Breakeven: ~{breakeven_points:.0f} pts move needed{' (already ITM)' if is_itm else ''}")

    if days_forward > 0 and theta:
        decay_cost = abs(theta) * days_forward
        print(f"Holding {days_forward} day(s): ~Rs.{decay_cost:.2f} lost to time, even if flat")
    else:
        print("Holding: Intraday")

    if ltp and spot:
        project_premium_table(ltp, spot, delta, theta, gamma, option_type, days_forward)

    print(f"\nChecked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def project_premium_table(ltp, spot, delta, theta, gamma, option_type, days_forward=0):
    """
    Estimates new premium for a range of underlying moves, using:
        new_premium = ltp + (delta * move) + (0.5 * gamma * move^2) + (theta * days_forward)

    This is a first/second-order approximation (delta + gamma convexity),
    not a full Black-Scholes repricing — good enough for quick live decisions,
    not for precise expiry-day payoff math.
    """
    if delta is None or theta is None:
        print("\n(Skipping projection table — delta/theta not available from chain.)")
        return

    gamma = gamma or 0.0
    is_call = option_type.upper() == "CE"
    sign = 1 if is_call else -1  # PE gains value when stock falls

    print(f"\n--- Premium Projection ({days_forward} day(s) forward) ---")
    print(f"{'Stock Move':>12} | {'New Spot':>10} | {'Est. Premium':>13} | {'Change':>8}")

    moves = [-20, -15, -10, -5, 0, 5, 10, 15, 20]
    for move in moves:
        signed_move = move * sign
        delta_effect = delta * signed_move
        gamma_effect = 0.5 * gamma * (signed_move ** 2)
        theta_effect = theta * days_forward  # theta is already negative in Dhan's data

        new_premium = ltp + delta_effect + gamma_effect + theta_effect
        new_premium = max(new_premium, 0.0)  # premium can't go negative
        change = new_premium - ltp

        new_spot = spot + move
        arrow = "+" if move >= 0 else ""
        print(f"{arrow}{move:>10} | {new_spot:>10.1f} | {new_premium:>13.2f} | "
              f"{'+' if change >= 0 else ''}{change:>7.2f}")

    print("\nNote: this is a delta+gamma approximation, not exact Black-Scholes.")
    print("Actual premium also moves with IV changes, which this doesn't model.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dhan option Greeks/breakeven checker")
    parser.add_argument("symbol", help="e.g. BHEL, NIFTY")
    parser.add_argument("strike", type=float, help="e.g. 450")
    parser.add_argument("option_type", choices=["CE", "PE", "ce", "pe"])
    parser.add_argument("--expiry", default=None, help="YYYY-MM-DD, defaults to nearest expiry")
    parser.add_argument("--days", type=int, default=0, help="Days forward to project theta decay (default 0 = today)")
    args = parser.parse_args()

    try:
        analyze(args.symbol, args.strike, args.option_type, args.expiry, args.days)
    except Exception as e:
        import traceback
        print(f"\n[UNEXPECTED ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()