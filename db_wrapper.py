"""
Database wrapper - PostgreSQL only
Railway deployment requires DATABASE_URL environment variable
"""
import os
import logging

logger = logging.getLogger(__name__)


def get_database():
    """
    Factory function that returns PostgreSQL database instance.

    Requires DATABASE_URL environment variable.
    This application is designed for Railway deployment with PostgreSQL only.
    """
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        error_msg = (
            "❌ DATABASE_URL environment variable is required!\n"
            "This application requires PostgreSQL.\n"
            "On Railway: Add PostgreSQL service to your project.\n"
            "Locally: Set DATABASE_URL=postgresql://user:pass@localhost/dbname"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("📊 Using PostgreSQL database")
    try:
        from database_postgres import PostgreSQLDatabase
        return PostgreSQLDatabase(database_url)
    except ImportError as e:
        logger.error(f"Failed to import PostgreSQL support: {e}")
        logger.error("Make sure psycopg2-binary is installed: pip install psycopg2-binary")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        raise
