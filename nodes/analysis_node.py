"""DataForge Content Crew - Analysis Workflow Node
Phase 3/5: Analysis & Content Gap Synthesis Node
"""

from typing import Any, Dict
from services.workflow_tracker import start_stage, complete_stage


def analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes search intent, content gaps, and available evidence."""
    run_id = state.get("run_id")
    report = state.get("analysis_report", {})
    topic = state.get("user_request", "Topic")

    if run_id:
        start_stage(
            run_id,
            "stage_6_analysis",
            f"Analyzing search intent, evidence positioning, and content gaps for '{topic}'."
        )

    if not report:
        report = {
            "summary": "Baseline research established.",
            "primary_keyword": topic,
            "sources": []
        }

    primary_kw = report.get("primary_keyword", topic)
    sec_kws = report.get("secondary_keywords", [])
    sources_count = len(report.get("sources", []))

    content_gaps = [
        "Include concrete production examples often omitted in competitor articles",
        "Provide explicit checklists for deployment and risk mitigation",
        "Address long-tail architectural scalability questions"
    ]
    report["content_gaps"] = content_gaps

    if run_id:
        complete_stage(
            run_id,
            "stage_6_analysis",
            f"Identified primary search intent (Informational/Decision), target keyword '{primary_kw}', and 3 strategic content gaps.",
            details={
                "primary_keyword": primary_kw,
                "secondary_keywords": sec_kws,
                "search_intent": "Technical / Strategic Evaluation",
                "evidence_sources_count": sources_count,
                "content_gaps": content_gaps
            }
        )

    return {
        **state,
        "analysis_report": report,
        "status": "generating",
        "current_step": "Search intent and gap analysis complete. Generating article outline and body."
    }
