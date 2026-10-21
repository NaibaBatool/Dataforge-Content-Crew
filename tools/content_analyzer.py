"""DataForge Content Crew - Content Quality & Structure Analysis Tool
Phase 3: Quality Review Tools
"""

import re
from typing import Any, Dict


def analyze_content(title: str, content_markdown: str, target_keyword: str = "") -> Dict[str, Any]:
    """Inspects draft structure, headings, word count, paragraph length, and readability."""
    words = content_markdown.split()
    word_count = len(words)

    # Check headings
    h2_matches = re.findall(r"^##\s+(.+)$", content_markdown, flags=re.MULTILINE)
    h3_matches = re.findall(r"^###\s+(.+)$", content_markdown, flags=re.MULTILINE)
    total_headings = len(h2_matches) + len(h3_matches)

    # Keyword usage
    keyword_count = 0
    if target_keyword:
        keyword_count = len(re.findall(re.escape(target_keyword), content_markdown, flags=re.IGNORECASE))

    # Citation linkages
    citations = re.findall(r"\[([^\]]+)\]\((https?://[^\)]+)\)", content_markdown)
    citations_count = len(citations)

    # Structural checks
    has_title = bool(title and len(title.strip()) >= 5)
    has_headings = total_headings >= 2
    has_reasonable_length = word_count >= 120
    has_intro = bool(content_markdown.strip().startswith("#") or "intro" in content_markdown[:300].lower())

    passed_checks = sum([has_title, has_headings, has_reasonable_length, has_intro])
    is_valid = passed_checks >= 3

    feedback = []
    if not has_title:
        feedback.append("Title is missing or too short.")
    if not has_headings:
        feedback.append("Add at least 2 subheadings (H2/H3) for readability.")
    if word_count < 120:
        feedback.append(f"Draft is brief ({word_count} words); expand key sections.")

    return {
        "is_valid": is_valid,
        "score_out_of_100": int((passed_checks / 4.0) * 100),
        "word_count": word_count,
        "headings_count": total_headings,
        "h2_sections": h2_matches,
        "citations_count": citations_count,
        "citations": [{"title": c[0], "url": c[1]} for c in citations],
        "keyword_occurrences": keyword_count,
        "feedback": feedback
    }
