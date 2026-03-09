"""
Topic utilities for semantic/synonym matching across the Persnally system.
Provides synonym expansion and relevance scoring for interest-based content matching.
"""
from typing import List


SYNONYM_MAP = {
    "ai": ["artificial intelligence", "machine learning", "ml", "deep learning", "neural network", "llm", "large language model", "gpt", "claude", "transformer", "nlp", "natural language processing", "computer vision", "generative ai", "ai agent"],
    "ml": ["machine learning", "ai", "artificial intelligence", "deep learning", "neural network", "pytorch", "tensorflow", "scikit", "scikit-learn", "huggingface", "model training", "inference"],
    "deep learning": ["neural network", "pytorch", "tensorflow", "cnn", "rnn", "transformer", "gpu", "training"],
    "llm": ["large language model", "ai", "gpt", "claude", "gemini", "llama", "mistral", "transformer", "chatbot", "language model", "generative ai", "fine-tuning", "rag", "retrieval augmented generation", "langchain", "llamaindex", "ai agent"],
    "nlp": ["natural language processing", "text analysis", "sentiment analysis", "named entity recognition", "llm", "transformer"],
    "computer vision": ["opencv", "image recognition", "object detection", "yolo", "image processing"],
    "web3": ["blockchain", "crypto", "ethereum", "solidity", "defi", "nft", "smart contract", "web 3"],
    "blockchain": ["web3", "crypto", "ethereum", "solidity", "defi", "distributed ledger"],
    "crypto": ["cryptocurrency", "bitcoin", "ethereum", "defi", "web3", "blockchain"],
    "defi": ["decentralized finance", "yield", "liquidity", "amm", "web3", "ethereum"],
    "rust": ["systems programming", "memory safety", "cargo", "wasm", "webassembly", "tokio", "actix", "async rust"],
    "systems programming": ["rust", "c++", "c", "low level", "operating system", "kernel"],
    "go": ["golang", "goroutine", "gin", "fiber", "concurrency"],
    "react": ["reactjs", "react.js", "next.js", "nextjs", "remix", "gatsby", "jsx", "frontend"],
    "vue": ["vuejs", "vue.js", "nuxt", "nuxtjs", "frontend"],
    "svelte": ["sveltekit", "frontend"],
    "angular": ["angularjs", "frontend"],
    "next.js": ["nextjs", "react", "vercel", "frontend"],
    "frontend": ["react", "vue", "angular", "svelte", "nextjs", "next.js", "css", "ui", "ux", "web development"],
    "django": ["python", "backend", "web framework"],
    "fastapi": ["python", "backend", "api"],
    "flask": ["python", "backend", "web framework"],
    "express": ["node", "nodejs", "javascript", "backend"],
    "backend": ["api", "server", "database", "microservices", "rest", "graphql", "node", "express", "fastapi", "django"],
    "graphql": ["api", "query language", "apollo", "relay"],
    "kubernetes": ["k8s", "docker", "container", "orchestration", "devops", "cloud native"],
    "docker": ["container", "containerization", "kubernetes", "devops"],
    "terraform": ["infrastructure as code", "iac", "devops", "cloud"],
    "devops": ["docker", "kubernetes", "k8s", "ci/cd", "terraform", "aws", "cloud", "infrastructure"],
    "aws": ["amazon web services", "lambda", "s3", "ec2", "cloud", "serverless"],
    "cloud": ["aws", "gcp", "azure", "serverless", "lambda", "devops", "infrastructure"],
    "supabase": ["postgresql", "firebase alternative", "backend as a service", "baas"],
    "firebase": ["google cloud", "backend as a service", "baas", "realtime database"],
    "redis": ["cache", "in-memory", "pub/sub", "database"],
    "postgresql": ["postgres", "sql", "database", "relational"],
    "mongodb": ["nosql", "document database", "database"],
    "database": ["sql", "postgresql", "mongodb", "redis", "supabase", "firebase", "nosql"],
    "swift": ["ios", "apple", "xcode", "swiftui", "mobile"],
    "kotlin": ["android", "jetpack compose", "mobile", "jvm"],
    "flutter": ["dart", "mobile", "cross-platform", "ios", "android"],
    "react native": ["mobile", "cross-platform", "ios", "android", "javascript"],
    "mobile": ["ios", "android", "react native", "flutter", "swift", "kotlin"],
    "webassembly": ["wasm", "rust", "performance", "browser"],
    "microservices": ["distributed systems", "api gateway", "service mesh", "grpc"],
    "distributed systems": ["microservices", "consensus", "raft", "paxos", "cap theorem", "eventual consistency"],
    "data engineering": ["etl", "pipeline", "airflow", "spark", "kafka", "data warehouse", "dbt"],
    "data science": ["pandas", "numpy", "jupyter", "matplotlib", "statistics", "analytics", "visualization"],
    "data": ["data science", "data engineering", "analytics", "etl", "pipeline", "warehouse", "big data"],
    "startup": ["saas", "founder", "yc", "y combinator", "venture", "fundraising", "mvp", "product", "venture capital", "vc", "seed", "series a", "product market fit"],
    "saas": ["software as a service", "subscription", "b2b", "startup", "product"],
    "fintech": ["financial technology", "payments", "banking", "stripe", "plaid"],
    "devrel": ["developer relations", "developer experience", "dx", "developer advocacy", "community"],
    "security": ["cybersecurity", "infosec", "vulnerability", "penetration testing", "encryption", "auth"],
    "typescript": ["javascript", "js", "ts", "node", "deno", "bun"],
    "javascript": ["typescript", "js", "ts", "node", "react", "vue", "angular"],
    "python": ["django", "flask", "fastapi", "pytorch", "pandas", "numpy"],
    "open source": ["oss", "foss", "github", "contribute", "open-source"],
}


