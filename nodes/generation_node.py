"""DataForge Content Crew - Generation Workflow Node
Phase 3/5: Outline & Generation Workflow Node
"""

from typing import Any, Dict
from agents.generation_agent import run_generation_agent
from db import save_draft
from services.workflow_tracker import start_stage, complete_stage, fail_stage


def generation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Prepares outline and generates the initial or regenerated blog post draft."""
    run_id = state.get("run_id")
    plan = state.get("plan", {})
    topic = plan.get("topic") or state.get("user_request", "Content Topic")
    analysis_report = state.get("analysis_report", {})
    company_profile = state.get("company_profile", {})
    is_regeneration = state.get("is_regeneration", False)
    target_version = state.get("target_version", 1)
    session_id = state.get("session_id", "default")
    company_name = company_profile.get("company_name", "")

    # Stage 7: Preparing Article Outline
    if run_id:
        start_stage(
            run_id,
            "stage_7_outline",
            f"Structuring semantic heading hierarchy (H1, H2, H3) and narrative flow for '{topic}'."
        )

    sections = [
        f"Introduction: Navigating {topic.title()}",
        "1. Core Principles and Best Practices",
        "Key Architectural Considerations",
        "2. Platform Value & Strategic Impact",
        "Frequently Asked Questions",
        "Conclusion & Next Steps"
    ]

    if run_id:
        complete_stage(
            run_id,
            "stage_7_outline",
            f"Article outline structured into {len(sections)} sections including evidence anchors.",
            details={"sections": sections}
        )

    # Stage 8: Generating Blog Article
    if run_id:
        start_stage(
            run_id,
            "stage_8_generation",
            f"Synthesizing complete blog article for '{topic}' ({'Regeneration' if is_regeneration else 'Initial draft'})."
        )

    try:
        generated = run_generation_agent(
            topic=topic,
            analysis_report=analysis_report,
            company_profile=company_profile,
            is_regeneration=is_regeneration
        )

        # Persist in SQLite
        saved_draft = save_draft(
            title=generated["title"],
            content_markdown=generated["content_markdown"],
            status="draft",
            version=target_version,
            session_id=session_id,
            company_name=company_name,
            create_new_row=is_regeneration  # Keep previous versions in DB on regeneration!
        )

        if run_id:
            complete_stage(
                run_id,
                "stage_8_generation",
                f"Generated draft '{saved_draft['title']}' ({saved_draft['word_count']} words, Version {target_version}).",
                details={
                    "title": saved_draft["title"],
                    "word_count": saved_draft["word_count"],
                    "version": target_version,
                    "is_live_ai": generated.get("is_live_ai", False)
                }
            )

    except Exception as e:
        if run_id:
            fail_stage(run_id, "stage_8_generation", f"Generation failed: {str(e)}")
        raise

    draft_state = {
        "id": saved_draft["id"],
        "title": saved_draft["title"],
        "content_markdown": saved_draft["content_markdown"],
        "word_count": saved_draft["word_count"],
        "version": target_version,
        "status": "draft"
    }

    return {
        **state,
        "draft": draft_state,
        "status": "reviewing",
        "current_step": "Draft generated. Running content quality validation."
    }
