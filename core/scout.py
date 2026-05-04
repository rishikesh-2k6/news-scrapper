"""
Scout Module
------------
Discovers raw links about AI news from two sources:
  1. RSS feeds (OpenAI, DeepMind, Hugging Face)
  2. Google Search via Serper.dev API

All network I/O is run through ``asyncio.to_thread`` so the event loop stays
responsive even though feedparser and requests are synchronous.
"""

import feedparser
import requests
import json
import os
import asyncio
from typing import List, Dict


class RSSScout:
    """Fetches the latest entries from a set of AI-related RSS feeds."""

    # Default feeds — extend this list as needed
    FEEDS = [
        "https://openai.com/blog/rss/",
        "https://deepmind.google/blog/rss/",
        "https://huggingface.co/blog/feed.xml",
    ]

    def __init__(self, feeds: List[str] | None = None):
        self.feeds = feeds or self.FEEDS

    async def fetch_feed(self, url: str) -> List[Dict]:
        """Parse a single RSS feed and return up to 5 entries."""
        print(f"[Scout] Fetching RSS feed: {url}")
        try:
            # feedparser is synchronous — offload to a thread
            parsed = await asyncio.to_thread(feedparser.parse, url)
            results = []
            for entry in parsed.entries[:5]:
                results.append({
                    "source": url,
                    "title": getattr(entry, "title", "Untitled"),
                    "link": getattr(entry, "link", ""),
                })
            return results
        except Exception as exc:
            print(f"[Scout] Failed to parse RSS feed {url}: {exc}")
            return []

    async def scout_all(self) -> List[Dict]:
        """Fetch all configured feeds concurrently."""
        tasks = [self.fetch_feed(url) for url in self.feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_links: List[Dict] = []
        for res in results:
            if isinstance(res, list):
                all_links.extend(res)
            else:
                print(f"[Scout] Error fetching RSS feed: {res}")
        return all_links


class SearchScout:
    """Queries Serper.dev for AI-related Google Search results."""

    SEARCH_ENDPOINT = "https://google.serper.dev/search"

    DEFAULT_QUERIES = [
        "new AI model release benchmark",
        "site:x.com new LLM benchmark state of the art",
    ]

    def __init__(self, queries: List[str] | None = None):
        self.api_key = os.getenv("SERPER_API_KEY", "")
        self.queries = queries or self.DEFAULT_QUERIES

    async def fetch_search(self, query: str) -> List[Dict]:
        """Run a single Serper search query and return up to 5 results."""
        if not self.api_key or self.api_key.startswith("your_"):
            print("[Scout] SERPER_API_KEY not configured. Skipping search.")
            return []

        print(f"[Scout] Searching Serper.dev for: {query}")
        payload = json.dumps({"q": query, "num": 5})
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            response = await asyncio.to_thread(
                requests.post,
                self.SEARCH_ENDPOINT,
                headers=headers,
                data=payload,
                timeout=30,  # 30-second hard timeout
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("organic", []):
                results.append({
                    "source": "Serper Search",
                    "title": item.get("title", "Untitled"),
                    "link": item.get("link", ""),
                })
            return results
        except requests.exceptions.Timeout:
            print(f"[Scout] Serper request timed out for query: {query}")
            return []
        except Exception as exc:
            print(f"[Scout] Serper search error for query '{query}': {exc}")
            return []

    async def scout_all(self) -> List[Dict]:
        """Run all search queries concurrently."""
        tasks = [self.fetch_search(q) for q in self.queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_links: List[Dict] = []
        for res in results:
            if isinstance(res, list):
                all_links.extend(res)
            else:
                print(f"[Scout] Serper error: {res}")
        return all_links


async def gather_all_links() -> List[Dict]:
    """Aggregate links from both RSS and Search scouts, deduplicating by URL."""
    rss_scout = RSSScout()
    search_scout = SearchScout()

    rss_results, search_results = await asyncio.gather(
        rss_scout.scout_all(),
        search_scout.scout_all(),
    )

    combined = rss_results + search_results

    # Deduplicate by URL before returning
    seen_urls: set = set()
    unique: List[Dict] = []
    for item in combined:
        url = item.get("link", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(item)
    return unique
