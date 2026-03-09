"""
Skill Analyzer Engine - The core intelligence layer for career analysis.

Industry-driven approach:
- Detects frameworks from dependency files (package.json, requirements.txt, etc.)
- Scores proficiency based on repo count, recency, code volume, and complexity
- Maps skills to industry domains (frontend, backend, ML, DevOps, etc.)
- Identifies gaps by comparing user stack against market trends
- Uses Claude only for narrative synthesis, not mechanical analysis
"""
import asyncio
import json
import base64
import re
import httpx
import anthropic
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


# ============================================================
# FRAMEWORK DETECTION RULES
# Industry-standard mapping of dependency files → technologies
# ============================================================
DEPENDENCY_FILE_MAP = {
    "package.json": "npm",
    "requirements.txt": "pip",
    "Pipfile": "pipenv",
    "pyproject.toml": "python",
    "Cargo.toml": "cargo",
    "go.mod": "go",
    "Gemfile": "ruby",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "composer.json": "composer",
    "pubspec.yaml": "dart",
    "mix.exs": "elixir",
    "Package.swift": "swift",
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
    "docker-compose.yaml": "docker",
    ".github/workflows": "github_actions",
    "terraform": "terraform",
    "serverless.yml": "serverless",
    "vercel.json": "vercel",
    "netlify.toml": "netlify",
    "railway.toml": "railway",
    "next.config.js": "nextjs",
    "next.config.ts": "nextjs",
    "next.config.mjs": "nextjs",
    "nuxt.config.ts": "nuxt",
    "vite.config.ts": "vite",
    "tailwind.config.js": "tailwind",
    "tailwind.config.ts": "tailwind",
    "tsconfig.json": "typescript",
    ".eslintrc": "eslint",
    "prisma/schema.prisma": "prisma",
    "drizzle.config.ts": "drizzle",
    "supabase": "supabase",
}

# NPM package → framework/tool mapping
NPM_FRAMEWORK_MAP = {
    # Frontend frameworks
    "react": ("React", "frontend"),
    "react-dom": ("React", "frontend"),
    "next": ("Next.js", "frontend"),
    "vue": ("Vue.js", "frontend"),
    "nuxt": ("Nuxt.js", "frontend"),
    "svelte": ("Svelte", "frontend"),
    "@sveltejs/kit": ("SvelteKit", "frontend"),
    "angular": ("Angular", "frontend"),
    "@angular/core": ("Angular", "frontend"),
    "solid-js": ("Solid.js", "frontend"),
    "astro": ("Astro", "frontend"),
    "remix": ("Remix", "frontend"),
    "@remix-run/react": ("Remix", "frontend"),
    # Styling
    "tailwindcss": ("Tailwind CSS", "frontend"),
    "styled-components": ("styled-components", "frontend"),
    "@chakra-ui/react": ("Chakra UI", "frontend"),
    "@radix-ui/react-dialog": ("Radix UI", "frontend"),
    "shadcn-ui": ("shadcn/ui", "frontend"),
    # State management
    "zustand": ("Zustand", "frontend"),
    "redux": ("Redux", "frontend"),
    "@reduxjs/toolkit": ("Redux Toolkit", "frontend"),
    "jotai": ("Jotai", "frontend"),
    "recoil": ("Recoil", "frontend"),
    # Backend
    "express": ("Express.js", "backend"),
    "fastify": ("Fastify", "backend"),
    "hono": ("Hono", "backend"),
    "koa": ("Koa", "backend"),
    "nestjs": ("NestJS", "backend"),
    "@nestjs/core": ("NestJS", "backend"),
    "trpc": ("tRPC", "backend"),
    "@trpc/server": ("tRPC", "backend"),
    # Database
    "prisma": ("Prisma", "database"),
    "@prisma/client": ("Prisma", "database"),
    "drizzle-orm": ("Drizzle ORM", "database"),
    "mongoose": ("Mongoose", "database"),
    "typeorm": ("TypeORM", "database"),
    "sequelize": ("Sequelize", "database"),
    "@supabase/supabase-js": ("Supabase", "database"),
    "firebase": ("Firebase", "database"),
    # AI/ML
    "openai": ("OpenAI SDK", "ai_ml"),
    "@anthropic-ai/sdk": ("Anthropic SDK", "ai_ml"),
    "langchain": ("LangChain", "ai_ml"),
    "@langchain/core": ("LangChain", "ai_ml"),
    "ai": ("Vercel AI SDK", "ai_ml"),
    # Testing
    "jest": ("Jest", "testing"),
    "vitest": ("Vitest", "testing"),
    "@testing-library/react": ("Testing Library", "testing"),
    "playwright": ("Playwright", "testing"),
    "cypress": ("Cypress", "testing"),
    # DevOps/Infra
    "docker": ("Docker", "devops"),
    "aws-sdk": ("AWS SDK", "devops"),
    "@aws-sdk/client-s3": ("AWS SDK v3", "devops"),
    # Mobile
    "react-native": ("React Native", "mobile"),
    "expo": ("Expo", "mobile"),
    "@capacitor/core": ("Capacitor", "mobile"),
}

