import os
import aiohttp
import asyncio
import json
from typing import Optional

class Librarian:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        self.url = "https://api.firecrawl.dev/v0/scrape"

    async def extract_markdown(self, target_url: str) -> Optional[str]:
        if not self.api_key or self.api_key == "your_firecrawl_api_key_here":
            print("[Librarian] FIRECRAWL_API_KEY not configured. Skipping extraction.")
            return None

        print(f"[Librarian] Extracting content from: {target_url}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": target_url,
            "pageOptions": {
                "onlyMainContent": True
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[Librarian] Firecrawl API Error ({response.status}): {error_text}")
                        return None
                    
                    data = await response.json()
                    
                    if data.get("success"):
                        # Extract markdown content from the response
                        markdown_content = data.get("data", {}).get("markdown", "")
                        return markdown_content
                    else:
                        print(f"[Librarian] Firecrawl scraping failed for {target_url}")
                        return None
        except Exception as e:
            print(f"[Librarian] Exception during extraction for {target_url}: {e}")
            return None
