import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.database import async_session
from app.models import Candidate, User

SEED_USERS = [
    {
        "email": os.getenv("ADMIN_EMAIL", "admin@techkraft.com"),
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "role": "admin",
    },
    {"email": "alice@techkraft.com", "password": "reviewer123", "role": "reviewer"},
    {"email": "bob@techkraft.com", "password": "reviewer123", "role": "reviewer"},
]

SEED_CANDIDATES = [
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "role_applied": "Backend Engineer",
        "status": "new",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    },
    {
        "name": "James Chen",
        "email": "james.chen@example.com",
        "role_applied": "Frontend Engineer",
        "status": "reviewed",
        "skills": ["React", "TypeScript", "Tailwind CSS", "Next.js"],
    },
    {
        "name": "Maria Garcia",
        "email": "maria.garcia@example.com",
        "role_applied": "Full Stack Engineer",
        "status": "new",
        "skills": ["Python", "React", "AWS", "GraphQL"],
    },
    {
        "name": "Alex Kim",
        "email": "alex.kim@example.com",
        "role_applied": "DevOps Engineer",
        "status": "hired",
        "skills": ["Kubernetes", "Terraform", "CI/CD", "AWS"],
    },
    {
        "name": "Sarah Johnson",
        "email": "sarah.johnson@example.com",
        "role_applied": "Backend Engineer",
        "status": "rejected",
        "skills": ["Java", "Spring Boot", "MySQL"],
    },
]


async def run_seed():
    async with async_session() as session:
        existing = await session.execute(select(User))
        if existing.scalars().first() is not None:
            return

        await _seed_users(session)
        await _seed_candidates(session)
        await session.commit()


async def _seed_users(session: AsyncSession):
    for u in SEED_USERS:
        user = User(
            email=u["email"],
            hashed_password=hash_password(u["password"]),
            role=u["role"],
        )
        session.add(user)


async def _seed_candidates(session: AsyncSession):
    for c in SEED_CANDIDATES:
        candidate = Candidate(
            name=c["name"],
            email=c["email"],
            role_applied=c["role_applied"],
            status=c["status"],
            skills=c["skills"],
        )
        session.add(candidate)
