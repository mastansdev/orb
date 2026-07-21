"""
NEWS PIPELINE CHECK  (run any time: py tools/news_pipeline_check.py)

Answers ONE question with hard numbers:
"Is the Railway news engine actually feeding the bot today?"

If this fails, the CATALYST GATE will (correctly) block every
trade — the bot only trades news-armed stocks now. So run this
BEFORE market open every day.
"""

import os
import sys
from datetime import datetime, date

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from dotenv import load_dotenv

load_dotenv()


def main():
    today = date.today().strftime("%Y-%m-%d")
    print("=" * 56)
    print(f"NEWS PIPELINE CHECK — {today}")
    print("=" * 56)

    # 1. DATABASE_URL present?
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("❌ DATABASE_URL missing from .env — the bot cannot")
        print("   read Railway stories at all. Fix .env first.")
        return
    host = url.split("@")[-1].split("/")[0] if "@" in url else "?"
    print(f"1. DATABASE_URL          : set ({host})")

    # 2. Can we connect?
    try:
        import psycopg
        conn = psycopg.connect(url, connect_timeout=10)
        cur = conn.cursor()
        print("2. Postgres connection   : ✅ OK")
    except Exception as e:
        print(f"2. Postgres connection   : ❌ FAIL — {e}")
        print("   → Railway DB unreachable. Check Railway service")
        print("     status + that bot .env matches Railway's URL.")
        return

    # 3. Raw news flowing today? (collectors alive)
    # NOTE: rows saved by Railway BEFORE the 2026-07-21
    # created_at fix have created_at = NULL and cannot be
    # dated. Until Railway is redeployed with the fix,
    # this step is informational only — steps 4-6 are the
    # real verdict.
    cur.execute(
        "SELECT COUNT(*), MAX(created_at) FROM raw_news "
        "WHERE created_at >= %s", (today,)
    )
    n_raw, last_raw = cur.fetchone()
    cur.execute(
        "SELECT COUNT(*) FROM raw_news "
        "WHERE created_at IS NULL"
    )
    n_undated = cur.fetchone()[0]
    print(f"3. Raw news today        : {n_raw}  (last: {last_raw})")
    if n_undated:
        print(f"   ℹ️ {n_undated} undated rows (pre-fix Railway build —")
        print("     redeploy Railway to start dating raw news)")
    if not n_raw and not n_undated:
        print("   ❌ Collectors produced NOTHING →")
        print("     the Railway service is down or crashed.")
        print("     Check: railway logs / redeploy railway_main.py")

    # 3c. PER-SOURCE breakdown — the critical question:
    # is the BSE Corporate collector actually working from
    # Railway's IP? BSE often blocks datacenter IPs. If
    # "BSE Corporate" shows 0 while RSS flows, results
    # detection is limping on slower news mentions only.
    print("3c. Per-source (all time / today):")
    try:
        # COALESCE + LIKE 'YYYY-MM-DD%%': robust across the
        # mixed timestamp formats in the table (naive,
        # +05:30-aware, and pre-fix NULL created_at rows).
        cur.execute(
            "SELECT source, COUNT(*), "
            "COUNT(*) FILTER (WHERE "
            " COALESCE(created_at, published_at) LIKE %s), "
            "MAX(COALESCE(created_at, published_at)) "
            "FROM raw_news GROUP BY source "
            "ORDER BY 2 DESC", (today + "%",)
        )
        rows = cur.fetchall()
        if not rows:
            print("   (raw_news table empty)")
        for src, total, n_today, last in rows:
            warn = ""
            if "BSE" in str(src).upper() and not n_today:
                warn = "  ← ❌ RESULTS DETECTION AT RISK"
            print(
                f"   {str(src):<18} total={total:<6} "
                f"today={n_today:<5} last={last}{warn}"
            )
        srcs = " ".join(str(r[0]).upper() for r in rows)
        if "BSE" not in srcs:
            print("   ❌ NO BSE rows AT ALL — BSE API likely")
            print("     blocks Railway's IP. Result filings are")
            print("     NOT reaching the bot directly; only")
            print("     slower RSS mentions. Consider running")
            print("     the BSE collector from your home PC/IP.")
    except Exception as e:
        print(f"   (per-source query failed: {e})")

    # 3d. Publish→collect latency (only rows where both
    # timestamps exist, i.e. post-fix). This is the real
    # "how fast after BSE publishes" number.
    try:
        cur.execute(
            "SELECT source, "
            "AVG(EXTRACT(EPOCH FROM "
            " (created_at::timestamp - published_at::timestamp)))/60.0, "
            "COUNT(*) "
            "FROM raw_news "
            "WHERE created_at IS NOT NULL "
            "AND published_at IS NOT NULL "
            "AND created_at >= %s "
            "AND created_at::timestamp >= published_at::timestamp "
            "AND created_at::timestamp - published_at::timestamp "
            "    < INTERVAL '4 hours' "
            "GROUP BY source", (today,)
        )
        lat = cur.fetchall()
        if lat:
            print("3d. Publish→collect latency (today, avg):")
            for src, mins, n in lat:
                flag = "✅" if mins is not None and mins <= 3 else "⚠️"
                print(
                    f"   {flag} {str(src):<18} "
                    f"{mins:.1f} min  (n={n})"
                )
    except Exception:
        pass  # timestamp formats vary on old rows — skip

    # 4. Stories built today? (classifier alive)
    cur.execute(
        "SELECT COUNT(*), MAX(created_at) FROM market_stories "
        "WHERE created_at >= %s", (today,)
    )
    n_stories, last_story = cur.fetchone()
    print(f"4. Stories today         : {n_stories}  (last: {last_story})")
    if n_raw and not n_stories:
        print("   ❌ Raw news arrives but no stories are built —")
        print("     classifier/story-builder failing on Railway.")

    # 5. Stories matched to SYMBOLS today? (this is what arms stocks)
    cur.execute(
        "SELECT COUNT(*) FROM market_stories "
        "WHERE created_at >= %s "
        "AND affected_symbols IS NOT NULL "
        "AND array_length(affected_symbols, 1) > 0", (today,)
    )
    n_sym = cur.fetchone()[0]
    print(f"5. Symbol-matched today  : {n_sym}")
    if n_stories and not n_sym:
        print("   ❌ Stories exist but NONE map to a stock symbol —")
        print("     symbol matcher is failing. Without a symbol,")
        print("     no stock ever gets armed → catalyst gate")
        print("     blocks everything.")

    # 6. Freshest story age — the KEY number. Catalysts
    # expire; a feed that died hours ago means stale/no
    # arming during market hours.
    age_min = None
    if last_story:
        try:
            from datetime import timedelta
            ts = datetime.fromisoformat(str(last_story))
            raw_age = (
                datetime.now() - ts
            ).total_seconds() / 60
            # Rows written by a pre-fix Railway build are UTC
            # (IST minus 5h30m = 330 min). If shifting by 330
            # gives a sane recent age, use it and say so.
            utc_age = raw_age - 330
            if 0 <= utc_age < raw_age:
                age_min = utc_age
                print(
                    f"6. Last story age        : "
                    f"{'✅' if age_min < 90 else '❌'} "
                    f"{age_min:.0f} min "
                    f"(UTC timestamp from pre-fix Railway — "
                    f"raw said {raw_age:.0f})"
                )
            else:
                age_min = raw_age
                flag = "✅" if age_min < 90 else "❌"
                print(f"6. Last story age        : {flag} {age_min:.0f} min")
            if age_min >= 90:
                print("   ❌ Feed went SILENT — Railway was alive")
                print("     earlier but has stopped producing.")
                print("     Restart/redeploy the Railway service,")
                print("     then re-run this check.")
        except Exception:
            pass

    print("-" * 56)
    fresh = age_min is not None and age_min < 90
    if n_stories and n_sym and fresh:
        print("VERDICT: ✅ pipeline ALIVE — catalyst gate will arm")
        print("stocks as symbol-matched news lands today.")
    elif n_stories and n_sym:
        print("VERDICT: ⚠️ pipeline STALLED — it worked earlier")
        print("today (stories + symbols exist) but nothing new")
        print("is arriving. Restart the Railway service. The bot")
        print("will only trade on catalysts fresh enough to")
        print("still be armed.")
    else:
        print("VERDICT: ❌ pipeline BROKEN at the step marked above.")
        print("Until fixed, the bot will (by design) take ZERO")
        print("trades — that is the catalyst gate doing its job.")
    print("=" * 56)


if __name__ == "__main__":
    main()
