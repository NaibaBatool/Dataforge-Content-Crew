"""DataForge Content Crew - REST API Routes
Phase 3: Gemini & LangGraph Multi-Agent Workflows
"""

import datetime
from flask import Blueprint, jsonify, request
from db import (
    add_message,
    create_competitor,
    delete_competitor,
    get_company_profile,
    get_competitor,
    get_draft,
    get_latest_draft,
    list_drafts,
    list_blogs,
    get_or_create_session,
    get_session_messages,
    list_competitors,
    list_sessions,
    save_company_profile,
    save_draft,
    update_competitor,
    get_latest_workflow_run
)
from validators import (
    validate_chat_message,
    validate_company_profile,
    validate_competitor,
    validate_draft
)
from services.gemini_service import test_gemini_connection, get_gemini_config
from services.workflow_tracker import get_formatted_workflow_events
from graph.workflow import (
    start_workflow,
    start_workflow_async,
    get_workflow_state,
    request_workflow_revision,
    regenerate_workflow_draft,
    approve_workflow_draft,
    publish_workflow_draft,
    invalidate_workflow_approval
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@api_bp.route("/health", methods=["GET"])
def health_check():
    """Confirms Flask backend, SQLite database connectivity, and Gemini status."""
    db_status = "connected"
    try:
        get_company_profile()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    gemini_cfg = get_gemini_config()

    return jsonify({
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "DataForge Content Crew",
        "version": "1.0.0",
        "phase": 3,
        "phase_name": "Gemini and LangGraph Agents",
        "database": db_status,
        "gemini": {
            "configured": gemini_cfg["is_configured"],
            "model": gemini_cfg["model"]
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "endpoints": {
            "health": "/api/health",
            "gemini_status": "/api/gemini/status",
            "workflow_start": "/api/workflow/start",
            "company_profile": "/api/company-profile",
            "competitors": "/api/competitors",
            "chat_sessions": "/api/chat/sessions",
            "draft": "/api/draft"
        }
    })


@api_bp.route("/contracts", methods=["GET"])
def api_contracts():
    """Provides formal API contracts for Phase 3 endpoints."""
    contracts = {
        "description": "DataForge Content Crew API Specifications for Phases 3-4",
        "phase": "Phase 3 Active - LangGraph & Google Gemini Integration",
        "contracts": {
            "chat": {
                "endpoint": "/api/chat/sessions/<id>/messages",
                "method": "POST",
                "request_schema": { "message": "string" },
                "response_schema": { "user_message": "object", "assistant_message": "object", "is_demo": "boolean" }
            },
            "company_profile": {
                "endpoint": "/api/company-profile",
                "methods": ["GET", "POST", "PUT"],
                "schema": {
                    "company_name": "string",
                    "description": "string",
                    "products_services": "string",
                    "industry": "string",
                    "target_audience": "string",
                    "usp": "string",
                    "website": "string (URL)",
                    "tone": "string",
                    "content_goals": "string"
                }
            },
            "draft": {
                "endpoint": "/api/draft",
                "methods": ["GET", "POST", "PUT"],
                "schema": {
                    "id": "integer",
                    "title": "string",
                    "content_markdown": "string",
                    "status": "draft | review | approved | published"
                }
            },
            "workflow": {
                "start": "/api/workflow/start",
                "status": "/api/workflow/<session_id>/status",
                "revise": "/api/workflow/<session_id>/revise",
                "approve": "/api/workflow/<session_id>/approve",
                "publish": "/api/workflow/<session_id>/publish"
            },
            "gemini_status": "/api/gemini/status"
        }
    }
    return jsonify(contracts), 200


# ---------------------------------------------------------------------------
# Gemini Provider Status Endpoint
# ---------------------------------------------------------------------------
@api_bp.route("/gemini/status", methods=["GET"])
def gemini_status():
    """Reports Gemini configuration status safely without leaking secrets.
    
    By default, checks configuration presence without making paid/external API calls.
    Pass `?live=true` or `?test=true` to explicitly perform a live network ping.
    """
    test_live = request.args.get("live", "false").lower() in ("true", "1", "yes") or \
                request.args.get("test", "false").lower() in ("true", "1", "yes")

    config = get_gemini_config()

    if not config["is_configured"]:
        return jsonify({
            "status": "unconfigured",
            "connected": False,
            "message": "Gemini API key is not configured. Add GEMINI_API_KEY to your .env file.",
            "meta": {
                "configured": False,
                "model": config["model"],
                "live_tested": False
            }
        }), 200

    if test_live:
        success, message, meta = test_gemini_connection()
        return jsonify({
            "status": "success" if success else "failed",
            "connected": success,
            "message": message,
            "meta": meta
        }), 200 if success else (400 if meta.get("error") else 200)

    # Safe passive status check (does not incur API usage)
    return jsonify({
        "status": "configured",
        "connected": True,
        "message": f"Gemini API key configured for model '{config['model']}'. Append ?live=true to test live connectivity.",
        "meta": {
            "configured": True,
            "model": config["model"],
            "live_tested": False
        }
    }), 200


# ---------------------------------------------------------------------------
# Company Profile Endpoints
# ---------------------------------------------------------------------------
@api_bp.route("/company-profile", methods=["GET"])
def get_profile():
    """Retrieves the configured company profile."""
    profile = get_company_profile()
    return jsonify({
        "status": "success",
        "profile": profile,
        "is_configured": profile is not None
    }), 200


@api_bp.route("/company-profile", methods=["POST", "PUT"])
def update_profile():
    """Creates or updates the company profile."""
    data = request.get_json(silent=True)
    is_valid, errors, cleaned = validate_company_profile(data)
    if not is_valid:
        return jsonify({
            "status": "error",
            "error": "Validation failed",
            "details": errors
        }), 400

    saved_profile = save_company_profile(cleaned)
    return jsonify({
        "status": "success",
        "message": "Company profile saved successfully.",
        "profile": saved_profile
    }), 200


# ---------------------------------------------------------------------------
# Competitors Endpoints
# ---------------------------------------------------------------------------
@api_bp.route("/competitors", methods=["GET"])
def get_competitors():
    """Lists all tracked competitors."""
    competitors = list_competitors()
    return jsonify({
        "status": "success",
        "count": len(competitors),
        "competitors": competitors
    }), 200


@api_bp.route("/competitors", methods=["POST"])
def add_competitor():
    """Adds a new competitor."""
    data = request.get_json(silent=True)
    is_valid, errors, cleaned = validate_competitor(data)
    if not is_valid:
        return jsonify({
            "status": "error",
            "error": "Validation failed",
            "details": errors
        }), 400

    competitor = create_competitor(
        name=cleaned["name"],
        website_url=cleaned["website_url"],
        notes=cleaned.get("notes", "")
    )
    return jsonify({
        "status": "success",
        "message": "Competitor added successfully.",
        "competitor": competitor
    }), 201


@api_bp.route("/competitors/<int:competitor_id>", methods=["GET"])
def get_single_competitor(competitor_id: int):
    """Retrieves a single competitor by ID."""
    competitor = get_competitor(competitor_id)
    if not competitor:
        return jsonify({
            "status": "error",
            "error": f"Competitor with ID {competitor_id} not found."
        }), 404

    return jsonify({
        "status": "success",
        "competitor": competitor
    }), 200


@api_bp.route("/competitors/<int:competitor_id>", methods=["PUT"])
def edit_competitor(competitor_id: int):
    """Updates an existing competitor."""
    data = request.get_json(silent=True)
    is_valid, errors, cleaned = validate_competitor(data)
    if not is_valid:
        return jsonify({
            "status": "error",
            "error": "Validation failed",
            "details": errors
        }), 400

    updated = update_competitor(
        competitor_id=competitor_id,
        name=cleaned["name"],
        website_url=cleaned["website_url"],
        notes=cleaned.get("notes", "")
    )
    if not updated:
        return jsonify({
            "status": "error",
            "error": f"Competitor with ID {competitor_id} not found."
        }), 404

    return jsonify({
        "status": "success",
        "message": "Competitor updated successfully.",
        "competitor": updated
    }), 200


@api_bp.route("/competitors/<int:competitor_id>", methods=["DELETE"])
def remove_competitor(competitor_id: int):
    """Deletes a competitor."""
    deleted = delete_competitor(competitor_id)
    if not deleted:
        return jsonify({
            "status": "error",
            "error": f"Competitor with ID {competitor_id} not found."
        }), 404

    return jsonify({
        "status": "success",
        "message": "Competitor removed successfully."
    }), 200


# ---------------------------------------------------------------------------
# Blog Draft Endpoints
# ---------------------------------------------------------------------------
@api_bp.route("/draft", methods=["GET"])
def get_current_draft():
    """Retrieves the latest blog draft."""
    draft = get_latest_draft()
    return jsonify({
        "status": "success",
        "draft": draft,
        "has_draft": draft is not None
    }), 200


@api_bp.route("/draft/<int:draft_id>", methods=["GET"])
def get_single_draft(draft_id: int):
    """Retrieves a specific draft by ID."""
    draft = get_draft(draft_id)
    if not draft:
        return jsonify({
            "status": "error",
            "error": f"Draft with ID {draft_id} not found."
        }), 404

    return jsonify({
        "status": "success",
        "draft": draft
    }), 200


@api_bp.route("/drafts", methods=["GET"])
def get_all_drafts():
    """Retrieves all drafts stored in the local library."""
    drafts = list_drafts()
    return jsonify({
        "status": "success",
        "drafts": drafts,
        "count": len(drafts),
        "is_demo_library": True
    }), 200


@api_bp.route("/blogs", methods=["GET"])
def get_blogs_list():
    """Retrieves published blogs for the /blogs catalog with optional search and status filtering."""
    status_param = request.args.get("status")
    search_param = request.args.get("q")
    blogs = list_blogs(status_filter=status_param, search_query=search_param)
    return jsonify({
        "status": "success",
        "count": len(blogs),
        "blogs": blogs
    }), 200


@api_bp.route("/draft", methods=["POST", "PUT"])
def save_current_draft():
    """Saves or updates blog draft content."""
    data = request.get_json(silent=True)
    is_valid, errors, cleaned = validate_draft(data)
    if not is_valid:
        return jsonify({
            "status": "error",
            "error": "Validation failed",
            "details": errors
        }), 400

    status = cleaned.get("status", "draft")
    if status != "approved":
        invalidate_workflow_approval("default")

    saved = save_draft(
        title=cleaned["title"],
        content_markdown=cleaned["content_markdown"],
        status=status,
        draft_id=cleaned.get("draft_id")
    )
    return jsonify({
        "status": "success",
        "message": "Draft saved successfully.",
        "draft": saved
    }), 200


# ---------------------------------------------------------------------------
# LangGraph Workflow Endpoints
# ---------------------------------------------------------------------------
@api_bp.route("/workflow/start", methods=["POST"])
def start_content_workflow():
    """Starts a LangGraph multi-agent run for a given user prompt."""
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    is_async = data.get("async", False) or request.args.get("async", "false").lower() == "true"

    if not message:
        return jsonify({"status": "error", "error": "Message content is required."}), 400

    # Retrieve context from SQLite
    profile = get_company_profile() or {}
    competitors = list_competitors() or []

    if is_async:
        # Launch asynchronously so client can poll real-time stage events
        run_id = start_workflow_async(
            session_id=session_id,
            user_request=message,
            company_profile=profile,
            competitors=competitors
        )
        return jsonify({
            "status": "started",
            "session_id": session_id,
            "run_id": run_id,
            "message": f"Workflow run '{run_id}' initiated in background."
        }), 202

    # Run LangGraph pipeline synchronously (default for unit tests)
    final_state = start_workflow(
        session_id=session_id,
        user_request=message,
        company_profile=profile,
        competitors=competitors
    )

    # Store assistant response in SQLite chat history
    draft = final_state.get("draft", {})
    reply_text = (
        f"Research and initial draft completed for '{draft.get('title', message)}'. "
        f"Generated {draft.get('word_count', 0)} words with {len(final_state.get('analysis_report', {}).get('sources', []))} evidence sources. "
        "Awaiting your editorial review in the workspace."
    )
    add_message(session_id, "user", message)
    add_message(session_id, "assistant", reply_text)

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "run_id": final_state.get("run_id"),
        "reply": reply_text,
        "workflow": {
            "status": final_state.get("status"),
            "current_step": final_state.get("current_step"),
            "draft": final_state.get("draft"),
            "analysis_report": final_state.get("analysis_report"),
            "validation_result": final_state.get("validation_result")
        },
        "events": final_state.get("events", [])
    }), 200


