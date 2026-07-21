"""
==========================================================
Dashboard Bridge
==========================================================

dashboard.py runs as its OWN separate process (see its
docstring: "Run (alongside or after the bot): py
dashboard.py") -- it cannot call engine methods directly.
Every other cross-process channel in this codebase is
file-based (open_positions.json, trade_log_v2.csv,
market_recorder.db); this extends that same pattern to make
the dashboard interactive:

    dashboard_commands.json  -- dashboard WRITES requests here
                                 (Sell / Check Now / Schedule
                                 Check); engine reads + clears.
    dashboard_state.json     -- engine WRITES both watchlists,
                                 pending schedules, and recent
                                 command responses; dashboard
                                 reads.

Safety, by construction:
  • Sell never touches a broker or moves real money -- it only
    sets the same one-shot per-symbol exit flag TradeController
    already exposes, which the engine's own existing exit
    pipeline (core/engine.py) turns into a normal EXIT_MANUAL
    close at the live price. In PAPER mode (the only mode this
    bot currently runs in) that's a simulated close, same as
    every other exit reason already logged.
  • Check Now / Schedule Check only ever call
    TradeSelectionEngine.snapshot_opinion() -- a read-only
    method that can't place an order or touch the opportunity
    pool (see its docstring).

Author : H&M ORB AUTO TRADER
==========================================================
"""

import json
import os
import uuid
from datetime import datetime


