"""
option_leg.py — Additive ATM option leg for ORB breakout entries.

On a confirmed breakout entry (equity), this places ONE lot of the
nearest-MONTHLY ATM option (CE on a long breakout, PE on a breakdown)
IN ADDITION to the equity position. The equity path is never modified.

Design guarantees
-----------------
* NEVER raises into the engine. Every public method is wrapped so any
  failure here can never block, delay, or crash the equity trade.
* Paper / Live agnostic. Routes through the same Execution gateway the
  equity path uses, so PAPER stays PAPER and LIVE stays LIVE.
* Contracts are resolved from the Dhan scrip master
  (data/api-scrip-master.csv). NSE OPTSTK rows carry the option
  security_id, lot size, expiry, strike and CE/PE type.
* The option premium (LTP) is read LIVE from the Dhan option chain.
  If the premium cannot be fetched, the leg is SKIPPED — we never
  fabricate a fill price.
* Exit is mirrored to the parent equity: when the equity position
  closes, the linked option leg is closed too. A hard time-stop is a
  safety net for anything still open late in the session.

This module is intentionally standalone and imports nothing from the
engine, brain, or risk layers, so it cannot create import cycles.
"""

import os
import re
import csv
import time
from datetime import datetime, date

import requests

try:
    from config import (
        ENABLE_OPTION_LEG,
        OPTION_LOTS,
        OPTION_EXPIRY_PREF,
        OPTION_EXIT_WITH_EQUITY,
        OPTION_TIME_STOP,
        SCRIP_MASTER_PATH,
        OPTION_INDEPENDENT_EXIT,
        OPTION_INITIAL_STOP_PCT,
        OPTION_TRAIL_ACTIVATE_PCT,
        OPTION_TRAIL_GIVEBACK_PCT,
        OPTION_TARGET_PCT,
        OPTION_POLL_SECONDS,
    )
except Exception:  # pragma: no cover - defensive defaults if config missing keys
    ENABLE_OPTION_LEG = True
    OPTION_LOTS = 1
    OPTION_EXPIRY_PREF = "MONTHLY"
    OPTION_EXIT_WITH_EQUITY = True
    OPTION_TIME_STOP = "15:10"
    SCRIP_MASTER_PATH = "data/api-scrip-master.csv"
    OPTION_INDEPENDENT_EXIT = True
    OPTION_INITIAL_STOP_PCT = 25.0
    OPTION_TRAIL_ACTIVATE_PCT = 20.0
    OPTION_TRAIL_GIVEBACK_PCT = 15.0
    OPTION_TARGET_PCT = 0.0
    OPTION_POLL_SECONDS = 5

# Best-effort .env load so DHAN_* creds are available for the chain call
try:
    from dotenv import load_dotenv
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(_root, ".env"))
except Exception:
    pass

BASE_URL = "https://api.dhan.co/v2"
UNDERLYING_SEG = "NSE_EQ"
LEG_LOG_FILE = "option_legs_log.csv"

# Strip the "-<Mon><Year>-<strike>-<CE|PE>" suffix to recover the underlying
# root. Written this way so hyphenated names (BAJAJ-AUTO, M&M) survive.
_SUFFIX_RE = re.compile(r"-[A-Za-z]{3}\d{4}-\d+(?:\.\d+)?-(?:CE|PE)$", re.IGNORECASE)


class OptionContract:
    __slots__ = (
        "security_id", "trading_symbol", "custom_symbol", "lot_size",
        "expiry_date", "expiry_flag", "strike", "option_type", "underlying",
    )

    def __init__(self, security_id, trading_symbol, custom_symbol, lot_size,
                 expiry_date, expiry_flag, strike, option_type, underlying):
        self.security_id = security_id
        self.trading_symbol = trading_symbol
        self.custom_symbol = custom_symbol
        self.lot_size = lot_size
        self.expiry_date = expiry_date        # datetime.date
        self.expiry_flag = expiry_flag        # "M" = monthly, "W" = weekly
        self.strike = strike                  # float
        self.option_type = option_type        # "CE" / "PE"
        self.underlying = underlying          # e.g. "ABB"


