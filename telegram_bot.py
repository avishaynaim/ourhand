"""
Telegram Bot Module for Yad2 Monitor
Handles webhook, commands, and inline keyboard interactions
"""
import os
import json
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for multi-user apartment monitoring"""

    def __init__(self, token: str, database):
        # Validate token format (numeric_id:alphanumeric_string)
        if not token or not isinstance(token, str) or ':' not in token:
            raise ValueError("Invalid Telegram bot token format")
        self._token = token  # Private - never log this
        self.db = database
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.scrape_callback = None  # Set by monitor to allow /scrape command
        self.dashboard_url = None  # Set by monitor from TELEGRAM_WEBHOOK_URL

    def _mask_token_in_url(self, url: str) -> str:
        """Mask token in URL for safe logging"""
        if self._token and self._token in url:
            return url.replace(self._token, "***TOKEN***")
        return url

    def set_my_commands(self) -> bool:
        """Register bot commands so they appear in Telegram's menu"""
        try:
            url = f"{self.base_url}/setMyCommands"
            commands = [
                {"command": "start", "description": "התחלה והרשמה"},
                {"command": "help", "description": "מדריך שימוש"},
                {"command": "subscribe", "description": "הרשמה לכתובת יד2"},
                {"command": "unsubscribe", "description": "הסרת כתובת מעקב"},
                {"command": "myurls", "description": "הצג כתובות מעקב"},
                {"command": "status", "description": "סטטוס המערכת והמשתמש"},
                {"command": "stats", "description": "סטטיסטיקות שוק"},
                {"command": "favorites", "description": "הצג מועדפים"},
                {"command": "search", "description": "חיפוש דירות"},
                {"command": "filter", "description": "ניהול פילטרים"},
                {"command": "pause", "description": "השהה התראות"},
                {"command": "resume", "description": "חידוש התראות"},
                {"command": "scrape", "description": "סריקה מיידית של יד2"},
                {"command": "dashboard", "description": "פתח את לוח הבקרה"},
                {"command": "analytics", "description": "תובנות שוק"},
            ]
            response = requests.post(url, json={"commands": commands}, timeout=10)
            result = response.json()
            if result.get('ok'):
                logger.info("✓ Bot commands registered with Telegram")
                return True
            else:
                logger.error(f"Failed to set commands: {result}")
                return False
        except Exception as e:
            logger.error(f"Error setting commands: {e}", exc_info=True)
            return False

    def set_webhook(self, webhook_url: str) -> bool:
        """Set the webhook URL for receiving updates"""
        try:
            url = f"{self.base_url}/setWebhook"
            data = {
                'url': webhook_url,
                'allowed_updates': ['message', 'callback_query']
            }
            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get('ok'):
                logger.info(f"Webhook set successfully: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result}")
                return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}", exc_info=True)
            return False

    def send_message(self, chat_id: str, text: str, parse_mode: str = 'HTML',
                    reply_markup: Optional[Dict] = None) -> bool:
        """Send a text message to a chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            if reply_markup:
                data['reply_markup'] = reply_markup

            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if not result.get('ok'):
                logger.error(f"Failed to send message: {result}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            return False

    def answer_callback_query(self, callback_query_id: str, text: str = None,
                              show_alert: bool = False) -> bool:
        """Answer a callback query from inline keyboard"""
        try:
            url = f"{self.base_url}/answerCallbackQuery"
            data = {'callback_query_id': callback_query_id}
            if text:
                data['text'] = text
            data['show_alert'] = show_alert

            response = requests.post(url, json=data, timeout=10)
            return response.json().get('ok', False)
        except Exception as e:
            logger.error(f"Error answering callback: {e}", exc_info=True)
            return False

    def handle_webhook(self, update: Dict) -> Dict:
        """
        Handle incoming webhook update from Telegram.
        Returns response for Flask endpoint.
        """
        try:
            # Handle callback query (inline button clicks)
            if 'callback_query' in update:
                return self.handle_callback_query(update['callback_query'])

            # Handle regular messages
            if 'message' in update:
                message = update['message']
                chat_id = str(message['chat']['id'])

                # Register/update user
                self._register_user(message)

                # Handle commands
                if 'text' in message and message['text'].startswith('/'):
                    return self.handle_command(message)

                # Handle regular text messages
                return self.handle_text_message(message)

            return {'status': 'ok', 'message': 'Update received'}

        except Exception as e:
            logger.error(f"Error handling webhook: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def _register_user(self, message: Dict):
        """Register or update user from message"""
        chat = message['chat']
        user = message.get('from', chat)

        try:
            self.db.add_or_update_user(
                chat_id=str(chat['id']),
                username=user.get('username'),
                first_name=user.get('first_name'),
                last_name=user.get('last_name'),
                language_code=user.get('language_code', 'he')
            )
        except TypeError:
            # PostgreSQL version doesn't accept language_code
            self.db.add_or_update_user(
                chat_id=str(chat['id']),
                username=user.get('username'),
                first_name=user.get('first_name'),
                last_name=user.get('last_name')
            )

    def handle_command(self, message: Dict) -> Dict:
        """Route command to appropriate handler"""
        chat_id = str(message.get('chat', {}).get('id', ''))
        if not chat_id:
            return {'status': 'error', 'message': 'Invalid chat ID'}

        text = message.get('text', '')
        if not text or not isinstance(text, str):
            return {'status': 'error', 'message': 'Invalid message text'}

        # Limit text length to prevent abuse
        text = text[:500]
        command_parts = text.split(maxsplit=10)  # Limit number of arguments
        command = command_parts[0].lower() if command_parts else ''
        args = command_parts[1:] if len(command_parts) > 1 else []

        # Command routing
        command_handlers = {
            '/start': self.cmd_start,
            '/help': self.cmd_help,
            '/subscribe': self.cmd_subscribe,
            '/unsubscribe': self.cmd_unsubscribe,
            '/myurls': self.cmd_myurls,
            '/status': self.cmd_status,
            '/stats': self.cmd_stats,
            '/favorites': self.cmd_favorites,
            '/search': self.cmd_search,
            '/filter': self.cmd_filter,
            '/pause': self.cmd_pause,
            '/resume': self.cmd_resume,
            '/analytics': self.cmd_analytics,
            '/scrape': self.cmd_scrape,
            '/dashboard': self.cmd_dashboard,
        }

        handler = command_handlers.get(command)
        if handler:
            handler(chat_id, args)
        else:
            self.send_message(chat_id,
                f"פקודה לא מוכרת: {command}\nשלח /help לרשימת הפקודות")

        return {'status': 'ok', 'command': command}

    def cmd_start(self, chat_id: str, args: List[str]):
        """Handle /start command"""
        user = self.db.get_user(chat_id)
        name = user.get('first_name', 'משתמש') if user else 'משתמש'

        text = f"""
