# Local Files Audit

### `knowledge_harvester.py`
- **Purpose**: Autonomously crawls DuckDuckGo and utilizes Gemini AI to extract up-to-date regional legal/financial knowledge (like GST rates and minimum wage) to store in the database. 
- **State**: Experimental / Working
- **Dependencies**: Relies on `PROXY_URL`, `GEMINI_API_KEY`, `google-genai`, and `database.py` (SessionLocal, KnowledgeFact model).

### `marketing_campaign.py`
- **Purpose**: Fully automated outbound WhatsApp drip campaign system that parses leads from the database and A/B tests different ad templates utilizing an epsilon-greedy algorithm.
- **State**: Working
- **Dependencies**: Relies on `database.py` (MarketingLead, MarketingTemplate models), `bot.py` (`send_whatsapp_message`), and `RAILWAY_URL`.

### `marketing_scraper.py`
- **Purpose**: Autonomous discovery scraper that searches state directories and leverages regex and DOM context proximity parsing to find and categorize new contractor phone numbers to load into the marketing engine.
- **State**: Experimental
- **Dependencies**: Relies on `database.py` (MarketingLead models), `PROXY_URL`, `requests`, and `bs4`.

### `scraper.py`
- **Purpose (Local vs origin/main)**: The local modifications inject a rotating `PROXY_URL` configuration into all outbound `requests.get` calls for `scrape_nicgep_portal` and `scrape_cppp_portal`, defending against portal-side IP rate limiting.
- **State**: Working
- **Dependencies**: Standard external API constraints, `PROXY_URL` environment variables, `requests`, and `bs4`.

### `self_optimization.py`
- **Purpose**: A generative refining engine that parses the active system instructions in the DB to formulate a 10% more effective iteration via Gemini and saves the active prompt as a new version.
- **State**: Experimental
- **Dependencies**: Relies on `prompts.py`, `database.py` (SystemPrompt, Analysis models), and `GEMINI_API_KEY`.

### `test_scrape.py`
- **Purpose**: A lightweight, standalone unit test for safely validating DOM connectivity and table-parsing logic securely against a portal without touching the DB.
- **State**: Working
- **Dependencies**: `PROXY_URL`, `requests` and `bs4`.

### `check_live_stats.py`
- **Purpose**: A diagnostic monitoring script that pings the active database configuration and emits organic user counts, scraped leads, webhook traffic, and daemon lock execution times.
- **State**: Working
- **Dependencies**: Loads connection bounds via `python-dotenv`, actively parses `database.py`.

### `verify_all.py`
- **Purpose**: Syntactic pipeline integration check that spins up all underlying python modules strictly monitoring for breaking resolution failures or missing library definitions.
- **State**: Working
- **Dependencies**: `.env` and standard architecture paths.