# Python package → framework/tool mapping
PYTHON_FRAMEWORK_MAP = {
    "django": ("Django", "backend"),
    "flask": ("Flask", "backend"),
    "fastapi": ("FastAPI", "backend"),
    "uvicorn": ("Uvicorn", "backend"),
    "starlette": ("Starlette", "backend"),
    "celery": ("Celery", "backend"),
    # Data/ML
    "pandas": ("Pandas", "data_science"),
    "numpy": ("NumPy", "data_science"),
    "scikit-learn": ("scikit-learn", "ai_ml"),
    "sklearn": ("scikit-learn", "ai_ml"),
    "tensorflow": ("TensorFlow", "ai_ml"),
    "torch": ("PyTorch", "ai_ml"),
    "pytorch": ("PyTorch", "ai_ml"),
    "transformers": ("Hugging Face", "ai_ml"),
    "langchain": ("LangChain", "ai_ml"),
    "openai": ("OpenAI SDK", "ai_ml"),
    "anthropic": ("Anthropic SDK", "ai_ml"),
    # Database
    "sqlalchemy": ("SQLAlchemy", "database"),
    "alembic": ("Alembic", "database"),
    "prisma": ("Prisma", "database"),
    "supabase": ("Supabase", "database"),
    "pymongo": ("PyMongo", "database"),
    "redis": ("Redis", "database"),
    # Web scraping
    "beautifulsoup4": ("BeautifulSoup", "data_science"),
    "scrapy": ("Scrapy", "data_science"),
    "selenium": ("Selenium", "testing"),
    # DevOps
    "boto3": ("AWS SDK", "devops"),
    "docker": ("Docker SDK", "devops"),
    "ansible": ("Ansible", "devops"),
    # Testing
    "pytest": ("Pytest", "testing"),
    "unittest": ("unittest", "testing"),
}

# Cargo.toml → Rust framework mapping
RUST_FRAMEWORK_MAP = {
    "actix-web": ("Actix Web", "backend"),
    "axum": ("Axum", "backend"),
    "rocket": ("Rocket", "backend"),
    "tokio": ("Tokio", "backend"),
    "serde": ("Serde", "backend"),
    "diesel": ("Diesel", "database"),
    "sqlx": ("SQLx", "database"),
    "wasm-bindgen": ("WebAssembly", "frontend"),
    "tauri": ("Tauri", "desktop"),
}

# Domain classification based on detected technologies
DOMAIN_SIGNALS = {
    "frontend": ["React", "Vue.js", "Svelte", "Angular", "Next.js", "Nuxt.js",
                  "Tailwind CSS", "CSS", "HTML", "Astro", "Remix", "SvelteKit"],
    "backend": ["Express.js", "FastAPI", "Django", "Flask", "NestJS", "Spring",
                "Actix Web", "Axum", "Hono", "Fastify", "tRPC"],
    "ai_ml": ["TensorFlow", "PyTorch", "scikit-learn", "Hugging Face", "LangChain",
              "OpenAI SDK", "Anthropic SDK", "Vercel AI SDK", "Pandas", "NumPy"],
    "data_science": ["Pandas", "NumPy", "Jupyter", "R", "Matplotlib", "Plotly",
                     "BeautifulSoup", "Scrapy"],
    "devops": ["Docker", "Kubernetes", "Terraform", "AWS SDK", "GitHub Actions",
               "Ansible", "Jenkins", "Vercel", "Railway", "Netlify"],
    "mobile": ["React Native", "Expo", "Flutter", "Swift", "Kotlin", "Capacitor"],
    "database": ["Prisma", "Drizzle ORM", "Supabase", "Firebase", "MongoDB",
                 "PostgreSQL", "Redis", "SQLAlchemy"],
    "systems": ["Rust", "C", "C++", "Go", "Tokio", "WebAssembly"],
    "blockchain": ["Solidity", "Hardhat", "Ethers.js", "Web3.js", "Foundry"],
    "security": ["Burp", "Nmap", "Metasploit", "OWASP"],
}


