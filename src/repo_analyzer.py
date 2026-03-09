"""
Repository Analyzer - Extracts file-level details from GitHub repos
Provides specific file names, line counts, and code patterns for hyper-personalization
"""

import asyncio
import base64
from typing import Any

import httpx


class RepoFileAnalyzer:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}

    async def analyze_repo_files(self, username: str, repo_name: str) -> dict[str, Any]:
        """
        Analyze a repository to extract file-level details:
        - Main files (with line counts)
        - Directory structure
        - Key patterns (e.g., number of classes, functions, imports)
        """

        try:
            async with httpx.AsyncClient() as client:
                # Get repository tree
                tree_url = f"https://api.github.com/repos/{username}/{repo_name}/git/trees/main?recursive=1"
                response = await client.get(tree_url, headers=self.headers)

                if response.status_code == 404:
                    # Try 'master' branch
                    tree_url = f"https://api.github.com/repos/{username}/{repo_name}/git/trees/master?recursive=1"
                    response = await client.get(tree_url, headers=self.headers)

                if response.status_code != 200:
                    return self._create_fallback_analysis(repo_name)

                tree_data = response.json()
                tree_items = tree_data.get("tree", [])

                # Filter for important files (source code, configs)
                important_extensions = {
                    ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".java",
                    ".go",
                    ".rs",
                    ".rb",
                    ".php",
                    ".cpp",
                    ".c",
                    ".h",
                }

                files = []
                for item in tree_items:
                    if item["type"] == "blob":
                        path = item["path"]
                        ext = "." + path.split(".")[-1] if "." in path else ""

                        if ext in important_extensions:
                            files.append({"path": path, "size": item.get("size", 0), "sha": item["sha"]})

                # Get line counts for top files (increased to 10 for more context)
                analyzed_files = []
                for file_info in files[:10]:
                    line_count = await self._get_file_line_count(client, username, repo_name, file_info["path"])
                    analyzed_files.append(
                        {"path": file_info["path"], "size_bytes": file_info["size"], "lines": line_count}
                    )

                return {
                    "repo_name": repo_name,
                    "total_files": len(files),
                    "analyzed_files": analyzed_files,
                    "primary_files": [f["path"] for f in analyzed_files[:3]],
                    "file_summary": self._generate_file_summary(analyzed_files),
                }

        except Exception as e:
            print(f"⚠️ Error analyzing {repo_name}: {e}")
            return self._create_fallback_analysis(repo_name)

    async def _get_file_line_count(
        self, client: httpx.AsyncClient, username: str, repo_name: str, file_path: str
    ) -> int:
        """Get line count for a specific file"""
        try:
            file_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{file_path}"
            response = await client.get(file_url, headers=self.headers, timeout=10.0)

            if response.status_code == 200:
                content_data = response.json()
                if content_data.get("encoding") == "base64":
                    content = base64.b64decode(content_data["content"]).decode("utf-8", errors="ignore")
                    return len(content.split("\n"))

            return 0
        except Exception as e:
            print(f"⚠️ Could not get line count for {file_path}: {e}")
            return 0

    def _generate_file_summary(self, files: list[dict]) -> str:
        """Generate a human-readable summary of files"""
        if not files:
            return "No files analyzed"

        summaries = []
        for f in files[:3]:
            filename = f["path"].split("/")[-1]
            lines = f["lines"]
            summaries.append(f"{filename} ({lines} lines)")

        return ", ".join(summaries)

    def _create_fallback_analysis(self, repo_name: str) -> dict[str, Any]:
        """Create fallback analysis when API fails"""
        return {
            "repo_name": repo_name,
            "total_files": 0,
            "analyzed_files": [],
            "primary_files": [],
            "file_summary": "Analysis unavailable",
        }

    async def analyze_multiple_repos(self, username: str, repo_names: list[str]) -> list[dict[str, Any]]:
        """Analyze multiple repositories concurrently"""
        tasks = [self.analyze_repo_files(username, repo_name) for repo_name in repo_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        analyses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️ Failed to analyze {repo_names[i]}: {result}")
                analyses.append(self._create_fallback_analysis(repo_names[i]))
            else:
                analyses.append(result)

        return analyses
