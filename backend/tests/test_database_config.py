"""
Unit tests for Database URL normalization and engine configuration.
Verifies that:
1. Standard PostgreSQL URLs (postgresql://) are normalized to postgresql+asyncpg://
2. Already normalized URLs (postgresql+asyncpg://) are not modified again
3. Legacy postgres:// URLs are normalized to postgresql+asyncpg://
4. Supabase pooler query parameters (?pgbouncer=true) are preserved
5. The async engine uses the asyncpg driver and does not attempt to import psycopg2
"""
import pytest
from app.core.config import normalize_database_url
from sqlalchemy.ext.asyncio import create_async_engine


def test_normalize_postgresql_url():
    raw_url = "postgresql://user:pass@localhost:5432/testdb"
    expected = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
    assert normalize_database_url(raw_url) == expected


def test_normalize_already_asyncpg_url():
    raw_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
    assert normalize_database_url(raw_url) == raw_url


def test_normalize_legacy_postgres_url():
    raw_url = "postgres://user:pass@localhost:5432/testdb"
    expected = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
    assert normalize_database_url(raw_url) == expected


def test_normalize_preserves_supabase_pooler_params():
    raw_url = (
        "postgresql://postgres.abcxyz:mypassword@"
        "aws-0-ap-south-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
    )
    expected = (
        "postgresql+asyncpg://postgres.abcxyz:mypassword@"
        "aws-0-ap-south-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
    )
    normalized = normalize_database_url(raw_url)
    assert normalized == expected
    # Robustness check: normalizing again produces the exact same string
    assert normalize_database_url(normalized) == expected


def test_normalize_strips_whitespace_and_quotes():
    raw_url = '  "postgresql://user:pass@host:5432/db?pgbouncer=true"  '
    expected = "postgresql+asyncpg://user:pass@host:5432/db?pgbouncer=true"
    assert normalize_database_url(raw_url) == expected


def test_async_engine_uses_asyncpg_with_pooler_url():
    raw_url = (
        "postgresql://postgres.abcxyz:mypassword@"
        "aws-0-ap-south-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
    )
    normalized = normalize_database_url(raw_url)
    engine = create_async_engine(normalized)

    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"
    assert "pgbouncer" in engine.url.query
    assert engine.url.query["pgbouncer"] == "true"