🏠 <b>ברוך הבא ל-OurHand Monitor, {name}!</b>

אני אעזור לך למצוא את הדירה המושלמת ביד2.
כדי להתחיל, שלח לי כתובת חיפוש מיד2 עם הפקודה /subscribe

<b>🚀 התחל כאן:</b>
/subscribe [כתובת יד2] - הרשמה למעקב
/myurls - הצג כתובות מעקב

<b>📋 פקודות נוספות:</b>
/status - סטטוס המערכת והמשתמש
/favorites - הצג מועדפים
/search [טקסט] - חיפוש דירות
/filter - ניהול פילטרים
/pause - השהה התראות
/resume - חידוש התראות
/scrape - סריקה מיידית
/help - עזרה

💡 <b>טיפ:</b> חפש ביד2, העתק את הכתובת ושלח:
<code>/subscribe https://www.yad2.co.il/realestate/rent/tel-aviv-area</code>
"""
        if self.dashboard_url:
            text += f'\n🖥️ <a href="{self.dashboard_url}">פתח את לוח הבקרה</a>'
        self.send_message(chat_id, text)

    def cmd_subscribe(self, chat_id: str, args: List[str]):
        """Handle /subscribe command - subscribe to a Yad2 URL"""
        if not args:
            self.send_message(chat_id,
                "🔗 <b>הרשמה למעקב כתובת יד2</b>\n\n"
                "שלח את כתובת החיפוש מיד2:\n"
                "<code>/subscribe https://www.yad2.co.il/realestate/rent/...</code>\n\n"
                "💡 <b>איך למצוא כתובת?</b>\n"
                "1. חפש ביד2 עם הפילטרים שאתה רוצה\n"
                "2. העתק את הכתובת מהדפדפן\n"
                "3. שלח אותה כאן עם /subscribe")
            return

        url = args[0].strip()

        # Validate URL
        if 'yad2.co.il' not in url:
            self.send_message(chat_id,
                "❌ כתובת לא תקינה.\n"
                "הכתובת חייבת להיות מיד2, לדוגמה:\n"
                "<code>/subscribe https://www.yad2.co.il/realestate/rent/tel-aviv-area</code>")
            return

        # Ensure URL starts with https
        if not url.startswith('http'):
            url = 'https://' + url

        # Extract a friendly name from the URL
        name = url.split('/')[-1] if '/' in url else 'yad2'
        # Clean up query params from name
        if '?' in name:
            name = name.split('?')[0]
        if not name or name == 'rent':
            name = 'All Israel'

        try:
            url_id = self.db.add_user_search_url(chat_id, name, url)
            if url_id:
                user_urls = self.db.get_user_search_urls(chat_id)
                self.send_message(chat_id,
                    f"✅ <b>נרשמת בהצלחה!</b>\n\n"
                    f"📍 <b>שם:</b> {name}\n"
                    f"🔗 <b>כתובת:</b> {url}\n\n"
                    f"📋 סה\"כ כתובות מעקב: {len(user_urls)}\n\n"
                    f"הסריקה הבאה תכלול את הכתובת הזו.\n"
                    f"לצפייה בכתובות: /myurls")
            else:
                self.send_message(chat_id, "❌ שגיאה בהוספת הכתובת")
        except Exception as e:
            logger.error(f"Error in cmd_subscribe: {e}", exc_info=True)
            self.send_message(chat_id, "❌ שגיאה בהוספת הכתובת")

    def cmd_unsubscribe(self, chat_id: str, args: List[str]):
        """Handle /unsubscribe command - remove a monitored URL"""
        user_urls = self.db.get_user_search_urls(chat_id)

        if not user_urls:
            self.send_message(chat_id,
                "אין לך כתובות מעקב 🤷‍♂️\n"
                "הוסף כתובת עם /subscribe")
            return

        if args:
            # Try to parse URL ID from args
            try:
                url_id = int(args[0])
                success = self.db.remove_user_search_url(chat_id, url_id)
                if success:
                    self.send_message(chat_id, "✅ הכתובת הוסרה בהצלחה!")
                else:
                    self.send_message(chat_id, "❌ כתובת לא נמצאה")
            except ValueError:
                self.send_message(chat_id,
                    "❌ שלח מספר כתובת להסרה.\n"
                    "לדוגמה: <code>/unsubscribe 1</code>\n\n"
                    "השתמש ב-/myurls לצפייה במספרי הכתובות")
            return

        # Show URLs with IDs for removal
        text = "🗑️ <b>הסרת כתובת מעקב</b>\n\n"
        text += "שלח <code>/unsubscribe [מספר]</code> להסרה:\n\n"

        for u in user_urls:
            text += f"<b>{u['id']}</b> - {u['name']}\n"
            text += f"   🔗 {u['url'][:60]}...\n\n"

        self.send_message(chat_id, text)

    def cmd_myurls(self, chat_id: str, args: List[str]):
        """Handle /myurls command - list monitored URLs"""
        user_urls = self.db.get_user_search_urls(chat_id)

        if not user_urls:
            self.send_message(chat_id,
                "📋 <b>אין לך כתובות מעקב</b>\n\n"
                "הוסף כתובת עם:\n"
                "<code>/subscribe https://www.yad2.co.il/realestate/rent/...</code>")
            return

        text = f"📋 <b>כתובות המעקב שלך</b> ({len(user_urls)})\n\n"

        for u in user_urls:
            last_scraped = str(u['last_scraped'])[:16] if u.get('last_scraped') else 'טרם נסרק'
            needs_initial = u.get('needs_initial_scrape', True)
            status = "🔄 ממתין לסריקה ראשונית" if needs_initial else f"✅ נסרק: {last_scraped}"

            text += f"<b>{u['id']}. {u['name']}</b>\n"
            text += f"   🔗 {u['url'][:60]}{'...' if len(u['url']) > 60 else ''}\n"
            text += f"   {status}\n\n"

        text += "להסרת כתובת: /unsubscribe [מספר]\nלהוספת כתובת: /subscribe [כתובת]"
        self.send_message(chat_id, text)

    def cmd_help(self, chat_id: str, args: List[str]):
        """Handle /help command"""
        text = """
