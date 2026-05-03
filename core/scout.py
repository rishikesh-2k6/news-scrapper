import feedparser
import requests
import json
import os
import asyncio
from typing import List, Dict

class RSSScout:
    def __init__(self):
        self.feeds = [
            "https://openai.com/blog/rss/",
            "https://deepmind.google/blog/rss/",
            "https://huggingface.co/blog/feed.xml"
        ]

    async def fetch_feed(self, url: str) -> List[Dict]:
        print(f"[Scout] Fetching RSS feed: {url}")
        # Run synchronous feedparser in a thread to avoid blocking
        parsed = await asyncio.to_thread(feedparser.parse, url)
        results = []
        for entry in parsed.entries[:5]:  # Get latest 5 entries per feed
            results.append({
                "source": url,
                "title": entry.title,
                "link": entry.link
            })
        return results

    async def scout_all(self) -> List[Dict]:
        tasks = [self.fetch_feed(url) for url in self.feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_links = []
        for res in results:
            if isinstance(res, list):
                all_links.extend(res)
            else:
                print(f"[Scout] Error fetching RSS feed: {res}")
        return all_links

class SearchScout:
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.url = "https://google.serper.dev/search"
        self.queries = [
            "new AI model release benchmark",
            "site:x.com new LLM benchmark state of the art"
        ]

    async def fetch_search(self, query: str) -> List[Dict]:
        if not self.api_key or self.api_key == "your_serper_api_key_here":
            print("[Scout] SERPER_API_KEY not configured. Skipping search.")
            return []

        print(f"[Scout] Searching Serper.dev for: {query}")
        payload = json.dumps({"q": query, "num": 5})
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        try:
            # Using standard requests synchronously inside async (should ideally be aiohttp, but keeping simple for now, using to_thread)
            response = await asyncio.to_thread(requests.post, self.url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("organic", []):
                results.append({
                    "source": "Serper Search",
                    "title": item.get("title"),
                    "link": item.get("link")
                })
            return results
        except Exception as e:
            print(f"[Scout] Serper search error for query '{query}': {e}")
            return []

    async def scout_all(self) -> List[Dict]:
        tasks = [self.fetch_search(query) for query in self.queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_links = []
        for res in results:
            if isinstance(res, list):
                all_links.extend(res)
        return all_links

async def gather_all_links() -> List[Dict]:
    rss_scout = RSSScout()
    search_scout = SearchScout()
    
    rss_results, search_results = await asyncio.gather(
        rss_scout.scout_all(),
        search_scout.scout_all()
    )
    
    return rss_results + search_results
