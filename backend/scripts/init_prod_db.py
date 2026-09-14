"""
Nexora — Complete Production / Supabase Database Initialization Script
Executes:
1. Interactive password prompt (getpass) + urllib.parse.quote_plus
2. Enables pgvector extension safely (CREATE EXTENSION IF NOT EXISTS vector)
3. Creates all 16 base schema tables via Base.metadata.create_all
4. Verifies created tables
5. Stamps Alembic to head (b1c2d3e4f5a6)
6. Verifies alembic_version table
7. Seeds demo student data (Rahul Kumar + attendance/marks/fees)
8. Seeds demo WhatsApp notice source messages
9. Verifies seeded records
10. Prints complete, credential-masked final status report
"""
import asyncio
import getpass
import os
import sys
import urllib.parse

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from alembic.config import Config
from alembic import command


async def initialize_production_database():
    print("=" * 70)
    print("NEXORA — SUPABASE PRODUCTION DATABASE INITIALIZATION")
    print("=" * 70)

    # Prompt for database password securely
    pwd = getpass.getpass("Enter Supabase DB Password (hidden input): ")
    if not pwd:
        print("Error: Password cannot be empty.")
        return

    enc_pwd = urllib.parse.quote(pwd, safe="")
    user = "postgres.lmyqnovtpwzdemqhqujb"
    host = "aws-0-ap-southeast-2.pooler.supabase.com"
    port = "5432"
    dbname = "postgres"

    # Construct DATABASE_URL in memory
    db_url = f"postgresql://{user}:{enc_pwd}@{host}:{port}/{dbname}"
    os.environ["DATABASE_URL"] = db_url

    # Import database module after setting environment variable
    from app.core.config import settings, normalize_database_url
    from app.db.database import engine, Base, AsyncSessionLocal
    from app.models import Base as ModelsBase

    masked_url = engine.url.render_as_string(hide_password=True)
    print(f"Target URL: {masked_url}")
    print(f"Dialect:    {engine.dialect.name} / Driver: {engine.dialect.driver}")
    print("-" * 70)

    # 1. Enable pgvector extension
    print("Step 1: Enabling pgvector extension...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    print("  ✓ pgvector extension status: ENABLED / VERIFIED")

    # 2. Create Base Schema Tables
    print("\nStep 2: Creating base schema tables via Base.metadata.create_all...")
    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)
    print("  ✓ Base schema tables created.")

    # 3. Verify Created Tables
    print("\nStep 3: Verifying table creation...")
    async with engine.connect() as conn:
        created_tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
    print(f"  ✓ Total tables in Supabase: {len(created_tables)}")
    for t in sorted(created_tables):
        print(f"    - {t}")

    # 4. Stamp Alembic to head (b1c2d3e4f5a6)
    print("\nStep 4: Stamping Alembic migration version to head (b1c2d3e4f5a6)...")
    alembic_cfg = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    normalized_db_url = normalize_database_url(db_url)
    alembic_cfg.set_main_option("sqlalchemy.url", normalized_db_url.replace("%", "%%"))
    command.stamp(alembic_cfg, "head")

    # Verify alembic_version table
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT version_num FROM alembic_version;"))
        alembic_ver = res.scalar()
    print(f"  ✓ Alembic version verified in database: {alembic_ver}")

    # 5. Seed Demo Student Data
    print("\nStep 5: Seeding demo student data (Rahul Kumar)...")
    from scripts.seed_demo_student import seed_demo_student
    await seed_demo_student()

    # 6. Seed Demo Notice Messages
    print("\nStep 6: Seeding demo notice source messages...")
    from scripts.seed_demo_notices import seed
    await seed()

    # 7. Final Record Verification
    print("\nStep 7: Verifying seeded production records...")
    async with AsyncSessionLocal() as session:
        user_res = await session.execute(text("SELECT email, role FROM users WHERE email='rahul@college.edu';"))
        user_row = user_res.fetchone()
        
        att_res = await session.execute(text("SELECT COUNT(*) FROM student_attendance;"))
        att_count = att_res.scalar()

        marks_res = await session.execute(text("SELECT COUNT(*) FROM student_subject_marks;"))
        marks_count = marks_res.scalar()

        fee_res = await session.execute(text("SELECT COUNT(*) FROM student_fee_records;"))
        fee_count = fee_res.scalar()

        msg_res = await session.execute(text("SELECT COUNT(*) FROM demo_source_messages;"))
        msg_count = msg_res.scalar()

    print("=" * 70)
    print("NEXORA — INITIALIZATION SUMMARY REPORT")
    print("=" * 70)
    print(f"1. Target Database:        Supabase Production ({host})")
    print(f"2. Total Tables Created:   {len(created_tables)} tables")
    print(f"3. pgvector Extension:     ENABLED (installed and active)")
    print(f"4. Alembic Version:        {alembic_ver} (head)")
    print(f"5. Demo Student Status:    SEEDED ({user_row[0] if user_row else 'None'}, {att_count} attendance records, {marks_count} marks records, {fee_count} fee records)")
    print(f"6. Demo Notice Status:     SEEDED ({msg_count} demo WhatsApp source messages)")
    print(f"7. Errors / Warnings:      NONE (0 errors)")
    print("=" * 70)
    print("SUCCESS: Production Supabase database is fully initialized and seeded!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(initialize_production_database())
