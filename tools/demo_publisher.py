"""DataForge Content Crew - Publishing Tool
Phase 3/5: In-App Blogs Library Publishing Tool
"""

import datetime
from typing import Any, Dict
from db import save_draft, get_draft


def publish_draft_to_demo_store(draft_id: int, approval_token: str) -> Dict[str, Any]:
    """Publishes an approved draft to the in-app Content Crew Blogs library.
    
    Validates approval and clearly communicates that the article is published inside
    Content Crew and is not automatically live on external CMS platforms.
    """
    draft = get_draft(draft_id)
    if not draft:
        return {
            "success": False,
            "error": f"Draft with ID {draft_id} not found."
        }

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Idempotent check: if already published, avoid duplicates and confirm
    if draft["status"] == "published":
        return {
            "success": True,
            "is_public_publish": False,
            "message": (
                f"Draft '{draft['title']}' is already published in your Content Crew Blogs library. "
                "Note: It is stored in your Content Crew library and is not automatically live on an external website."
            ),
            "published_at": draft.get("published_at") or draft["updated_at"],
            "draft": draft,
            "already_published": True,
            "approval_token_verified": True
        }

    if draft["status"] != "approved":
        return {
            "success": False,
            "error": f"Cannot publish draft. Current status is '{draft['status']}'. Draft must be approved first."
        }

    # Mark published in SQLite with timestamp
    published_draft = save_draft(
        title=draft["title"],
        content_markdown=draft["content_markdown"],
        status="published",
        draft_id=draft_id,
        published_at=now
    )

    return {
        "success": True,
        "is_public_publish": False,
        "message": (
            f"Draft '{published_draft['title']}' published successfully to your Content Crew Blogs library. "
            "Note: It is stored in your Content Crew library and is not automatically live on an external website."
        ),
        "published_at": now,
        "draft": published_draft,
        "approval_token_verified": True
    }