📖 <b>מדריך שימוש - OurHand Monitor</b>

<b>🔗 מעקב כתובות:</b>
/subscribe [כתובת יד2] - הרשמה למעקב אחרי כתובת
/unsubscribe - הסרת כתובת מעקב
/myurls - הצג כתובות מעקב פעילות

<b>פקודות בסיסיות:</b>
/start - התחלה והרשמה
/help - מדריך זה
/status - סטטוס המערכת שלך

<b>חיפוש ומעקב:</b>
/search תל אביב 3 חדרים - חיפוש דירות
/favorites - רשימת המועדפים שלך
/filter - הגדרת פילטרים אישיים

<b>סטטיסטיקות:</b>
/stats - סטטיסטיקות שוק כלליות
/analytics - ניתוח מעמיק של השוק

<b>ניהול התראות:</b>
/pause - השהה התראות זמנית
/resume - חידוש התראות

<b>סריקה:</b>
/scrape - הפעל סריקה מיידית של יד2

<b>💡 דוגמאות שימוש:</b>
• <code>/subscribe https://www.yad2.co.il/realestate/rent/tel-aviv-area</code>
• <code>/search רמת גן</code> - חיפוש בעיר
• לחיצה על ⭐ בהתראה - הוספה למועדפים

<b>🔔 התראות אוטומטיות:</b>
תקבל התראות על:
• דירות חדשות שמתאימות לפילטרים שלך
• ירידות מחיר משמעותיות
• דירות שחזרו לשוק

