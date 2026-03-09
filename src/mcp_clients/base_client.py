"""
Base MCP Client - template for all MCP clients
"""

from abc import ABC, abstractmethod


class BaseMCPClient(ABC):
    """Base class for all MCP clients"""

    def __init__(self, config, client_name: str):
        self.config = config
        self.client_name = client_name
        self.is_connected = False

    def _log_success(self, message: str):
        """Log success message"""
        print(f"✅ {self.client_name}: {message}")

    def _log_error(self, operation: str, error: Exception):
        """Log error message"""
        print(f"❌ {self.client_name} {operation} failed: {error}")

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the MCP client"""
        pass

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text (simple implementation)"""
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html_content)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
