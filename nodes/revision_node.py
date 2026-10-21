"""DataForge Content Crew - Revision Workflow Node
Phase 3: Workflow Nodes
"""

from typing import Any, Dict
from agents.generation_agent import run_generation_agent
from db import save_draft


def revision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Applies user revision requests, increments version, and invalidates previous approvals."""
    draft = state.get("draft", {})
    plan = state.get("plan", {})
    topic = plan.get("topic") or state.get("user_request", "Content Topic")
    analysis_report = state.get("analysis_report", {})
    company_profile = state.get("company_profile", {})
    revision_notes = state.get("revision_notes", "")

    current_version = draft.get("version", 1)
    new_version = current_version + 1

    revised = run_generation_agent(
        topic=topic,
        analysis_report=analysis_report,
        company_profile=company_profile,
        revision_feedback=revision_notes
    )

    # Update in SQLite
    saved_draft = save_draft(
        title=revised["title"],
        content_markdown=revised["content_markdown"],
        status="draft",
        draft_id=draft.get("id"),
        version=new_version
    )

    draft_state = {
        "id": saved_draft["id"],
        "title": saved_draft["title"],
        "content_markdown": saved_draft["content_markdown"],
        "word_count": saved_draft["word_count"],
        "version": new_version,
        "status": "draft"
    }

    # CRITICAL: Invalidate previous approvals upon revision
    approval_state = {
        "is_approved": False,
        "approved_version": None,
        "approval_token": None
    }

    return {
        **state,
        "draft": draft_state,
        "approval_state": approval_state,
        "revision_notes": "",
        "status": "reviewing",
        "current_step": f"Revision {new_version} generated. Ready for re-review."
    }
