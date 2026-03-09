"""
Clean Data Models for Real Data Processing
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class UserProfile:
    name: str
    email: str
    github_username: str | None
    skills: list[str]
    interests: list[str]
    goals: list[str]
    experience_level: str
    content_preferences: dict[str, str]


@dataclass
class ResearchData:
    trending_repos: list[dict[str, Any]]
    hackernews_stories: list[dict[str, Any]]
    user_context: dict[str, Any]
    language_trends: dict[str, list[dict[str, Any]]]
    timestamp: str


@dataclass
class EditorialContent:
    headline: str
    content: str
    key_insights: list[str]
    date: str
    data_sources: list[str]


@dataclass
class TopicSelection:
    selected_topic: str
    angle: str
    supporting_data: list[str]
    why_now: str
    personal_relevance: str
