"""
Takes raw articles saved by fetch_rss.py and uses Claude to pull out
structured funding round data: company, stage, amount, sector, investors.

This is the step that turns "TechCrunch: Acme Biotech raises $40M Series B
led by ARCH Venture to advance its CAR-T pipeline" into a clean row:
  company: Acme Biotech
  stage: Series B
  amount_usd_millions: 40
  sector: Cell therapy
  lead_investor: ARCH Venture
"""
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from db import get_connection, init_db

load_dotenv()

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

EXTRACTION_PROMPT = """You are extracting structured funding round data from a news article snippet.

Title: {title}
Summary: {summary}

If this article describes a specific company raising a specific funding round (equity financing — seed, Series A/B/C/D+, or similar), extract the details.

If it is NOT about a specific funding round (e.g. it's about clinical trial results, FDA approval, M&A, layoffs, or a vague industry trend piece), respond with exactly: {{"is_funding_round": false}}

Otherwise respond with ONLY this JSON object, no other text:
{{
  "is_funding_round": true,
  "company": "company name",
  "stage": "Seed | Series A | Series B | Series C | Series D+ | Debt | Grant | Other",
  "amount_usd_millions": <number, or null if not stated>,
  "sector": "short sector label, e.g. 'Cell therapy', 'Gene editing', 'Digital health', 'AI drug discovery', 'Diagnostics', 'Medical device'",
  "location": "city, state/country if mentioned, else null",
  "lead_investor": "lead investor name if stated, else null",
  "other_investors": "comma-separated list of other investors mentioned, else null",
  "one_line_summary": "one plain sentence describing what the company does and what the funds are for"
}}"""


def extract_funding_data(title, summary):
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(title=title, summary=summary)
            }]
        )
        text = message.content[0].text.strip()
        # Strip markdown code fences if Claude adds them
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        print(f"  Could not parse response: {e}")
        return None


def process_new_articles():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM raw_articles WHERE processed = 0")
    articles = cur.fetchall()
    print(f"Processing {len(articles)} new articles...")

    added = 0
    for article in articles:
        result = extract_funding_data(article["title"], article["summary"])

        if result and result.get("is_funding_round"):
            try:
                cur.execute(
                    """INSERT OR IGNORE INTO funding_rounds
                       (company, stage, amount_usd_millions, sector, location,
                        lead_investor, other_investors, source_url, source_name, summary)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        result.get("company"),
                        result.get("stage"),
                        result.get("amount_usd_millions"),
                        result.get("sector"),
                        result.get("location"),
                        result.get("lead_investor"),
                        result.get("other_investors"),
                        article["url"],
                        article["source"],
                        result.get("one_line_summary"),
                    ),
                )
                if cur.rowcount > 0:
                    added += 1
                    print(f"  + {result.get('company')} — {result.get('stage')} "
                          f"${result.get('amount_usd_millions')}M")
            except Exception as e:
                print(f"  Error saving round: {e}")

        cur.execute(
            "UPDATE raw_articles SET processed = 1 WHERE id = ?",
            (article["id"],)
        )
        conn.commit()

    conn.close()
    print(f"\nDone. {added} new funding rounds added.")
    return added


if __name__ == "__main__":
    process_new_articles()
