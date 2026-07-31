"""
Takes raw articles saved by fetch_rss.py and uses Claude to pull out
structured funding round data — including the deeper science/investor
context (what the company is working on, who's leading the round and why).

This is the step that turns "TechCrunch: Acme Biotech raises $40M Series B
led by ARCH Venture to advance its in vivo CAR-T pipeline for lupus" into:
  company: Acme Biotech
  stage: Series B
  amount_usd_millions: 40
  modality: In vivo CAR-T
  target_indication: Lupus
  lead_investor: ARCH Venture
  lead_investor_type: Specialist VC
"""
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from db import get_connection, init_db

load_dotenv()

client = Anthropic(api_key=(os.environ.get("ANTHROPIC_API_KEY") or "").strip())

EXTRACTION_PROMPT = """You are extracting structured funding round data from a news article snippet, for a biotech/healthtech investor tracking tool.

Title: {title}
Summary: {summary}

If this article describes a specific company raising a specific equity funding round (seed, Series A/B/C/D+, growth, or similar), extract the details below.

If it is NOT about a specific funding round (e.g. it's about clinical trial results, FDA approval, M&A/acquisitions, layoffs, or a vague industry trend piece), respond with exactly: {{"is_funding_round": false}}

Otherwise respond with ONLY this JSON object, no other text:
{{
  "is_funding_round": true,
  "company": "company name",
  "stage": "Seed | Series A | Series B | Series C | Series D+ | Growth | Debt | Grant | Other",
  "amount_usd_millions": <number, or null if not stated>,
  "sector": "short sector label, e.g. 'Cell therapy', 'Gene editing', 'Digital health', 'AI drug discovery', 'Diagnostics', 'Medical device'",
  "modality": "the specific scientific/technical approach if this is a therapeutics company, e.g. 'In vivo CAR-T', 'Allogeneic CAR-T', 'AAV gene therapy', 'mRNA', 'Antibody-drug conjugate', 'Small molecule', 'Digital therapeutic'. Use null if not applicable (e.g. a pure software/digital health company with no therapeutic modality).",
  "target_indication": "the disease/condition being targeted, e.g. 'B-cell lymphoma', 'Duchenne muscular dystrophy', 'Type 2 diabetes'. Null if not stated or not applicable.",
  "trial_phase": "Preclinical | Phase 1 | Phase 2 | Phase 3 | Approved | Not applicable | Not stated",
  "mechanism_summary": "1-2 plain-English sentences on what the company is actually trying to achieve scientifically or clinically — written for someone who knows the industry but wants the specific hook of THIS company, not generic boilerplate.",
  "location": "city, state/country if mentioned, else null", "lead_investor": "lead investor name if stated, else null",
  "lead_investor_type": "Specialist VC | Corporate Strategic | Growth/Generalist | Government/Nonprofit | Undisclosed — classify based on the investor named. Corporate Strategic means a pharma/biotech company's venture arm (e.g. Eli Lilly, GV, Novartis Venture Fund, Amgen Ventures, J&J Innovation). Specialist VC means a dedicated life-science fund (e.g. ARCH Venture, RA Capital, Third Rock, Flagship, Polaris).",
  "lead_investor_rationale": "If the article states WHY this investor is participating (strategic interest, licensing option, thesis on the space, etc.) summarize it in one sentence. If not stated, use null — do not guess.",
  "other_investors": "comma-separated list of other investors mentioned, else null",
  "one_line_summary": "one plain sentence describing what the company does and what the funds are for"
}}"""


def extract_funding_data(title, summary):
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(title=title, summary=summary)
            }]
        )
        text = message.content[0].text.strip()
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
                        lead_investor, lead_investor_type, lead_investor_rationale,
                        other_investors, modality, target_indication, trial_phase,
                        mechanism_summary, source_url, source_name, summary)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        result.get("company"),
                        result.get("stage"),
                        result.get("amount_usd_millions"),
                        result.get("sector"),
                        result.get("location"),
                        result.get("lead_investor"),
                        result.get("lead_investor_type"),
                        result.get("lead_investor_rationale"),
                        result.get("other_investors"),
                        result.get("modality"),
                        result.get("target_indication"),
                        result.get("trial_phase"),
                        result.get("mechanism_summary"),
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
