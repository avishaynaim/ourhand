# OurHand Monitor 🇮🇱

**Full Israel Rentals Monitoring** - A professional real estate monitoring system that tracks ALL rental apartments across Israel from Yad2.co.il (~29,000+ apartments).

> ⚠️ **IMPORTANT**: This is a SEPARATE project from Myhand. You MUST create a new Telegram bot and use different environment variables for this deployment.

## Key Differences from Myhand

| Feature | Myhand | OurHand |
|---------|--------|---------|
| Scope | Specific city/area | All Israel |
| Apartments | ~1,000-5,000 | ~29,000+ |
| Pages | ~50 | 700+ |
| Initial Scrape | ~10 minutes | 30-60 minutes |
| Check Interval | 60-90 min | 20-40 min |
| Smart-Stop Threshold | 4 consecutive | 6 consecutive |

## Features

### Full-Site Scraping
- **Initial Scrape**: First run scrapes ALL 700+ pages (29K+ apartments)
- **Smart Monitoring**: Subsequent runs use smart-stop after 6 consecutive known listings
- **Faster Delays**: Initial scrape uses 1-3s delays, monitoring uses 3-8s
- **More Frequent Checks**: Runs every 20-40 minutes (randomized)

### Multi-User Telegram Bot
- 12 interactive commands
- Per-user preferences and filters
- Inline buttons for favorites/ignore
- Filter-based notification routing

### Web Dashboard
- Modern, responsive UI with dark mode
- Interactive Chart.js visualizations
- Advanced filtering and search
- CSV/JSON export

## Deployment on Railway

### 1. Create New Telegram Bot

**CRITICAL: Do NOT reuse the same bot from Myhand!**

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Name it something like "OurHand Monitor" or "Israel Rentals Bot"
4. Save the token - this is your new `TELEGRAM_BOT_TOKEN`

### 2. Create New Railway Project

```bash
# Clone the repository
git clone https://github.com/avishaynaim/ourhand.git
cd ourhand

# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create NEW project (don't link to Myhand!)
railway init
```

### 3. Add PostgreSQL Database

1. Go to your Railway project dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Railway will automatically set `DATABASE_URL`

### 4. Set Environment Variables

```bash
# REQUIRED - New bot token from step 1!
railway variables set TELEGRAM_BOT_TOKEN=your_NEW_bot_token

# Your chat ID (same as Myhand is OK)
railway variables set TELEGRAM_CHAT_ID=your_chat_id

# Generate new API key
railway variables set API_KEY=$(openssl rand -hex 32)

# After deployment, set webhook URL
railway variables set TELEGRAM_WEBHOOK_URL=https://your-ourhand-app.up.railway.app
```

### 5. Deploy

```bash
railway up
```

### 6. Set Webhook

After deployment, set the Telegram webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_NEW_BOT_TOKEN>/setWebhook" \
  -d "url=https://your-ourhand-app.up.railway.app/telegram/webhook"
```

## Environment Variables

```bash
# ============================================
# OurHand - Full Israel Rentals Monitor
# ============================================

# REQUIRED - CREATE A NEW BOT for this project!
TELEGRAM_BOT_TOKEN=your_NEW_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id

# Webhook URL (must be different from Myhand!)
TELEGRAM_WEBHOOK_URL=https://yourourhand.up.railway.app

# Yad2 URL - All Israel rentals
YAD2_URL=https://www.yad2.co.il/realestate/rent

# Scraping intervals (more frequent)
MIN_INTERVAL_MINUTES=20
MAX_INTERVAL_MINUTES=40

# API Security
API_KEY=your_secret_key

# Web Dashboard
ENABLE_WEB=true
WEB_PORT=5000
```

## First Run Behavior

When the database has fewer than 5,000 apartments:

1. **Initial Full Scrape** starts automatically
2. Scrapes all 700+ pages (~29,000 apartments)
3. Uses faster delays (1-3s between pages)
4. Progress logged every 50 pages
5. Takes approximately 30-60 minutes
6. Startup message indicates initial scrape mode

After initial scrape:

1. **Monitoring Mode** activates
2. Checks every 20-40 minutes
3. Uses smart-stop (6 consecutive known = stop)
4. Typically processes only 5-15 pages per run

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome & registration |
| `/help` | Command reference |
| `/status` | System status |
| `/stats` | Market statistics |
| `/favorites` | View favorites |
| `/search [query]` | Search apartments |
| `/filter` | Manage filters |
| `/pause` | Pause notifications |
| `/resume` | Resume notifications |
| `/scrape` | Trigger immediate scan |
| `/dashboard` | Open web dashboard |
| `/analytics` | Market insights |

## API Endpoints

All endpoints require `X-API-Key` header.

- `GET /api/apartments` - List apartments with filters
- `GET /api/apartments/:id` - Get apartment details
- `GET /api/search?q=...` - Search apartments
- `GET /api/stats` - Overall statistics
- `GET /api/analytics` - Market analytics
- `GET /api/price-drops` - Recent price drops
- `GET /api/export/csv` - Export to CSV
- `GET /health` - Health check (no auth)

## Troubleshooting

### Initial scrape is slow
This is normal - 700+ pages takes time. Check logs for progress updates every 50 pages.

### Rate limiting / blocks
The system automatically adapts delays. If blocked, it waits and retries with longer delays.

### Bot not responding
Verify:
1. New bot token is set (not Myhand's token)
2. Webhook URL points to correct Railway deployment
3. Check webhook status: `curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"`

### Database issues
Ensure PostgreSQL is attached in Railway and `DATABASE_URL` is set.

## Technical Details

### Constants (constants.py)
```python
CONSECUTIVE_KNOWN_THRESHOLD = 6      # Stop after 6 known listings
MIN_RESULTS_FOR_REMOVAL = 1000       # Need 1000+ before marking removed
MAX_PAGES_FULL_SITE = 800            # Max pages for initial scrape
INITIAL_SCRAPE_PAGE_DELAY = (1, 3)   # Faster delays for initial
NORMAL_SCRAPE_PAGE_DELAY = (3, 8)    # Normal monitoring delays
```

### Auto-Detection
```python
INITIAL_SCRAPE_THRESHOLD = 5000  # If DB has <5000, do full scrape
```

## License

MIT License

## Related Projects

- [Myhand](https://github.com/avishaynaim/Myhand) - City-specific monitoring
