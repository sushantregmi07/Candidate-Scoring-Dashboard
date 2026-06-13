import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["SECRET_KEY"] = "test-secret"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


def _enable_fk(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


event.listen(test_engine.sync_engine, "connect", _enable_fk)


async def _override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "admin-fixture@test.com", "password": "password123"},
    )
    async with TestSession() as session:
        from sqlalchemy import update
        from app.models import User

        await session.execute(
            update(User)
            .where(User.email == "admin-fixture@test.com")
            .values(role="admin")
        )
        await session.commit()

    resp = await client.post(
        "/auth/login",
        json={"email": "admin-fixture@test.com", "password": "password123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def reviewer_token(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "reviewer-a@test.com", "password": "password123"},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "reviewer-a@test.com", "password": "password123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def reviewer_b_token(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={"email": "reviewer-b@test.com", "password": "password123"},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "reviewer-b@test.com", "password": "password123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def seeded_candidates(admin_token, client: AsyncClient):
    from app.models import Candidate

    ids = []
    candidates = [
        {"name": "Alice Dev", "email": "alice@dev.com", "role_applied": "Backend Engineer", "status": "new", "skills": ["Python", "FastAPI"]},
        {"name": "Bob Ops", "email": "bob@ops.com", "role_applied": "DevOps Engineer", "status": "reviewed", "skills": ["Docker", "AWS"]},
        {"name": "Carol Full", "email": "carol@full.com", "role_applied": "Backend Engineer", "status": "new", "skills": ["Python", "React"]},
    ]
    async with TestSession() as session:
        for c in candidates:
            candidate = Candidate(**c)
            session.add(candidate)
            await session.flush()
            ids.append(candidate.id)
        await session.commit()
    return ids
