"""
Reads current data from the database and bakes it into docs/index.html
as embedded JSON. Also dedupes rows at display time and converts the
"updated" timestamp from server UTC time to US Eastern.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from collections import Counter
from db import get_connection, init_db

BASE = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.join(BASE, "docs", "template.html")
OUTPUT_PATH = os.path.join(BASE, "docs", "index.html")

UTC_TO_EASTERN_HOURS = -4


def dedupe_rows(rows):
    def completeness(r):
        return sum(1 for v in r.values() if v not in (None, ""))

    deduped = []
    for row in rows:
        match_index = None
        for i, existing in enumerate(deduped):
            same_company = (row["company"] or "").strip().lower() == (existing["company"] or "").strip().lower()
            amt_a, amt_b = row["amount_usd_millions"], existing["amount_usd_millions"]
            if amt_a is None or amt_b is None:
                same_amount = amt_a == amt_b
            else:
                same_amount = abs(amt_a - amt_b) <= max(1.0, amt_b * 0.05)
            if same_company and same_amount:
                match_index = i
                break

        if match_index is None:
            deduped.append(row)
        else:
            if completeness(row) > completeness(deduped[match_index]):
                deduped[match_index] = row

    return deduped


def format_added_date(added_at_str):
    if not added_at_str:
        return None
    try:
        dt = datetime.strptime(added_at_str, "%Y-%m-%d %H:%M:%S")
        dt = dt + timedelta(hours=UTC_TO_EASTERN_HOURS)
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return added_at_str


def build_dashboard_data():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT company, stage, amount_usd_millions, sector, location,
               lead_investor, lead_investor_type, lead_investor_rationale,
               other_investors, modality, target_indication, trial_phase,
               mechanism_summary, added_at
        FROM funding_rounds
        ORDER BY added_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    rows = dedupe_rows(rows)

    for r in rows:
        r["added_display"] = format_added_date(r.get("added_at"))

    total = len(rows)

    stage_counts = Counter(r["stage"] or "Other" for r in rows)
    stage_breakdown = []
    if total > 0:
        for stage, count in stage_counts.most_common():
            stage_breakdown.append({
                "stage": stage,
                "pct": round(100 * count / total),
            })

    lead_counts = Counter(r["lead_investor"] for r in rows if r["lead_investor"])
    top_leads = [{"investor": inv, "count": c} for inv, c in lead_counts.most_common(5)]

    now_eastern = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=UTC_TO_EASTERN_HOURS)

    return {
        "rounds": rows,
        "stage_breakdown": stage_breakdown,
        "top_leads": top_leads,
        "total_rounds_all_time": total,
        "updated_at": now_eastern.strftime("%b %d, %Y %-I:%M %p") + " ET",
    }


def export():
    data = build_dashboard_data()

    with open(TEMPLATE_PATH, "r") as f:
        template = f.read()

    html = template.replace("__DATA_JSON__", json.dumps(data))

    with open(OUTPUT_PATH, "w") as f:
        f.write(html)

    print(f"Dashboard exported to {OUTPUT_PATH}")
    print(f"  {data['total_rounds_all_time']} total rounds (after dedup)")


if __name__ == "__main__":
    export()