class DashboardBridge:

    COMMANDS_FILE = "dashboard_commands.json"
    STATE_FILE = "dashboard_state.json"

    # This is a live control surface, not a permanent log --
    # permanent decision history already lives in market_
    # memory's trade_decisions table (see engine.why_report).
    MAX_RESPONSES = 30

    def __init__(self, engine):
        self.engine = engine
        self.responses = []   # dicts, newest first
        self.scheduled = []   # pending {"id","symbol","at","created_at"}

    # --------------------------------------------------
    # Commands : dashboard -> engine
    # --------------------------------------------------

    def _read_commands(self):
        if not os.path.exists(self.COMMANDS_FILE):
            return []
        try:
            with open(
                self.COMMANDS_FILE, "r", encoding="utf-8"
            ) as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _clear_commands(self):
        try:
            with open(
                self.COMMANDS_FILE, "w", encoding="utf-8"
            ) as f:
                json.dump([], f)
        except OSError as e:
            print(f"[DASHBOARD BRIDGE] clear commands: {e}")

    # --------------------------------------------------

    def _add_response(self, resp):
        resp.setdefault("id", str(uuid.uuid4())[:8])
        resp["completed_at"] = datetime.now().isoformat()
        self.responses.insert(0, resp)
        self.responses = self.responses[: self.MAX_RESPONSES]

    # --------------------------------------------------

    def process_commands(self):
        """
        Call once per throttled tick. Executes any pending
        dashboard commands, then clears the command file so
        each one is only ever actioned once.
        """
        commands = self._read_commands()
        if not commands:
            return

        for cmd in commands:
            try:
                self._execute(cmd)
            except Exception as e:
                self._add_response({
                    "type": cmd.get("type", "?"),
                    "symbol": cmd.get("symbol", ""),
                    "error": str(e),
                })

        self._clear_commands()

    # --------------------------------------------------

    def _execute(self, cmd):
        ctype = str(cmd.get("type", "")).upper()

        if ctype == "SELL":
            self._execute_sell(cmd)
        elif ctype == "CHECK_NOW":
            self._execute_check(cmd)
        elif ctype == "SCHEDULE_CHECK":
            self._execute_schedule(cmd)
        else:
            self._add_response({
                "type": ctype,
                "error": f"Unknown command type: {ctype}",
            })

    # --------------------------------------------------

    def _execute_sell(self, cmd):
        security_id = str(cmd.get("security_id", "")).strip()
        symbol = cmd.get("symbol", "")

        if not security_id or security_id not in self.engine.trades:
            self._add_response({
                "type": "SELL",
                "symbol": symbol,
                "security_id": security_id,
                "error": (
                    "No open position found for that security_id "
                    "(it may have already closed)."
                ),
            })
            return

        self.engine.trade_controller.request_exit_symbol(
            security_id
        )
        self._add_response({
            "type": "SELL",
            "symbol": symbol,
            "security_id": security_id,
            "message": (
                f"Sell requested for {symbol} -- will close on "
                f"the next tick at the live market price."
            ),
        })

    # --------------------------------------------------

    def _execute_check(self, cmd):
        symbol = str(cmd.get("symbol", "")).upper().strip()
        if not symbol:
            self._add_response({
                "type": "CHECK_NOW",
                "error": "No symbol given.",
            })
            return

        snapshot = (
            self.engine.trade_selection_engine
            .snapshot_opinion(symbol)
        )
        history = self._safe_history(symbol)
        self._add_response({
            "type": "CHECK_NOW",
            "symbol": symbol,
            "snapshot": snapshot,
            "history": history,
        })

    # --------------------------------------------------

    def _safe_history(self, symbol):
        """
        Recent decision history for the symbol -- the same
        permanent record /why SYMBOL reads on Telegram.
        Bundled onto every check response (on-demand or
        scheduled) so one lookup covers both "what does the
        brain think right now" and "what has it actually
        decided about this stock before."
        """
        try:
            return self.engine.why_report(symbol)
        except Exception as e:
            return f"(history unavailable: {e})"

    # --------------------------------------------------

    def _execute_schedule(self, cmd):
        symbol = str(cmd.get("symbol", "")).upper().strip()
        at = str(cmd.get("at", "")).strip()  # "HH:MM"

        if not symbol or not at:
            self._add_response({
                "type": "SCHEDULE_CHECK",
                "error": "Need both a symbol and a time (HH:MM).",
            })
            return

        try:
            datetime.strptime(at, "%H:%M")
        except ValueError:
            self._add_response({
                "type": "SCHEDULE_CHECK",
                "symbol": symbol,
                "error": f"'{at}' isn't a valid HH:MM time.",
            })
            return

        self.scheduled.append({
            "id": str(uuid.uuid4())[:8],
            "symbol": symbol,
            "at": at,
            "created_at": datetime.now().isoformat(),
        })
        self._add_response({
            "type": "SCHEDULE_CHECK",
            "symbol": symbol,
            "message": f"Scheduled: will check {symbol} at {at}.",
        })

    # --------------------------------------------------
    # Scheduler
    # --------------------------------------------------

    def run_due_schedules(self):
        """
        Call once per throttled tick. Fires any scheduled
        check whose target time has arrived. Runs on the same
        few-second throttle as everything else here, so a
        target minute is never missed even though this checks
        HH:MM (minute) resolution, not exact seconds.
        """
        if not self.scheduled:
            return

        now_hm = datetime.now().strftime("%H:%M")
        due = [s for s in self.scheduled if s["at"] <= now_hm]
        if not due:
            return

        for s in due:
            try:
                snapshot = (
                    self.engine.trade_selection_engine
                    .snapshot_opinion(s["symbol"])
                )
                self._add_response({
                    "type": "SCHEDULED_CHECK_FIRED",
                    "symbol": s["symbol"],
                    "scheduled_for": s["at"],
                    "snapshot": snapshot,
                    "history": self._safe_history(s["symbol"]),
                })
            except Exception as e:
                self._add_response({
                    "type": "SCHEDULED_CHECK_FIRED",
                    "symbol": s["symbol"],
                    "scheduled_for": s["at"],
                    "error": str(e),
                })

        self.scheduled = [
            s for s in self.scheduled if s["at"] > now_hm
        ]

    # --------------------------------------------------
    # State : engine -> dashboard
    # --------------------------------------------------

    def write_state(self):
        try:
            news = []
            nw = getattr(self.engine, "news_watchlist", None)
            if nw is not None:
                news = nw.as_list()

            results = {"watching": [], "announced": []}
            rw = getattr(self.engine, "results_watchlist", None)
            if rw is not None:
                results = rw.as_dict()

            payload = {
                "updated_at": datetime.now().isoformat(),
                "news_watchlist": news,
                "results_watchlist": results,
                "scheduled_pending": list(self.scheduled),
                "responses": list(self.responses),
            }

            with open(
                self.STATE_FILE, "w", encoding="utf-8"
            ) as f:
                json.dump(payload, f, indent=2, default=str)

        except Exception as e:
            print(f"[DASHBOARD BRIDGE] write_state: {e}")