class SkillAnalyzer:
    """
    Deep skill analysis engine that produces a comprehensive developer profile.

    Strategy:
    1. Fetch repos with metadata (languages, topics, dates)
    2. For top active repos, fetch dependency files to detect actual frameworks
    3. Score each skill by: repo count, recency, code volume, complexity signals
    4. Map skills to industry domains
    5. Use Claude for narrative synthesis (career stage, strengths, growth areas)
    6. Identify skill gaps based on market trends and adjacent technologies
    """

    def __init__(self, config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    async def analyze(self, github_token: str, username: str,
                      user_interests: List[str] = None,
                      experience_level: str = "intermediate") -> Dict[str, Any]:
        """
        Full skill analysis pipeline. Returns a complete SkillSnapshot.

        This is designed to run in <15 seconds for the "wow moment" on first login.
        """
        user_interests = user_interests or []

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {github_token}",
            "User-Agent": "Persnally-Career/1.0"
        }

        async with httpx.AsyncClient(timeout=30.0) as http:
            # Step 1: Fetch user profile + repos + stars in parallel
            user_data, repos, starred = await asyncio.gather(
                self._fetch_user(http, headers, username),
                self._fetch_repos(http, headers),
                self._fetch_starred(http, headers, username),
            )

            if not repos:
                return self._empty_snapshot(username)

            # Step 2: Analyze language distribution from GitHub's language data
            languages = self._analyze_languages(repos)

            # Step 3: Detect frameworks from dependency files (top 8 active repos)
            active_repos = self._get_active_repos(repos, limit=8)
            frameworks = await self._detect_frameworks(http, headers, active_repos)

            # Step 4: Build skill scores
            skills = self._build_skill_scores(languages, frameworks, repos, active_repos)

            # Step 5: Classify domains
            domains = self._classify_domains(skills, languages, frameworks)

            # Step 6: Identify skill gaps
            gaps = self._identify_gaps(skills, domains, user_interests, starred)

            # Step 7: AI synthesis — career narrative, strengths, growth areas
            synthesis = await self._synthesize_with_ai(
                username, user_data, languages, frameworks, skills,
                domains, gaps, active_repos, starred, user_interests,
                experience_level
            )

        return {
            "username": username,
            "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "skills": skills,
            "languages": languages,
            "frameworks": frameworks,
            "domains": domains,
            "experience_level": synthesis.get("experience_level", experience_level),
            "career_stage": synthesis.get("career_stage", "professional"),
            "specialization": synthesis.get("specialization", ""),
            "summary": synthesis.get("summary", ""),
            "strengths": synthesis.get("strengths", []),
            "growth_areas": synthesis.get("growth_areas", []),
            "skill_gaps": gaps,
            "repo_count": len(repos),
            "active_repo_count": len(active_repos),
            "top_repos": [
                {
                    "name": r.get("name", ""),
                    "language": r.get("language", ""),
                    "stars": r.get("stargazers_count", 0),
                    "description": (r.get("description") or "")[:100],
                    "updated_at": r.get("pushed_at", ""),
                }
                for r in active_repos[:5]
            ],
        }

    # ============================================================
    # DATA FETCHING
    # ============================================================

    async def _fetch_user(self, http: httpx.AsyncClient, headers: dict,
                          username: str) -> dict:
        try:
            resp = await http.get(f"https://api.github.com/users/{username}",
                                  headers=headers)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {}

    async def _fetch_repos(self, http: httpx.AsyncClient, headers: dict) -> list:
        """Fetch all user repos (including private if token allows)."""
        try:
            resp = await http.get(
                "https://api.github.com/user/repos",
                params={"sort": "pushed", "per_page": 100, "visibility": "all"},
                headers=headers,
            )
            if resp.status_code == 200:
                repos = resp.json()
                # Filter out forks for skill analysis (forks don't represent your skills)
                return [r for r in repos if not r.get("fork", False)]
            return []
        except Exception:
            return []

    async def _fetch_starred(self, http: httpx.AsyncClient, headers: dict,
                             username: str) -> list:
        try:
            resp = await http.get(
                f"https://api.github.com/users/{username}/starred",
                params={"per_page": 50},
                headers=headers,
            )
            return resp.json() if resp.status_code == 200 else []
        except Exception:
            return []

    # ============================================================
    # LANGUAGE ANALYSIS
    # ============================================================

    def _analyze_languages(self, repos: list) -> Dict[str, Any]:
        """
        Analyze language distribution across all repos.
        Uses GitHub's detected language + topics for accuracy.
        """
        lang_repos = defaultdict(list)
        lang_stars = defaultdict(int)

        for repo in repos:
            lang = repo.get("language")
            if lang:
                lang_repos[lang].append(repo["name"])
                lang_stars[lang] += repo.get("stargazers_count", 0)

        total_repos = max(len(repos), 1)
        languages = {}

        for lang, repo_names in lang_repos.items():
            count = len(repo_names)
            # Check recency — any of these repos updated in last 90 days?
            recent = any(
                self._days_since(r.get("pushed_at", "")) < 90
                for r in repos if r.get("language") == lang
            )
            languages[lang] = {
                "percentage": round(count / total_repos * 100, 1),
                "repos": count,
                "stars": lang_stars[lang],
                "recent": recent,
            }

        # Sort by repo count
        return dict(sorted(languages.items(), key=lambda x: x[1]["repos"], reverse=True))

    # ============================================================
    # FRAMEWORK DETECTION (the differentiator)
    # ============================================================

    def _get_active_repos(self, repos: list, limit: int = 8) -> list:
        """Get most recently active non-fork repos."""
        sorted_repos = sorted(
            repos,
            key=lambda r: r.get("pushed_at", ""),
            reverse=True,
        )
        return sorted_repos[:limit]

    async def _detect_frameworks(self, http: httpx.AsyncClient, headers: dict,
                                  repos: list) -> List[Dict[str, Any]]:
        """
        For each active repo, fetch key dependency files and extract frameworks.
        This is what makes the analysis 10x better than just counting languages.
        """
        detected = {}  # framework_name -> {info}

        # Fetch dependency files in parallel, batched per repo
        tasks = []
        for repo in repos:
            tasks.append(self._analyze_repo_deps(http, headers, repo))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for repo, result in zip(repos, results):
            if isinstance(result, Exception):
                continue
            for fw_name, fw_info in result.items():
                if fw_name in detected:
                    detected[fw_name]["repos"].append(repo["name"])
                    detected[fw_name]["confidence"] = min(
                        1.0, detected[fw_name]["confidence"] + 0.1
                    )
                else:
                    detected[fw_name] = {
                        "name": fw_name,
                        "category": fw_info["category"],
                        "confidence": fw_info["confidence"],
                        "source": fw_info["source"],
                        "repos": [repo["name"]],
                    }

        return sorted(detected.values(), key=lambda x: x["confidence"], reverse=True)

    async def _analyze_repo_deps(self, http: httpx.AsyncClient, headers: dict,
                                  repo: dict) -> Dict[str, Dict]:
        """Analyze a single repo's dependency files."""
        detected = {}
        full_name = repo["full_name"]

        # Check for common dependency files
        dep_checks = [
            ("package.json", self._parse_npm),
            ("requirements.txt", self._parse_pip),
            ("Cargo.toml", self._parse_cargo),
            ("go.mod", self._parse_gomod),
        ]

        # Also detect from repo topics
        for topic in repo.get("topics", []):
            topic_lower = topic.lower()
            topic_map = {
                "nextjs": ("Next.js", "frontend"),
                "react": ("React", "frontend"),
                "vue": ("Vue.js", "frontend"),
                "svelte": ("Svelte", "frontend"),
                "django": ("Django", "backend"),
                "fastapi": ("FastAPI", "backend"),
                "flask": ("Flask", "backend"),
                "docker": ("Docker", "devops"),
                "kubernetes": ("Kubernetes", "devops"),
                "tensorflow": ("TensorFlow", "ai_ml"),
                "pytorch": ("PyTorch", "ai_ml"),
                "machine-learning": ("ML", "ai_ml"),
                "rust": ("Rust", "systems"),
                "typescript": ("TypeScript", "frontend"),
                "tailwindcss": ("Tailwind CSS", "frontend"),
                "supabase": ("Supabase", "database"),
                "prisma": ("Prisma", "database"),
                "graphql": ("GraphQL", "backend"),
            }
            if topic_lower in topic_map:
                name, cat = topic_map[topic_lower]
                detected[name] = {"category": cat, "confidence": 0.6, "source": "topic"}

        # Fetch and parse actual dependency files
        for filename, parser in dep_checks:
            try:
                resp = await http.get(
                    f"https://api.github.com/repos/{full_name}/contents/{filename}",
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
                    parsed = parser(content)
                    for fw_name, fw_info in parsed.items():
                        # Dependency file detection is high confidence
                        fw_info["confidence"] = max(fw_info.get("confidence", 0.8), 0.8)
                        detected[fw_name] = fw_info

                await asyncio.sleep(0.05)  # Gentle rate limiting
            except Exception:
                continue

        # Detect from config files (no content parsing needed, just existence)
        config_checks = {
            "next.config.js": ("Next.js", "frontend"),
            "next.config.ts": ("Next.js", "frontend"),
            "next.config.mjs": ("Next.js", "frontend"),
            "nuxt.config.ts": ("Nuxt.js", "frontend"),
            "vite.config.ts": ("Vite", "frontend"),
            "tailwind.config.js": ("Tailwind CSS", "frontend"),
            "tailwind.config.ts": ("Tailwind CSS", "frontend"),
            "tsconfig.json": ("TypeScript", "frontend"),
            "Dockerfile": ("Docker", "devops"),
            "docker-compose.yml": ("Docker Compose", "devops"),
        }

        try:
            resp = await http.get(
                f"https://api.github.com/repos/{full_name}/contents/",
                headers=headers,
            )
            if resp.status_code == 200:
                files = {f["name"]: f for f in resp.json() if isinstance(f, dict)}
                for filename, (name, cat) in config_checks.items():
                    if filename in files:
                        if name not in detected:
                            detected[name] = {
                                "category": cat,
                                "confidence": 0.7,
                                "source": filename,
                            }
        except Exception:
            pass

        return detected

    def _parse_npm(self, content: str) -> Dict[str, Dict]:
        """Parse package.json for framework detection."""
        detected = {}
        try:
            pkg = json.loads(content)
            all_deps = {}
            all_deps.update(pkg.get("dependencies", {}))
            all_deps.update(pkg.get("devDependencies", {}))

            for dep_name in all_deps:
                dep_lower = dep_name.lower()
                if dep_lower in NPM_FRAMEWORK_MAP:
                    fw_name, category = NPM_FRAMEWORK_MAP[dep_lower]
                    detected[fw_name] = {
                        "category": category,
                        "confidence": 0.9,
                        "source": "package.json",
                    }
        except (json.JSONDecodeError, KeyError):
            pass
        return detected

    def _parse_pip(self, content: str) -> Dict[str, Dict]:
        """Parse requirements.txt for framework detection."""
        detected = {}
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Extract package name (before ==, >=, etc.)
            pkg = re.split(r"[>=<!\[]", line)[0].strip().lower()
            if pkg in PYTHON_FRAMEWORK_MAP:
                fw_name, category = PYTHON_FRAMEWORK_MAP[pkg]
                detected[fw_name] = {
                    "category": category,
                    "confidence": 0.9,
                    "source": "requirements.txt",
                }
        return detected

    def _parse_cargo(self, content: str) -> Dict[str, Dict]:
        """Parse Cargo.toml for Rust framework detection."""
        detected = {}
        in_deps = False
        for line in content.split("\n"):
            if "[dependencies]" in line or "[dev-dependencies]" in line:
                in_deps = True
                continue
            if line.startswith("[") and in_deps:
                in_deps = False
                continue
            if in_deps and "=" in line:
                pkg = line.split("=")[0].strip().lower()
                if pkg in RUST_FRAMEWORK_MAP:
                    fw_name, category = RUST_FRAMEWORK_MAP[pkg]
                    detected[fw_name] = {
                        "category": category,
                        "confidence": 0.9,
                        "source": "Cargo.toml",
                    }
        return detected

    def _parse_gomod(self, content: str) -> Dict[str, Dict]:
        """Parse go.mod for Go framework detection."""
        detected = {}
        go_map = {
            "github.com/gin-gonic/gin": ("Gin", "backend"),
            "github.com/gofiber/fiber": ("Fiber", "backend"),
            "github.com/labstack/echo": ("Echo", "backend"),
            "github.com/gorilla/mux": ("Gorilla Mux", "backend"),
            "gorm.io/gorm": ("GORM", "database"),
            "github.com/jmoiron/sqlx": ("sqlx", "database"),
        }
        for line in content.split("\n"):
            for path, (name, cat) in go_map.items():
                if path in line:
                    detected[name] = {
                        "category": cat,
                        "confidence": 0.9,
                        "source": "go.mod",
                    }
        return detected

    # ============================================================
    # SKILL SCORING
    # ============================================================

    def _build_skill_scores(self, languages: dict, frameworks: list,
                            all_repos: list, active_repos: list) -> Dict[str, Any]:
        """
        Build a unified skill map with proficiency scores.

        Scoring formula (0-1):
          base = min(repo_count / 5, 0.4)     # More repos = more experience
          recency = 0.3 if used in last 90d    # Recent usage matters
          volume = min(percentage / 30, 0.2)   # Code volume
          complexity = 0.1 if in active repos  # Active development
        """
        skills = {}

        # Score languages
        for lang, data in languages.items():
            repo_count = data["repos"]
            recent = data.get("recent", False)

            base = min(repo_count / 5, 0.4)
            recency = 0.3 if recent else 0.1
            volume = min(data["percentage"] / 30, 0.2)
            complexity = 0.1 if any(
                r.get("language") == lang for r in active_repos
            ) else 0.0

            score = round(min(base + recency + volume + complexity, 1.0), 2)

            skills[lang] = {
                "level": score,
                "category": "language",
                "repos": repo_count,
                "recent": recent,
            }

        # Score frameworks
        for fw in frameworks:
            fw_name = fw["name"]
            repo_count = len(fw.get("repos", []))
            confidence = fw.get("confidence", 0.5)

            # Frameworks detected from actual deps are more meaningful
            base = min(repo_count / 3, 0.4)
            source_bonus = 0.2 if fw.get("source") in ("package.json", "requirements.txt", "Cargo.toml", "go.mod") else 0.1
            recency = 0.3 if any(
                r["name"] in fw.get("repos", []) for r in active_repos
            ) else 0.1

            score = round(min(base + source_bonus + recency + confidence * 0.1, 1.0), 2)

            skills[fw_name] = {
                "level": score,
                "category": fw.get("category", "tool"),
                "repos": repo_count,
                "recent": recency > 0.1,
                "detected_from": fw.get("source", ""),
            }

        return dict(sorted(skills.items(), key=lambda x: x[1]["level"], reverse=True))

    # ============================================================
    # DOMAIN CLASSIFICATION
    # ============================================================

    def _classify_domains(self, skills: dict, languages: dict,
                          frameworks: list) -> Dict[str, float]:
        """
        Classify user's domain expertise using weighted signals.
        Returns domain -> confidence (0-1).
        """
        domain_scores = defaultdict(float)
        all_tech = set(skills.keys())

        for domain, signals in DOMAIN_SIGNALS.items():
            matches = all_tech & set(signals)
            if matches:
                # Weight by skill level
                total_weight = sum(
                    skills.get(m, {}).get("level", 0) for m in matches
                )
                # Normalize: 3+ strong matches = 1.0
                domain_scores[domain] = round(min(total_weight / 2.0, 1.0), 2)

        # Ensure at least one domain if we have any skills
        if skills and not domain_scores:
            domain_scores["general"] = 0.5

        return dict(sorted(domain_scores.items(), key=lambda x: x[1], reverse=True))

    # ============================================================
    # GAP ANALYSIS
    # ============================================================

    def _identify_gaps(self, skills: dict, domains: dict,
                       user_interests: list, starred: list) -> List[Dict[str, Any]]:
        """
        Identify skill gaps by analyzing:
        1. Technologies in starred repos the user doesn't have
        2. Adjacent technologies in their strongest domains
        3. User-stated interests they have no repos for
        """
        gaps = []
        user_techs = set(k.lower() for k in skills.keys())

        # 1. From starred repos — what they're interested in but don't use
        starred_techs = defaultdict(int)
        for repo in starred[:30]:
            lang = repo.get("language", "")
            if lang:
                starred_techs[lang] += 1
            for topic in repo.get("topics", []):
                starred_techs[topic] += 1

        for tech, count in sorted(starred_techs.items(), key=lambda x: x[1], reverse=True):
            if tech.lower() not in user_techs and count >= 2:
                gaps.append({
                    "skill_name": tech,
                    "reason": f"You've starred {count} repos using {tech} but don't use it yet",
                    "category": "emerging",
                    "market_demand": 0.6,
                    "gap_score": round(min(count / 5, 1.0), 2),
                })
                if len(gaps) >= 3:
                    break

        # 2. Adjacent technologies based on domain
        adjacency_map = {
            "frontend": ["TypeScript", "Next.js", "Tailwind CSS", "Testing Library", "Playwright"],
            "backend": ["Docker", "Redis", "PostgreSQL", "GraphQL", "tRPC"],
            "ai_ml": ["PyTorch", "Hugging Face", "LangChain", "MLOps", "Vector DB"],
            "devops": ["Kubernetes", "Terraform", "GitHub Actions", "Prometheus"],
            "mobile": ["React Native", "Expo", "Flutter"],
            "database": ["Redis", "PostgreSQL", "Prisma", "Drizzle ORM"],
        }

        top_domain = max(domains, key=domains.get) if domains else "general"
        adjacent = adjacency_map.get(top_domain, [])
        for tech in adjacent:
            if tech.lower() not in user_techs:
                gaps.append({
                    "skill_name": tech,
                    "reason": f"Common in {top_domain} — complements your existing stack",
                    "category": "complementary",
                    "market_demand": 0.7,
                    "gap_score": 0.5,
                })
                if len(gaps) >= 6:
                    break

        # 3. From stated interests with no matching repos
        interest_tech_map = {
            "ai/ml": ["PyTorch", "TensorFlow", "LangChain"],
            "web development": ["React", "Next.js", "TypeScript"],
            "mobile development": ["React Native", "Flutter", "Swift"],
            "devops/cloud": ["Docker", "Kubernetes", "Terraform"],
            "blockchain/web3": ["Solidity", "Hardhat", "Ethers.js"],
            "cybersecurity": ["Burp Suite", "OWASP", "Penetration Testing"],
        }

        for interest in user_interests:
            interest_lower = interest.lower()
            if interest_lower in interest_tech_map:
                for tech in interest_tech_map[interest_lower]:
                    if tech.lower() not in user_techs and not any(
                        g["skill_name"] == tech for g in gaps
                    ):
                        gaps.append({
                            "skill_name": tech,
                            "reason": f"Matches your stated interest in {interest}",
                            "category": "recommended",
                            "market_demand": 0.8,
                            "gap_score": 0.6,
                        })
                        break  # One gap per interest

        return gaps[:8]  # Cap at 8 gaps

    # ============================================================
    # AI SYNTHESIS
    # ============================================================

    async def _synthesize_with_ai(self, username: str, user_data: dict,
                                   languages: dict, frameworks: list,
                                   skills: dict, domains: dict,
                                   gaps: list, active_repos: list,
                                   starred: list, user_interests: list,
                                   experience_level: str) -> dict:
        """
        Use Claude to generate a human-readable career narrative.
        This is the ONLY AI call in the pipeline — everything else is deterministic.
        """
        # Build a concise summary for Claude
        top_skills = list(skills.items())[:10]
        top_domains = list(domains.items())[:5]
        active_repo_summary = [
            f"{r['name']} ({r.get('language', 'N/A')}): {(r.get('description') or 'No desc')[:60]}"
            for r in active_repos[:5]
        ]
        starred_summary = [
            f"{r.get('full_name', r.get('name', 'unknown'))} ({r.get('language', 'N/A')})"
            for r in starred[:8]
        ]

        prompt = f"""Analyze this developer's GitHub profile and generate a career intelligence summary.

DEVELOPER: {username}
BIO: {user_data.get('bio', 'N/A')}
ACCOUNT AGE: {user_data.get('created_at', 'N/A')}
PUBLIC REPOS: {user_data.get('public_repos', 0)}
FOLLOWERS: {user_data.get('followers', 0)}
STATED INTERESTS: {', '.join(user_interests) if user_interests else 'Not specified'}
SELF-ASSESSED LEVEL: {experience_level}

TOP SKILLS (name: level 0-1):
{json.dumps(dict(top_skills), indent=2)}

DOMAIN STRENGTHS:
{json.dumps(dict(top_domains), indent=2)}

ACTIVE REPOS (last 30 days):
{chr(10).join(active_repo_summary) or 'None detected'}

RECENTLY STARRED:
{chr(10).join(starred_summary) or 'None'}

DETECTED SKILL GAPS:
{json.dumps([g['skill_name'] + ': ' + g['reason'] for g in gaps[:5]], indent=2)}

Generate a JSON response with EXACTLY these fields:
{{
  "summary": "2-3 sentence career narrative. Be specific about their tech identity — not generic. Reference actual technologies and repos. Example: 'Full-stack TypeScript developer specializing in Next.js applications with a growing interest in AI integration. Your recent work on [repo] shows strong frontend architecture skills, while your starred repos suggest you're exploring LLM tooling.'",
  "experience_level": "beginner|intermediate|advanced|expert (based on evidence, not self-assessment)",
  "career_stage": "student|early_career|professional|senior|lead|founder",
  "specialization": "A concise label like 'Full-Stack TypeScript' or 'ML Engineer' or 'DevOps & Cloud Infrastructure'",
  "strengths": ["List 3-5 specific strengths based on evidence. Not generic like 'problem solving' — specific like 'React component architecture' or 'Python data pipeline development'"],
  "growth_areas": ["List 3-4 specific growth recommendations. Not generic like 'learn more' — specific like 'Add TypeScript to your Python projects for type safety' or 'Your React skills would pair well with Next.js server components'"]
}}

Rules:
- Be SPECIFIC. Reference actual technologies, repos, and patterns you see.
- Be HONEST about experience level. 2 tutorial repos ≠ intermediate.
- Strengths must be evidenced by actual repos/skills, not assumed.
- Growth areas should be actionable and connected to their existing stack.
- Keep summary under 3 sentences. No fluff."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                temperature=0.3,  # Low temp for consistency
                system="You are a career intelligence analyst for developers. Return ONLY valid JSON, no markdown.",
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text.strip()
            # Strip markdown if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            return json.loads(content)

        except Exception as e:
            print(f"AI synthesis failed: {e}")
            # Deterministic fallback
            top_lang = list(languages.keys())[0] if languages else "General"
            top_domain = list(domains.keys())[0] if domains else "development"
            return {
                "summary": f"{top_lang} developer with focus on {top_domain}. Connect more repos for deeper analysis.",
                "experience_level": experience_level,
                "career_stage": "professional",
                "specialization": f"{top_lang} {top_domain.replace('_', ' ').title()}",
                "strengths": [f"{top_lang} development"],
                "growth_areas": [g["skill_name"] for g in gaps[:3]],
            }

    # ============================================================
    # HELPERS
    # ============================================================

    def _days_since(self, date_str: str) -> int:
        if not date_str:
            return 999
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - dt).days
        except Exception:
            return 999

    def _empty_snapshot(self, username: str) -> dict:
        return {
            "username": username,
            "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "skills": {},
            "languages": {},
            "frameworks": [],
            "domains": {},
            "experience_level": "beginner",
            "career_stage": "early_career",
            "specialization": "",
            "summary": "No public repositories found. Start building to unlock your skill profile!",
            "strengths": [],
            "growth_areas": ["Start with a project in your area of interest"],
            "skill_gaps": [],
            "repo_count": 0,
            "active_repo_count": 0,
            "top_repos": [],
        }
