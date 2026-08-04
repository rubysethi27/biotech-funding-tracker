"""
Pulls the latest articles from biotech/healthtech news RSS feeds and saves
new ones (not seen before) into the local database for the enrich step to
process.

Also fetches the full article page text (not just the short RSS summary),
since RSS summaries are often just one sentence — too little for the AI
to reliably pull out location, lead investor, stage, etc.
"""
import feedparser
import requests
from bs4 import BeautifulSoup
from db import get_connection, init_db

FEEDS = [
    ("Fierce Biotech", "https://www.fiercebiotech.com/rss/xml"),
    ("Fierce Healthcare", "https://www.fiercehealthcare.com/rss/xml"),
    ("Endpoints News", "https://endpoints.news/feed/"),
    ("MedCity News", "https://medcitynews.com/feed/"),
    ("STAT News", "https://www.statnews.com/feed/"),
]

FUNDING_KEYWORDS = [
    "raises", "raised", "funding", "series a", "series b", "series c",
    "series d", "seed round", "seed funding", "financing", "investment",
    "closes round", "secures", "backed by", "venture capital", "ipo",
    "million in funding", "capital raise",
]

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FundingTrackerBot/1.0)"
}
MAX_ARTICLE_CHARS = 4000


def looks_like_funding_news(title, summary):
    text = f"{title} {summary}".lower()
    return any(kw in text for kw in FUNDING_KEYWORDS)


def fetch_full_article_text(url):
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs)
        text = text.strip()

        if len(text) < 200:
            return None

        return text[:MAX_ARTICLE_CHARS]
    except Exception:
        return None


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

            full_text = fetch_full_article_text(link)

            try:
                cur.execute(
                    """INSERT OR IGNORE INTO raw_articles
                       (url, source, title, summary, full_text, published)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (link, source_name, title, summary, full_text, published),
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
