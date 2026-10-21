"""DataForge Content Crew - Competitor Analysis Tool
Phase 3: Research Tools
"""

from typing import Any, Dict, List


def analyze_competitors(competitors: List[Dict[str, Any]], topic: str) -> Dict[str, Any]:
    """Analyzes saved competitors against the topic based solely on verified records."""
    if not competitors:
        return {
            "has_competitors": False,
            "competitor_count": 0,
            "findings": "No tracked competitors are currently saved in your database.",
            "gaps": ["Add competitor URLs in the workspace sidebar to identify specific content angles."]
        }

    competitor_summaries = []
    for c in competitors:
        name = c.get("name", "Unknown Competitor")
        url = c.get("website_url", "")
        notes = c.get("notes", "")
        competitor_summaries.append({
            "name": name,
            "domain": url,
            "tracked_context": notes or "Tracked peer in workspace."
        })

    return {
        "has_competitors": True,
        "competitor_count": len(competitors),
        "analyzed_peers": competitor_summaries,
        "strategic_opportunity": (
            f"Focus on practical architecture and verifiable case studies around '{topic}' "
            f"to differentiate from standard competitor overviews."
        )
    }
