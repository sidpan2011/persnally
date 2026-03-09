import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import FRONTEND_URL
from routers import health, users, preferences, newsletters, github, skills, digest


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start digest scheduler on startup
    from services.scheduler import digest_scheduler_loop
    task = asyncio.create_task(digest_scheduler_loop())
    yield
    task.cancel()


app = FastAPI(title="Persnally API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(preferences.router)
app.include_router(newsletters.router)
app.include_router(github.router)
app.include_router(skills.router)
app.include_router(digest.router)