@api_bp.route("/workflow/<session_id>/status", methods=["GET"])
def get_workflow_progress(session_id: str):
    """Polls progress of an active workflow, returning live events and draft."""
    state = get_workflow_state(session_id)
    requested_run_id = request.args.get("run_id")

    # If run_id is supplied or in state, retrieve real-time stage events
    run_id = requested_run_id or (state.get("run_id") if state else None)
    if not run_id:
        latest_run = get_latest_workflow_run(session_id)
        if latest_run:
            run_id = latest_run["run_id"]

    events = get_formatted_workflow_events(run_id) if run_id else []

    if not state:
        if run_id:
            return jsonify({
                "status": "running",
                "session_id": session_id,
                "run_id": run_id,
                "events": events
            }), 200
        return jsonify({
            "status": "not_found",
            "message": f"No active workflow for session '{session_id}'."
        }), 404

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "run_id": run_id,
        "events": events,
        "workflow": {
            "status": state.get("status"),
            "current_step": state.get("current_step"),
            "draft": state.get("draft"),
            "analysis_report": state.get("analysis_report"),
            "validation_result": state.get("validation_result"),
            "approval_state": state.get("approval_state"),
            "error": state.get("error")
        }
    }), 200


@api_bp.route("/workflow/runs/<run_id>", methods=["GET"])
def get_run_events(run_id: str):
    """Retrieves full stage event timeline for a specific workflow run ID."""
    events = get_formatted_workflow_events(run_id)
    return jsonify({
        "status": "success",
        "run_id": run_id,
        "events": events
    }), 200


