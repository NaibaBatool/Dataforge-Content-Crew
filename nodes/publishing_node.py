"""DataForge Content Crew - Publishing Workflow Node
Phase 3: Workflow Nodes
"""

from typing import Any, Dict
from tools.demo_publisher import publish_draft_to_demo_store


def publishing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Publishes the approved draft to the local demo store after verifying exact version approval."""
    draft = state.get("draft", {})
    draft_id = draft.get("id")
    current_version = draft.get("version", 1)
    approval_state = state.get("approval_state", {})

    is_approved = approval_state.get("is_approved", False)
    approved_version = approval_state.get("approved_version")
    approval_token = approval_state.get("approval_token")

    # Security check: Approval must be valid for the EXACT draft version
    if not is_approved or approved_version != current_version or not approval_token:
        return {
            **state,
            "status": "error",
            "error": (
                f"Publishing rejected: Draft version {current_version} has not been explicitly approved. "
                "Revisions or edits require fresh editorial approval prior to publication."
            )
        }

    publish_result = publish_draft_to_demo_store(draft_id, approval_token)

    if not publish_result.get("success"):
        return {
            **state,
            "status": "error",
            "error": publish_result.get("error", "Publishing failed.")
        }

    return {
        **state,
        "status": "published",
        "current_step": "Draft published to your Content Crew Blogs library. Not live on external platforms.",
        "publish_result": publish_result
    }
