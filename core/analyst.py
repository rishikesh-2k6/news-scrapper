"""
Analyst Module
--------------
Elite AI Intelligence Analyst + Content Strategist.

Interfaces with a local Ollama LLM to classify, score, extract, and
generate content-ready insights from scraped AI/tech articles.

Falls back to mock data when Ollama is unreachable (useful for dry-runs).
"""

import os
import json
import hashlib
import aiohttp
import asyncio
from typing import Dict, Optional

# Maximum characters of article markdown sent to the LLM to avoid OOM
MAX_CONTEXT_CHARS = 8000

# Timeout for Ollama requests (local inference can be slow on CPU)
OLLAMA_TIMEOUT = 300  # 5 minutes

# The elite analyst system prompt
SYSTEM_PROMPT = """You are an Elite AI Intelligence Analyst + Content Strategist.

Your goal is to extract HIGH-VALUE, CONTENT-WORTHY insights from AI/tech updates.

----------------------------------
STEP 1: CLASSIFY CONTENT
----------------------------------

Classify into ONE:

- NEW_MODEL → new AI model release
- FEATURE_UPDATE → new feature in existing AI product
- TOOL_RELEASE → new tool / API / framework
- RESEARCH → new method / architecture / paper
- INDUSTRY → company move / strategy
- LOW_VALUE → ignore

----------------------------------
STEP 2: RELEVANCE FILTER
----------------------------------

KEEP if:
- It introduces something new
- OR improves something significantly
- OR is useful for developers/users
- OR can become engaging content

Else:
RETURN {"status": "DISCARD"}

----------------------------------
STEP 3: IMPACT SCORING
----------------------------------

Score (1–10):

9–10 → Game-changing (new model / major feature)
7–8 → Strong feature/tool update
5–6 → Useful but not groundbreaking
<5 → discard

----------------------------------
STEP 4: EXTRACTION
----------------------------------

Extract:

- company
- name (model / feature / tool)
- category
- innovation (what changed)
- use_case (who benefits & how)
- technical_depth (low / medium / high)

Benchmark is OPTIONAL:
- Include ONLY if present
- Else return "N/A"

----------------------------------
STEP 5: CONTENT ENGINE
----------------------------------

Generate:

hook:
- Short, curiosity-driven

explanation:
- Simple and clear

why_it_matters:
- Real-world value

content_idea:
- Specific idea for video/post

----------------------------------
OUTPUT (STRICT JSON)
----------------------------------

{
  "status": "KEEP",
  "category": "",
  "impact_score": 0,
  "company": "",
  "name": "",
  "innovation": "",
  "use_case": "",
  "technical_depth": "",
  "benchmark": "",
  "hook": "",
  "explanation": "",
  "why_it_matters": "",
  "content_idea": ""
}
"""


class Analyst:
    """Analyses scraped article content via a local Ollama model."""

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = "gemma3:4b"

    async def analyze_article(
        self, markdown_content: str, source_url: str
    ) -> Optional[Dict]:
        """
        Send article content to the LLM and return a structured dict, or
        ``None`` if the article is not relevant or analysis fails.
        """
        if not markdown_content or not markdown_content.strip():
            return None

        print(f"[Analyst] Analysing content from {source_url} using {self.model}")

        # Truncate to stay within GPU memory limits
        truncated = markdown_content[:MAX_CONTEXT_CHARS]

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Now analyse the following article:\n\n"
            f"{truncated}\n"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }

        timeout = aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate", json=payload
                ) as response:
                    if response.status != 200:
                        body = await response.text()
                        print(
                            f"[Analyst] Ollama API Error ({response.status}): "
                            f"{body[:200]}"
                        )
                        return None

                    result = await response.json()
                    response_text = result.get("response", "").strip()

                    if not response_text:
                        print("[Analyst] Empty response from LLM.")
                        return None

                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError:
                        print(
                            f"[Analyst] Failed to parse JSON from LLM. "
                            f"Raw output: {response_text[:300]}"
                        )
                        return None

                    # Check for DISCARD verdict
                    status = str(data.get("status", "")).upper()
                    if status == "DISCARD":
                        print("[Analyst] Content classified as DISCARD.")
                        return None

                    # Check for LOW_VALUE category
                    category = str(data.get("category", "")).upper()
                    if category == "LOW_VALUE":
                        print("[Analyst] Content classified as LOW_VALUE.")
                        return None

                    # Check impact score — discard if below threshold
                    try:
                        impact = int(data.get("impact_score", 0))
                    except (ValueError, TypeError):
                        impact = 0
                    if impact < 5:
                        print(f"[Analyst] Impact score too low ({impact}). Discarding.")
                        return None

                    # Ensure essential fields exist
                    name = data.get("name", "")
                    company = data.get("company", "")
                    if not name and not company:
                        print("[Analyst] LLM response missing name and company. Skipping.")
                        return None

                    # Generate a SemanticHash for deduplication from company+name
                    raw_hash = f"{company} {name}".strip().lower()
                    data["SemanticHash"] = raw_hash if raw_hash else hashlib.md5(
                        source_url.encode()
                    ).hexdigest()[:10]

                    data["SourceURL"] = source_url
                    return data

        except aiohttp.ClientConnectorError:
            print(
                f"[Analyst] Could not connect to Ollama at {self.ollama_url}. "
                "Using MOCK data for dry run!"
            )
            return self._mock_result(source_url)
        except asyncio.TimeoutError:
            print(f"[Analyst] Ollama request timed out after {OLLAMA_TIMEOUT}s.")
            return None
        except Exception as exc:
            print(f"[Analyst] Exception during analysis: {exc}")
            return None

    @staticmethod
    def _mock_result(source_url: str) -> Dict:
        """Generate deterministic mock data when Ollama is unavailable."""
        hash_str = hashlib.md5(source_url.encode()).hexdigest()[:6]
        return {
            "status": "KEEP",
            "category": "NEW_MODEL",
            "impact_score": 8,
            "company": "Mock AI Labs",
            "name": f"AutoBot-{hash_str}",
            "innovation": "A simulated breakthrough in neural architecture.",
            "use_case": "Developers building AI-powered applications.",
            "technical_depth": "medium",
            "benchmark": "MMLU: 92%, HumanEval: 88%",
            "hook": "This model just changed the game.",
            "explanation": "A new model that pushes the state of the art.",
            "why_it_matters": "Faster, cheaper, and more capable AI for everyone.",
            "content_idea": "Comparison video: AutoBot vs GPT-4o on coding tasks.",
            "SemanticHash": f"mock ai labs autobot-{hash_str}",
            "SourceURL": source_url,
        }