@api_bp.route("/workflow/<session_id>/regenerate", methods=["POST"])
def regenerate_draft(session_id: str):
    """Regenerates a fresh draft version, invalidates approval, and records events."""
    try:
        updated_state = regenerate_workflow_draft(session_id)
        draft = updated_state.get("draft", {})
        ver = draft.get("version", 2)
        add_message(session_id, "user", "Regenerate Article Request")
        add_message(session_id, "assistant", f"Draft regenerated to Version {ver}. Ready for editorial re-review.")

        return jsonify({
            "status": "success",
            "session_id": session_id,
            "workflow": {
                "status": updated_state.get("status"),
                "draft": draft,
                "approval_state": updated_state.get("approval_state")
            },
            "events": updated_state.get("events", [])
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "error": str(e)}), 400


@api_bp.route("/workflow/<session_id>/revise", methods=["POST"])
def revise_workflow_draft(session_id: str):
    """Submits revision notes, increments version, and invalidates previous approvals."""
    data = request.get_json(silent=True) or {}
    notes = data.get("revision_notes", "").strip()
    if not notes:
        return jsonify({"status": "error", "error": "Revision notes are required."}), 400

    try:
        updated_state = request_workflow_revision(session_id, notes)
        add_message(session_id, "user", f"Revision Request: {notes}")
        add_message(session_id, "assistant", f"Draft revised to Version {updated_state.get('draft', {}).get('version', 2)}. Ready for re-review.")

        return jsonify({
            "status": "success",
            "session_id": session_id,
            "workflow": {
                "status": updated_state.get("status"),
                "draft": updated_state.get("draft"),
                "approval_state": updated_state.get("approval_state")
            }
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "error": str(e)}), 400


