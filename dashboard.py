"""
==========================================================
ORB Auto Trader — Live Dashboard
==========================================================

Local website showing the bot's trading visually:

    • Live PnL curve (from market recorder snapshots)
    • Open positions
    • Today's + historical entries/exits with timestamps
    • PnL by hour of day  (the "market slows after
      11 AM" question, answered with your own data)
    • Trade quality: conviction vs outcome
    • Edge summary (net of charges)

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
# Data access (read-only)
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
                        "conviction": float(
                            row.get("Conviction", 0) or 0
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


def load_positions():
    if not os.path.exists(POSITIONS_FILE):
        return []

    try:
        with open(
            POSITIONS_FILE, encoding="utf-8"
        ) as f:
            data = json.load(f) or {}

        return [
            {
                "symbol": t.get("symbol", ""),
                "entry": t.get("entry", 0),
                "stop_loss": t.get("trail_sl", 0)
                or t.get("stop_loss", 0),
                "target": t.get("target", 0),
                "qty": t.get("qty", 0),
                "entry_time": t.get("entry_time", ""),
                "sector": t.get("sector", ""),
                "conviction": t.get("conviction", 0),
                "stage": t.get("stage", ""),
            }
            for t in data.values()
        ]
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
         font:14px/1.45 'Segoe UI',system-ui,sans-serif; padding:18px; }
  h1 { font-size:19px; margin-bottom:2px; }
  .sub { color:var(--dim); font-size:12px; margin-bottom:16px; }
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
</style>
</head>
<body>
<h1>ORB AUTO TRADER — LIVE DASHBOARD</h1>
<div class="sub" id="updated">loading…</div>

<div class="grid cards" id="kpis"></div>

<div class="grid two" style="margin-top:14px">
  <div class="card">
    <h2>Live PnL — today's session</h2>
    <div class="chart-box"><canvas id="pnlChart"></canvas></div>
  </div>
  <div class="card">
    <h2>PnL by entry hour (all history)</h2>
    <div class="chart-box small"><canvas id="hourChart"></canvas></div>
  </div>
</div>

<div class="grid two" style="margin-top:14px">
  <div class="card">
    <h2>Open positions</h2>
    <table id="positions"><thead><tr>
      <th>Symbol</th><th>Entry</th><th>Stop</th><th>Target</th>
      <th>Qty</th><th>Time</th><th>Stage</th><th>Conviction</th>
    </tr></thead><tbody></tbody></table>
  </div>
  <div class="card">
    <h2>Trade quality — conviction vs PnL</h2>
    <div class="chart-box small"><canvas id="qualityChart"></canvas></div>
  </div>
</div>

<div class="card" style="margin-top:14px">
  <h2>Trades (latest 40)</h2>
  <table id="trades"><thead><tr>
    <th>Date</th><th>Entry</th><th>Exit</th><th>Symbol</th>
    <th>Sector</th><th>Qty</th><th>In</th><th>Out</th>
    <th>PnL</th><th>Hold</th><th>Exit Reason</th><th>Conviction</th>
  </tr></thead><tbody></tbody></table>
</div>

<script>
let pnlChart, hourChart, qualityChart;

function fmt(n){ return (n>=0?'+':'')+Number(n).toLocaleString('en-IN',
  {maximumFractionDigits:0}); }

async function refresh(){
  const r = await fetch('/api/all');
  const d = await r.json();

  document.getElementById('updated').textContent =
    'updated ' + new Date().toLocaleTimeString() +
    ' — auto-refreshes every 5s';

  // KPIs
  const s = d.summary;
  const kpis = [
    ['Today PnL', fmt(s.today_pnl||0), (s.today_pnl||0)>=0],
    ['Today Trades', s.today_trades||0, true],
    ['Open Positions', d.positions.length, true],
    ['All-time Trades', s.trades||0, true],
    ['Win Rate', (s.win_rate||0)+'%', (s.win_rate||0)>=50],
    ['Gross PnL', fmt(s.gross_pnl||0), (s.gross_pnl||0)>=0],
  ];
  document.getElementById('kpis').innerHTML = kpis.map(k=>
    `<div class="card kpi"><div class="l">${k[0]}</div>
     <div class="v ${k[2]?'pos':'neg'}">${k[1]}</div></div>`).join('');

  // PnL curve
  const series = d.pnl_series;
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

  // Hour analysis
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

  // Quality scatter
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

  // Positions table
  document.querySelector('#positions tbody').innerHTML =
    d.positions.length ? d.positions.map(p=>
      `<tr><td><b>${p.symbol}</b></td><td>${p.entry}</td>
       <td>${p.stop_loss}</td><td>${p.target}</td><td>${p.qty}</td>
       <td>${p.entry_time}</td><td>${p.stage}</td>
       <td>${p.conviction}</td></tr>`).join('')
    : '<tr><td colspan="8" style="color:#8b949e">No open positions</td></tr>';

  // Trades table
  document.querySelector('#trades tbody').innerHTML =
    t.slice(-40).reverse().map(x=>{
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
    }).join('');
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
            payload = {
                "summary": summary(trades),
                "trades": trades,
                "positions": load_positions(),
                "pnl_series": load_pnl_series(),
                "by_hour": hour_analysis(trades),
            }
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
