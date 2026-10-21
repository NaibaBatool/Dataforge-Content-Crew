"""DataForge Content Crew - LangGraph Workflow Construction
Phase 3: Workflow Graph & Execution Engine
"""

import hashlib
import threading
import time
from typing import Any, Dict, Optional
from langgraph.graph import StateGraph, START, END

from graph.state import ContentCrewState
from nodes.planning_node import planning_node
from nodes.research_node import research_node
from nodes.analysis_node import analysis_node
from nodes.generation_node import generation_node
from nodes.review_node import review_node
from nodes.revision_node import revision_node
from nodes.publishing_node import publishing_node
from services.workflow_tracker import initialize_workflow_run, get_formatted_workflow_events

# In-memory session workflow state store (keyed by session_id)
_workflow_states: Dict[str, ContentCrewState] = {}


def build_graph():
    """Constructs and compiles the DataForge LangGraph workflow."""
    builder = StateGraph(ContentCrewState)

    # Add workflow nodes
    builder.add_node("planning", planning_node)
    builder.add_node("research", research_node)
    builder.add_node("analysis", analysis_node)
    builder.add_node("generation", generation_node)
    builder.add_node("review", review_node)
    builder.add_node("revision", revision_node)
    builder.add_node("publishing", publishing_node)

    # Primary linear creation path
    builder.add_edge(START, "planning")
    builder.add_edge("planning", "research")
    builder.add_edge("research", "analysis")
    builder.add_edge("analysis", "generation")
    builder.add_edge("generation", "review")
    builder.add_edge("review", END)

    # Revision loop: revision -> review -> pauses
    builder.add_edge("revision", "review")

    # Publishing terminal path
    builder.add_edge("publishing", END)

    return builder.compile()


# Compile once on module load
compiled_graph = build_graph()


def get_workflow_state(session_id: str) -> Optional[ContentCrewState]:
    """Retrieves current persisted workflow state for a session."""
    return _workflow_states.get(session_id)


def start_workflow(
    session_id: str,
    user_request: str,
    company_profile: Dict[str, Any],
    competitors: list,
    run_id: Optional[str] = None
) -> ContentCrewState:
    """Executes the planning -> research -> generation -> review pipeline."""
    if not run_id:
        run_id = initialize_workflow_run(session_id, user_request)

    initial_state: ContentCrewState = {
        "session_id": session_id,
        "run_id": run_id,
        "user_request": user_request,
        "company_profile": company_profile or {},
        "competitors": competitors or [],
        "approval_state": {
            "is_approved": False,
            "approved_version": None,
            "approval_token": None
        },
        "status": "planning",
        "current_step": "Initializing supervisor planning..."
    }

    _workflow_states[session_id] = initial_state

    # Run graph from START
    final_state = compiled_graph.invoke(initial_state)

    # Attach live event history
    final_state["events"] = get_formatted_workflow_events(run_id)
    _workflow_states[session_id] = final_state
    return final_state


def start_workflow_async(
    session_id: str,
    user_request: str,
    company_profile: Dict[str, Any],
    competitors: list
) -> str:
    """Launches the workflow in a background worker and returns the run_id immediately."""
    run_id = initialize_workflow_run(session_id, user_request)

    initial_state: ContentCrewState = {
        "session_id": session_id,
        "run_id": run_id,
        "user_request": user_request,
        "company_profile": company_profile or {},
        "competitors": competitors or [],
        "approval_state": {
            "is_approved": False,
            "approved_version": None,
            "approval_token": None
        },
        "status": "running",
        "current_step": "Initializing supervisor planning..."
    }
    _workflow_states[session_id] = initial_state

    def _worker():
        try:
            start_workflow(
                session_id=session_id,
                user_request=user_request,
                company_profile=company_profile,
                competitors=competitors,
                run_id=run_id
            )
        except Exception as e:
            st = _workflow_states.get(session_id) or initial_state
            st["status"] = "error"
            st["error"] = str(e)
            st["current_step"] = f"Workflow failed: {str(e)}"
            _workflow_states[session_id] = st

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return run_id


