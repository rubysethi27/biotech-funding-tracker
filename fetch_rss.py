"""
Pulls the latest articles from biotech/healthtech news RSS feeds and saves
new ones (not seen before) into the local database for the enrich step to
process.

To add more sources, just add more URLs to FEEDS below. Most news sites
publish an RSS feed even if it's not obvious from their homepage — search
"[site name] RSS feed" to find it.
"""
import feedparser
from db import get_connection, init_db

FEEDS = [
    ("Fierce Biotech", "https://www.fiercebiotech.com/rss/xml"),
    ("Fierce Healthcare", "https://www.fiercehealthcare.com/rss/xml"),
    ("Endpoints News", "https://endpoints.news/feed/"),
    ("MedCity News", "https://medcitynews.com/feed/"),
    ("STAT News", "https://www.statnews.com/feed/"),
]

# Rough keyword filter so we don't waste AI calls on unrelated articles
# (clinical trial results, FDA approvals, etc. that aren't funding news).
FUNDING_KEYWORDS = [
    "raises", "raised", "funding", "series a", "series b", "series c",
    "series d", "seed round", "seed funding", "financing", "investment",
    "closes round", "secures", "backed by", "venture capital", "ipo",
    "million in funding", "capital raise",
]


def looks_like_funding_news(title, summary):
    text = f"{title} {summary}".lower()
    return any(kw in text for kw in FUNDING_KEYWORDS)


def fetch_all():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    total_new = 0
    for source_name, url in FEEDS:
        print(f"Checking {source_name}...")
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"  Could not fetch {source_name}: {e}")
            continue

        if feed.bozo and not feed.entries:
            print(f"  Feed error for {source_name}, skipping")
            continue

        new_count = 0
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            link = entry.get("link", "")
            published = entry.get("published", "")

            if not link:
                continue
            if not looks_like_funding_news(title, summary):
                continue

            try:
                cur.execute(
                    """INSERT OR IGNORE INTO raw_articles
                       (url, source, title, summary, published)
                       VALUES (?, ?, ?, ?, ?)""",
                    (link, source_name, title, summary, published),
                )
                if cur.rowcount > 0:
                    new_count += 1
            except Exception as e:
                print(f"  Error saving article: {e}")

        conn.commit()
        print(f"  {new_count} new funding-related articles")
        total_new += new_count

    conn.close()
    print(f"\nDone. {total_new} new articles saved for processing.")
    return total_new


if __name__ == "__main__":
    fetch_all()
