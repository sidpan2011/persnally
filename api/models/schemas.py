from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PreferencesUpdate(BaseModel):
    interests: list[str] = []
    experience_level: str = "intermediate"
    location: str = ""
    timezone: str = "UTC"
    content_style: str = "technical_with_business_context"
    prioritize_local: bool = True
    opportunity_types: list[str] = ["hackathons", "jobs", "funding"]
    send_frequency: str = "daily"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    onboarded: Optional[bool] = None


class NewsletterSummary(BaseModel):
    id: str
    subject: str
    headline: str
    status: str
    quality_score: Optional[float] = None
    sent_at: str
    item_count: int = 0


class GenerateResponse(BaseModel):
    job_id: str
    status: str


class JobStatus(BaseModel):
    id: str
    status: str
    newsletter_id: Optional[str] = None
    error: Optional[str] = None
    created_at: str
