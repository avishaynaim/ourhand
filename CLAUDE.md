# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OurHand Monitor is a Python real estate monitoring system that scrapes ALL rental apartments from Yad2.co.il (~29,000+ apartments across Israel). It provides a REST API, web dashboard, and Telegram bot notifications.

## Commands

### Run the Application
```bash
# Set required environment variables first
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id
export DATABASE_URL=postgresql://user:pass@localhost/dbname

# Run main application (starts scraper + web server)
python app.py
```

### Run Web Server Only
```bash
python -c "from web import create_web_app, run_web_server; run_web_server(create_web_app(get_database()))"
```

### Docker
```bash
docker build -t ourhand .
docker run -p 5000:5000 --env-file .env ourhand
```

### Deploy to Railway
```bash
railway login
railway up
```

## Architecture

### Entry Points
- **`app.py`** - Main orchestrator: starts scraper loop and web server in parallel threads
- **`web.py`** - Flask REST API and dashboard (can be imported independently)

### Data Flow
```
Yad2.co.il → app.py (scraper) → database_postgres.py → web.py (API) → dashboard/Telegram
                                      ↓
                              notifications.py → Telegram users
```

### Key Modules
- **`db_wrapper.py`** - Factory that returns `PostgreSQLDatabase` instance (requires `DATABASE_URL`)
- **`database_postgres.py`** - All database operations (apartments, price_history, user_preferences, favorites)
- **`telegram_bot.py`** - Webhook-based bot with 12 commands, per-user filters
- **`notifications.py`** - Notification routing, rate limiting, daily digests
- **`analytics.py`** - Market statistics and trend analysis
- **`config.py`** - Environment variable loading with validation
- **`constants.py`** - All magic numbers and thresholds

### Scraping Logic (app.py)
- **Initial scrape** (DB < 5000 apartments): Scrapes all 700+ pages with fast 1-3s delays
- **Monitoring mode**: Uses smart-stop after 6 consecutive known listings, 3-8s delays
- `AdaptiveDelayManager` adjusts delays based on block/rate-limit events
- Runs every 20-40 minutes (randomized)

### Database Schema (PostgreSQL)
- `apartments` - Main listing data (yad2_id, price, rooms, sqm, city, neighborhood, floor, status)
- `price_history` - Price changes with timestamps
- `user_preferences` - Per-user Telegram filters and settings
- `favorites` / `ignored_ids` - Per-user lists

### API Authentication
All `/api/*` endpoints require `X-API-Key` header (except `/health`, `/ping`).

## Environment Variables

**Required:**
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID
- `DATABASE_URL` - PostgreSQL connection string (auto-set on Railway)

**Optional:**
- `API_KEY` - API authentication key
- `MIN_INTERVAL_MINUTES` / `MAX_INTERVAL_MINUTES` - Scrape frequency (default: 20/40)
- `ENABLE_WEB` - Enable web server (default: true)
- `WEB_PORT` - Web server port (default: 5000)

## Important Patterns

### Database Access
Always use `db_wrapper.get_database()` to get database instance:
```python
from db_wrapper import get_database
db = get_database()  # Returns PostgreSQLDatabase
```

### Constants
All thresholds and magic numbers are in `constants.py`:
- `CONSECUTIVE_KNOWN_THRESHOLD = 6` - Stop scraping after N consecutive known
- `MIN_RESULTS_FOR_REMOVAL = 1000` - Min apartments before marking removed
- `INITIAL_SCRAPE_PAGE_DELAY = (1, 3)` - Fast delays for initial scrape
- `NORMAL_SCRAPE_PAGE_DELAY = (3, 8)` - Normal monitoring delays

### Web Dashboard
Dashboard HTML is in `dashboard_embedded.py` (returns full HTML string). Templates in `templates/` and static assets in `static/js/` and `static/css/`.