זקוק לעזרה? צור קשר עם המפתח.
"""
        if self.dashboard_url:
            text += f'\n🖥️ <a href="{self.dashboard_url}">פתח את לוח הבקרה</a>'
        self.send_message(chat_id, text)

    def cmd_status(self, chat_id: str, args: List[str]):
        """Handle /status command"""
        user = self.db.get_user(chat_id)
        prefs = self.db.get_user_preferences(chat_id)
        favorites_count = len(self.db.get_user_favorites(chat_id))
        filters = self.db.get_user_filters(chat_id, active_only=True)

        is_paused = user.get('is_paused') if user else False
        status_emoji = "⏸️" if is_paused else "✅"
        status_text = "מושהה" if is_paused else "פעיל"

        # Safely extract dates with fallbacks
        created_at = 'לא ידוע'
        last_interaction = 'עכשיו'
        if user:
            if user.get('created_at'):
                created_at = str(user['created_at'])[:10]
            if user.get('last_interaction'):
                last_interaction = str(user['last_interaction'])[:16]

        text = f"""
👤 <b>סטטוס המשתמש</b>

{status_emoji} <b>סטטוס:</b> {status_text}
⭐ <b>מועדפים:</b> {favorites_count} דירות
🔍 <b>פילטרים פעילים:</b> {len(filters)}

<b>🔔 הגדרות התראות:</b>
• התראות מיידיות: {'✓' if prefs.get('instant_notifications') else '✗'}
• דייג'סט יומי: {'✓' if prefs.get('daily_digest') else '✗'}
• שעת דייג'סט: {prefs.get('digest_hour', 20)}:00

<b>📊 מידע כללי:</b>
• תאריך הצטרפות: {created_at}
• אינטראקציה אחרונה: {last_interaction}

