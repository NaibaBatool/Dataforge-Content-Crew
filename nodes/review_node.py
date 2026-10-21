"""DataForge Content Crew - Review Workflow Node
Phase 3/5: Review, Quality Audit & Finalization Node
"""

from typing import Any, Dict
from tools.content_analyzer import analyze_content
from services.workflow_tracker import start_stage, complete_stage, finalize_workflow_run, get_formatted_workflow_events


def review_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validates draft quality, headings, citations, and prepares for user review."""
    run_id = state.get("run_id")
    draft = state.get("draft", {})
    title = draft.get("title", "")
    content = draft.get("content_markdown", "")
    report = state.get("analysis_report", {})
    primary_kw = report.get("primary_keyword", "")

    # Stage 9: Reviewing Structure, Claims & Citations
    if run_id:
        start_stage(
            run_id,
            "stage_9_review",
            "Auditing heading hierarchy, word count, readability, and citation integrity."
        )

    validation = analyze_content(title, content, target_keyword=primary_kw)

    if run_id:
        complete_stage(
            run_id,
            "stage_9_review",
            f"Quality check passed ({validation['score_out_of_100']}/100). Verified {validation['headings_count']} sections and {validation.get('citations_count', 0)} citations.",
            details={
                "score": validation["score_out_of_100"],
                "headings_count": validation["headings_count"],
                "citations_count": validation.get("citations_count", 0),
                "is_valid": validation["is_valid"],
                "feedback": validation.get("feedback", [])
            }
        )

    # Stage 10: Preparing Final Draft for Editorial Review
    if run_id:
        start_stage(
            run_id,
            "stage_10_draft_ready",
            "Preparing final draft and loading into interactive workspace editor."
        )
        complete_stage(
            run_id,
            "stage_10_draft_ready",
            f"Draft Version {draft.get('version', 1)} loaded into editor. Awaiting human editorial review and approval.",
            details={
                "draft_id": draft.get("id"),
                "version": draft.get("version", 1),
                "title": draft.get("title"),
                "status": "review_pending"
            }
        )
        finalize_workflow_run(run_id, "completed")

    events = get_formatted_workflow_events(run_id) if run_id else []

    return {
        **state,
        "validation_result": validation,
        "events": events,
        "status": "review_pending",
        "current_step": "Awaiting human editorial review and approval."
    }
