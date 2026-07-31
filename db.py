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

    # Raw articles pulled from RSS feeds, before AI extraction.
    # This lets us avoid re-processing the same article twice.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            source TEXT,
            title TEXT,
            summary TEXT,
            published TEXT,
            processed INTEGER DEFAULT 0,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Structured funding rounds extracted by Claude.
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

    # Lightweight migration: add new columns if this is an existing
    # database created before this update.
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

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
