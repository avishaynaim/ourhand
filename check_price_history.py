#!/usr/bin/env python3
"""
Diagnostic script to check price history data
Run this to see if price changes are being tracked
"""
import os
import sys

# Check if DATABASE_URL is set
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("❌ DATABASE_URL not set. This script requires PostgreSQL.")
    print("Set DATABASE_URL environment variable first.")
    sys.exit(1)

try:
    from database_postgres import PostgreSQLDatabase

    db = PostgreSQLDatabase(database_url)

    print("=" * 60)
    print("PRICE HISTORY DIAGNOSTIC")
    print("=" * 60)

    # Check total apartments
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Total apartments
        cursor.execute("SELECT COUNT(*) FROM apartments WHERE is_active = 1")
        total_apts = cursor.fetchone()[0]
        print(f"\n📊 Total active apartments: {total_apts}")

        # Total price history entries
        cursor.execute("SELECT COUNT(*) FROM price_history")
        total_history = cursor.fetchone()[0]
        print(f"📈 Total price history entries: {total_history}")

        # Apartments with price changes (>1 history entry)
        cursor.execute("""
            SELECT apartment_id, COUNT(*) as count
            FROM price_history
            GROUP BY apartment_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        apts_with_changes = cursor.fetchall()

        print(f"\n🔄 Apartments with price history (>1 entry): {len(apts_with_changes)}")

        if apts_with_changes:
            print("\nTop 10 apartments with most price changes:")
            for apt_id, count in apts_with_changes:
                cursor.execute("""
                    SELECT price, recorded_at
                    FROM price_history
                    WHERE apartment_id = %s
                    ORDER BY recorded_at ASC
                """, (apt_id,))
                prices = cursor.fetchall()
                first_price = prices[0][0]
                last_price = prices[-1][0]
                diff = last_price - first_price
                trend = "📉" if diff < 0 else "📈" if diff > 0 else "➡️"
                print(f"  {trend} ID: {apt_id[:20]}... - {count} changes - ₪{first_price:,} → ₪{last_price:,} ({diff:+,})")

        # Recent price changes (last 7 days)
        cursor.execute("""
            SELECT COUNT(DISTINCT apartment_id)
            FROM price_history
            WHERE recorded_at > NOW() - INTERVAL '7 days'
        """)
        recent_changes = cursor.fetchone()[0]
        print(f"\n⏰ Apartments with price history in last 7 days: {recent_changes}")

        # Sample price history
        if total_history > 0:
            print("\n📋 Sample price history entries (latest 5):")
            cursor.execute("""
                SELECT apartment_id, price, recorded_at
                FROM price_history
                ORDER BY recorded_at DESC
                LIMIT 5
            """)
            for apt_id, price, recorded_at in cursor.fetchall():
                print(f"  - {apt_id[:30]}... : ₪{price:,} at {recorded_at}")

    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("=" * 60)

    if total_history == 0:
        print("❌ NO price history data found!")
        print("   Possible causes:")
        print("   1. The scraper hasn't run yet")
        print("   2. No apartments have been added to the database")
        print("   3. Price tracking is not working")
    elif len(apts_with_changes) == 0:
        print("⚠️  Price history exists, but no apartments have multiple entries")
        print("   This means:")
        print("   1. Apartments have been added only once (no price changes yet)")
        print("   2. The scraper needs to run again to detect changes")
        print("   3. Wait for the next scrape cycle")
    else:
        print(f"✅ Price history is working! {len(apts_with_changes)} apartments have price changes")
        print("   The dashboard should show price trend indicators (📈📉➡️)")
        print("   If you don't see them:")
        print("   1. Hard refresh the browser (Ctrl+Shift+R)")
        print("   2. Check browser console for errors")
        print("   3. Verify include_price_history=1 in API call")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
