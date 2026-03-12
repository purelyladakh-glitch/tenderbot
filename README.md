# TenderBot — WhatsApp Tender Analysis Bot 🤖

AI-powered WhatsApp bot for Indian government contractors. Send a tender PDF → get complete analysis in 3 minutes.

## Features

- ✅ **9-part Tender Analysis** via Google Gemini 3 Flash
- ✅ **WhatsApp Interface** via AiSensy
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
- Google Gemini 3 Flash Preview (AI analysis)
- AiSensy WhatsApp API
- Razorpay (payments)
- SQLite + SQLAlchemy (database)
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
AISENSY_API_KEY=
AISENSY_PHONE=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAILWAY_URL=https://your-app.up.railway.app
DATABASE_URL=sqlite:///./tenderbot.db
PORT=8000
```

## Deployment

1. Push to GitHub
2. Connect repo to Railway
3. Add env variables in Railway dashboard
4. Railway auto-deploys
5. Set AiSensy (Pro) webhook: `https://your-domain/receive_message`
6. Set Razorpay webhook: `https://your-domain/payment-webhook`

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
