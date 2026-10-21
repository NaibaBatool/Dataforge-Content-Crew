"""DataForge Content Crew - Request Validation & Sanitization
Phase 2: Validation Layer
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

VALID_STATUSES = {"draft", "review", "approved", "published"}
VALID_TONES = {
    "authoritative",
    "conversational",
    "technical",
    "educational",
    "thought_leadership",
    "approachable",
    "analytical"
}


def validate_url(url: str) -> bool:
    """Validates if a URL has an http/https scheme and a valid netloc."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    # If user provided a domain without scheme (e.g., example.com), allow with prepended scheme check
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        result = urlparse(url)
        return bool(result.scheme in ("http", "https") and result.netloc and "." in result.netloc)
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """Ensures URL starts with http:// or https://."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def validate_company_profile(data: Any) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """Validates company profile submission.
    
    Required fields:
    - company_name
    - description
    - products_services
    - industry
    - target_audience
    - usp
    - website
    - tone
    - content_goals
    """
    if not isinstance(data, dict):
        return False, {"_general": "Request body must be a JSON object."}, {}

    errors = {}
    cleaned = {}

    required_fields = [
        ("company_name", 1, 150),
        ("description", 5, 2000),
        ("products_services", 3, 1000),
        ("industry", 2, 100),
        ("target_audience", 3, 500),
        ("usp", 3, 500),
        ("website", 3, 255),
        ("tone", 2, 100),
        ("content_goals", 3, 1000),
    ]

    for field, min_len, max_len in required_fields:
        val = data.get(field)
        if not val or not isinstance(val, str) or not val.strip():
            errors[field] = f"{field.replace('_', ' ').capitalize()} is required."
        else:
            val_clean = val.strip()
            if len(val_clean) < min_len:
                errors[field] = f"{field.replace('_', ' ').capitalize()} must be at least {min_len} characters."
            elif len(val_clean) > max_len:
                errors[field] = f"{field.replace('_', ' ').capitalize()} must not exceed {max_len} characters."
            else:
                cleaned[field] = val_clean

    # Specific website URL validation
    if "website" in cleaned and not validate_url(cleaned["website"]):
        errors["website"] = "Please provide a valid website URL (e.g., https://example.com)."
    elif "website" in cleaned:
        cleaned["website"] = normalize_url(cleaned["website"])

    return len(errors) == 0, errors, cleaned


def validate_competitor(data: Any) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """Validates competitor payload."""
    if not isinstance(data, dict):
        return False, {"_general": "Request body must be a JSON object."}, {}

    errors = {}
    cleaned = {}

    name = data.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        errors["name"] = "Competitor name is required."
    elif len(name.strip()) > 150:
        errors["name"] = "Competitor name must not exceed 150 characters."
    else:
        cleaned["name"] = name.strip()

    website_url = data.get("website_url")
    if not website_url or not isinstance(website_url, str) or not website_url.strip():
        errors["website_url"] = "Competitor website URL is required."
    elif not validate_url(website_url):
        errors["website_url"] = "Please provide a valid competitor website URL."
    else:
        cleaned["website_url"] = normalize_url(website_url)

    notes = data.get("notes", "")
    if notes and isinstance(notes, str):
        cleaned["notes"] = notes.strip()[:500]
    else:
        cleaned["notes"] = ""

    return len(errors) == 0, errors, cleaned


def validate_draft(data: Any) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
    """Validates draft article payload."""
    if not isinstance(data, dict):
        return False, {"_general": "Request body must be a JSON object."}, {}

    errors = {}
    cleaned = {}

    title = data.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        errors["title"] = "Draft title is required."
    elif len(title.strip()) > 300:
        errors["title"] = "Title must not exceed 300 characters."
    else:
        cleaned["title"] = title.strip()

    content = data.get("content_markdown")
    if content is None or not isinstance(content, str):
        errors["content_markdown"] = "Content markdown string is required."
    else:
        cleaned["content_markdown"] = content.strip()

    status = data.get("status", "draft")
    if status not in VALID_STATUSES:
        errors["status"] = f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}."
    else:
        cleaned["status"] = status

    if "id" in data and data["id"]:
        try:
            cleaned["draft_id"] = int(data["id"])
        except (ValueError, TypeError):
            errors["id"] = "Draft ID must be an integer."

    return len(errors) == 0, errors, cleaned


def validate_chat_message(data: Any) -> Tuple[bool, Dict[str, str], str]:
    """Validates chat message text."""
    if not isinstance(data, dict):
        return False, {"_general": "Request body must be a JSON object."}, ""

    message = data.get("message") or data.get("content")
    if not message or not isinstance(message, str) or not message.strip():
        return False, {"message": "Message content cannot be empty."}, ""

    clean_msg = message.strip()
    if len(clean_msg) > 3000:
        return False, {"message": "Message must not exceed 3000 characters."}, ""

    return True, {}, clean_msg