def expand_terms(terms: list[str]) -> list[str]:
    """Take a list of interest strings and return an expanded list including synonyms.

    The original terms are always included. Duplicates are removed while
    preserving order (originals first, then synonyms).
    """
    seen: set[str] = set()
    expanded: list[str] = []

    for term in terms:
        term_lower = term.lower().strip()
        if term_lower and term_lower not in seen:
            seen.add(term_lower)
            expanded.append(term_lower)

        # Check each word and the full term against the synonym map
        keys_to_check = [term_lower]
        # Also check individual words for multi-word interests
        if " " in term_lower:
            keys_to_check.extend(term_lower.split())

        for key in keys_to_check:
            if key in SYNONYM_MAP:
                for synonym in SYNONYM_MAP[key]:
                    syn_lower = synonym.lower()
                    if syn_lower not in seen:
                        seen.add(syn_lower)
                        expanded.append(syn_lower)

    return expanded


def relevance_score(text: str, interests: list[str]) -> int:
    """Score text against interests using synonym expansion.

    Scoring:
    - Direct keyword match: 2 points per matching interest
    - Synonym match: 1 point per matching synonym

    Args:
        text: The text to score (e.g. a title, description).
        interests: List of user interest strings.

    Returns:
        Integer relevance score (higher is better).
    """
    text_lower = text.lower()
    score = 0

    for interest in interests:
        interest_lower = interest.lower().strip()
        if not interest_lower:
            continue

        # Direct keyword match = 2 points
        if interest_lower in text_lower:
            score += 2
            continue

        # Synonym match = 1 point (check if any synonym of this interest appears)
        keys_to_check = [interest_lower]
        if " " in interest_lower:
            keys_to_check.extend(interest_lower.split())

        synonym_matched = False
        for key in keys_to_check:
            if key in SYNONYM_MAP:
                for synonym in SYNONYM_MAP[key]:
                    if synonym.lower() in text_lower:
                        synonym_matched = True
                        break
            if synonym_matched:
                break

        if synonym_matched:
            score += 1

    return score
