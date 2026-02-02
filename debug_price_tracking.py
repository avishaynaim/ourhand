#!/usr/bin/env python3
"""
DEEP DIAGNOSTIC: Price tracking debugging
Google Engineer level code review and debugging
"""
import os
import sys
import json

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

try:
    from database_postgres import PostgreSQLDatabase
    import psycopg2.extras

    db = PostgreSQLDatabase(database_url)

    print("=" * 80)
    print("DEEP DIAGNOSTIC: PRICE TRACKING DEBUG")
    print("=" * 80)

    with db.get_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. Basic stats
        print("\n📊 DATABASE STATS:")
        cursor.execute("SELECT COUNT(*) as total FROM apartments WHERE is_active = 1")
        total = cursor.fetchone()['total']
        print(f"   Total active apartments: {total}")

        cursor.execute("SELECT COUNT(*) as total FROM price_history")
        history_total = cursor.fetchone()['total']
        print(f"   Total price_history entries: {history_total}")

        # 2. Check apartments with multiple price entries
        cursor.execute("""
            SELECT COUNT(DISTINCT apartment_id) as count
            FROM price_history
        """)
        apts_with_history = cursor.fetchone()['count']
        print(f"   Apartments with price history: {apts_with_history}")

        cursor.execute("""
            SELECT apartment_id, COUNT(*) as entry_count
            FROM price_history
            GROUP BY apartment_id
            HAVING COUNT(*) > 1
        """)
        apts_with_changes = cursor.fetchall()
        print(f"   Apartments with 2+ history entries: {len(apts_with_changes)}")

        # 3. Check recent price history entries
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM price_history
            WHERE recorded_at > NOW() - INTERVAL '24 hours'
        """)
        recent = cursor.fetchone()['count']
        print(f"   Price history entries in last 24h: {recent}")

        # 4. Show sample data with detailed info
        print("\n🔍 DETAILED SAMPLE (10 apartments with most history):")
        cursor.execute("""
            SELECT apartment_id, COUNT(*) as entry_count
            FROM price_history
            GROUP BY apartment_id
            ORDER BY entry_count DESC
            LIMIT 10
        """)
        samples = cursor.fetchall()

        for sample in samples:
            apt_id = sample['apartment_id']
            count = sample['entry_count']

            # Get apartment details
            cursor.execute("SELECT title, price, link FROM apartments WHERE id = %s", (apt_id,))
            apt = cursor.fetchone()

            # Get price history
            cursor.execute("""
                SELECT price, recorded_at
                FROM price_history
                WHERE apartment_id = %s
                ORDER BY recorded_at ASC
            """, (apt_id,))
            history = cursor.fetchall()

            print(f"\n   Apartment: {apt_id[:40]}...")
            print(f"   Title: {apt['title'][:60]}...")
            print(f"   Current price: ₪{apt['price']:,}")
            print(f"   History entries: {count}")
            print(f"   Price changes:")

            for i, h in enumerate(history):
                date = h['recorded_at'].strftime('%Y-%m-%d %H:%M')
                price = h['price']
                if i == 0:
                    print(f"      {date}: ₪{price:,} (initial)")
                else:
                    prev = history[i-1]['price']
                    diff = price - prev
                    if diff != 0:
                        trend = "📈" if diff > 0 else "📉"
                        print(f"      {date}: ₪{price:,} {trend} ({diff:+,})")
                    else:
                        print(f"      {date}: ₪{price:,} (no change)")

        # 5. Check for potential issues
        print("\n⚠️  POTENTIAL ISSUES CHECK:")

        # Check if apartments have NULL prices
        cursor.execute("SELECT COUNT(*) as count FROM apartments WHERE price IS NULL AND is_active = 1")
        null_prices = cursor.fetchone()['count']
        if null_prices > 0:
            print(f"   ⚠️  {null_prices} apartments have NULL price!")

        # Check if price history has apartments not in apartments table
        cursor.execute("""
            SELECT COUNT(DISTINCT ph.apartment_id) as count
            FROM price_history ph
            LEFT JOIN apartments a ON ph.apartment_id = a.id
            WHERE a.id IS NULL
        """)
        orphaned = cursor.fetchone()['count']
        if orphaned > 0:
            print(f"   ⚠️  {orphaned} price_history entries for non-existent apartments!")

        # Check for apartments scraped multiple times but no history
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM apartments a
            WHERE a.is_active = 1
            AND a.last_seen < NOW() - INTERVAL '1 hour'
            AND NOT EXISTS (
                SELECT 1 FROM price_history ph
                WHERE ph.apartment_id = a.id
                AND ph.recorded_at > NOW() - INTERVAL '24 hours'
            )
        """)
        old_no_history = cursor.fetchone()['count']
        if old_no_history > 0:
            print(f"   ⚠️  {old_no_history} apartments last seen >1h ago with no recent price history!")
            print(f"       This suggests price tracking might not be working correctly.")

        # 6. Test the comparison logic
        print("\n🧪 TESTING PRICE COMPARISON LOGIC:")

        # Get a sample apartment that should have changed
        cursor.execute("""
            SELECT apartment_id
            FROM price_history
            GROUP BY apartment_id
            HAVING COUNT(*) = 1
            LIMIT 1
        """)
        test_apt = cursor.fetchone()

        if test_apt:
            test_id = test_apt['apartment_id']
            cursor.execute("SELECT price FROM apartments WHERE id = %s", (test_id,))
            current = cursor.fetchone()
            cursor.execute("SELECT price FROM price_history WHERE apartment_id = %s", (test_id,))
            history = cursor.fetchone()

            if current and history:
                current_price = current['price']
                history_price = history['price']
                print(f"   Sample apartment: {test_id[:30]}...")
                print(f"   Current price in apartments: {current_price} (type: {type(current_price).__name__})")
                print(f"   Price in history: {history_price} (type: {type(history_price).__name__})")
                print(f"   Are they equal? {current_price == history_price}")
                print(f"   Comparison result: {current_price} == {history_price} → {current_price == history_price}")

        # 7. Check API response simulation
        print("\n🌐 API RESPONSE SIMULATION:")
        all_histories = db.get_all_price_histories()
        print(f"   get_all_price_histories() returned {len(all_histories)} apartments")

        # Show sample
        sample_ids = list(all_histories.keys())[:3]
        for apt_id in sample_ids:
            hist = all_histories[apt_id]
            print(f"   {apt_id[:30]}... has {len(hist)} entries")
            if len(hist) > 1:
                first = hist[0]['price']
                last = hist[-1]['price']
                print(f"      ₪{first:,} → ₪{last:,} (diff: {last-first:+,})")
            else:
                print(f"      Only 1 entry - no trend available")

        # 8. Final diagnosis
        print("\n" + "=" * 80)
        print("DIAGNOSIS:")
        print("=" * 80)

        if history_total == 0:
            print("❌ CRITICAL: No price history at all!")
            print("   → The scraper hasn't saved any apartments yet")
        elif apts_with_history == total:
            print("✅ All apartments have at least 1 price history entry")
            if len(apts_with_changes) == 0:
                print("⚠️  But NONE have 2+ entries (no price changes detected)")
                print("   → Scraper ran only once, or not detecting price changes")
                print("   → Need to wait for next scrape cycle")
            elif len(apts_with_changes) < total * 0.05:
                print(f"⚠️  Only {len(apts_with_changes)} apartments have 2+ entries")
                print("   → Less than 5% have price changes")
                print("   → Either: 1) Prices haven't changed much")
                print("   →        2) Price comparison logic not working")
                print("   →        3) Scraper not running frequently enough")
            else:
                print(f"✅ {len(apts_with_changes)} apartments have price changes!")
                print("   → Price tracking is working")
                print("   → Check frontend to see if indicators display correctly")
        else:
            print(f"⚠️  Only {apts_with_history}/{total} apartments have price history")
            print("   → Some apartments missing from price_history table")

        if old_no_history > 100:
            print(f"\n❌ PROBLEM FOUND: {old_no_history} old apartments with no recent history")
            print("   → This indicates price tracking is NOT running on updates")
            print("   → Check the batch_upsert_apartments() implementation")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
