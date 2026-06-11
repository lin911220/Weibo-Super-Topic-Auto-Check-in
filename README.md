# Weibo Super Topic Auto Check-in

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-GCP%20Cloud%20Functions-4285F4.svg)](https://cloud.google.com/functions)
[![Scheduler](https://img.shields.io/badge/Trigger-Cloud%20Scheduler-34A853.svg)](https://cloud.google.com/scheduler)

## Description

Automatically checks in to all followed Weibo super topics every day, with no manual intervention required.

The system uses Playwright to scan a QR code locally and obtain a login cookie, which is stored in GCS. Each day, Cloud Scheduler triggers a Cloud Functions deployment that reads the cookie, fetches the list of followed super topics, checks in to each one, and sends an email report of the daily results and cookie health.

## System Name

**weibo-checkin** — Weibo Super Topic Auto Check-in System

## System Environment

| Item | Description |
| --- | --- |
| Platform | GCP Cloud Functions (2nd gen, HTTP trigger, region: `asia-east1`) |
| Schedule | Cloud Scheduler, daily at 09:00 Taiwan time (cron `0 9 * * *`) |
| Language | Python 3.11 |
| Storage | Google Cloud Storage (stores login cookie) |
| Notifications | Gmail SMTP |
| Login Tool | Playwright (local use only) |

## Installation

### 1. Get the code and create a virtual environment

```bash
git clone <repo-url>
cd weibo-checkin
python -m venv myenv
myenv\Scripts\activate   # Windows
```

### 2. Install dependencies

Local development (includes Playwright, used for login):

```bash
pip install -r requirements-local.txt
playwright install chromium
```

Cloud deployment (without Playwright):

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

| Variable | Description |
| --- | --- |
| `GCS_BUCKET_NAME` | GCS bucket name for storing the cookie |
| `SMTP_USERNAME` | Gmail account |
| `SMTP_PASSWORD` | Gmail app password |
| `EMAIL_SENDER` | Sender email address |
| `EMAIL_RECEIVER` | Recipient email address |
| `ENV` | Runtime environment (`local` or `gcp`) |

## Quick Start

1. **Log in locally and upload the cookie** (first run, or when the cookie expires)

   ```bash
   python auth.py
   ```

   This opens a browser showing a QR code. Scan it with the Weibo app to log in, and the cookie is automatically uploaded to GCS.

   You can also double-click `relogin.bat` (or the "Weibo Re-login" desktop shortcut) to do this with one click.

2. **Deploy to Cloud Functions**

   ```bash
   gcloud functions deploy weibo-checkin \
     --gen2 \
     --runtime=python311 \
     --region=asia-east1 \
     --source=. \
     --entry-point=run \
     --trigger-http \
     --no-allow-unauthenticated
   ```

3. **Set up the daily schedule**

   ```bash
   gcloud scheduler jobs create http weibo-checkin-daily \
     --schedule="0 9 * * *" \
     --time-zone="Asia/Taipei" \
     --uri="https://asia-east1-weibo-checkin.cloudfunctions.net/weibo-checkin" \
     --http-method=POST \
     --oidc-service-account-email=<service-account-email>
   ```

4. **Manually test the full flow locally**

   ```bash
   python -c "import main; main.run(None)"
   ```

## Workflow

```
1. Run auth.py locally
   - Playwright opens a browser -> scan QR code to log in to Weibo
   - Obtain the full cookie (with domain info) -> upload to GCS

2. Cloud Scheduler triggers Cloud Functions daily at 09:00 (Taiwan time)

3. Cloud Functions (main.py) runs
   - Read the cookie from GCS and verify it is valid
       - If invalid -> send a "cookie expired" notification and stop
   - Fetch the "followed super topics" list via weibo_api.py (auto pagination)
   - Send a check-in request for each topic (random 3-8s delay, mimics human behavior)
   - Write each check-in result to Cloud Logging
   - If any check-ins failed -> send a "failure details" notification
   - Send a "daily summary" email (date, success/failure counts)
```

## Architecture

```
weibo-checkin/
├── main.py                   # Cloud Functions entry point (HTTP trigger)
├── auth.py                   # Cookie management (Playwright login, GCS read/write, validation)
├── weibo_api.py              # Weibo API wrapper (paginated topic list, check-in request, HTTP headers)
├── checkin.py                # Main flow orchestrator (combines auth + weibo_api, controls random delays)
├── notifier.py               # Gmail SMTP email notifications
├── config.py                 # Centralized config constants (endpoints, bucket, delay range, recipients)
├── requirements.txt          # Cloud Functions deployment dependencies (no playwright)
├── requirements-local.txt    # Local dev dependencies (includes playwright, used by auth.py)
├── .gcloudignore             # Excludes myenv/, .env, test files, etc. from deployment
├── relogin.bat               # One-click local re-login shortcut (with desktop shortcut)
├── .env                      # Actual environment variables (not in git)
└── .env.example              # Environment variable template (no real values)
```

### Component Diagram

```
                ┌────────────┐
   (local)      │  auth.py   │── Playwright QR code login
                └─────┬──────┘
                      │ writes cookie
                      ▼
                ┌────────────┐
                │    GCS     │  weibo-checkin-bucket
                └─────┬──────┘
                      │ reads cookie
                      ▼
 Cloud Scheduler ──▶ main.py (Cloud Functions)
   (daily 09:00)       │
                       ├─▶ auth.verify_cookie()
                       ├─▶ checkin.run_checkin()
                       │     └─▶ weibo_api.py (topic list + check-in API)
                       ├─▶ Cloud Logging (per check-in record)
                       └─▶ notifier.py ──▶ Gmail SMTP ──▶ Email notification
```

## Constraints & Notes

- No username/password login (Weibo restriction); QR code login only
- The cookie is persisted in GCS and **must not** be committed to git
- Check-in requests mimic human behavior (random delays, browser-like headers) to reduce bot detection risk
- An expired cookie requires a manual re-scan; the system detects this automatically and sends an email notification
- The Cloud Function is deployed with `--no-allow-unauthenticated`, so only a service account with invoker permission (Cloud Scheduler via OIDC token) can call it

See [SPEC.md](./SPEC.md) for more details.
