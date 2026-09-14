"""
Read-only database inspector.
Safely connects to the configured DATABASE_URL and prints:
- Connection status
- Resolved database host/port/driver
- Existing table names in the database
Does NOT modify, create, or drop any data.
"""
import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from app.db.database import engine, DATABASE_URL


async def inspect_database():
    masked_url = engine.url.render_as_string(hide_password=True)
    print("=" * 60)
    print("NEXORA — READ-ONLY SUPABASE DATABASE INSPECTION")
    print("=" * 60)
    print(f"Target Database URL: {masked_url}")
    print(f"Dialect:             {engine.dialect.name}")
    print(f"Driver:              {engine.dialect.driver}")
    print("-" * 60)
    print("Connecting to Supabase...")

    try:
        async with engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
            print("Status: Connected successfully!")
            print(f"Total tables found: {len(tables)}")
            print("-" * 60)
            if tables:
                print("Existing tables:")
                for t in sorted(tables):
                    print(f"  - {t}")
            else:
                print("The database is currently completely EMPTY (0 tables).")
            print("=" * 60)
            return tables
    except Exception as exc:
        print("Status: Connection failed!")
        print(f"Error: {type(exc).__name__}: {exc}")
        print("=" * 60)
        return None
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(inspect_database())
