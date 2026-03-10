# WhatsApp Tender Analysis Bot

Production-ready WhatsApp bot for Indian government contractors that uses AI to analyze tender documents.

## Tech Stack
- Python 3.11, FastAPI
- SQLite & SQLAlchemy
- Twilio WhatsApp API
- Google Gemini 3 Flash Preview (`gemini-3-flash-preview`)
- Razorpay

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Copy `.env.example` to `.env` and fill in the actual keys:
```bash
cp .env.example .env
```
Ensure you provide:
- `GEMINI_API_KEY`: Google AI studio key.
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`: Twilio Sandbox or Prod details.
- `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`: Razorpay dashboard.

### 3. Run Locally
```bash
uvicorn main:app --reload --port 8000
```

### 4. Setting Twilio Webhook (Local Testing)
Use `ngrok` to expose your local server:
```bash
ngrok http 8000
```
Copy the ngrok URL and configure your Twilio WhatsApp Sandbox webhook URL as `https://<ngrok-url>/webhook`.

### 5. Deployment on Railway.app
- Push this repo to GitHub.
- Connect the repo to a new Railway project.
- The platform will auto-detect the `railway.toml` and `Procfile`.
- Add all Environment Variables in the Railway project settings.
- Get the Railway URL and set `RAILWAY_URL` respectively in variables.
- Update your Twilio Webhook URL to point to `https://<railway-url>/webhook`.

### 6. Razorpay Webhook
- In the Razorpay Dashboard, set the Webhook URL as `https://<railway-url>/payment-webhook`.
- Secret is implicitly taken from `RAZORPAY_KEY_SECRET` or you can define a `RAZORPAY_WEBHOOK_SECRET`.

## Application Architecture
- `main.py` - FastAPI app and webhook endpoints
- `bot.py` - WhatsApp conversation state machine 
- `analyzer.py` - Gemini AI analysis module
- `payments.py` - Razorpay integration module
- `database.py` - Models and queries
- `utils.py` / `prompts.py` - AI prompts and generation scripts
