"""
KOROBOS — Database Service Repository Tests

Unit tests for database, property, and record repositories.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.services.database_service.app.repositories.database_repository import (
    DatabaseRepository,
)
from backend.services.database_service.app.repositories.property_repository import (
    PropertyRepository,
)
from backend.services.database_service.app.repositories.record_repository import (
    RecordRepository,
)
from backend.shared.database.base_model import Base


@pytest.fixture
async def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_create_database(db_session):
    """Test creating a database."""
    repo = DatabaseRepository(db_session)
    user_id = uuid.uuid4()

    db = await repo.create(
        user_id=user_id,
        name="Test Database",
        icon="📊",
        description="A test database",
    )

    assert db.id is not None
    assert db.user_id == user_id
    assert db.name == "Test Database"
    assert db.icon == "📊"


@pytest.mark.asyncio
async def test_get_database_by_id(db_session):
    """Test fetching a database by ID."""
    repo = DatabaseRepository(db_session)
    user_id = uuid.uuid4()

    db = await repo.create(
        user_id=user_id,
        name="Test Database",
    )
    db_id = db.id

    fetched = await repo.get_by_id(db_id)

    assert fetched is not None
    assert fetched.id == db_id
    assert fetched.name == "Test Database"


@pytest.mark.asyncio
async def test_list_databases_by_user(db_session):
    """Test listing databases for a user."""
    repo = DatabaseRepository(db_session)
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    # Create multiple databases
    for i in range(3):
        await repo.create(
            user_id=user_id,
            name=f"Database {i}",
        )

    # Create database for another user
    await repo.create(
        user_id=other_user_id,
        name="Other User's Database",
    )

    # Fetch databases for first user
    dbs, total = await repo.list_by_user(user_id)

    assert len(dbs) == 3
    assert total == 3
    assert all(db.user_id == user_id for db in dbs)


@pytest.mark.asyncio
async def test_create_property(db_session):
    """Test creating a property."""
    db_repo = DatabaseRepository(db_session)
    prop_repo = PropertyRepository(db_session)

    user_id = uuid.uuid4()
    db = await db_repo.create(user_id=user_id, name="Test Database")

    prop = await prop_repo.create(
        database_id=db.id,
        name="Title",
        type="text",
        position=0,
    )

    assert prop.id is not None
    assert prop.database_id == db.id
    assert prop.name == "Title"
    assert prop.type == "text"


@pytest.mark.asyncio
async def test_create_record(db_session):
    """Test creating a record."""
    db_repo = DatabaseRepository(db_session)
    rec_repo = RecordRepository(db_session)

    user_id = uuid.uuid4()
    db = await db_repo.create(user_id=user_id, name="Test Database")

    record = await rec_repo.create(database_id=db.id)

    assert record.id is not None
    assert record.database_id == db.id
    assert record.note_id is None


@pytest.mark.asyncio
async def test_upsert_record_value(db_session):
    """Test upserting record values."""
    db_repo = DatabaseRepository(db_session)
    prop_repo = PropertyRepository(db_session)
    rec_repo = RecordRepository(db_session)

    user_id = uuid.uuid4()
    db = await db_repo.create(user_id=user_id, name="Test Database")
    prop = await prop_repo.create(
        database_id=db.id,
        name="Title",
        type="text",
    )
    record = await rec_repo.create(database_id=db.id)

    # Create value
    value = await rec_repo.upsert_value(
        record_id=record.id,
        property_id=prop.id,
        value="Test Title",
    )

    assert value.record_id == record.id
    assert value.property_id == prop.id
    assert value.value == "Test Title"

    # Update value
    updated = await rec_repo.upsert_value(
        record_id=record.id,
        property_id=prop.id,
        value="Updated Title",
    )

    assert updated.value == "Updated Title"


@pytest.mark.asyncio
async def test_delete_database_cascade(db_session):
    """Test that deleting a database cascades to records."""
    db_repo = DatabaseRepository(db_session)
    rec_repo = RecordRepository(db_session)

    user_id = uuid.uuid4()
    db = await db_repo.create(user_id=user_id, name="Test Database")

    # Create records
    record1 = await rec_repo.create(database_id=db.id)
    record2 = await rec_repo.create(database_id=db.id)

    # Delete database
    await db_repo.delete(db)
    await db_session.commit()

    # Records should be deleted
    fetched1 = await rec_repo.get_by_id(record1.id)
    fetched2 = await rec_repo.get_by_id(record2.id)

    assert fetched1 is None
    assert fetched2 is None
