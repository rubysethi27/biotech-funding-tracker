# Biotech/Healthtech Funding Tracker

A daily-updating dashboard that watches biotech and healthtech news, pulls out
new funding rounds, and shows them in a dashboard like Fierce Biotech's
fundraising tracker — company, stage, amount, sector, lead investor.

You do not need to know how to code to run this. You need to know how to
copy-paste and click "run" inside Claude Code. That's it.

## How this works (big picture)

1. `fetch_rss.py` checks a list of biotech/healthtech news RSS feeds for new
   articles and saves the raw headlines/text.
2. `enrich.py` sends each new article to Claude (the AI) and asks it to pull
   out structured info: company name, funding stage, dollar amount, sector,
   lead investor. This is the "smart" part — it turns messy news text into
   clean rows.
3. Everything gets saved into a small local database file (`funding.db`).
4. `export_dashboard.py` writes that data into `dashboard/index.html`, which
   you can just open in a browser.
5. `run_daily.py` runs all three steps in order. You (or a scheduled job)
   run this once a day.

## One-time setup

### Step 1 — Install Claude Code
If you haven't already: go to https://claude.com/claude-code and follow the
install instructions for your computer (Mac, Windows, or Linux).

### Step 2 — Open this folder in Claude Code
Unzip the file you downloaded, then open Claude Code and point it at the
`funding-tracker` folder. In the Claude Code chat, just say:

> "Set up this project — install any Python packages it needs and confirm
> everything runs."

Claude Code will read `requirements.txt` and install what's needed
(`feedparser` for reading RSS feeds, `anthropic` for the AI enrichment step).
You don't need to type any pip/terminal commands yourself — just ask Claude
Code to do it, and if it hits an error, paste the error back and ask it to
fix it.

### Step 3 — Get an Anthropic API key
This project calls the Claude API to structure the news data, which is
separate from your claude.ai subscription and has its own small usage cost
(this task is cheap — a few cents a day at most).

1. Go to https://console.anthropic.com
2. Create an account if you don't have one, add a small amount of credit
3. Go to "API Keys" and create a new key
4. Copy `.env.example` to a new file named `.env`
5. Paste your key in: `ANTHROPIC_API_KEY=sk-ant-...`

Tell Claude Code: "help me set up the .env file with my API key" if you get
stuck — don't paste your key into the chat, just do it directly in the file.

### Step 4 — Run it for the first time
In Claude Code, say:

> "Run run_daily.py and show me what happened"

This will fetch news, extract funding rounds, and build the dashboard.
First run may pull in a backlog of recent articles from each feed.

### Step 5 — View your dashboard
Open `dashboard/index.html` by double-clicking it — it opens in your browser
and works completely offline, no server needed.

## Running it daily automatically

Ask Claude Code:

> "Set up a scheduled task (cron on Mac/Linux, Task Scheduler on Windows)
> that runs run_daily.py every morning at 7am"

Claude Code can write the scheduling config for your OS — you don't need to
know cron syntax.

## Customizing

- **Add more news sources**: edit `FEEDS` in `fetch_rss.py` — just paste in
  more RSS feed URLs.
- **Focus on cell therapy / gene editing / immuno-oncology**: the `sector`
  field already tags this. Ask Claude Code to "add a filter view to the
  dashboard for cell therapy and gene editing rounds only."
- **Change the look**: ask Claude Code to restyle `dashboard/index.html` —
  it's a single self-contained file, easy to hand to Claude Code for design
  changes.

## Files in this project

| File | What it does |
|---|---|
| `fetch_rss.py` | Pulls raw articles from news RSS feeds |
| `enrich.py` | Uses Claude to extract structured funding data from articles |
| `db.py` | Sets up and manages the local SQLite database |
| `export_dashboard.py` | Writes current data into the dashboard HTML |
| `run_daily.py` | Runs the full pipeline (fetch → enrich → export) |
| `dashboard/index.html` | The dashboard you actually look at |
| `funding.db` | The database file (created automatically, don't edit by hand) |
