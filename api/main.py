from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import FRONTEND_URL
from api.routers import health, users, preferences, newsletters, github

app = FastAPI(title="Persnally API", version="1.0.0")

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