class OptionLeg:

    def __init__(self, execution, telegram=None):
        self.execution = execution
        self.telegram = telegram
        # parent_security_id -> open leg dict
        self.open_legs = {}
        # underlying(str) -> list[OptionContract]
        self._by_underlying = {}
        self._loaded = False
        try:
            self._load_contracts()
        except Exception as e:
            print(f"[OPTION_LEG] Contract master load failed (leg disabled): {e}")

    # ------------------------------------------------------------------
    # Contract master
    # ------------------------------------------------------------------

    def _load_contracts(self):
        path = SCRIP_MASTER_PATH
        if not os.path.exists(path):
            print(f"[OPTION_LEG] Scrip master not found at {path} — leg disabled.")
            return

        count = 0
        with open(path, "r", newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                # Guard against short/blank lines
                if len(row) < 14:
                    continue
                exch = row[0]
                instrument = row[3]
                if exch != "NSE" or instrument != "OPTSTK":
                    continue
                try:
                    security_id = str(row[2]).strip()
                    trading_symbol = row[5].strip()
                    lot_size = int(float(row[6]))
                    custom_symbol = row[7].strip()
                    expiry_raw = row[8].strip()          # "2026-07-28 14:30:00"
                    strike = float(row[9])
                    option_type = row[10].strip().upper()
                    expiry_flag = row[12].strip().upper()
                except (ValueError, IndexError):
                    continue

                if option_type not in ("CE", "PE"):
                    continue

                try:
                    expiry_date = datetime.strptime(
                        expiry_raw.split(" ")[0], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    continue

                underlying = _SUFFIX_RE.sub("", trading_symbol).upper()

                contract = OptionContract(
                    security_id, trading_symbol, custom_symbol, lot_size,
                    expiry_date, expiry_flag, strike, option_type, underlying,
                )
                self._by_underlying.setdefault(underlying, []).append(contract)
                count += 1

        self._loaded = count > 0
        print(f"[OPTION_LEG] Loaded {count} NSE option contracts "
              f"across {len(self._by_underlying)} underlyings.")

    # ------------------------------------------------------------------
    # Contract resolution
    # ------------------------------------------------------------------

    def _nearest_expiry(self, underlying, today, monthly_only=True):
        contracts = self._by_underlying.get(underlying, [])
        expiries = {
            c.expiry_date for c in contracts
            if c.expiry_date >= today and (not monthly_only or c.expiry_flag == "M")
        }
        return min(expiries) if expiries else None

    def resolve_atm(self, symbol, direction, spot, today=None):
        """Return the nearest-monthly ATM OptionContract, or None."""
        today = today or date.today()
        underlying = str(symbol).strip().upper()
        opt_type = self._direction_to_type(direction)

        monthly_only = str(OPTION_EXPIRY_PREF).upper() == "MONTHLY"
        expiry = self._nearest_expiry(underlying, today, monthly_only=monthly_only)
        if expiry is None:
            # Fall back to any nearest expiry if no monthly qualifies
            expiry = self._nearest_expiry(underlying, today, monthly_only=False)
        if expiry is None:
            return None

        candidates = [
            c for c in self._by_underlying.get(underlying, [])
            if c.option_type == opt_type and c.expiry_date == expiry
        ]
        if not candidates:
            return None

        # ATM = listed strike closest to spot
        return min(candidates, key=lambda c: abs(c.strike - spot))

    @staticmethod
    def _direction_to_type(direction):
        d = str(direction).strip().upper()
        if d in ("PE", "SHORT", "SELL", "PUT", "BREAKDOWN"):
            return "PE"
        return "CE"

    # ------------------------------------------------------------------
    # Live premium (Dhan option chain)
    # ------------------------------------------------------------------

    def _headers(self):
        cid = os.environ.get("DHAN_CLIENT_ID")
        tok = os.environ.get("DHAN_ACCESS_TOKEN")
        if not cid or not tok:
            return None
        return {
            "Content-Type": "application/json",
            "access-token": tok,
            "client-id": cid,
        }

    def _fetch_leg_data(self, parent_security_id, expiry_date, strike, opt_type):
        """
        Best-effort snapshot of the ATM leg from the live option chain:
        {ltp, delta, theta, gamma, vega, iv}. Returns None on any failure.
        The premium (ltp) already embeds all Greeks, which is why premium-based
        management is the correct, all-in-one exit signal; the Greeks themselves
        are captured for context, alerts and logging.
        """
        headers = self._headers()
        if headers is None:
            print("[OPTION_LEG] DHAN creds not set — cannot price option, skipping.")
            return None
        try:
            resp = requests.post(
                f"{BASE_URL}/optionchain",
                headers=headers,
                json={
                    "UnderlyingScrip": int(parent_security_id),
                    "UnderlyingSeg": UNDERLYING_SEG,
                    "Expiry": expiry_date.strftime("%Y-%m-%d"),
                },
                timeout=10,
            )
            resp.raise_for_status()
            oc = resp.json().get("data", {}).get("oc", {})
            leg = oc.get(f"{strike:.6f}", {}).get(opt_type.lower())
            if not leg:
                return None
            ltp = leg.get("last_price")
            if not ltp:
                return None
            greeks = leg.get("greeks", {}) or {}
            return {
                "ltp": float(ltp),
                "delta": greeks.get("delta"),
                "theta": greeks.get("theta"),
                "gamma": greeks.get("gamma"),
                "vega": greeks.get("vega"),
                "iv": leg.get("implied_volatility"),
            }
        except Exception as e:
            print(f"[OPTION_LEG] Chain fetch failed: {e}")
            return None

    def _fetch_premium(self, parent_security_id, expiry_date, strike, opt_type):
        """Thin wrapper: just the premium (LTP), or None."""
        data = self._fetch_leg_data(parent_security_id, expiry_date, strike, opt_type)
        return data["ltp"] if data else None

    @staticmethod
    def _greek_line(g):
        if not g:
            return "Greeks : n/a"
        def fmt(v):
            return f"{v:.3f}" if isinstance(v, (int, float)) else "n/a"
        iv = g.get("iv")
        iv_s = f"{iv:.1f}%" if isinstance(iv, (int, float)) else "n/a"
        return (f"Greeks : Δ {fmt(g.get('delta'))}  "
                f"Θ {fmt(g.get('theta'))}  "
                f"Γ {fmt(g.get('gamma'))}  "
                f"vega {fmt(g.get('vega'))}  IV {iv_s}")

    # ------------------------------------------------------------------
    # Entry
    # ------------------------------------------------------------------

    def try_enter(self, symbol, direction, underlying_ltp, entry_time,
                  parent_security_id):
        """Place 1 lot ATM monthly option alongside the equity. Never raises."""
        try:
            if not ENABLE_OPTION_LEG or not self._loaded:
                return None
            if parent_security_id in self.open_legs:
                return None  # already have a leg for this parent

            contract = self.resolve_atm(symbol, direction, underlying_ltp)
            if contract is None:
                print(f"[OPTION_LEG] No ATM monthly contract for {symbol} — skipped.")
                return None

            data = self._fetch_leg_data(
                parent_security_id, contract.expiry_date,
                contract.strike, contract.option_type,
            )
            premium = data["ltp"] if data else None
            if premium is None or premium <= 0:
                print(f"[OPTION_LEG] No live premium for "
                      f"{contract.trading_symbol} — leg skipped (no fabricated fill).")
                return None

            lots = max(1, int(OPTION_LOTS))
            qty = contract.lot_size * lots

            result = self.execution.buy(
                contract.security_id,
                contract.trading_symbol,
                premium,
                qty,
                segment="NSE_FNO",      # route to the F&O segment, not cash
            )
            if not result or not result.get("success"):
                print(f"[OPTION_LEG] Execution rejected leg for {contract.trading_symbol}.")
                return None

            greeks = {
                "delta": data.get("delta"), "theta": data.get("theta"),
                "gamma": data.get("gamma"), "vega": data.get("vega"),
                "iv": data.get("iv"),
            }
            days_to_expiry = (contract.expiry_date - date.today()).days

            leg = {
                "parent_security_id": parent_security_id,
                "underlying": symbol,
                "option_security_id": contract.security_id,
                "trading_symbol": contract.trading_symbol,
                "option_type": contract.option_type,
                "strike": contract.strike,
                "expiry": contract.expiry_date.strftime("%Y-%m-%d"),
                "days_to_expiry": days_to_expiry,
                "lot_size": contract.lot_size,
                "lots": lots,
                "qty": qty,
                "entry_premium": premium,
                "peak_premium": premium,          # ratchet reference (only moves up)
                "current_premium": premium,
                "stop_level": round(premium * (1 - OPTION_INITIAL_STOP_PCT / 100), 2),
                "trail_armed": False,
                "entry_greeks": greeks,
                "entry_time": entry_time,
                "entry_date": datetime.now().strftime("%Y-%m-%d"),
                "underlying_entry": underlying_ltp,
                "_last_poll": time.monotonic(),
            }
            self.open_legs[parent_security_id] = leg
            self._log(leg, event="ENTRY")

            print(f"[OPTION_LEG] BUY {contract.trading_symbol} "
                  f"(ATM {contract.option_type} {contract.strike:g}) "
                  f"{qty} @ Rs.{premium:.2f} | init stop Rs.{leg['stop_level']:.2f} "
                  f"| {days_to_expiry}d to expiry")

            self._notify(
                f"\U0001F535 OPTION LEG (ATM {contract.option_type})\n\n"
                f"Underlying : {symbol} @ Rs.{underlying_ltp:.2f}\n"
                f"Contract : {contract.custom_symbol}\n"
                f"Strike : {contract.strike:g} ({contract.option_type})\n"
                f"Expiry : {leg['expiry']} ({days_to_expiry}d)\n"
                f"Lots : {lots} (qty {qty})\n"
                f"Premium : Rs.{premium:.2f}\n"
                f"Init stop : Rs.{leg['stop_level']:.2f} (-{OPTION_INITIAL_STOP_PCT:g}%)\n"
                f"{self._greek_line(greeks)}\n"
                f"Time : {entry_time}"
            )
            return leg
        except Exception as e:
            print(f"[OPTION_LEG] try_enter failed safely (equity unaffected): {e}")
            return None

    # ------------------------------------------------------------------
    # Exit
    # ------------------------------------------------------------------

    def exit_for_parent(self, parent_security_id, reason="EQUITY_EXIT"):
        """Close the linked option leg when its equity position exits."""
        try:
            if not OPTION_EXIT_WITH_EQUITY:
                return None
            leg = self.open_legs.get(parent_security_id)
            if leg is None:
                return None
            return self._close(leg, reason)
        except Exception as e:
            print(f"[OPTION_LEG] exit_for_parent failed safely: {e}")
            return None

    def manage(self, current_hhmmss):
        """
        Per-tick management of every open option leg. Never raises.

        Order of checks per leg:
          1. Time stop (no network) — flatten past OPTION_TIME_STOP so no
             position is ever carried overnight (kills multi-day theta/gap risk).
          2. Independent premium management (throttled poll):
             - refresh live premium + Greeks
             - ratchet the peak premium UP (never down)
             - arm the trailing stop once +OPTION_TRAIL_ACTIVATE_PCT in profit
             - trailing stop = peak * (1 - giveback%), and it NEVER widens
             - hard floor = entry * (1 - initial_stop%)
             - optional hard target
             - exit when premium <= effective stop, or >= target
        """
        try:
            if not self.open_legs:
                return

            past_time = str(current_hhmmss) >= (str(OPTION_TIME_STOP) + ":00")

            for parent_id in list(self.open_legs.keys()):
                leg = self.open_legs.get(parent_id)
                if leg is None:
                    continue

                # 1) Same-day time stop
                if past_time:
                    self._close(leg, "TIME_STOP")
                    continue

                if not OPTION_INDEPENDENT_EXIT:
                    continue

                # 2) Throttled premium/greeks poll (rate-limit friendly)
                now = time.monotonic()
                if now - leg.get("_last_poll", 0.0) < max(1, int(OPTION_POLL_SECONDS)):
                    continue
                leg["_last_poll"] = now

                data = self._fetch_leg_data(
                    parent_id,
                    datetime.strptime(leg["expiry"], "%Y-%m-%d").date(),
                    leg["strike"],
                    leg["option_type"],
                )
                if not data or not data.get("ltp"):
                    continue

                price = data["ltp"]
                entry = leg["entry_premium"]
                leg["current_premium"] = price
                leg["live_greeks"] = {
                    "delta": data.get("delta"), "theta": data.get("theta"),
                    "gamma": data.get("gamma"), "vega": data.get("vega"),
                    "iv": data.get("iv"),
                }

                # Ratchet the peak up only
                peak = max(leg.get("peak_premium", entry), price)
                leg["peak_premium"] = peak

                # Hard floor stop
                hard = entry * (1 - OPTION_INITIAL_STOP_PCT / 100)
                stop = hard

                # Arm + apply trailing stop once far enough in profit
                if peak >= entry * (1 + OPTION_TRAIL_ACTIVATE_PCT / 100):
                    leg["trail_armed"] = True
                if leg.get("trail_armed"):
                    trail = peak * (1 - OPTION_TRAIL_GIVEBACK_PCT / 100)
                    stop = max(stop, trail)   # never widens: only ratchets up

                leg["stop_level"] = round(stop, 2)

                # Hard target (optional)
                if OPTION_TARGET_PCT and price >= entry * (1 + OPTION_TARGET_PCT / 100):
                    self._close(leg, "TARGET", known_price=price)
                    continue

                # Stop hit
                if price <= stop:
                    reason = "TRAIL_STOP" if leg.get("trail_armed") and stop > hard \
                        else "HARD_STOP"
                    self._close(leg, reason, known_price=price)
                    continue
        except Exception as e:
            print(f"[OPTION_LEG] manage failed safely: {e}")

    def time_stop_check(self, current_hhmmss):
        """Backwards-compatible alias — full management lives in manage()."""
        self.manage(current_hhmmss)

    def _close(self, leg, reason, known_price=None):
        parent_id = leg["parent_security_id"]
        if known_price and known_price > 0:
            exit_premium = known_price
        else:
            exit_premium = self._fetch_premium(
                parent_id,
                datetime.strptime(leg["expiry"], "%Y-%m-%d").date(),
                leg["strike"],
                leg["option_type"],
            )
        # If we cannot fetch an exit price, fall back to entry premium so the
        # order still squares off; PnL for that leg is then treated as flat.
        price = exit_premium if (exit_premium and exit_premium > 0) else leg["entry_premium"]

        result = self.execution.sell(
            leg["option_security_id"],
            leg["trading_symbol"],
            price,
            leg["qty"],
            segment="NSE_FNO",          # route to the F&O segment, not cash
        )
        if not result or not result.get("success"):
            print(f"[OPTION_LEG] Exit execution rejected for {leg['trading_symbol']}.")
            return None

        entry = leg["entry_premium"]
        pnl = round((price - entry) * leg["qty"], 2)
        pnl_pct = round((price - entry) / entry * 100, 1) if entry else 0.0
        peak = leg.get("peak_premium", entry)
        leg_out = dict(leg)
        leg_out.update({
            "exit_premium": price,
            "exit_reason": reason,
            "exit_time": datetime.now().strftime("%H:%M:%S"),
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        })
        self._log(leg_out, event="EXIT")
        self.open_legs.pop(parent_id, None)

        print(f"[OPTION_LEG] SELL {leg['trading_symbol']} @ Rs.{price:.2f} "
              f"| {reason} | PnL Rs.{pnl:.2f} ({pnl_pct:+.1f}%) "
              f"| peak Rs.{peak:.2f} stop Rs.{leg.get('stop_level', 0):.2f}")
        self._notify(
            f"\U0001F534 OPTION LEG CLOSED\n\n"
            f"Contract : {leg['trading_symbol']}\n"
            f"Entry : Rs.{entry:.2f}  Peak : Rs.{peak:.2f}\n"
            f"Exit : Rs.{price:.2f} ({reason})\n"
            f"PnL : Rs.{pnl:.2f} ({pnl_pct:+.1f}%)\n"
            f"{self._greek_line(leg.get('live_greeks') or leg.get('entry_greeks'))}"
        )
        return leg_out

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def has_leg(self, parent_security_id):
        return parent_security_id in self.open_legs

    def _notify(self, message):
        try:
            if self.telegram is not None:
                self.telegram.send(message)
        except Exception:
            pass

    def _log(self, leg, event):
        try:
            new_file = not os.path.exists(LEG_LOG_FILE)
            fields = [
                "event", "underlying", "trading_symbol", "option_type", "strike",
                "expiry", "days_to_expiry", "lots", "qty",
                "entry_premium", "peak_premium", "stop_level", "exit_premium",
                "pnl", "pnl_pct", "entry_time", "exit_time", "exit_reason",
                "entry_delta", "entry_theta", "entry_gamma", "entry_vega", "entry_iv",
                "logged_at",
            ]
            row = {k: leg.get(k, "") for k in fields}
            g = leg.get("entry_greeks") or {}
            row["entry_delta"] = g.get("delta", "")
            row["entry_theta"] = g.get("theta", "")
            row["entry_gamma"] = g.get("gamma", "")
            row["entry_vega"] = g.get("vega", "")
            row["entry_iv"] = g.get("iv", "")
            row["event"] = event
            row["logged_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(LEG_LOG_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                if new_file:
                    writer.writeheader()
                writer.writerow(row)
        except Exception as e:
            print(f"[OPTION_LEG] Log write failed (non-fatal): {e}")
