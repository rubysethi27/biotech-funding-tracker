"""
Reads current data from the database and bakes it into docs/index.html
as embedded JSON (avoids browser CORS issues you'd get from loading a
separate data file directly off disk).
"""
import json
import os
from datetime import datetime
from collections import Counter
from db import get_connection, init_db

BASE = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.join(BASE, "docs", "template.html")
OUTPUT_PATH = os.path.join(BASE, "docs", "index.html")


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

    return {
        "rounds": rows,
        "stage_breakdown": stage_breakdown,
        "top_leads": top_leads,
        "total_rounds_all_time": total,
        "updated_at": datetime.now().strftime("%b %d, %Y %-I:%M %p"),
    }


def export():
    data = build_dashboard_data()

    with open(TEMPLATE_PATH, "r") as f:
        template = f.read()

    html = template.replace("__DATA_JSON__", json.dumps(data))

    with open(OUTPUT_PATH, "w") as f:
        f.write(html)

    print(f"Dashboard exported to {OUTPUT_PATH}")
    print(f"  {data['total_rounds_all_time']} total rounds")


if __name__ == "__main__":
    export()
