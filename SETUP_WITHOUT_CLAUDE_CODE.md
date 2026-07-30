# Running this WITHOUT Claude Code (100% free automation)

This guide sets the tracker up to run automatically every day, for free,
using GitHub Actions — a scheduled task runner GitHub gives away free for
projects like this. Nothing needs to stay running on your computer.

The only cost is your Anthropic API key usage (pennies/month for this
volume) — that part is unavoidable no matter how you run it, since it's
what powers the "read messy news → extract structured data" step.

## What you'll need (all free)
- A GitHub account (github.com — free to sign up)
- An Anthropic API key (console.anthropic.com — pay-as-you-go, no
  subscription)

## Step-by-step

### 1. Create a GitHub account
Go to **github.com** and sign up if you don't have an account.

### 2. Create a new repository
- Click the **+** in the top right → **New repository**
- Name it something like `funding-tracker`
- Set it to **Private** (keeps your data/API usage private) or Public,
  your choice
- Don't check any of the "initialize with" boxes
- Click **Create repository**

### 3. Upload this project
On the new repo's page, click **uploading an existing file**, then drag in
the entire unzipped `funding-tracker` folder contents (all the files and
the `dashboard` and `.github` folders). Commit the upload.

If you'd rather use the command line (optional, not required):
```
cd funding-tracker
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/funding-tracker.git
git push -u origin main
```

### 4. Add your API key as a secret (not in the code — this keeps it private)
- In your repo, go to **Settings → Secrets and variables → Actions**
- Click **New repository secret**
- Name: `ANTHROPIC_API_KEY`
- Value: paste your actual key from console.anthropic.com
- Click **Add secret**

### 5. Turn on the scheduled run
The workflow file is already set up at
`.github/workflows/daily.yml` — it's configured to run every day at
7am US Eastern automatically. No further setup needed; GitHub reads that
file and handles the scheduling.

To test it immediately rather than waiting until tomorrow morning:
- Go to the **Actions** tab in your repo
- Click **Daily Funding Tracker Update** on the left
- Click **Run workflow** → **Run workflow** (green button)
- Watch it run — takes 1-2 minutes

### 6. View your dashboard
After a run completes, the updated `dashboard/index.html` is committed
back into your repo automatically. To view it as an actual website
(instead of downloading the file each time):

- Go to **Settings → Pages**
- Under "Source," choose the `main` branch and `/dashboard` folder
- Save — GitHub gives you a free URL like
  `https://your-username.github.io/funding-tracker/`
- It updates automatically every day after each scheduled run

That's it — from here it runs itself, free, forever, with no computer of
yours needing to be on.

## If something breaks
Go to the **Actions** tab and click on the failed run — it shows you the
exact error. Common ones:
- **RSS feed URL changed**: edit `fetch_rss.py` directly in GitHub (click
  the file, click the pencil icon to edit, fix the URL, commit)
- **API key issue**: double check the secret name is exactly
  `ANTHROPIC_API_KEY` and the key itself is valid

You can paste any error message into a chat with me here and I'll tell you
exactly what to change.
