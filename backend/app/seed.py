import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.database import async_session
from app.models import Candidate, User

SEED_USERS = [
    {
        "username": "Admin User",
        "email": os.getenv("ADMIN_EMAIL", "admin@techkraft.com"),
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "role": "admin",
    },
    {"username": "Alice Rivera", "email": "alice@techkraft.com", "password": "reviewer123", "role": "reviewer"},
    {"username": "Bob Martinez", "email": "bob@techkraft.com", "password": "reviewer123", "role": "reviewer"},
]

SEED_CANDIDATES = [
    {"name": "Priya Sharma", "email": "priya.sharma@example.com", "role_applied": "Backend Engineer", "status": "new", "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]},
    {"name": "James Chen", "email": "james.chen@example.com", "role_applied": "Frontend Engineer", "status": "reviewed", "skills": ["React", "TypeScript", "Tailwind CSS", "Next.js"]},
    {"name": "Maria Garcia", "email": "maria.garcia@example.com", "role_applied": "Full Stack Engineer", "status": "new", "skills": ["Python", "React", "AWS", "GraphQL"]},
    {"name": "Alex Kim", "email": "alex.kim@example.com", "role_applied": "DevOps Engineer", "status": "hired", "skills": ["Kubernetes", "Terraform", "CI/CD", "AWS"]},
    {"name": "Sarah Johnson", "email": "sarah.johnson@example.com", "role_applied": "Backend Engineer", "status": "rejected", "skills": ["Java", "Spring Boot", "MySQL"]},
    {"name": "Liam Nguyen", "email": "liam.nguyen@example.com", "role_applied": "Frontend Engineer", "status": "new", "skills": ["React", "Vue.js", "CSS", "Figma"]},
    {"name": "Emma Davis", "email": "emma.davis@example.com", "role_applied": "Backend Engineer", "status": "new", "skills": ["Go", "gRPC", "PostgreSQL", "Redis"]},
    {"name": "Carlos Ruiz", "email": "carlos.ruiz@example.com", "role_applied": "Full Stack Engineer", "status": "reviewed", "skills": ["Node.js", "React", "MongoDB", "Docker"]},
    {"name": "Yuki Tanaka", "email": "yuki.tanaka@example.com", "role_applied": "DevOps Engineer", "status": "new", "skills": ["Docker", "AWS", "GitHub Actions", "Linux"]},
    {"name": "Fatima Hassan", "email": "fatima.hassan@example.com", "role_applied": "Backend Engineer", "status": "reviewed", "skills": ["Python", "Django", "Celery", "PostgreSQL"]},
    {"name": "Daniel Park", "email": "daniel.park@example.com", "role_applied": "Frontend Engineer", "status": "new", "skills": ["Angular", "TypeScript", "RxJS", "SCSS"]},
    {"name": "Olivia Brown", "email": "olivia.brown@example.com", "role_applied": "Full Stack Engineer", "status": "hired", "skills": ["Python", "React", "Docker", "PostgreSQL"]},
    {"name": "Raj Patel", "email": "raj.patel@example.com", "role_applied": "Backend Engineer", "status": "new", "skills": ["Java", "Spring Boot", "Kafka", "AWS"]},
    {"name": "Sofia Martinez", "email": "sofia.martinez@example.com", "role_applied": "Frontend Engineer", "status": "rejected", "skills": ["React", "JavaScript", "Webpack", "Jest"]},
    {"name": "Ahmed Khan", "email": "ahmed.khan@example.com", "role_applied": "DevOps Engineer", "status": "reviewed", "skills": ["Terraform", "Ansible", "AWS", "Python"]},
    {"name": "Chloe Wilson", "email": "chloe.wilson@example.com", "role_applied": "Full Stack Engineer", "status": "new", "skills": ["Ruby on Rails", "React", "PostgreSQL", "Heroku"]},
    {"name": "Miguel Torres", "email": "miguel.torres@example.com", "role_applied": "Backend Engineer", "status": "new", "skills": ["Python", "FastAPI", "SQLAlchemy", "Docker"]},
    {"name": "Hannah Lee", "email": "hannah.lee@example.com", "role_applied": "Frontend Engineer", "status": "new", "skills": ["Svelte", "TypeScript", "Tailwind CSS", "Vite"]},
    {"name": "David Wright", "email": "david.wright@example.com", "role_applied": "DevOps Engineer", "status": "hired", "skills": ["Kubernetes", "Helm", "ArgoCD", "Prometheus"]},
    {"name": "Aisha Mohammed", "email": "aisha.mohammed@example.com", "role_applied": "Full Stack Engineer", "status": "reviewed", "skills": ["Django", "React", "AWS", "Redis"]},
    {"name": "Lucas Evans", "email": "lucas.evans@example.com", "role_applied": "Backend Engineer", "status": "new", "skills": ["Rust", "Actix", "PostgreSQL", "Docker"]},
    {"name": "Mia Thompson", "email": "mia.thompson@example.com", "role_applied": "Frontend Engineer", "status": "reviewed", "skills": ["React", "Next.js", "GraphQL", "Storybook"]},
    {"name": "Arjun Reddy", "email": "arjun.reddy@example.com", "role_applied": "Backend Engineer", "status": "new", "skills": ["Python", "Flask", "MongoDB", "Docker"]},
    {"name": "Isabella Scott", "email": "isabella.scott@example.com", "role_applied": "Full Stack Engineer", "status": "new", "skills": ["TypeScript", "Node.js", "React", "PostgreSQL"]},
    {"name": "Ethan Clark", "email": "ethan.clark@example.com", "role_applied": "DevOps Engineer", "status": "rejected", "skills": ["Jenkins", "Docker", "Bash", "AWS"]},
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
            username=u["username"],
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
