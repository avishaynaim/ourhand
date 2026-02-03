"""
Version information for OurHand Monitor
"""

__version__ = "1.7.0"

# Version History:
# 1.7.0 - 2026-02-03: Add manual scrape trigger button + fix smart-stop for price changes
# 1.6.0 - 2026-02-02: Full responsive redesign with Tailwind - fix all cutoff issues
# 1.5.0 - 2026-02-02: Replace bar chart with line chart + add filtered stats to table view
# 1.4.0 - 2026-02-02: Add median price statistic to dashboard
# 1.3.2 - 2026-02-02: Fix tooltip cutoff - position to right side instead of below
# 1.3.1 - 2026-02-02: Fix price drops count to match filter (data consistency)
# 1.3.0 - 2026-02-02: Major UX improvements: graph in tooltip, better icons, loading state
# 1.2.5 - 2026-02-02: Fix price trend tooltip being cut off by table overflow
# 1.2.4 - 2026-02-02: Fix price-drop filter to actually filter apartments with price decreases
# 1.2.3 - 2026-02-02: Add remote diagnostic API endpoint for price tracking
# 1.2.2 - 2026-02-02: Add detailed price tracking diagnostics and logging
# 1.2.1 - 2026-02-02: Fix embedded dashboard to use database API instead of localStorage
# 1.2.0 - 2026-02-02: Remove SQLite support, PostgreSQL only (prevent future dual-db issues)
# 1.1.2 - 2026-02-02: Add PostgreSQL support for filter presets (fix Railway deployment)
# 1.1.1 - 2026-02-02: Add version display to embedded dashboard
# 1.1.0 - 2026-02-02: Save dashboard filter presets to database instead of localStorage
# 1.0.0 - 2026-02-01: Initial release
