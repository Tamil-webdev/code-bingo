"""
Code Bingo Tournament - FastAPI Main Application
Entry point for the backend server.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import auth, teams, tournaments, questions, game


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle - initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Code Bingo Tournament",
    description="A multiplayer programming quiz game for coding competitions",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(tournaments.router)
app.include_router(questions.router)
app.include_router(game.router)


@app.get("/")
async def root():
    return {"message": "Code Bingo Tournament API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
