"""
Analyst Module
--------------
Interfaces with a local Ollama LLM to decide whether an article describes
a new AI model/benchmark and, if so, extracts structured metadata.

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
            "You are an expert AI news analyst. Review the following markdown "
            "text extracted from an article.\n"
            "Determine if the article is about a *new AI model release* or a "
            "*new AI benchmark*.\n\n"
            "If it is NOT about a new model or benchmark, reply with ONLY the "
            'JSON object: {"verdict": "NOT_RELEVANT"}\n\n'
            "If it IS relevant, return ONLY a JSON object with these keys:\n"
            '- "Company": The name of the company or organisation.\n'
            '- "Model": The name of the AI model.\n'
            '- "Metrics": A brief summary of any specific metrics mentioned '
            '(e.g., "MMLU: 85%, GSM8K: 92%"). If none, put "None".\n'
            '- "InnovationSummary": A 1-sentence summary of the core innovation.\n'
            '- "SemanticHash": A short 3-5 word string summarising the core '
            'entity/innovation for deduplication (e.g., "Meta Llama 3 70B").\n\n'
            "Markdown Content:\n"
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

                    # Check for NOT_RELEVANT verdict
                    if (
                        data.get("verdict", "").upper() == "NOT_RELEVANT"
                        or "NOT_RELEVANT" in response_text.upper()
                    ):
                        print("[Analyst] Content determined to be not relevant.")
                        return None

                    # Ensure essential fields exist
                    if not data.get("SemanticHash"):
                        print("[Analyst] LLM response missing SemanticHash. Skipping.")
                        return None

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
            "Company": "Mock AI Labs",
            "Model": f"AutoBot-{hash_str}",
            "Metrics": "Accuracy: 99.9%, Speed: 10x",
            "InnovationSummary": "Simulated AI model analysis for the dry run.",
            "SemanticHash": f"mock hash {hash_str}",
            "SourceURL": source_url,
        }
