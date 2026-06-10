from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import digest, github, health, preferences, skills, users

from config import FRONTEND_URL

app = FastAPI(title="Persnally API", version="1.0.0")

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add configured frontend URL (strip trailing slash)
if FRONTEND_URL:
    allowed_origins.append(FRONTEND_URL.rstrip("/"))

# Add common Vercel preview/production URLs
VERCEL_URLS = [
    "https://persnally.vercel.app",
    "https://persnally.com",
    "https://www.persnally.com",
]
for url in VERCEL_URLS:
    if url not in allowed_origins:
        allowed_origins.append(url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(preferences.router)
app.include_router(github.router)
app.include_router(skills.router)
app.include_router(digest.router)
