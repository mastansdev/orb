"""
==========================================================
ORB Auto Trader — Live Dashboard
==========================================================

Local website showing the bot's trading visually:

    • Today's PnL, trades, open/closed positions up top
    • Live PnL curve + a big "digital" current PnL readout
    • Open positions with live MTM (when available) and a
      one-click Sell action per position
    • Today's closed trades
    • All-time stats + PnL-by-hour + trade-quality history,
      moved to the bottom, with a date-range filter

Run (alongside or after the bot):

    py dashboard.py

Then open:  http://localhost:8181

Pure standard library — no new dependencies. Reads the
same files the bot writes; never modifies anything.

Author : H&M ORB AUTO TRADER
==========================================================
"""

import csv
import json
import os
import sqlite3
from datetime import datetime
from http.server import (
    HTTPServer,
    BaseHTTPRequestHandler,
)

PORT = 8181

TRADE_LOG = "trade_log_v2.csv"
RECORDER_DB = "market_recorder.db"
POSITIONS_FILE = "open_positions.json"


# ==========================================================
# Data access (read-only, except the Sell-request writer below)
# ==========================================================

def load_trades():
    if not os.path.exists(TRADE_LOG):
        return []

    trades = []
    try:
        with open(
            TRADE_LOG, newline="", encoding="utf-8"
        ) as f:
            for row in csv.DictReader(f):
                if "SMOKETEST" in (
                    row.get("Sector", "") or ""
                ):
                    continue
                try:
                    trades.append({
                        "date": row.get("Date", ""),
                        "entry_time": row.get("EntryTime", ""),
                        "exit_time": row.get("ExitTime", ""),
                        "symbol": row.get("Symbol", ""),
                        "sector": row.get("Sector", "")
                        or "UNKNOWN",
                        "qty": int(float(row.get("Qty", 0))),
                        "entry": float(
                            row.get("EntryPrice", 0)
                        ),
                        "exit": float(
                            row.get("ExitPrice", 0)
                        ),
                        "pnl": float(row.get("PnL", 0)),
                        "reason": row.get("ExitReason", ""),
                        # Rounded to the nearest whole number --
                        # 96.33333333333334 -> 96, not a long
                        # repeating decimal on screen.
                        "conviction": round(
                            float(row.get("Conviction", 0) or 0)
                        ),
                        "holding_seconds": int(
                            float(
                                row.get("HoldingSeconds", 0)
                                or 0
                            )
                        ),
                    })
                except (ValueError, TypeError):
                    continue
    except Exception:
        pass

    return trades


# Live-price field name candidates, checked in order. We don't
# actually know which (if any) key engine.py writes into
# open_positions.json for the current price -- checking several
# plausible names rather than guessing at just one.
_LIVE_PRICE_KEYS = ("ltp", "current_price", "live_price", "last_price")


def load_positions():
    if not os.path.exists(POSITIONS_FILE):
        return []

    try:
        with open(
            POSITIONS_FILE, encoding="utf-8"
        ) as f:
            data = json.load(f) or {}

        positions = []
        for security_id, t in data.items():
            entry = t.get("entry", 0) or 0
            qty = t.get("qty", 0) or 0

            ltp = None
            for key in _LIVE_PRICE_KEYS:
                if t.get(key):
                    ltp = t.get(key)
                    break

            live_pnl = (
                round((ltp - entry) * qty, 2)
                if ltp is not None else None
            )

            positions.append({
                "security_id": security_id,
                "symbol": t.get("symbol", ""),
                "entry": entry,
                "stop_loss": t.get("trail_sl", 0)
                or t.get("stop_loss", 0),
                "target": t.get("target", 0),
                "qty": qty,
                "entry_time": t.get("entry_time", ""),
                "sector": t.get("sector", ""),
                "conviction": round(
                    float(t.get("conviction", 0) or 0)
                ),
                "stage": t.get("stage", ""),
                "ltp": ltp,
                "live_pnl": live_pnl,
            })

        return positions
    except Exception:
        return []


