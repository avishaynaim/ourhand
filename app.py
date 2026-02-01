"""
Yad2 Real Estate Monitor - Enhanced Version
Features:
- SQLite persistent storage
- Price history tracking
- Proxy rotation
- Market analytics
- Web dashboard with REST API
- Telegram notifications with filters
- Daily summaries
- Smart pagination
- Adaptive delay management
"""
import requests
from bs4 import BeautifulSoup
import time
import json
import os
import re
import random
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from constants import (
    CONSECUTIVE_KNOWN_THRESHOLD, MIN_RESULTS_FOR_REMOVAL, MIN_PRICE, MAX_PRICE,
    MAX_PAGES_FULL_SITE, INITIAL_SCRAPE_PAGE_DELAY, NORMAL_SCRAPE_PAGE_DELAY
)
from concurrent.futures import ThreadPoolExecutor

# Import our modules
from db_wrapper import get_database
from proxy_manager import ProxyManager, ProxyRotator
from analytics import MarketAnalytics
from notifications import NotificationManager
from web import create_web_app, run_web_server

# Configure logging with environment variable support
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yad2_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_database_path():
    """
    Get the database path with persistent storage support.

    For Railway persistent storage:
    1. Add PostgreSQL database (free, persistent)
    2. Or add Volume mounted at /data
    """
    # Check for explicit environment variable
    db_path = os.environ.get('DATABASE_PATH')
    if db_path:
        return db_path

    # Check for persistent volume mount at /data
    data_dir = '/data'
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        db_file = os.path.join(data_dir, 'yad2_monitor.db')
        logger.info(f"✅ Using persistent storage: {db_file}")
        return db_file

    # Check if PostgreSQL is available (Railway provides DATABASE_URL)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        logger.warning(f"⚠️  DATABASE_URL detected but SQLite is being used")
        logger.warning(f"⚠️  For PostgreSQL support, database.py needs to be updated")
        logger.warning(f"⚠️  Currently using ephemeral SQLite - data will be lost on deploy!")

    # Default to current directory (EPHEMERAL on Railway!)
    db_file = 'yad2_monitor.db'
    if 'RAILWAY_ENVIRONMENT' in os.environ:
        logger.error(f"❌ USING EPHEMERAL STORAGE: {db_file}")
        logger.error(f"❌ DATA WILL BE DELETED ON EVERY DEPLOYMENT!")
        logger.error(f"❌ Add PostgreSQL in Railway dashboard to fix this!")
        logger.error(f"❌ Go to: https://railway.app → New → Database → PostgreSQL")
    else:
        logger.info(f"📁 Using local storage: {db_file}")

    return db_file


