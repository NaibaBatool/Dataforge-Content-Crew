"""DataForge Content Crew - Planning Workflow Node
Phase 3/5: Workflow Nodes & Execution Tracking
"""

from typing import Any, Dict
from agents.supervisor_agent import run_supervisor, normalize_topic
from services.workflow_tracker import start_stage, complete_stage, fail_stage


def planning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Interprets user prompt, understands context, and generates an editorial plan."""
    run_id = state.get("run_id")
    user_request = state.get("user_request", "Editorial Blog Topic")
    clean_topic = normalize_topic(user_request)
    profile = state.get("company_profile", {})

    # Stage 1: Understanding Request & Brand Context
    if run_id:
        start_stage(
            run_id,
            "stage_1_understanding",
            f"Analyzing subject '{clean_topic}' against brand positioning and target audience."
        )

    company_name = profile.get("company_name", "DataForge Organization")
    tone = profile.get("tone", "Authoritative & Technical")
    target_audience = profile.get("target_audience", "Technical & Business Leaders")

    if run_id:
        complete_stage(
            run_id,
            "stage_1_understanding",
            f"Understood context for {company_name}: Tone is '{tone}', targeting '{target_audience}'.",
            details={
                "company_name": company_name,
                "tone": tone,
                "target_audience": target_audience,
                "industry": profile.get("industry", "Technology"),
                "content_goals": profile.get("content_goals", "Drive thought leadership")
            }
        )

    # Stage 2: Creating Content Execution Plan
    if run_id:
        start_stage(
            run_id,
            "stage_2_planning",
            "Supervisor agent formulating editorial angles and orchestrating research agents."
        )

    try:
        plan = run_supervisor(user_request, profile)
        if run_id:
            complete_stage(
                run_id,
                "stage_2_planning",
                f"Execution plan formulated: Focus on '{plan.get('topic')}' with strategic angle '{plan.get('target_angle', 'Industry Overview')}'.",
                details={
                    "topic": plan.get("topic"),
                    "target_angle": plan.get("target_angle"),
                    "steps": plan.get("steps", ["research", "analysis", "generation", "review"])
                }
            )
    except Exception as e:
        if run_id:
            fail_stage(run_id, "stage_2_planning", f"Planning failed: {str(e)}")
        raise

    return {
        **state,
        "plan": plan,
        "status": "researching",
        "current_step": "Planning complete. Beginning competitor and keyword research."
    }