להשהיית התראות: /pause
לחידוש התראות: /resume
"""
        if self.dashboard_url:
            text += f'\n🖥️ <a href="{self.dashboard_url}">פתח את לוח הבקרה</a>'
        self.send_message(chat_id, text)

    def cmd_stats(self, chat_id: str, args: List[str]):
        """Handle /stats command"""
        try:
            # Get overall stats
            all_apts = self.db.get_all_apartments(active_only=True)
            total = len(all_apts)

            if total == 0:
                self.send_message(chat_id, "אין דירות במעקב כרגע 🤷‍♂️")
                return

            prices = [apt['price'] for apt in all_apts if apt.get('price')]
            avg_price = sum(prices) // len(prices) if prices else 0

            # Get recent stats
            today_str = datetime.now().strftime('%Y-%m-%d')
            recent_apts = [apt for apt in all_apts if str(apt.get('first_seen', ''))[:10] == today_str]
            new_today = len(recent_apts)

            # Safe min/max with fallbacks for empty list
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0

            text = f"""
📊 <b>סטטיסטיקות שוק - OurHand</b>
🇮🇱 <b>כל ישראל</b>

<b>🏢 דירות במעקב:</b>
• סה"כ דירות פעילות: {total:,}
• חדשות היום: {new_today}

<b>💰 מחירים:</b>
• מחיר ממוצע: ₪{avg_price:,}
• מחיר נמוך ביותר: ₪{min_price:,}
• מחיר גבוה ביותר: ₪{max_price:,}

<b>🔥 ערים פופולריות:</b>
"""
            # Top cities
            cities = {}
            for apt in all_apts:
                city = apt.get('city', 'לא ידוע')
                cities[city] = cities.get(city, 0) + 1

            top_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]
            for city, count in top_cities:
                text += f"• {city}: {count} דירות\n"

            text += "\nלניתוח מפורט: /analytics"

            self.send_message(chat_id, text)
        except Exception as e:
            logger.error(f"Error in cmd_stats: {e}", exc_info=True)
            self.send_message(chat_id, "שגיאה בטעינת סטטיסטיקות 😞")

    def cmd_favorites(self, chat_id: str, args: List[str]):
        """Handle /favorites command"""
        favorites = self.db.get_user_favorites(chat_id)

        if not favorites:
            self.send_message(chat_id, "אין לך מועדפים עדיין 🤷‍♂️\n\nלחץ על ⭐ בהתראות כדי להוסיף דירות למועדפים!")
            return

        text = f"⭐ <b>הדירות המועדפות שלך</b> ({len(favorites)})\n\n"

        for i, apt in enumerate(favorites[:10], 1):
            price = f"₪{apt['price']:,}" if apt.get('price') else 'לא ידוע'
            rooms = f"{apt['rooms']} חד'" if apt.get('rooms') else 'לא ידוע'
            location = apt.get('city', apt.get('location', 'לא ידוע'))

            text += f"{i}. <b>{apt.get('title', 'ללא כותרת')[:40]}</b>\n"
            text += f"   📍 {location} | 🛏️ {rooms} | 💰 {price}\n"
            text += f"   <a href=\"{apt['link']}\">🔗 צפייה ביד2</a>\n\n"

        if len(favorites) > 10:
            text += f"\n... ועוד {len(favorites) - 10} דירות"

        self.send_message(chat_id, text)

    def cmd_search(self, chat_id: str, args: List[str]):
        """Handle /search command"""
        if not args:
            self.send_message(chat_id,
                "🔍 <b>חיפוש דירות</b>\n\n"
                "דוגמאות שימוש:\n"
                "• <code>/search תל אביב</code>\n"
                "• <code>/search רמת גן 3 חדרים</code>\n"
                "• <code>/search 5000 8000</code> (טווח מחירים)")
            return

        query = ' '.join(args)
        # Use SQL-based search for better performance
        results = self.db.search_apartments(query, limit=100)

        if not results:
            self.send_message(chat_id, f"לא נמצאו תוצאות עבור: {query} 😞")
            return

        text = f"🔍 <b>תוצאות חיפוש</b> ({len(results)})\n\n"

        for i, apt in enumerate(results[:8], 1):
            price = f"₪{apt['price']:,}" if apt.get('price') else 'לא ידוע'
            rooms = f"{apt['rooms']} חד'" if apt.get('rooms') else ''
            location = apt.get('city', apt.get('location', ''))

            text += f"{i}. {apt.get('title', 'ללא כותרת')[:50]}\n"
            text += f"   📍 {location} | 💰 {price}"
            if rooms:
                text += f" | 🛏️ {rooms}"
            text += f"\n   <a href=\"{apt['link']}\">🔗 צפייה</a>\n\n"

        if len(results) > 8:
            text += f"\n... ועוד {len(results) - 8} תוצאות"

        self.send_message(chat_id, text)

    def cmd_filter(self, chat_id: str, args: List[str]):
        """Handle /filter command"""
        filters = self.db.get_user_filters(chat_id, active_only=False)

        text = "🔍 <b>ניהול פילטרים</b>\n\n"

        if filters:
            text += "<b>הפילטרים שלך:</b>\n"
            for f in filters:
                status = "✓" if f['is_active'] else "✗"
                name = f['name']
                ftype = f['filter_type']

                if ftype in ['price', 'rooms', 'sqm']:
                    min_val = f['min_value'] if f['min_value'] else ''
                    max_val = f['max_value'] if f['max_value'] else ''
                    text += f"{status} {name}: {min_val}-{max_val}\n"
                else:
                    text += f"{status} {name}: {f['text_value']}\n"
        else:
            text += "אין לך פילטרים מוגדרים.\n\n"

        text += """
