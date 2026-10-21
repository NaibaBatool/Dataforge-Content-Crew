"""DataForge Content Crew - Analysis Agent
Phase 3: Agent Definitions
"""

from typing import Any, Dict, List, Optional
from agents.supervisor_agent import normalize_topic
from tools.web_search import search_web
from tools.competitor_analyzer import analyze_competitors
from tools.keyword_analyzer import analyze_keywords
from services.gemini_service import generate_content
from services.workflow_tracker import start_stage, complete_stage


def run_analysis_agent(
    topic: str,
    competitors: List[Dict[str, Any]],
    company_profile: Dict[str, Any],
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """Runs research tools and synthesizes an evidence-based report."""
    clean_topic = normalize_topic(topic)
    # Stage 3: Web search (real configured provider or honest notice)
    if run_id:
        start_stage(run_id, "stage_3_search", f"Searching web sources for '{clean_topic}'...")

    search_res = search_web(clean_topic, max_results=3)

    if run_id:
        if search_res.get("is_available") and search_res.get("results"):
            complete_stage(
                run_id,
                "stage_3_search",
                f"Retrieved {len(search_res['results'])} live public search results for query '{clean_topic}'.",
                details={
                    "provider": search_res.get("provider", "Web"),
                    "query": clean_topic,
                    "count": len(search_res["results"]),
                    "sources": search_res["results"],
                    "is_live": True
                }
            )
        else:
            complete_stage(
                run_id,
                "stage_3_search",
                search_res.get("message", "Live web search provider is unconfigured."),
                details={
                    "provider": "None",
                    "query": topic,
                    "count": 0,
                    "sources": [],
                    "is_live": False,
                    "notice": search_res.get("message")
                }
            )

    # Stage 4: Reviewing and extracting source information
    if run_id:
        start_stage(run_id, "stage_4_sources", "Reviewing source excerpts and extracting verified evidence.")

    evidence_sources = []
    if search_res.get("is_available") and search_res.get("results"):
        evidence_sources = search_res["results"]
    elif competitors:
        for c in competitors:
            evidence_sources.append({
                "title": f"Competitor Profile: {c.get('name')}",
                "url": c.get("website_url", ""),
                "snippet": c.get("notes") or f"Tracked competitor record for {c.get('name')}."
            })

    if run_id:
        source_summary = (
            f"Extracted {len(evidence_sources)} evidence sources."
            if evidence_sources
            else "No external sources retrieved; using company editorial context."
        )
        complete_stage(
            run_id,
            "stage_4_sources",
            source_summary,
            details={
                "count": len(evidence_sources),
                "sources": evidence_sources,
                "used_in_draft": True
            }
        )

    # Stage 5: Competitor comparison
    if run_id:
        start_stage(
            run_id,
            "stage_5_competitors",
            f"Comparing {len(competitors)} tracked competitors for market positioning and content overlap."
        )

    competitor_findings = analyze_competitors(competitors, topic)

    if run_id:
        complete_stage(
            run_id,
            "stage_5_competitors",
            f"Analyzed {competitor_findings.get('competitor_count', 0)} competitor profiles against '{topic}'.",
            details={
                "competitor_count": competitor_findings.get("competitor_count", 0),
                "competitors": [c.get("name") for c in competitors],
                "findings": competitor_findings.get("analyzed_peers", [])
            }
        )

    # Keyword analysis
    keyword_findings = analyze_keywords(
        topic=topic,
        content_goals=company_profile.get("content_goals", ""),
        company_industry=company_profile.get("industry", "")
    )

    summary = (
        f"Research synthesized for '{topic}'. Identified core keyword '{keyword_findings['primary_keyword']}'. "
        f"Analyzed {competitor_findings.get('competitor_count', 0)} competitor records. "
        f"Search status: {search_res.get('message')}."
    )

    return {
        "topic": topic,
        "primary_keyword": keyword_findings["primary_keyword"],
        "secondary_keywords": keyword_findings["secondary_keywords"],
        "competitor_analysis": competitor_findings,
        "search_results": search_res,
        "sources": evidence_sources,
        "summary": summary
    }
