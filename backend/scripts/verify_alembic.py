"""
Read-only script to query SELECT version_num FROM alembic_version
"""
import asyncio
import getpass
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.database import engine


async def verify():
    pwd = getpass.getpass("Enter Supabase DB Password (hidden input): ")
    if not pwd:
        print("Error: Password cannot be empty.")
        return
    enc_pwd = urllib.parse.quote(pwd, safe="")
    user = "postgres.lmyqnovtpwzdemqhqujb"
    host = "aws-0-ap-southeast-2.pooler.supabase.com"
    port = "5432"
    dbname = "postgres"

    os.environ["DATABASE_URL"] = f"postgresql://{user}:{enc_pwd}@{host}:{port}/{dbname}"

    masked_url = engine.url.render_as_string(hide_password=True)
    print(f"Target Database URL: {masked_url}")
    print(f"Dialect:             {engine.dialect.name} / Driver: {engine.dialect.driver}")

    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT version_num FROM alembic_version;"))
        rev = res.scalar()
        print(f"Stamped Revision in Supabase: {rev}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify())
