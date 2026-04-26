# TenderBot — WhatsApp Tender Analysis Bot 🤖

AI-powered WhatsApp bot for Indian government contractors. Send a tender PDF → get complete analysis in 3 minutes.

## Features

- ✅ **10-part Tender Analysis** via Google Gemini Flash (structured output)
- ✅ **WhatsApp Interface** via Meta Cloud API
- ✅ **Natural Language** — Hindi, English, Hinglish, regional languages
- ✅ **All India Coverage** — 28 states, 8 UTs, 20+ central portals
- ✅ **Ladakh Special Focus** — BRO, NHIDCL, LAHDC, MES tracking
- ✅ **4-Tier Subscriptions** — Free, ₹99, ₹399, ₹799/month
- ✅ **Razorpay Payments** — UPI payment links + webhook verification
- ✅ **PDF Reports** — Downloadable analysis report
- ✅ **Portal Search** — "SEARCH RCC Ladakh" returns relevant portals
- ✅ **Preference System** — Natural conversation setup for location, work type, value range

## Tech Stack

- Python 3.11 / FastAPI / Uvicorn
- Google Gemini Flash with response_schema structured output (AI analysis)
- Meta Cloud API
- Razorpay (payments)
- PostgreSQL + SQLAlchemy (database, via Railway)
- Railway.app (deployment)

## System Requirements

- **Server requires**: `tesseract-ocr`, `poppler-utils`
- These are auto-installed via `nixpacks.toml` on Railway deployment.
- Locally, you must install them manually:
  - Windows: [Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki), [Poppler for Windows](http://blog.alivate.com.au/poppler-windows/)
  - Linux: `sudo apt install tesseract-ocr poppler-utils`

## Project Structure

```
├── main.py          # FastAPI app, webhooks
├── bot.py           # Conversation engine, state machine, NLP
├── analyzer.py      # Gemini PDF analysis with retry
├── portals.py       # India portal database + NLP detection + search
├── payments.py      # Razorpay integration
├── database.py      # SQLAlchemy models
├── prompts.py       # Gemini analysis prompt
├── utils.py         # PDF download, language detection, PDF report
├── scraper.py       # Phase 2 scraper framework (NOT ACTIVE)
├── requirements.txt
├── Procfile
├── railway.toml
└── .python-version
```

## Environment Variables

```
GEMINI_API_KEY=
META_ACCESS_TOKEN=
META_PHONE_NUMBER_ID=
META_WEBHOOK_VERIFY_TOKEN=TenderBot2026Secret
META_API_VERSION=v18.0
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAILWAY_URL=https://your-app.up.railway.app
DATABASE_URL=postgresql://user:password@host:port/database
BOT_PHONE=919796700386
PORT=8000
```

## Deployment

1. Push to GitHub
2. Connect repo to Railway
3. Add env variables in Railway dashboard
4. Railway auto-deploys
5. Set Meta Webhook URL: `https://your-domain/webhook` with `TenderBot2026Secret`
6. Set Razorpay webhook: `https://your-domain/payment-webhook`

## CRITICAL: Getting Permanent Access Token

The `META_ACCESS_TOKEN` provided by the quickstart is a temporary 24-hour token.
**To get a token that NEVER expires:**
1. Go to business.facebook.com -> Settings -> Users -> System Users
2. Click "Add System User"
3. Name: `TenderBot-Bot`, Role: `Admin`
4. Click "Generate New Token"
5. Select your TenderBot app
6. Select these permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
   - `business_management`
7. Click "Generate Token" and copy it immediately.
8. Add this token to Railway as `META_ACCESS_TOKEN`.

## How to submit templates in Meta Business Manager

Meta requires pre-approved templates for proactive messages (alerts, reminders).
1. Go to WhatsApp Manager -> Message Templates
2. Click "Create Template" -> Select "Utility"
3. Replicate the names and exact placeholders `{{1}}` found in `template_manager.py`.
4. Submit for review.

## API Key Rotation without Downtime

To maintain security, rotate keys periodically:
1. **Gemini API**: Generate a new key in Google AI Studio. Update `GEMINI_API_KEY` in Railway dashboard. Railway will gracefully restart the service. Delete the old key.
2. **Meta Access Token**: Generate a new System User Token in Business Manager. Update `META_ACCESS_TOKEN` in Railway. Delete old token.
3. **Razorpay**: Roll keys in the Razorpay dashboard (creates a new active key while keeping the old one active for 24h). Update Railway. Deactivate old key after 24 hours.

## Phase 2 — Automated Scraping (Not Yet Active)

`scraper.py` contains the framework for automated tender portal scraping.

**Requirements for activation:**
- Separate scraping service (Railway worker dyno)
- Proxy management for government portals
- APScheduler for periodic scraping
- Per-portal HTML parsers
- Rate limiting and CAPTCHA handling

See `scraper.py` for detailed activation instructions.

## License

Private — All rights reserved.
