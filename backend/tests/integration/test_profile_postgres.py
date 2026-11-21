"""Integration checks against a migrated local Supabase/PostgreSQL database.

Set SUPABASE_TEST_DATABASE_URL to the local Supabase database URL after running
`supabase db reset`. These checks are skipped during the fast unit test run.
"""

import os

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.models.profile import Profile

DATABASE_URL = os.getenv("SUPABASE_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="Set SUPABASE_TEST_DATABASE_URL to run PostgreSQL integration checks",
)


def test_profile_orm_reads_seeded_supabase_profile() -> None:
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            profile = session.scalars(select(Profile).order_by(Profile.created_at)).first()

        assert profile is not None, "Run `supabase db reset` to load the deterministic seed"
        assert profile.role in {"customer", "operator", "admin"}
        assert profile.created_at is not None
        assert profile.updated_at is not None
    finally:
        engine.dispose()


def test_profile_role_is_the_migrated_app_enum() -> None:
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            enum_labels = connection.execute(
                text(
                    """
                    SELECT enumlabel
                    FROM pg_enum
                    JOIN pg_type ON pg_type.oid = pg_enum.enumtypid
                    JOIN pg_namespace ON pg_namespace.oid = pg_type.typnamespace
                    WHERE pg_namespace.nspname = 'app'
                      AND pg_type.typname = 'user_role'
                    ORDER BY enumsortorder
                    """
                )
            ).scalars().all()

        assert enum_labels == ["customer", "operator", "admin"]
        assert Profile.__table__.c.role.type.name == "user_role"
        assert Profile.__table__.c.role.type.schema == "app"
    finally:
        engine.dispose()
