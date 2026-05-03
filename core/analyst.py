import os
import json
import aiohttp
from typing import Dict, Optional

class Analyst:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = "gemma4:e4b"

    async def analyze_article(self, markdown_content: str, source_url: str) -> Optional[Dict]:
        if not markdown_content:
            return None

        print(f"[Analyst] Analyzing content from {source_url} using {self.model}")
        
        prompt = f"""
You are an expert AI news analyst. Review the following markdown text extracted from an article.
Determine if the article is about a *new AI model release* or a *new AI benchmark*.
If it is NOT about a new model or benchmark, reply with the exact string "NOT_RELEVANT".

If it IS relevant, extract the following information and return it strictly as a JSON object:
- "Company": The name of the company or organization.
- "Model": The name of the AI model.
- "Metrics": A brief summary of any specific metrics mentioned (e.g., "MMLU: 85%, GSM8K: 92%"). If none, put "None".
- "InnovationSummary": A 1-sentence summary of the core innovation.
- "SemanticHash": A short 3-5 word string summarizing the core entity/innovation to be used for deduplication (e.g., "Meta Llama 3 70B", "GPT 4o Release", "Gemma 4 e4b").

Markdown Content:
{markdown_content[:8000]}  # Truncating to avoid massive context overflow for local GPU
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json" # Force JSON output format if supported by Ollama/model
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as response:
                    if response.status != 200:
                        print(f"[Analyst] Ollama API Error: {response.status}")
                        return None
                    
                    result = await response.json()
                    response_text = result.get("response", "").strip()

                    if "NOT_RELEVANT" in response_text.upper():
                        print(f"[Analyst] Content determined to be not relevant.")
                        return None
                    
                    try:
                        data = json.loads(response_text)
                        data["SourceURL"] = source_url
                        return data
                    except json.JSONDecodeError:
                        print(f"[Analyst] Failed to parse JSON from LLM response. Raw output: {response_text}")
                        return None
        except aiohttp.ClientConnectorError:
            print(f"[Analyst] Could not connect to Ollama at {self.ollama_url}. Is it running?")
            return None
        except Exception as e:
            print(f"[Analyst] Exception during analysis: {e}")
            return None
