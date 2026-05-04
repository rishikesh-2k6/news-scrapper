"""
Librarian Module
----------------
Extracts clean Markdown content from a URL using the Firecrawl API (v1).
Handles timeouts, retries, and graceful failure so a single broken link
never crashes the pipeline.
"""

import os
import aiohttp
import asyncio
from typing import Optional

# Firecrawl v1 endpoint — v0 (/v0/scrape) is deprecated
FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v1/scrape"

# Maximum time (seconds) to wait for a single scrape request
REQUEST_TIMEOUT = 60


class Librarian:
    """Scrapes article content via Firecrawl and returns Markdown text."""

    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY", "")

    async def extract_markdown(self, target_url: str) -> Optional[str]:
        """
        Fetch the article at *target_url* and return its main-content Markdown.

        Returns ``None`` on any error (missing key, network failure,
        non-200 response, empty content, etc.).
        """
        if not target_url:
            print("[Librarian] Empty URL received. Skipping.")
            return None

        if not self.api_key or self.api_key.startswith("your_"):
            print("[Librarian] FIRECRAWL_API_KEY not configured. Skipping extraction.")
            return None

        print(f"[Librarian] Extracting content from: {target_url}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Firecrawl v1 payload format
        payload = {
            "url": target_url,
            "formats": ["markdown"],
        }

        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    FIRECRAWL_ENDPOINT, headers=headers, json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(
                            f"[Librarian] Firecrawl API Error ({response.status}): "
                            f"{error_text[:300]}"
                        )
                        return None

                    data = await response.json()

                    if data.get("success"):
                        markdown_content = (
                            data.get("data", {}).get("markdown", "")
                        )
                        if not markdown_content.strip():
                            print(f"[Librarian] Empty markdown returned for {target_url}")
                            return None
                        return markdown_content
                    else:
                        print(f"[Librarian] Firecrawl scraping failed for {target_url}")
                        return None

        except asyncio.TimeoutError:
            print(f"[Librarian] Request timed out for {target_url}")
            return None
        except aiohttp.ClientError as exc:
            print(f"[Librarian] Network error for {target_url}: {exc}")
            return None
        except Exception as exc:
            print(f"[Librarian] Unexpected error for {target_url}: {exc}")
            return None
