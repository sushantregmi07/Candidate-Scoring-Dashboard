import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.auth import hash_password
from app.database import async_session, init_db
from app.models import User
from app.routers import auth as auth_router


async def _seed_admin():
    """Create the default admin account if it doesn't already exist."""
    email = os.getenv("ADMIN_EMAIL", "admin@techkraft.com")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none() is None:
            admin = User(
                email=email,
                hashed_password=hash_password(password),
                role="admin",
            )
            session.add(admin)
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _seed_admin()
    yield


app = FastAPI(
    title="Candidate Scoring Dashboard",
    description="Internal recruitment scoring and review API for TechKraft",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