def load_pnl_series(limit=3000):
    """
    Latest session's PnL curve from recorder snapshots.
    Downsampled for the chart.
    """
    if not os.path.exists(RECORDER_DB):
        return []

    try:
        db = sqlite3.connect(RECORDER_DB)

        session = db.execute(
            "SELECT session_id FROM sessions "
            "ORDER BY rowid DESC LIMIT 1"
        ).fetchone()

        if not session:
            db.close()
            return []

        rows = db.execute(
            """
            SELECT timestamp, net_pnl, floating_mtm,
                   realized_pnl, open_positions
            FROM portfolio_snapshots
            WHERE session_id = ?
            ORDER BY id
            """,
            (session[0],),
        ).fetchall()
        db.close()

        # Downsample to ~limit points
        step = max(1, len(rows) // limit)
        rows = rows[::step]

        return [
            {
                "t": r[0],
                "net": r[1],
                "floating": r[2],
                "realized": r[3],
                "positions": r[4],
            }
            for r in rows
        ]
    except Exception:
        return []


def hour_analysis(trades):
    buckets = {}

    for t in trades:
        hour = (
            t["entry_time"][:2] + ":00"
            if t["entry_time"] else "?"
        )
        b = buckets.setdefault(
            hour, {"trades": 0, "wins": 0, "pnl": 0.0}
        )
        b["trades"] += 1
        if t["pnl"] > 0:
            b["wins"] += 1
        b["pnl"] += t["pnl"]

    return [
        {
            "hour": hour,
            "trades": b["trades"],
            "win_rate": round(
                b["wins"] / b["trades"] * 100, 1
            ),
            "pnl": round(b["pnl"], 2),
        }
        for hour, b in sorted(buckets.items())
    ]


def summary(trades):
    if not trades:
        return {"trades": 0}

    wins = [t for t in trades if t["pnl"] > 0]
    gross = sum(t["pnl"] for t in trades)

    today = datetime.now().strftime("%Y-%m-%d")
    today_trades = [
        t for t in trades if t["date"] == today
    ]

    return {
        "trades": len(trades),
        "win_rate": round(
            len(wins) / len(trades) * 100, 1
        ),
        "gross_pnl": round(gross, 2),
        "avg_per_trade": round(gross / len(trades), 2),
        "today_trades": len(today_trades),
        "today_pnl": round(
            sum(t["pnl"] for t in today_trades), 2
        ),
        # Same count as today_trades -- a trade "closed today"
        # IS a closed position closed today. Exposed under its
        # own name so the dashboard can label/position it
        # separately per the requested layout.
        "today_closed_positions": len(today_trades),
    }


def summary_range(trades, from_date, to_date):
    """
    All-time-style stats, but scoped to a [from_date, to_date]
    inclusive range (both "YYYY-MM-DD" strings). Empty/missing
    bounds mean "no limit" on that side.
    """
    filtered = [
        t for t in trades
        if (not from_date or t["date"] >= from_date)
        and (not to_date or t["date"] <= to_date)
    ]

    if not filtered:
        return {"trades": 0, "win_rate": 0, "gross_pnl": 0}

    wins = [t for t in filtered if t["pnl"] > 0]
    gross = sum(t["pnl"] for t in filtered)

    return {
        "trades": len(filtered),
        "win_rate": round(len(wins) / len(filtered) * 100, 1),
        "gross_pnl": round(gross, 2),
    }


# ==========================================================
# HTML (single page, Chart.js from CDN)
# ==========================================================

PAGE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ORB Auto Trader — Live</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root { --bg:#0d1117; --card:#161b22; --border:#30363d;
          --text:#e6edf3; --dim:#8b949e;
          --green:#3fb950; --red:#f85149; --blue:#58a6ff; }
  * { box-sizing:border-box; margin:0; }
  body { background:var(--bg); color:var(--text);
         font-family:-apple-system,Segoe UI,Roboto,sans-serif;
         padding:20px; }
  h1 { font-size:20px; letter-spacing:.5px; }
  .sub { color:var(--dim); font-size:12px; margin:4px 0 16px; }
  .grid { display:grid; gap:14px; }
  .cards { grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); }
  .card { background:var(--card); border:1px solid var(--border);
          border-radius:8px; padding:14px; }
  .kpi .v { font-size:22px; font-weight:600; margin-top:4px; }
  .kpi .l { color:var(--dim); font-size:11px; text-transform:uppercase; }
  .pos { color:var(--green); } .neg { color:var(--red); }
  .two { grid-template-columns:2fr 1fr; }
  @media (max-width:900px){ .two{grid-template-columns:1fr;} }
  h2 { font-size:13px; color:var(--dim); text-transform:uppercase;
       margin-bottom:10px; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th { color:var(--dim); text-align:left; font-weight:500;
       padding:5px 8px; border-bottom:1px solid var(--border); }
  td { padding:5px 8px; border-bottom:1px solid #21262d; }
  .chart-box { position:relative; height:260px; }
  .chart-box.small { height:200px; }
  .tag { padding:1px 7px; border-radius:10px; font-size:11px; }
  .tag.T { background:#1a7f37; } .tag.S { background:#8e1519; }
  .tag.O { background:#1f6feb; }
  .digital { font-family:"SF Mono",Consolas,monospace;
             font-size:38px; font-weight:700; letter-spacing:1px; }
  .digital-label { color:var(--dim); font-size:11px;
                    text-transform:uppercase; margin-bottom:6px; }
  .section-divider { margin:28px 0 14px; border-top:1px solid var(--border);
                      padding-top:16px; }
  .section-divider h2 { font-size:14px; }
  .daterange { display:flex; gap:8px; align-items:center;
               margin-bottom:12px; font-size:12px; color:var(--dim); }
  .daterange input { background:#0d1117; border:1px solid var(--border);
                      color:var(--text); border-radius:5px; padding:4px 8px;
                      font-size:12px; }
  .daterange button { background:var(--blue); color:#fff; border:none;
                       border-radius:5px; padding:5px 12px; font-size:12px;
                       cursor:pointer; }
</style>
</head>
<body>
<h1>ORB AUTO TRADER — LIVE DASHBOARD</h1>
<div class="sub" id="updated">loading…</div>

<!-- TOP: today-focused KPIs -->
<div class="grid cards" id="kpis-today"></div>

<!-- MIDDLE: live PnL, with a big digital readout -->
<div class="grid two" style="margin-top:14px">
  <div class="card">
    <h2>Live PnL — today's session</h2>
    <div class="digital-label">Current</div>
    <div class="digital pos" id="digitalPnl">₹0</div>
    <div class="chart-box" style="margin-top:10px"><canvas id="pnlChart"></canvas></div>
  </div>
  <div class="card">
    <h2>Open positions</h2>
    <table id="positions"><thead><tr>
      <th>Symbol</th><th>Entry</th><th>Stop</th><th>Target</th>
      <th>Qty</th><th>Time</th><th>Live PnL</th>
    </tr></thead><tbody></tbody></table>
  </div>
</div>

<div class="card" style="margin-top:14px">
  <h2>Trades closed today</h2>
  <table id="trades"><thead><tr>
    <th>Date</th><th>Entry</th><th>Exit</th><th>Symbol</th>
    <th>Sector</th><th>Qty</th><th>In</th><th>Out</th>
    <th>PnL</th><th>Hold</th><th>Exit Reason</th><th>Conviction</th>
  </tr></thead><tbody></tbody></table>
</div>

<!-- BOTTOM: all-time / historical, with date-range filter -->
<div class="section-divider">
  <h2>All-time performance</h2>
  <div class="daterange">
    From <input type="date" id="fromDate"> to
    <input type="date" id="toDate">
    <button onclick="applyRange()">Filter</button>
    <button onclick="clearRange()">All-time</button>
  </div>
</div>
<div class="grid cards" id="kpis-alltime"></div>

<div class="grid two" style="margin-top:14px">
  <div class="card">
    <h2>PnL by entry hour (all history)</h2>
    <div class="chart-box small"><canvas id="hourChart"></canvas></div>
  </div>
  <div class="card">
    <h2>Trade quality — conviction vs PnL</h2>
    <div class="chart-box small"><canvas id="qualityChart"></canvas></div>
  </div>
</div>

<script>
let pnlChart, hourChart, qualityChart;
let latestData = null;

function fmt(n){ return (n>=0?'+':'')+Number(n).toLocaleString('en-IN',
  {maximumFractionDigits:0}); }

function fmtOrDash(n){
  return (n===null || n===undefined) ? '—' : fmt(n);
}

async function applyRange(){
  const from = document.getElementById('fromDate').value;
  const to = document.getElementById('toDate').value;
  const r = await fetch('/api/range?from=' + from + '&to=' + to);
  const rangeSummary = await r.json();
  renderAllTimeKpis(rangeSummary);
}

function clearRange(){
  document.getElementById('fromDate').value = '';
  document.getElementById('toDate').value = '';
  renderAllTimeKpis(latestData.summary);
}

function renderAllTimeKpis(s){
  const kpis = [
    ['All-time Trades', s.trades||0, true],
    ['Win Rate', (s.win_rate||0)+'%', (s.win_rate||0)>=50],
    ['Gross PnL', fmt(s.gross_pnl||0), (s.gross_pnl||0)>=0],
  ];
  document.getElementById('kpis-alltime').innerHTML = kpis.map(k=>
    `<div class="card kpi"><div class="l">${k[0]}</div>
     <div class="v ${k[2]?'pos':'neg'}">${k[1]}</div></div>`).join('');
}

async function refresh(){
  const r = await fetch('/api/all');
  const d = await r.json();
  latestData = d;

  document.getElementById('updated').textContent =
    'updated ' + new Date().toLocaleTimeString() +
    ' — auto-refreshes every 5s';

  // TOP KPIs -- today-focused
  const s = d.summary;
  const todayKpis = [
    ['Today PnL', fmt(s.today_pnl||0), (s.today_pnl||0)>=0],
    ['Today Trades', s.today_trades||0, true],
    ['Open Positions', d.positions.length, true],
    ['Closed Positions', s.today_closed_positions||0, true],
  ];
  document.getElementById('kpis-today').innerHTML = todayKpis.map(k=>
    `<div class="card kpi"><div class="l">${k[0]}</div>
     <div class="v ${k[2]?'pos':'neg'}">${k[1]}</div></div>`).join('');

  // BOTTOM KPIs -- all-time (unless a range filter is active)
  const fromVal = document.getElementById('fromDate').value;
  const toVal = document.getElementById('toDate').value;
  if(!fromVal && !toVal) renderAllTimeKpis(s);

  // Digital PnL readout -- latest point of the live series
  const series = d.pnl_series;
  const latestNet = series.length ? series[series.length-1].net : 0;
  const dig = document.getElementById('digitalPnl');
  dig.textContent = fmt(latestNet);
  dig.className = 'digital ' + (latestNet>=0 ? 'pos':'neg');

  // PnL curve
  const cfgLine = {
    type:'line',
    data:{ labels:series.map(p=>p.t),
      datasets:[{label:'Net PnL', data:series.map(p=>p.net),
        borderColor:'#58a6ff', backgroundColor:'rgba(88,166,255,.08)',
        fill:true, pointRadius:0, borderWidth:1.6, tension:.2}]},
    options:{ responsive:true, maintainAspectRatio:false,
      animation:false, plugins:{legend:{display:false}},
      scales:{ x:{ticks:{color:'#8b949e',maxTicksLimit:10},
                  grid:{color:'#21262d'}},
               y:{ticks:{color:'#8b949e'}, grid:{color:'#21262d'}}}}};
  if(pnlChart){ pnlChart.data=cfgLine.data; pnlChart.update('none'); }
  else pnlChart = new Chart(document.getElementById('pnlChart'), cfgLine);

  // Hour analysis (bottom)
  const h = d.by_hour;
  const cfgBar = { type:'bar',
    data:{ labels:h.map(x=>x.hour),
      datasets:[{label:'PnL', data:h.map(x=>x.pnl),
        backgroundColor:h.map(x=>x.pnl>=0?'#3fb950':'#f85149')}]},
    options:{ responsive:true, maintainAspectRatio:false,
      animation:false, plugins:{legend:{display:false},
        tooltip:{callbacks:{afterLabel:(c)=>{
          const b=h[c.dataIndex];
          return b.trades+' trades, '+b.win_rate+'% wins';}}}},
      scales:{ x:{ticks:{color:'#8b949e'}, grid:{display:false}},
               y:{ticks:{color:'#8b949e'}, grid:{color:'#21262d'}}}}};
  if(hourChart){ hourChart.data=cfgBar.data; hourChart.update('none'); }
  else hourChart = new Chart(document.getElementById('hourChart'), cfgBar);

  // Quality scatter (bottom)
  const t = d.trades;
  const cfgScatter = { type:'scatter',
    data:{ datasets:[{label:'trades',
      data:t.map(x=>({x:x.conviction, y:x.pnl})),
      backgroundColor:t.map(x=>x.pnl>=0?'#3fb950':'#f85149'),
      pointRadius:4}]},
    options:{ responsive:true, maintainAspectRatio:false,
      animation:false, plugins:{legend:{display:false}},
      scales:{ x:{title:{display:true,text:'Conviction',color:'#8b949e'},
                  ticks:{color:'#8b949e'}, grid:{color:'#21262d'}},
               y:{title:{display:true,text:'PnL ₹',color:'#8b949e'},
                  ticks:{color:'#8b949e'}, grid:{color:'#21262d'}}}}};
  if(qualityChart){ qualityChart.data=cfgScatter.data;
    qualityChart.update('none'); }
  else qualityChart = new Chart(
    document.getElementById('qualityChart'), cfgScatter);

  // Open positions table -- Symbol/Entry/Stop/Target/Qty/Time/Live PnL/Sell
  document.querySelector('#positions tbody').innerHTML =
    d.positions.length ? d.positions.map(p=>{
      const pnlCls = (p.live_pnl||0)>=0 ? 'pos':'neg';
      return `<tr><td><b>${p.symbol}</b></td><td>${p.entry}</td>
       <td>${p.stop_loss}</td><td>${p.target}</td><td>${p.qty}</td>
       <td>${p.entry_time}</td>
       <td class="${pnlCls}">${fmtOrDash(p.live_pnl)}</td>
       </tr>`;
    }).join('')
    : '<tr><td colspan="7" style="color:#8b949e">No open positions</td></tr>';

  // Trades table — TODAY's closed trades only.
  const todayTrades = d.trades_today || [];
  document.querySelector('#trades tbody').innerHTML =
    todayTrades.length ? todayTrades.slice(-40).reverse().map(x=>{
      const cls = x.pnl>=0?'pos':'neg';
      const tag = x.reason==='TARGET'?'T':
                  (x.reason==='STOPLOSS'?'S':'O');
      const hold = Math.round(x.holding_seconds/60)+'m';
      return `<tr><td>${x.date}</td><td>${x.entry_time}</td>
        <td>${x.exit_time}</td><td><b>${x.symbol}</b></td>
        <td>${x.sector}</td><td>${x.qty}</td><td>${x.entry}</td>
        <td>${x.exit}</td><td class="${cls}">${fmt(x.pnl)}</td>
        <td>${hold}</td>
        <td><span class="tag ${tag}">${x.reason}</span></td>
        <td>${x.conviction}</td></tr>`;
    }).join('')
    : '<tr><td colspan="12" style="color:#8b949e">No trades closed today yet</td></tr>';
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>"""


# ==========================================================
# Server
# ==========================================================

class Handler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass  # quiet console

    def _send(self, body, content_type):
        data = (
            body.encode("utf-8")
            if isinstance(body, str) else body
        )
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Length", str(len(data))
        )
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/" or self.path.startswith(
            "/index"
        ):
            self._send(PAGE, "text/html; charset=utf-8")

        elif self.path == "/api/all":
            trades = load_trades()
            today = datetime.now().strftime("%Y-%m-%d")
            trades_today = [
                t for t in trades if t["date"] == today
            ]
            payload = {
                "summary": summary(trades),
                "trades": trades,
                "trades_today": trades_today,
                "positions": load_positions(),
                "pnl_series": load_pnl_series(),
                "by_hour": hour_analysis(trades),
            }
            self._send(
                json.dumps(payload),
                "application/json",
            )

        elif self.path.startswith("/api/range"):
            # /api/range?from=YYYY-MM-DD&to=YYYY-MM-DD
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            from_date = (qs.get("from", [""])[0] or "").strip()
            to_date = (qs.get("to", [""])[0] or "").strip()

            trades = load_trades()
            payload = summary_range(trades, from_date, to_date)
            self._send(
                json.dumps(payload),
                "application/json",
            )

        else:
            self.send_response(404)
            self.end_headers()


def main():
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print("=" * 55)
    print("  ORB AUTO TRADER DASHBOARD")
    print("=" * 55)
    print(f"  Open:  http://localhost:{PORT}")
    print("  (auto-refreshes every 5 seconds)")
    print("  Ctrl+C to stop")
    print("=" * 55)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")


if __name__ == "__main__":
    main()