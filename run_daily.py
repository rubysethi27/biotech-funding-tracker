"""
Runs the full daily pipeline: fetch new articles -> extract structured
funding data with Claude -> rebuild the dashboard.

Run this manually, or set it up as a scheduled task (ask Claude Code to
configure cron / Task Scheduler for you).
"""
from fetch_rss import fetch_all
from enrich import process_new_articles
from export_dashboard import export

if __name__ == "__main__":
    print("=" * 50)
    print("STEP 1: Fetching news")
    print("=" * 50)
    new_articles = fetch_all()

    print("\n" + "=" * 50)
    print("STEP 2: Extracting funding data")
    print("=" * 50)
    new_rounds = process_new_articles()

    print("\n" + "=" * 50)
    print("STEP 3: Rebuilding dashboard")
    print("=" * 50)
    export()

    print(f"\nDone! {new_articles} articles checked, {new_rounds} new rounds added.")
    print("Open dashboard/index.html to view.")