<b>💡 כיצד להגדיר פילטרים:</b>
השתמש בדאשבורד האינטרנטי שלנו להגדרת פילטרים מתקדמים!

הפילטרים מאפשרים לך לקבל התראות רק על דירות שמתאימות להעדפות שלך.
"""
        self.send_message(chat_id, text)

    def cmd_pause(self, chat_id: str, args: List[str]):
        """Handle /pause command"""
        self.db.pause_user_notifications(chat_id, paused=True)
        self.send_message(chat_id,
            "⏸️ <b>התראות הושהו</b>\n\n"
            "לא תקבל התראות חדשות עד שתחדש.\n"
            "לחידוש: /resume")

    def cmd_resume(self, chat_id: str, args: List[str]):
        """Handle /resume command"""
        self.db.pause_user_notifications(chat_id, paused=False)
        self.send_message(chat_id,
            "▶️ <b>התראות חודשו!</b>\n\n"
            "תתחיל לקבל התראות שוב על דירות חדשות ושינויי מחיר.")

    def cmd_dashboard(self, chat_id: str, args: List[str]):
        """Handle /dashboard command - send link to web dashboard"""
        if self.dashboard_url:
            text = (
                f'🖥️ <b>לוח הבקרה</b>\n\n'
                f'<a href="{self.dashboard_url}">👉 לחץ כאן לפתיחת לוח הבקרה</a>\n\n'
                f'בלוח הבקרה תוכל:\n'
                f'• לראות את כל הדירות\n'
                f'• לסנן לפי מחיר, חדרים ועוד\n'
                f'• לראות דירות חדשות וירידות מחיר\n'
                f'• לצפות בדירות שהוסרו'
            )
        else:
            text = '⚠️ לוח הבקרה לא מוגדר כרגע.'
        self.send_message(chat_id, text)

    def cmd_scrape(self, chat_id: str, args: List[str]):
        """Handle /scrape command - trigger immediate scrape and send all results"""
        if not self.scrape_callback:
            self.send_message(chat_id, "⚠️ פונקציית הסריקה לא זמינה כרגע.")
            return

        # Check if user has any URLs
        user_urls = self.db.get_user_search_urls(chat_id)
        if not user_urls:
            self.send_message(chat_id,
                "❌ אין לך כתובות מעקב.\n"
                "הוסף כתובת עם /subscribe קודם.")
            return

        self.send_message(chat_id,
            f"🔍 <b>מתחיל סריקה מיידית (עמוד ראשון)...</b>\n"
            f"📋 סורק {len(user_urls)} כתובות")

        try:
            import threading
            import time as _time
            def run_scrape():
                try:
                    apartments, debug_info = self.scrape_callback(chat_id)

                    # Send debug info about what the parser found
                    debug_msg = (
                        f"🔬 <b>דיבאג HTML:</b>\n"
                        f"• גודל דף: {debug_info.get('page_size', '?')} bytes\n"
                        f"• H2 elements (total): {debug_info.get('h2_total', '?')}\n"
                        f"• H2 elements (valid): {debug_info.get('h2_valid', '?')}\n"
                        f"• דירות שפורסרו: {debug_info.get('parsed', '?')}\n"
                        f"• דירות שנדחו (אין מחיר/לינק): {debug_info.get('rejected', '?')}"
                    )
                    self.send_message(chat_id, debug_msg)

                    if not apartments:
                        self.send_message(chat_id, "⚠️ <b>לא נמצאו דירות.</b>")
                        return

                    self.send_message(chat_id,
                        f"✅ <b>סריקה הושלמה!</b> נמצאו {len(apartments)} דירות.\n"
                        f"שולח את כולן...")

                    for i, apt in enumerate(apartments):
                        price = f"₪{apt['price']:,}" if apt.get('price') else 'לא ידוע'
                        location = apt.get('location', apt.get('street_address', 'לא ידוע'))
                        info = apt.get('item_info', '')
                        link = apt.get('link', '')

                        text = (
                            f"🏠 <b>דירה {i+1}/{len(apartments)}</b>\n\n"
                            f"📍 <b>מיקום:</b> {location}\n"
                            f"💰 <b>מחיר:</b> {price}\n"
                        )
                        if info:
                            text += f"ℹ️ <b>פרטים:</b> {info}\n"
                        if link:
                            text += f"\n🔗 <a href=\"{link}\">צפייה ביד2</a>"

                        self.send_message(chat_id, text)
                        if i < len(apartments) - 1:
                            _time.sleep(0.5)

                except Exception as e:
                    self.send_message(chat_id, f"❌ שגיאה בסריקה: {e}")

            threading.Thread(target=run_scrape, daemon=True).start()
        except Exception as e:
            self.send_message(chat_id, f"❌ שגיאה: {e}")

    def cmd_analytics(self, chat_id: str, args: List[str]):
        """Handle /analytics command"""
        dashboard_link = self.dashboard_url or "http://localhost:5000"
        text = f"""
