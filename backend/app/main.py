from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import auth as auth_router
from app.routers import candidates as candidates_router
from app.seed import run_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await run_seed()
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
app.include_router(candidates_router.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
