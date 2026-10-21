"""DataForge Content Crew - Research Workflow Node
Phase 3/5: Research Workflow Node
"""

from typing import Any, Dict
from agents.analysis_agent import run_analysis_agent


def research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Coordinates competitor analysis, web search, and evidence extraction."""
    run_id = state.get("run_id")
    plan = state.get("plan", {})
    topic = plan.get("topic") or state.get("user_request", "Content Topic")
    competitors = state.get("competitors", [])
    profile = state.get("company_profile", {})

    analysis_report = run_analysis_agent(topic, competitors, profile, run_id=run_id)

    return {
        **state,
        "analysis_report": analysis_report,
        "status": "generating",
        "current_step": "Research synthesis complete. Commencing draft generation."
    }
