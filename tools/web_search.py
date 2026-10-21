"""DataForge Content Crew - Web Search Tool
Phase 3: Research Tools
"""

import os
import requests
from typing import Any, Dict, List


def search_web(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Conducts web search using a configured provider (e.g. Tavily).
    
    If no search provider API key is configured, reports truthfully that live search
    is unavailable and returns an empty result set without fabricating sources.
    """
    clean_query = query.strip()
    if not clean_query:
        return {
            "is_available": False,
            "query": query,
            "results": [],
            "message": "Empty search query provided."
        }

    tavily_key = os.environ.get("TAVILY_API_KEY", "").strip()

    # 1. If Tavily search provider is configured
    if tavily_key and tavily_key != "your_tavily_api_key_here":
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": clean_query,
                    "max_results": max_results,
                    "include_answer": False
                },
                timeout=6
            )
            if resp.ok:
                data = resp.json()
                results = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", "")[:300]
                    }
                    for r in data.get("results", [])
                ]
                return {
                    "is_available": True,
                    "provider": "Tavily",
                    "query": clean_query,
                    "results": results,
                    "message": f"Retrieved {len(results)} live public search results."
                }
        except Exception as e:
            return {
                "is_available": False,
                "provider": "Tavily",
                "query": clean_query,
                "results": [],
                "error": str(e),
                "message": f"Search provider request failed: {e}"
            }

    # 2. Honest Fallback when search provider is unconfigured
    return {
        "is_available": False,
        "provider": "None",
        "query": clean_query,
        "results": [],
        "message": (
            "Live web search provider is unconfigured. Set TAVILY_API_KEY in .env to enable "
            "live search. Operating with local verified competitor records and company profile."
        )
    }
