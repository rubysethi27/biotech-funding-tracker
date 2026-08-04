"""
Local database for the funding tracker. Uses SQLite (a single file,
no server needed) — perfect for a solo daily-update project like this.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "funding.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            source TEXT,
            title TEXT,
            summary TEXT,
            full_text TEXT,
            published TEXT,
            processed INTEGER DEFAULT 0,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS funding_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            stage TEXT,
            amount_usd_millions REAL,
            sector TEXT,
            location TEXT,
            lead_investor TEXT,
            lead_investor_type TEXT,
            lead_investor_rationale TEXT,
            other_investors TEXT,
            modality TEXT,
            target_indication TEXT,
            trial_phase TEXT,
            mechanism_summary TEXT,
            source_url TEXT,
            source_name TEXT,
            summary TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company, amount_usd_millions, source_url)
        )
    """)

    existing_cols = [row["name"] for row in cur.execute("PRAGMA table_info(funding_rounds)")]
    new_cols = {
        "lead_investor_type": "TEXT",
        "lead_investor_rationale": "TEXT",
        "modality": "TEXT",
        "target_indication": "TEXT",
        "trial_phase": "TEXT",
        "mechanism_summary": "TEXT",
    }
    for col, coltype in new_cols.items():
        if col not in existing_cols:
            cur.execute(f"ALTER TABLE funding_rounds ADD COLUMN {col} {coltype}")

    existing_article_cols = [row["name"] for row in cur.execute("PRAGMA table_info(raw_articles)")]
    if "full_text" not in existing_article_cols:
        cur.execute("ALTER TABLE raw_articles ADD COLUMN full_text TEXT")

    conn.commit()
    conn.close()


def find_existing_round(cur, company, amount_usd_millions):
    """
    Checks whether a funding round for this company/amount already exists,
    regardless of which article URL reported it. Prevents the same round
    getting saved twice when multiple outlets cover the same news.
    """
    if not company:
        return None
    cur.execute("SELECT id, amount_usd_millions FROM funding_rounds WHERE lower(company) = lower(?)", (company,))
    for row in cur.fetchall():
        existing_amount = row["amount_usd_millions"]
        if amount_usd_millions is None or existing_amount is None:
            if amount_usd_millions == existing_amount:
                return row["id"]
        elif abs(existing_amount - amount_usd_millions) <= max(1.0, existing_amount * 0.05):
            return row["id"]
    return None


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