📊 <b>אנליטיקת שוק מתקדמת</b>

לאנליזה מפורטת עם גרפים וויזואליזציות,
בקר בדאשבורד האינטרנטי שלנו:

🌐 <a href="{dashboard_link}">פתח דאשבורד</a>

בדאשבורד תמצא:
• 📈 גרפים של התפלגות מחירים
• 🗺️ ניתוח לפי שכונות
• 📉 מגמות מחירים לאורך זמן
• 🔥 תובנות שוק מתקדמות
"""
        self.send_message(chat_id, text)

    def handle_text_message(self, message: Dict) -> Dict:
        """Handle regular text messages"""
        chat_id = str(message['chat']['id'])
        self.send_message(chat_id,
            "אני מבין רק פקודות 🤖\n"
            "שלח /help לרשימת הפקודות הזמינות.")
        return {'status': 'ok'}

    def handle_callback_query(self, callback_query: Dict) -> Dict:
        """Handle inline keyboard button clicks"""
        try:
            query_id = callback_query['id']
            chat_id = str(callback_query['from']['id'])
            data = callback_query['data']

            # Parse callback data
            parts = data.split(':')
            action = parts[0]
            apt_id = parts[1] if len(parts) > 1 else None

            if action == 'favorite' and apt_id:
                self.db.add_user_favorite(chat_id, apt_id)
                self.answer_callback_query(query_id, "✓ נוסף למועדפים!")

            elif action == 'ignore' and apt_id:
                self.db.add_user_ignored(chat_id, apt_id)
                self.answer_callback_query(query_id, "✓ הדירה תתעלם")

            elif action == 'open' and apt_id:
                self.answer_callback_query(query_id, "פותח ביד2...")

            else:
                self.answer_callback_query(query_id, "פעולה לא מוכרת")

            return {'status': 'ok', 'action': action}

        except Exception as e:
            logger.error(f"Error handling callback: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def create_inline_keyboard(self, apt_id: str) -> Dict:
        """Create inline keyboard with buttons for apartment notification"""
        return {
            'inline_keyboard': [[
                {'text': '⭐ הוסף למועדפים', 'callback_data': f'favorite:{apt_id}'},
                {'text': '🚫 התעלם', 'callback_data': f'ignore:{apt_id}'}
            ], [
                {'text': '🔗 פתח ביד2', 'url': f'https://www.yad2.co.il/item/{apt_id}'}
            ]]
        }

    def format_apartment_notification(self, apartment: Dict, notification_type: str = 'new') -> str:
        """Format apartment data into a nice notification message"""
        title = apartment.get('title', 'ללא כותרת')
        price = f"₪{apartment['price']:,}" if apartment.get('price') else 'לא ידוע'
        rooms = apartment.get('rooms', 'לא ידוע')
        sqm = apartment.get('sqm', 'לא ידוע')
        floor = apartment.get('floor', 'לא ידוע')
        city = apartment.get('city', '')
        neighborhood = apartment.get('neighborhood', '')
        location = f"{city}, {neighborhood}" if city and neighborhood else city or neighborhood or 'לא ידוע'

        if notification_type == 'new':
            emoji = "🆕"
            header = "<b>דירה חדשה נמצאה!</b>"
        elif notification_type == 'price_drop':
            emoji = "📉"
            header = "<b>ירידת מחיר!</b>"
            old_price = apartment.get('old_price')
            if old_price:
                drop_pct = ((old_price - apartment['price']) / old_price) * 100
                header += f" ({drop_pct:.1f}%-)"
        else:
            emoji = "🏠"
            header = "<b>עדכון דירה</b>"

        text = f"""
{emoji} {header}