@api_bp.route("/workflow/<session_id>/approve", methods=["POST"])
def approve_workflow(session_id: str):
    """Explicitly approves the current draft version and returns an approval token."""
    try:
        approval_data = approve_workflow_draft(session_id)
        # Update SQLite draft status
        draft = get_latest_draft()
        if draft:
            save_draft(title=draft["title"], content_markdown=draft["content_markdown"], status="approved", draft_id=draft["id"])

        add_message(session_id, "assistant", f"Draft version {approval_data['version']} approved by editorial reviewer.")

        return jsonify({
            "status": "success",
            "message": "Draft version approved.",
            "approval": approval_data
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "error": str(e)}), 400


@api_bp.route("/workflow/<session_id>/publish", methods=["POST"])
def publish_workflow(session_id: str):
    """Publishes the approved draft to the in-app Content Crew Blogs library."""
    try:
        result_state = publish_workflow_draft(session_id)
        if result_state.get("status") == "error":
            return jsonify({
                "status": "error",
                "error": result_state.get("error")
            }), 403

        msg = result_state.get("publish_result", {}).get("message") or "Draft published to your Content Crew Blogs library."
        add_message(session_id, "assistant", msg)

        return jsonify({
            "status": "success",
            "message": msg,
            "is_public_publish": False,
            "publish_result": result_state.get("publish_result")
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "error": str(e)}), 400


