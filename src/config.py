"""
Clean Configuration Management
Real environment variables only
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Required API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")

    # Optional but Recommended
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    # Cloudflare Browser Rendering (for real content crawling)
    CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

    # Validation
    def __init__(self):
        if not self.ANTHROPIC_API_KEY:
            raise ValueError("❌ ANTHROPIC_API_KEY is required in .env")
        if not self.RESEND_API_KEY:
            raise ValueError("❌ RESEND_API_KEY is required in .env")

        # Warnings for optional but useful keys
        if not self.GITHUB_TOKEN:
            print("⚠️ GITHUB_TOKEN not found - GitHub API will be rate limited")
        if not self.CLOUDFLARE_ACCOUNT_ID or not self.CLOUDFLARE_API_TOKEN:
            print("⚠️ Cloudflare not configured - digests will use AI-generated content only")


# Global config instance
config = Config()


def get_config() -> Config:
    """Get application configuration"""
    return config
