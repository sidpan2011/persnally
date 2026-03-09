"""
Content Formatter - Visual Enhancement for Email Content
Automatically highlights important information (dates, numbers, costs, repos)
"""

import re


class ContentFormatter:
    """Formats content to highlight important information visually"""

    @staticmethod
    def format_content(content: str, active_repos: list = None) -> str:
        """
        Simple content formatter - now relies on LLM-generated markdown highlighting.

        The LLM is instructed to use **bold markdown** for important information:
        - Company names, financial figures, key metrics, dates, etc.

        This method now just handles basic repository highlighting if needed.

        Args:
            content: Content text (may already contain markdown bold formatting)
            active_repos: List of user's active repos to highlight

        Returns:
            Content with minimal additional formatting
        """
        if not content:
            return content

        formatted = content

        # Only highlight repository names if they're not already in markdown bold
        if active_repos:
            for repo in active_repos:
                # Only highlight if not already in **bold** markdown
                repo_pattern = r"\b" + re.escape(repo) + r"\b"
                formatted = re.sub(
                    repo_pattern,
                    lambda m: (
                        m.group(0)
                        if "**" in formatted[max(0, m.start() - 10) : m.start() + 10]
                        else f"**{m.group(0)}**"
                    ),
                    formatted,
                    flags=re.IGNORECASE,
                )

        return formatted

    @staticmethod
    def add_source_attribution(content: str, source: str, source_url: str = None) -> str:
        """
        Add source attribution to content for transparency

        Args:
            content: Content text
            source: Source name (e.g., "GitHub Trending", "HackerNews")
            source_url: Optional source URL

        Returns:
            Content with source attribution appended
        """
        if not content:
            return content

        # Add a subtle source line at the end
        if source_url:
            attribution = f'<br><br><small style="color: #6b7280; font-size: 13px;">Source: <a href="{source_url}" style="color: #6b7280;">{source}</a></small>'
        else:
            attribution = f'<br><br><small style="color: #6b7280; font-size: 13px;">Source: {source}</small>'

        return content + attribution