def regenerate_workflow_draft(session_id: str, run_id: Optional[str] = None) -> ContentCrewState:
    """Regenerates a fresh draft version using current context and approved research."""
    current_state = get_workflow_state(session_id)
    if not current_state:
        # Check if there is an existing draft in SQLite to regenerate from
        from db import get_latest_draft, get_company_profile, list_competitors
        latest_draft = get_latest_draft()
        if not latest_draft:
            raise ValueError(f"No active workflow or existing draft found for session '{session_id}'.")
        profile = get_company_profile() or {}
        competitors = list_competitors() or []
        user_req = latest_draft.get("title", "Modern Content Strategy")
        current_state = {
            "session_id": session_id,
            "user_request": user_req,
            "company_profile": profile,
            "competitors": competitors,
            "draft": latest_draft,
            "analysis_report": {"summary": "Existing research context", "sources": []},
            "status": "draft"
        }

    # Increment version
    curr_draft = current_state.get("draft") or {}
    prev_version = curr_draft.get("version", 1)
    new_version = prev_version + 1

    # Invalidate approval for the newly regenerated version
    current_state["approval_state"] = {
        "is_approved": False,
        "approved_version": None,
        "approval_token": None
    }
    current_state["is_regeneration"] = True
    current_state["target_version"] = new_version
    current_state["status"] = "generating"

    if not run_id:
        run_id = initialize_workflow_run(
            session_id,
            f"Regenerate Article (v{new_version}): {current_state.get('user_request', 'Draft')}"
        )
    current_state["run_id"] = run_id

    # Execute generation and review stages
    generated_state = generation_node(current_state)
    reviewed_state = review_node(generated_state)

    reviewed_state["events"] = get_formatted_workflow_events(run_id)
    _workflow_states[session_id] = reviewed_state
    return reviewed_state


def request_workflow_revision(session_id: str, revision_notes: str) -> ContentCrewState:
    """Invokes the revision node, updates the draft version, and clears prior approvals."""
    current_state = get_workflow_state(session_id)
    if not current_state:
        raise ValueError(f"No active workflow found for session '{session_id}'.")

    # Set revision notes
    current_state["revision_notes"] = revision_notes
    current_state["status"] = "revision_pending"

    # Run revision node specifically
    revised_state = revision_node(current_state)
    reviewed_state = review_node(revised_state)

    _workflow_states[session_id] = reviewed_state
    return reviewed_state


def approve_workflow_draft(session_id: str) -> Dict[str, Any]:
    """Generates a cryptographically signed approval token bound strictly to the draft version."""
    state = get_workflow_state(session_id)
    if not state or not state.get("draft"):
        raise ValueError("Cannot approve: No active draft found.")

    draft = state["draft"]
    version = draft.get("version", 1)

    # Compute server-side approval token
    raw_sig = f"{session_id}:{draft.get('id')}:{version}:{time.time()}"
    token = hashlib.sha256(raw_sig.encode()).hexdigest()[:32]

    draft["status"] = "approved"
    if draft.get("id"):
        from db import save_draft
        save_draft(
            title=draft.get("title", "Draft"),
            content_markdown=draft.get("content_markdown", ""),
            status="approved",
            draft_id=draft["id"],
            version=version
        )

    state["approval_state"] = {
        "is_approved": True,
        "approved_version": version,
        "approval_token": token
    }
    state["status"] = "approved"
    state["current_step"] = f"Draft version {version} approved. Ready for in-app library publishing."

    _workflow_states[session_id] = state
    return {
        "status": "approved",
        "version": version,
        "approval_token": token
    }


def invalidate_workflow_approval(session_id: str = "default") -> None:
    """Invalidates active workflow approval for a session upon manual edits or external updates."""
    state = get_workflow_state(session_id)
    if state:
        state["approval_state"] = {
            "is_approved": False,
            "approved_version": None,
            "approval_token": None
        }
        if state.get("draft"):
            state["draft"]["version"] = state["draft"].get("version", 1) + 1
            state["draft"]["status"] = "draft"
        state["status"] = "review_pending"
        state["current_step"] = "Draft content was modified. Re-approval required before publication."
        _workflow_states[session_id] = state


def publish_workflow_draft(session_id: str) -> ContentCrewState:
    """Executes the publishing node with server-side version verification."""
    state = get_workflow_state(session_id)
    if not state:
        raise ValueError(f"No active workflow found for session '{session_id}'.")

    published_state = publishing_node(state)
    _workflow_states[session_id] = published_state
    return published_state