class AdaptiveDelayManager:
    """Analyzes historical scraping data and adapts delays to avoid blocks."""

    def __init__(self, database):
        self.db = database
        self.base_page_delay = NORMAL_SCRAPE_PAGE_DELAY  # (3, 8) seconds
        self.initial_page_delay = INITIAL_SCRAPE_PAGE_DELAY  # (1, 3) seconds for first full scrape
        self.base_cycle_delay = (20, 40)  # ~30 min avg, randomized to avoid patterns
        self.current_multiplier = 1.0
        self.initial_scrape_mode = False  # Fast mode for first full-site scrape
        self._load_strategy()

    def _load_strategy(self):
        """Load strategy from database"""
        multiplier = self.db.get_setting('delay_multiplier')
        if multiplier:
            self.current_multiplier = float(multiplier)

    def _save_strategy(self):
        """Save strategy to database"""
        self.db.set_setting('delay_multiplier', str(self.current_multiplier))

    def get_last_run_timestamp(self) -> Optional[int]:
        """Get timestamp of last successful run in milliseconds."""
        ts = self.db.get_setting('last_run_timestamp')
        return int(ts) if ts else None

    def set_last_run_timestamp(self, timestamp_ms: int):
        """Set timestamp of current run in milliseconds."""
        self.db.set_setting('last_run_timestamp', str(timestamp_ms))

    def log_event(self, event_type: str, details: Dict = None):
        """Log scraping event"""
        self.db.log_scrape_event(event_type, details)

        # Analyze and adapt on problems
        if event_type in ["rate_limit", "block"]:
            self.analyze_and_adapt()

    def analyze_and_adapt(self):
        """Analyze recent events and adapt strategy"""
        stats = self.db.get_scrape_stats(hours=24)

        total = sum(stats.values())
        if total < 5:
            return

        successes = stats.get('success', 0)
        blocks = stats.get('block', 0)
        rate_limits = stats.get('rate_limit', 0)

        success_rate = successes / total
        problem_rate = (blocks + rate_limits) / total

        logger.info(f"📊 Analysis - Last 24h: {total} events, {success_rate:.1%} success, {problem_rate:.1%} problems")

        old_multiplier = self.current_multiplier

        if problem_rate > 0.3:
            self.current_multiplier = min(5.0, self.current_multiplier * 1.5)
        elif problem_rate > 0.1:
            self.current_multiplier = min(3.0, self.current_multiplier * 1.2)
        elif problem_rate < 0.05 and success_rate > 0.9:
            self.current_multiplier = max(0.5, self.current_multiplier * 0.9)

        if old_multiplier != self.current_multiplier:
            logger.info(f"🔄 Strategy: multiplier {old_multiplier:.2f} → {self.current_multiplier:.2f}")
            self._save_strategy()

    def get_page_delay(self, initial_mode: bool = False) -> float:
        """Get adaptive page delay - faster in initial scrape mode"""
        if initial_mode or self.initial_scrape_mode:
            base_min, base_max = self.initial_page_delay
            # Add small random jitter
            return random.uniform(base_min, base_max) + random.uniform(0, 0.5)
        base_min, base_max = self.base_page_delay
        return random.uniform(
            base_min * self.current_multiplier,
            base_max * self.current_multiplier
        )

    def get_cycle_delay(self) -> int:
        """Get adaptive cycle delay in seconds with random jitter"""
        base_min, base_max = self.base_cycle_delay
        base = random.randint(
            int(base_min * self.current_multiplier * 60),
            int(base_max * self.current_multiplier * 60)
        )
        # Add ±20% random jitter so intervals are never predictable
        jitter = random.uniform(-0.2, 0.2) * base
        return max(600, int(base + jitter))  # minimum 10 minutes


