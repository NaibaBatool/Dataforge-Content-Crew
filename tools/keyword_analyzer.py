"""DataForge Content Crew - Keyword Analysis Tool
Phase 3: Research Tools
"""

import re
from typing import Any, Dict, List


def analyze_keywords(topic: str, content_goals: str = "", company_industry: str = "") -> Dict[str, Any]:
    """Extracts organic keyword anchors from topic, goals, and industry context.
    
    Adheres strictly to the integration honesty rule: does not fabricate fake search volumes,
    keyword difficulty scores, or false claims of live third-party SEO API access.
    """
    words = re.findall(r"\b[A-Za-z0-9_-]{3,}\b", topic.lower())
    stop_words = {"the", "and", "for", "with", "from", "that", "this", "about", "into", "over", "what", "how"}
    core_terms = [w for w in words if w not in stop_words]

    primary_keyword = " ".join(core_terms[:3]) if core_terms else topic.lower()

    # Derived semantic phrase anchors
    secondary_keywords = []
    if len(core_terms) >= 2:
        secondary_keywords.append(f"{core_terms[0]} {core_terms[1]} best practices")
        secondary_keywords.append(f"{core_terms[0]} architecture guide")
    if company_industry:
        secondary_keywords.append(f"{primary_keyword} for {company_industry.lower()}")

    return {
        "primary_keyword": primary_keyword,
        "secondary_keywords": secondary_keywords,
        "intent_type": "Informational / Technical Leadership",
        "honesty_notice": "Semantic keywords derived from topic context. No third-party search volume metrics fabricated."
    }
