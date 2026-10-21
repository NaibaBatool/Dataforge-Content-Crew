"""DataForge Content Crew - LangGraph State Definition
Phase 3: Workflow State
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class ContentCrewState(TypedDict, total=False):
    """Shared, typed state for the DataForge Content Crew workflow."""
    session_id: str
    run_id: str
    user_request: str
    plan: Dict[str, Any]
    company_profile: Dict[str, Any]
    competitors: List[Dict[str, Any]]
    analysis_report: Dict[str, Any]
    draft: Dict[str, Any]
    validation_result: Dict[str, Any]
    approval_state: Dict[str, Any]
    revision_notes: str
    status: str
    current_step: str
    publish_result: Dict[str, Any]
    events: List[Dict[str, Any]]
    error: Optional[str]