<b>{title}</b>

📍 <b>מיקום:</b> {location}
💰 <b>מחיר:</b> {price}
🛏️ <b>חדרים:</b> {rooms}
📏 <b>מ"ר:</b> {sqm}
🏢 <b>קומה:</b> {floor}
"""

        if notification_type == 'price_drop' and apartment.get('old_price'):
            text += f"\n💸 <b>מחיר קודם:</b> ₪{apartment['old_price']:,}"

        return text.strip()

    def notify_new_apartment(self, apartment: Dict, target_users: List[str] = None):
        """Send new apartment notification to users"""
        apt_id = apartment['id']
        message_text = self.format_apartment_notification(apartment, 'new')
        keyboard = self.create_inline_keyboard(apt_id)

        # Get target users
        if target_users is None:
            target_users = [u['chat_id'] for u in self.db.get_all_active_users()]

        for chat_id in target_users:
            # Check if apartment matches user's filters
            if not self.db.apartment_matches_user_filters(chat_id, apartment):
                continue

            # Check if user already ignored this apartment
            if self.db.is_user_ignored(chat_id, apt_id):
                continue

            self.send_message(chat_id, message_text, reply_markup=keyboard)

    def notify_price_change(self, apartment: Dict, old_price: float, target_users: List[str] = None):
        """Send price change notification to users"""
        apartment = dict(apartment)  # Copy to avoid mutating caller's dict
        apartment['old_price'] = old_price
        apt_id = apartment['id']
        message_text = self.format_apartment_notification(apartment, 'price_drop')
        keyboard = self.create_inline_keyboard(apt_id)

        # Get target users
        if target_users is None:
            target_users = [u['chat_id'] for u in self.db.get_all_active_users()]

        for chat_id in target_users:
            # Check if apartment matches user's filters
            if not self.db.apartment_matches_user_filters(chat_id, apartment):
                continue

            # Check if user already ignored this apartment
            if self.db.is_user_ignored(chat_id, apt_id):
                continue

            self.send_message(chat_id, message_text, reply_markup=keyboard)