class Yad2Monitor:
    """Main monitor class with all features integrated"""

    # Threshold: if DB has fewer apartments than this, do full initial scrape
    INITIAL_SCRAPE_THRESHOLD = 5000

    def __init__(self):
        logger.info("🚀 Initializing Enhanced Yad2Monitor (Full Israel Rentals)")

        # Initialize database with persistent storage support
        # get_database() auto-detects PostgreSQL (DATABASE_URL) or SQLite
        self.db = get_database()

        # Initialize components
        self.delay_manager = AdaptiveDelayManager(self.db)

        # Check if we need initial full scrape
        self.needs_initial_scrape = self._check_needs_initial_scrape()
        self.proxy_manager = ProxyManager()
        self.proxy_rotator = ProxyRotator(self.proxy_manager)
        self.analytics = MarketAnalytics(self.db)

        # Telegram bot for multi-user support
        telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        try:
            from telegram_bot import TelegramBot
            self.telegram_bot = TelegramBot(telegram_token, self.db)
            self.telegram_bot.scrape_callback = self.run_once_quick
            self.telegram_bot.dashboard_url = os.environ.get('TELEGRAM_WEBHOOK_URL', '')
            self.telegram_bot.set_my_commands()
            logger.info("✓ Telegram bot initialized (multi-user mode)")
        except Exception as e:
            logger.warning(f"Failed to initialize Telegram bot: {e}")
            self.telegram_bot = None

        self.notifier = NotificationManager(self.db, telegram_bot=self.telegram_bot)

        # Load search URLs
        self.search_urls = self._load_search_urls()

        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        ]

        # Web server thread
        self.web_thread = None

        if self.needs_initial_scrape:
            logger.info("⚠️ Database has < 5000 apartments - will perform FULL SITE SCRAPE on first run")
        logger.info("✅ Initialization complete")

    def _check_needs_initial_scrape(self) -> bool:
        """Check if we need to do a full initial scrape (DB is empty or very small)"""
        try:
            all_apts = self.db.get_all_apartments(active_only=False, limit=self.INITIAL_SCRAPE_THRESHOLD + 1)
            count = len(all_apts)
            logger.info(f"📊 Database has {count} apartments")
            return count < self.INITIAL_SCRAPE_THRESHOLD
        except Exception as e:
            logger.warning(f"Could not check apartment count: {e}")
            return True  # Assume we need initial scrape if can't check

    def _load_search_urls(self) -> List[Dict]:
        """Load search URLs from database or environment"""
        urls = self.db.get_search_urls()

        if not urls:
            # Default URL: ALL Israel rentals (700+ pages, 29K+ apartments)
            default_url = os.environ.get(
                "YAD2_URL",
                "https://www.yad2.co.il/realestate/rent"
            )
            url_id = self.db.add_search_url("All Israel Rentals", default_url)
            urls = [{'id': url_id, 'name': "All Israel Rentals", 'url': default_url}]

        logger.info(f"📋 Loaded {len(urls)} search URLs")
        return urls

    def get_headers(self) -> Dict:
        """Get request headers with random user agent"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

    def extract_price(self, text: str) -> Optional[int]:
        """Extract price from text with bounds checking"""
        if not text:
            return None
        text = text.replace(',', '').replace('₪', '').strip()
        numbers = re.findall(r'\d+', text)
        if numbers:
            price = int(max(numbers, key=int))
            # Bounds check using constants for reasonable prices
            if MIN_PRICE < price <= MAX_PRICE:
                return price
        return None

    def extract_data_updated_at_from_page(self, soup) -> List[int]:
        """Extract all dataUpdatedAt timestamps from page"""
        timestamps = []
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    matches = re.findall(r'"dataUpdatedAt"\s*:\s*(\d{13})', script.string)
                    for match in matches:
                        timestamps.append(int(match))
        except Exception as e:
            logger.debug(f"Error extracting timestamps: {e}")
        return timestamps

    def is_inside_yad1_listing(self, element) -> bool:
        """Check if element is inside Yad1 (promoted) listing"""
        parent = element.parent
        while parent:
            if parent.name == 'div' and parent.get('class'):
                classes = parent.get('class')
                if 'yad1-listing-data-content_yad1ListingDataContentBox__nWOxH' in classes:
                    return True
            parent = parent.parent
        return False

    def find_apartment_elements(self, soup) -> List:
        """Find valid apartment elements"""
        all_h2 = soup.find_all('h2', attrs={'data-nagish': 'content-section-title'})
        valid = [h2 for h2 in all_h2 if not self.is_inside_yad1_listing(h2)]
        return valid

    def get_apartment_container(self, h2_element):
        """Get the container element for an apartment"""
        parent = h2_element.parent
        depth = 0
        while parent and depth < 10:
            if parent.name in ['article', 'div']:
                if parent.find('a', href=True):
                    return parent
            parent = parent.parent
            depth += 1
        return h2_element.parent if h2_element.parent else h2_element

    def get_apartment_id(self, element) -> Optional[str]:
        """Extract apartment ID from element"""
        link = element.find('a', href=True)
        if link:
            href = link['href']
            m = re.search(r'/realestate/item/([A-Za-z0-9]+)', href)
            if m:
                return m.group(1)
        if element.get('data-id'):
            return element.get('data-id')
        import hashlib
        text_content = element.get_text(strip=True)
        return hashlib.md5(text_content.encode()).hexdigest()[:12]

    def parse_apartment(self, h2_element) -> Optional[Dict]:
        """Parse apartment data from HTML element"""
        try:
            container = self.get_apartment_container(h2_element)
            apt_id = self.get_apartment_id(container)

            if not apt_id:
                return None

            title = h2_element.get_text(strip=True)

            # Extract price
            price = None
            price_text = None
            price_elem = container.find('span', class_='feed-item-price_price__ygoeF')
            if not price_elem:
                price_elem = container.find('span', attrs={'data-testid': 'price'})
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self.extract_price(price_text)

            if not price:
                all_text = container.get_text()
                price = self.extract_price(all_text)

            # Extract link
            link = None
            link_elem = container.find('a', href=True)
            if link_elem:
                link = link_elem['href']
                if not link.startswith('http'):
                    link = f"https://www.yad2.co.il{link}"

            if not link or "/realestate/item/" not in link:
                return None

            # Extract address
            street_address = None
            street_elem = container.find('span', class_='item-data-content_heading__tphH4')
            if street_elem:
                street_address = street_elem.get_text(strip=True)

            # Extract item info (rooms, sqm, floor)
            item_info = None
            rooms = None
            sqm = None
            floor = None
            info_elem = container.find('span', class_='item-data-content_itemInfoLine__AeoPP')
            if info_elem:
                item_info = info_elem.get_text(strip=True)

            # Parse rooms/sqm/floor from item_info and title
            # Example HTML: "4 חדרים • קומה ‎7‏ • 215 מ״ר"
            # Separators: • (bullet), · (middle dot), | , comma
            # Numbers may have RTL/LTR marks: \u200e \u200f \u200b \u202a-\u202e
            for text_source in [item_info, title]:
                if not text_source:
                    continue
                # Strip Unicode directional marks so regex \d+ works
                clean = re.sub(r'[\u200e\u200f\u200b\u200c\u200d\u202a-\u202e\u2066-\u2069]', '', text_source)
                parts = re.split(r'[•·|,]', clean)
                for part in parts:
                    part = part.strip()
                    if not rooms and ('חדרים' in part or 'חדר' in part):
                        nums = re.findall(r'[\d.]+', part)
                        if nums:
                            rooms = float(nums[0])
                    if not sqm and ('מ"ר' in part or 'מ״ר' in part or 'מטר' in part):
                        nums = re.findall(r'\d+', part)
                        if nums:
                            sqm = int(nums[0])
                    if floor is None and 'קומה' in part:
                        nums = re.findall(r'\d+', part)
                        if nums:
                            floor = int(nums[0])
                    if floor is None and ('קומת קרקע' in part or 'קומת כניסה' in part):
                        floor = 0

            # Extract dataUpdatedAt
            data_updated_at = None
            container_str = str(container)
            match = re.search(r'"dataUpdatedAt"\s*:\s*(\d{13})', container_str)
            if match:
                data_updated_at = int(match.group(1))

            # Extract image URL
            image_url = None
            img_elem = container.find('img')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')

            return {
                'id': apt_id,
                'title': title or 'No title',
                'price': price,
                'price_text': price_text,
                'location': street_address,
                'street_address': street_address,
                'item_info': item_info,
                'rooms': rooms,
                'sqm': sqm,
                'floor': floor,
                'link': link,
                'image_url': image_url,
                'data_updated_at': data_updated_at,
                'last_seen': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error parsing apartment: {e}", exc_info=True)
            return None

    def fetch_page(self, url: str, page: int = 1, max_retries: int = 3, initial_mode: bool = False) -> Optional[str]:
        """Fetch a page with retry logic and proxy support"""
        for attempt in range(max_retries):
            try:
                delay = self.delay_manager.get_page_delay(initial_mode) * (attempt + 1)
                logger.info(f"⏳ Delay: {delay:.2f}s before page {page}")
                time.sleep(delay)

                if page > 1:
                    separator = '&' if '?' in url else '?'
                    page_url = f"{url}{separator}page={page}"
                else:
                    page_url = url

                logger.info(f"🌐 Fetching page {page}")

                # Use proxy if available
                if self.proxy_manager.proxies:
                    response = self.proxy_rotator.make_request(
                        page_url,
                        headers=self.get_headers(),
                        timeout=30
                    )
                else:
                    response = requests.get(
                        page_url,
                        headers=self.get_headers(),
                        timeout=30
                    )

                if response is None:
                    continue

                if response.status_code == 429:
                    self.delay_manager.log_event("rate_limit", {"page": page})
                    wait = 300 * (attempt + 1) * self.delay_manager.current_multiplier
                    logger.warning(f"⚠️ Rate limited! Waiting {wait // 60:.0f} minutes...")
                    time.sleep(wait)
                    continue

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    block_header = soup.find('h1', class_='title')

                    if block_header and "Are you for real" in block_header.get_text():
                        self.delay_manager.log_event("block", {"page": page, "type": "captcha"})
                        delay_seconds = random.randint(120, 300) * (attempt + 1)
                        logger.warning(f"🚫 Blocked! Waiting {delay_seconds // 60:.0f} minutes...")
                        time.sleep(delay_seconds)
                        continue

                    self.delay_manager.log_event("success", {"page": page})
                    logger.info(f"✅ Page {page} fetched successfully")
                    return response.text

                elif response.status_code >= 500:
                    self.delay_manager.log_event("error", {"page": page, "status": response.status_code})
                    continue

            except requests.exceptions.Timeout:
                self.delay_manager.log_event("timeout", {"page": page})
                continue
            except Exception as e:
                self.delay_manager.log_event("error", {"page": page, "exception": str(e)})
                if attempt < max_retries - 1:
                    continue
                return None

        return None

    def _fetch_page_for_batch(self, args: Tuple[str, int]) -> Tuple[int, List[Dict]]:
        """Fetch a single page and parse apartments - for concurrent use"""
        base_url, page = args
        apartments = []
        try:
            # Random delay to avoid pattern detection
            delay = random.uniform(0.5, 2.0)
            time.sleep(delay)

            if page > 1:
                separator = '&' if '?' in base_url else '?'
                page_url = f"{base_url}{separator}page={page}"
            else:
                page_url = base_url

            response = requests.get(page_url, headers=self.get_headers(), timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                h2_elements = self.find_apartment_elements(soup)

                for h2_elem in h2_elements:
                    apt = self.parse_apartment(h2_elem)
                    if apt and apt['price'] and apt['link']:
                        apartments.append(apt)

        except Exception as e:
            logger.debug(f"Error fetching page {page}: {e}")

        return page, apartments

    def scrape_full_site(self, base_url: str, max_pages: int = MAX_PAGES_FULL_SITE) -> Tuple[List[Dict], int]:
        """
        INITIAL SCRAPE: Scrape ALL pages with CONCURRENT requests.
        Saves to DB every 1000 apartments to avoid data loss on crash.
        """
        logger.info(f"🚀 INITIAL FULL SITE SCRAPE - PARALLEL MODE")
        logger.info(f"🔗 URL: {base_url}")
        logger.info(f"📄 Max pages: {max_pages}")

        self.delay_manager.initial_scrape_mode = True
        current_run_ts = int(datetime.now().timestamp() * 1000)
        pending_apartments = []  # Buffer for periodic saves
        total_saved = 0
        start_time = datetime.now()

        # Settings
        BATCH_SIZE = 5  # Pages per batch
        MAX_WORKERS = 5  # Concurrent requests
        SAVE_THRESHOLD = 1000  # Save to DB every N apartments
        consecutive_empty_batches = 0

        page = 1
        while page <= max_pages:
            # Create batch of pages to fetch
            batch_pages = list(range(page, min(page + BATCH_SIZE, max_pages + 1)))
            batch_args = [(base_url, p) for p in batch_pages]

            # Fetch batch concurrently
            batch_apartments = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                results = list(executor.map(self._fetch_page_for_batch, batch_args))

            # Collect results
            pages_with_data = 0
            for page_num, apts in results:
                if apts:
                    batch_apartments.extend(apts)
                    pages_with_data += 1

            pending_apartments.extend(batch_apartments)

            # Check for end of data
            if pages_with_data == 0:
                consecutive_empty_batches += 1
                if consecutive_empty_batches >= 2:
                    logger.info(f"🛑 2 consecutive empty batches - reached end at page {page}")
                    break
            else:
                consecutive_empty_batches = 0

            # PERIODIC SAVE - save every 1000 apartments
            if len(pending_apartments) >= SAVE_THRESHOLD:
                try:
                    saved = self.db.batch_upsert_apartments(pending_apartments)
                    total_saved += saved
                    logger.info(f"💾 SAVED {saved} apartments to DB (total saved: {total_saved})")
                    pending_apartments = []  # Clear buffer
                except Exception as e:
                    logger.error(f"❌ Periodic save failed: {e}")

            # Progress update
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            total_found = total_saved + len(pending_apartments)
            rate = total_found / max(elapsed, 0.1)
            logger.info(f"📊 Pages {batch_pages[0]}-{batch_pages[-1]}: +{len(batch_apartments)} | Found: {total_found} | Saved: {total_saved} | {elapsed:.1f}min | {rate:.0f}/min")

            page += BATCH_SIZE

            # Random delay between batches to avoid detection
            batch_delay = random.uniform(2, 5)
            time.sleep(batch_delay)

        # Save remaining apartments
        if pending_apartments:
            try:
                saved = self.db.batch_upsert_apartments(pending_apartments)
                total_saved += saved
                logger.info(f"💾 FINAL SAVE: {saved} apartments (total: {total_saved})")
            except Exception as e:
                logger.error(f"❌ Final save failed: {e}")

        self.delay_manager.initial_scrape_mode = False
        self.delay_manager.set_last_run_timestamp(current_run_ts)

        elapsed = (datetime.now() - start_time).total_seconds() / 60
        logger.info(f"{'=' * 60}")
        logger.info(f"✅ INITIAL SCRAPE COMPLETE!")
        logger.info(f"📊 Total saved: {total_saved} apartments in {elapsed:.1f} minutes")
        logger.info(f"{'=' * 60}")

        # Return empty list since we already saved everything
        return [], 0

    def scrape_all_pages(self, base_url: str, max_pages: int = 20) -> Tuple[List[Dict], int]:
        """
        MONITORING SCRAPE: Check first few pages until consecutive known apartments found.
        Used after initial scrape is complete.
        """
        logger.info(f"🔍 Starting monitoring scrape from {base_url}")

        current_run_ts = int(datetime.now().timestamp() * 1000)
        all_apartments = []
        pages_saved = 0
        page = 1
        consecutive_known = 0

        logger.info(f"📊 Stop strategy: Will stop after {CONSECUTIVE_KNOWN_THRESHOLD} consecutive known listings")

        while page <= max_pages:
            if page <= 5 or page % 10 == 0:
                logger.info(f"📄 Page {page} (consecutive known: {consecutive_known}/{CONSECUTIVE_KNOWN_THRESHOLD})")

            html = self.fetch_page(base_url, page)
            if not html:
                break

            soup = BeautifulSoup(html, 'html.parser')
            h2_elements = self.find_apartment_elements(soup)
            if not h2_elements:
                break

            parsed_count = 0
            new_on_page = 0
            known_on_page = 0

            for h2_elem in h2_elements:
                apt = self.parse_apartment(h2_elem)
                if apt and apt['price'] and apt['link']:
                    all_apartments.append(apt)
                    parsed_count += 1

                    # Check if apartment already exists in database
                    existing = self.db.get_apartment(apt['id'])
                    if existing:
                        # Known listing
                        consecutive_known += 1
                        known_on_page += 1

                        # Check if we've hit the threshold
                        if consecutive_known >= CONSECUTIVE_KNOWN_THRESHOLD:
                            pages_saved = max_pages - page
                            logger.info(f"🛑 Smart stop: {consecutive_known} consecutive known listings reached!")
                            logger.info(f"💾 Saved approximately {pages_saved} page requests!")
                            self.delay_manager.set_last_run_timestamp(current_run_ts)
                            logger.info(f"✅ Monitoring complete: {len(all_apartments)} apartments from {page} pages")
                            return all_apartments, pages_saved
                    else:
                        # New listing - reset counter
                        consecutive_known = 0
                        new_on_page += 1

            logger.info(f"✅ Page {page}: {parsed_count} apartments ({new_on_page} new, {known_on_page} known)")
            page += 1

        # Update last run timestamp
        self.delay_manager.set_last_run_timestamp(current_run_ts)

        logger.info(f"{'=' * 50}")
        logger.info(f"✅ Scraping complete: {len(all_apartments)} apartments from {page - 1} pages")
        if pages_saved > 0:
            logger.info(f"💾 Pages saved: {pages_saved}")

        return all_apartments, pages_saved

    def process_apartments_batch(self, apartments: List[Dict]) -> int:
        """
        BATCH SAVE for initial scrape - no change detection, just save all.
        Much faster for 29K+ apartments.
        """
        if not apartments:
            return 0

        logger.info(f"💾 Batch saving {len(apartments)} apartments...")
        try:
            count = self.db.batch_upsert_apartments(apartments)
            logger.info(f"✅ Saved {count} apartments to database")

            # Update daily summary
            self.db.update_daily_summary(new_apts=count, price_drops=0, price_increases=0, removed=0)

            return count
        except Exception as e:
            logger.error(f"❌ BATCH SAVE FAILED: {e}", exc_info=True)
            # Try individual saves as fallback
            logger.info("⚠️ Attempting individual saves as fallback...")
            saved = 0
            for apt in apartments:
                try:
                    self.db.upsert_apartment(apt)
                    saved += 1
                    if saved % 100 == 0:
                        logger.info(f"💾 Individual save progress: {saved}/{len(apartments)}")
                except Exception as e2:
                    logger.error(f"Failed to save apartment {apt.get('id')}: {e2}")
            logger.info(f"✅ Individual saves complete: {saved}/{len(apartments)}")
            return saved

    def process_apartments(self, apartments: List[Dict]) -> Tuple[List[Dict], List[Dict], List[str]]:
        """Process apartments and detect changes"""
        new_apartments = []
        price_changes = []
        active_ids = set()

        for apt in apartments:
            apt_id = apt['id']
            active_ids.add(apt_id)

            # Read existing apartment BEFORE upsert to detect price changes
            existing = self.db.get_apartment(apt_id)

            # Save to database
            _, is_new = self.db.upsert_apartment(apt)

            if is_new:
                new_apartments.append(apt)
                logger.info(f"🆕 New: {apt_id} - {apt['title'][:40]}")
            elif existing and existing.get('price') != apt.get('price'):
                # Check for price change using pre-upsert data
                old_price = existing['price']
                new_price = apt['price']
                if old_price and new_price:
                    change = new_price - old_price
                    change_pct = (change / old_price) * 100
                    price_changes.append({
                        'apartment': apt,
                        'old_price': old_price,
                        'new_price': new_price,
                        'change': change,
                        'change_pct': change_pct
                    })
                    logger.info(f"💰 Price change: {apt_id} ₪{old_price:,} → ₪{new_price:,}")

        # Mark inactive apartments - but only if we found enough results
        # to avoid false removals when scrape is incomplete
        removed = []
        if len(apartments) >= MIN_RESULTS_FOR_REMOVAL:
            removed = self.db.mark_apartments_inactive(active_ids)
        else:
            logger.warning(f"⚠️ Only {len(apartments)} apartments found - skipping removal to avoid false positives (need {MIN_RESULTS_FOR_REMOVAL}+)")

        # Update daily summary
        price_drops = len([p for p in price_changes if p['change'] < 0])
        price_increases = len([p for p in price_changes if p['change'] > 0])
        self.db.update_daily_summary(
            new_apts=len(new_apartments),
            price_drops=price_drops,
            price_increases=price_increases,
            removed=len(removed)
        )

        logger.info(f"📊 Summary - New: {len(new_apartments)}, Price changes: {len(price_changes)}, Removed: {len(removed)}")

        return new_apartments, price_changes, removed

    def send_notifications(self, new_apartments: List[Dict], price_changes: List[Dict]):
        """Send notifications for changes"""
        for apt in new_apartments:
            self.notifier.notify_new_apartment(apt)

        for change in price_changes:
            self.notifier.notify_price_change(
                change['apartment'],
                change['old_price'],
                change['new_price']
            )

    def start_web_server(self, port: int = 5000):
        """Start web server in background thread"""
        def run():
            run_web_server(self.db, self.analytics, self.telegram_bot, port=port, debug=False)

        self.web_thread = threading.Thread(target=run, daemon=True)
        self.web_thread.start()
        logger.info(f"🌐 Web server started on port {port}")

        # Set Telegram webhook if bot is configured
        if self.telegram_bot:
            webhook_url = os.environ.get('TELEGRAM_WEBHOOK_URL')
            if webhook_url:
                try:
                    success = self.telegram_bot.set_webhook(f"{webhook_url}/telegram/webhook")
                    if success:
                        logger.info(f"✓ Telegram webhook set: {webhook_url}/telegram/webhook")
                    else:
                        logger.warning("Failed to set Telegram webhook")
                except Exception as e:
                    logger.error(f"Error setting Telegram webhook: {e}", exc_info=True)
            else:
                logger.info("TELEGRAM_WEBHOOK_URL not set - webhook not configured (use polling or set webhook manually)")

    def run_once(self):
        """Run a single scrape cycle"""
        all_new = []
        all_changes = []

        for search in self.search_urls:
            logger.info(f"📋 Scraping: {search['name']}")

            # Choose scraping method based on initial scrape need
            if self.needs_initial_scrape:
                logger.info("🚀 Running INITIAL FULL SITE SCRAPE (parallel mode)...")
                # scrape_full_site saves directly to DB every 1000 apartments
                self.scrape_full_site(search['url'])

                # Switch to monitoring mode
                self.needs_initial_scrape = False
                logger.info("🔄 Switching to monitoring mode for future runs")

                # Update search URL last scraped
                self.db.update_search_url_scraped(search['id'])
            else:
                # Normal monitoring scrape with smart-stop
                apartments, pages_saved = self.scrape_all_pages(search['url'])

                if apartments:
                    new_apts, price_changes, _ = self.process_apartments(apartments)
                    all_new.extend(new_apts)
                    all_changes.extend(price_changes)

                    # Update search URL last scraped
                    self.db.update_search_url_scraped(search['id'])

        if all_new or all_changes:
            self.send_notifications(all_new, all_changes)

        # Check for daily digest time
        self.notifier.check_daily_digest_time()

        return len(all_new), len(all_changes)

    def run_once_quick(self):
        """Run a single scrape cycle - first page only (for /scrape command).
        Returns (apartments, debug_info) without DB changes."""
        all_apartments = []
        debug_info = {'page_size': 0, 'h2_total': 0, 'h2_valid': 0, 'parsed': 0, 'rejected': 0}

        for search in self.search_urls:
            logger.info(f"📋 Quick scraping (page 1 only): {search['name']}")
            html = self.fetch_page(search['url'], 1)
            if not html:
                continue

            debug_info['page_size'] = len(html)
            soup = BeautifulSoup(html, 'html.parser')

            all_h2 = soup.find_all('h2', attrs={'data-nagish': 'content-section-title'})
            debug_info['h2_total'] = len(all_h2)

            valid_h2 = [h2 for h2 in all_h2 if not self.is_inside_yad1_listing(h2)]
            debug_info['h2_valid'] = len(valid_h2)

            for h2 in valid_h2:
                apt = self.parse_apartment(h2)
                if apt and apt['price'] and apt['link']:
                    all_apartments.append(apt)
                    debug_info['parsed'] += 1
                else:
                    debug_info['rejected'] += 1

        return all_apartments, debug_info

    def monitor(self):
        """Main monitoring loop"""
        logger.info("=" * 80)
        logger.info("🚀 Starting Yad2 Monitor - Enhanced Edition")
        logger.info("=" * 80)

        # Start web server (Railway sets PORT automatically)
        web_port = int(os.environ.get('PORT', os.environ.get('WEB_PORT', 5000)))
        enable_web = os.environ.get('ENABLE_WEB', 'true').lower() == 'true'
        if enable_web:
            self.start_web_server(web_port)

        # Send startup notification
        startup_info = {
            'min_interval': int(os.environ.get('MIN_INTERVAL_MINUTES', 20)),
            'max_interval': int(os.environ.get('MAX_INTERVAL_MINUTES', 40))
        }
        if self.needs_initial_scrape:
            startup_info['initial_scrape'] = True
            logger.info("⚠️ INITIAL FULL SITE SCRAPE WILL RUN - This may take 30-60 minutes")
        self.notifier.send_startup_message(startup_info)

        iteration = 0

        while True:
            try:
                iteration += 1
                logger.info("=" * 80)
                logger.info(f"🔄 ITERATION {iteration} - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                logger.info("=" * 80)

                new_count, change_count = self.run_once()

                logger.info(f"✅ Cycle complete - New: {new_count}, Changes: {change_count}")

                # Status report every 10 iterations
                if iteration % 10 == 0:
                    stats = self.db.get_scrape_stats(hours=24)
                    self.notifier.send_status_report(stats, self.delay_manager.current_multiplier)

                # Wait for next cycle
                interval = self.delay_manager.get_cycle_delay()
                next_check = datetime.now() + timedelta(seconds=interval)
                logger.info(f"⏰ Next check: {next_check.strftime('%H:%M:%S')}")
                logger.info(f"😴 Sleeping {interval // 60} minutes...")

                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("🛑 Stopping monitor...")
                self.notifier.send_telegram_message("🛑 <b>Yad2 Monitor Stopped</b>")
                break
            except Exception as e:
                logger.error(f"❌ Error: {e}", exc_info=True)
                self.delay_manager.log_event("error", {"type": "monitor_loop", "exception": str(e)})
                self.notifier.send_error_alert(str(e), "Monitor loop")
                time.sleep(300)


def main():
    """Main entry point"""
    logger.info("🚀 Starting Yad2 Monitor - Enhanced Edition")

    # Validate environment
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        logger.error("❌ TELEGRAM_BOT_TOKEN required")
        exit(1)
    if not os.environ.get("TELEGRAM_CHAT_ID"):
        logger.error("❌ TELEGRAM_CHAT_ID required")
        exit(1)

    monitor = Yad2Monitor()
    monitor.monitor()


if __name__ == "__main__":
    main()