# ---------------------------------------------------------------------------
# Chat Sessions & Messages Endpoints
# ---------------------------------------------------------------------------
@api_bp.route("/chat/sessions", methods=["GET"])
def get_sessions():
    """Lists all chat sessions."""
    sessions = list_sessions()
    return jsonify({
        "status": "success",
        "sessions": sessions
    }), 200


@api_bp.route("/chat/sessions", methods=["POST"])
def create_session():
    """Creates a new chat session."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id") or f"session_{int(datetime.datetime.now().timestamp())}"
    title = data.get("title") or "Editorial Chat"
    session = get_or_create_session(session_id, title)
    return jsonify({
        "status": "success",
        "session": session
    }), 201


@api_bp.route("/chat/sessions/<session_id>/messages", methods=["GET"])
def get_messages(session_id: str):
    """Retrieves message history for a chat session."""
    messages = get_session_messages(session_id)
    return jsonify({
        "status": "success",
        "session_id": session_id,
        "count": len(messages),
        "messages": messages
    }), 200


@api_bp.route("/chat/sessions/<session_id>/messages", methods=["POST"])
def post_message(session_id: str):
    """Dispatches user message into the LangGraph multi-agent pipeline."""
    data = request.get_json(silent=True)
    is_valid, errors, message_text = validate_chat_message(data)
    if not is_valid:
        return jsonify({
            "status": "error",
            "error": "Validation failed",
            "details": errors
        }), 400

    profile = get_company_profile() or {}
    competitors = list_competitors() or []

    # Check async flag
    is_async = data.get("async", False) or request.args.get("async", "false").lower() == "true"
    if is_async:
        user_msg = add_message(session_id, "user", message_text)
        run_id = start_workflow_async(
            session_id=session_id,
            user_request=message_text,
            company_profile=profile,
            competitors=competitors
        )
        return jsonify({
            "status": "started",
            "session_id": session_id,
            "run_id": run_id,
            "user_message": user_msg
        }), 202

    # Run through LangGraph
    final_state = start_workflow(
        session_id=session_id,
        user_request=message_text,
        company_profile=profile,
        competitors=competitors
    )

    draft = final_state.get("draft", {})
    sources = final_state.get("analysis_report", {}).get("sources", [])

    reply = (
        f"Research and draft synthesized for '{draft.get('title', message_text)}'. "
        f"Generated {draft.get('word_count', 0)} words based on {len(sources)} source anchors. "
        "Draft is loaded in the workspace editor for review."
    )

    user_msg = add_message(session_id, "user", message_text)
    assistant_msg = add_message(session_id, "assistant", reply)

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "run_id": final_state.get("run_id"),
        "user_message": user_msg,
        "assistant_message": assistant_msg,
        "reply": reply,
        "is_demo": True,
        "events": final_state.get("events", []),
        "workflow": {
            "draft": draft,
            "status": final_state.get("status"),
            "current_step": final_state.get("current_step")
        }
    }), 200


@api_bp.route("/chat", methods=["POST"])
def legacy_chat():
    """Phase 1/2 legacy compatibility route forwarding to default session."""
    return post_message(session_id="default")
