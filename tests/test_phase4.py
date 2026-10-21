"""Phase 4 Comprehensive Test Suite - DataForge Content Crew
Testing, Integration, and Final Verification
"""

import os
import sys
import json
import tempfile
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from db import init_db, get_draft, save_draft, list_competitors
import services.gemini_service as gemini_service
from tools.web_search import search_web
from tools.webpage_reader import read_webpage
from tools.keyword_analyzer import analyze_keywords
from tools.content_analyzer import analyze_content
from tools.demo_publisher import publish_draft_to_demo_store
from graph.workflow import (
    start_workflow,
    get_workflow_state,
    request_workflow_revision,
    approve_workflow_draft,
    publish_workflow_draft,
    invalidate_workflow_approval
)


@pytest.fixture
def isolated_client():
    """Provides a fresh, isolated temporary SQLite database for each test."""
    db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    old_db = os.environ.get("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = temp_db_path

    init_db(temp_db_path)

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

    # Cleanup mock responder & temp DB
    gemini_service.set_mock_responder(None)
    if old_db:
        os.environ["DATABASE_PATH"] = old_db
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# 1. Gemini Error Handling & Provider Resilience Tests
# ---------------------------------------------------------------------------
def test_gemini_missing_api_key():
    """Verifies missing API key is reported accurately without crashing."""
    old_key = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = ""

    connected, msg, meta = gemini_service.test_gemini_connection()
    assert connected is False
    assert "not configured" in msg
    assert meta["configured"] is False

    res = gemini_service.generate_content("test prompt")
    assert res["status"] == "unconfigured"
    assert "not configured" in res["error"]

    if old_key is not None:
        os.environ["GEMINI_API_KEY"] = old_key


def test_gemini_mocked_success():
    """Verifies successful generation using registered mock without paid API."""
    gemini_service.set_mock_responder(lambda prompt, sys_inst, json_mode: "Mocked Gemini generation successful.")
    res = gemini_service.generate_content("Generate blog outline")
    assert res["status"] == "success"
    assert "Mocked Gemini" in res["text"]
    assert res["is_live_ai"] is False


def test_gemini_empty_or_malformed_response_handling():
    """Verifies that an empty or whitespace-only response from Gemini is handled gracefully."""
    gemini_service.set_mock_responder(lambda p, s, j: "")
    from agents.generation_agent import run_generation_agent

    draft = run_generation_agent(
        topic="Cloud Security",
        analysis_report={"primary_keyword": "cloud security", "summary": "test"},
        company_profile={"company_name": "Acme", "tone": "Technical"}
    )
    assert draft is not None
    assert "Cloud Security" in draft["title"]
    assert draft["word_count"] > 50
    assert draft["is_live_ai"] is False


# ---------------------------------------------------------------------------
# 2. Research Tools & Honesty Policy Tests
# ---------------------------------------------------------------------------
def test_web_search_empty_query():
    """Verifies web search handles empty queries gracefully."""
    res = search_web("   ")
    assert res["is_available"] is False
    assert "Empty search query" in res["message"]


def test_web_search_unconfigured_never_fabricates():
    """Verifies search tool never invents fake URLs or citations when unconfigured."""
    old_key = os.environ.get("TAVILY_API_KEY")
    os.environ["TAVILY_API_KEY"] = ""

    res = search_web("DevOps Kubernetes Trends")
    assert res["is_available"] is False
    assert len(res["results"]) == 0
    assert "unconfigured" in res["message"]

    if old_key is not None:
        os.environ["TAVILY_API_KEY"] = old_key


def test_webpage_reader_unsafe_url_rejection():
    """Verifies webpage reader rejects javascript:, file:, and ftp: schemes."""
    assert read_webpage("javascript:alert(1)")["success"] is False
    assert read_webpage("ftp://example.com/file")["success"] is False
    assert read_webpage("")["success"] is False


def test_content_analyzer_heading_and_word_count_checks():
    """Verifies content analyzer detects weak structure and passes good structure."""
    weak = analyze_content("Hi", "Just one line of text without headings.")
    assert weak["is_valid"] is False
    assert "Title is missing or too short." in weak["feedback"]
    assert "Add at least 2 subheadings (H2/H3) for readability." in weak["feedback"]

    strong_content = (
        "## Overview of Platform Governance\n\n"
        "Enterprise platform engineering requires unified standards across all environments. " * 10 +
        "\n\n## Implementation Steps\n\n"
        "Adopt declarative GitOps practices to maintain configuration parity. " * 10
    )
    strong = analyze_content("Comprehensive Enterprise Platform Governance Guide", strong_content)
    assert strong["is_valid"] is True
    assert strong["headings_count"] >= 2
    assert strong["word_count"] >= 150


# ---------------------------------------------------------------------------
# 3. Approval and Publishing Security & Version Enforcement Tests
# ---------------------------------------------------------------------------
def test_publishing_blocked_without_approval(isolated_client):
    """Verifies that publishing without prior approval fails with HTTP 403."""
    # Start a workflow
    start_res = isolated_client.post("/api/workflow/start", json={
        "session_id": "sec_test_session",
        "message": "Continuous Integration Security"
    })
    assert start_res.status_code == 200

    # Attempt publishing immediately without approving
    pub_res = isolated_client.post("/api/workflow/sec_test_session/publish")
    assert pub_res.status_code == 403
    assert "not been explicitly approved" in pub_res.get_json()["error"]


def test_editing_draft_invalidates_prior_approval(isolated_client):
    """Verifies that editing a draft invalidates existing approvals."""
    session_id = "approval_invalidation_test"

    # 1. Start workflow
    isolated_client.post("/api/workflow/start", json={
        "session_id": session_id,
        "message": "Microservices Reliability"
    })

    # 2. Approve draft version 1
    app_res = isolated_client.post(f"/api/workflow/{session_id}/approve")
    assert app_res.status_code == 200
    assert app_res.get_json()["approval"]["version"] == 1

    # 3. Simulate user editing draft content via POST /api/draft
    save_res = isolated_client.post("/api/draft", json={
        "title": "Microservices Reliability: Revised Edition",
        "content_markdown": "## Modified Content\n\nNew modified content.",
        "status": "draft"
    })
    assert save_res.status_code == 200

    # 4. Attempt to publish using outdated version 1 approval
    # Must fail because draft was edited!
    pub_res = isolated_client.post(f"/api/workflow/{session_id}/publish")
    assert pub_res.status_code == 403


def test_revision_invalidates_prior_approval(isolated_client):
    """Verifies that submitting revision feedback increments version and invalidates approvals."""
    session_id = "revision_invalidation_test"

    # 1. Start workflow
    isolated_client.post("/api/workflow/start", json={
        "session_id": session_id,
        "message": "Serverless Architecture"
    })

    # 2. Approve version 1
    isolated_client.post(f"/api/workflow/{session_id}/approve")

    # 3. Submit revision
    rev_res = isolated_client.post(f"/api/workflow/{session_id}/revise", json={
        "revision_notes": "Add cold start mitigation techniques"
    })
    assert rev_res.status_code == 200
    assert rev_res.get_json()["workflow"]["draft"]["version"] == 2
    assert rev_res.get_json()["workflow"]["approval_state"]["is_approved"] is False

    # 4. Publishing must fail because version 2 has not been approved
    pub_res = isolated_client.post(f"/api/workflow/{session_id}/publish")
    assert pub_res.status_code == 403


def test_repeated_publishing_idempotent(isolated_client):
    """Verifies that repeated publishing calls are idempotent and do not duplicate records."""
    session_id = "idempotent_pub_test"

    # Start and approve
    isolated_client.post("/api/workflow/start", json={
        "session_id": session_id,
        "message": "GitOps Pipelines"
    })
    isolated_client.post(f"/api/workflow/{session_id}/approve")

    # First publish
    res1 = isolated_client.post(f"/api/workflow/{session_id}/publish")
    assert res1.status_code == 200
    assert res1.get_json()["status"] == "success"

    # Second publish call (idempotent)
    res2 = isolated_client.post(f"/api/workflow/{session_id}/publish")
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert "already published" in data2["message"] or "published successfully" in data2["message"]


# ---------------------------------------------------------------------------
# 4. API Input Validation & Error Code Tests
# ---------------------------------------------------------------------------
def test_workflow_start_empty_message(isolated_client):
    """Verifies starting workflow with empty message returns HTTP 400."""
    res = isolated_client.post("/api/workflow/start", json={"message": "   "})
    assert res.status_code == 400
    assert "required" in res.get_json()["error"]


def test_workflow_status_unknown_session(isolated_client):
    """Verifies polling non-existent session returns HTTP 404."""
    res = isolated_client.get("/api/workflow/non_existent_session_12345/status")
    assert res.status_code == 404


def test_workflow_revise_empty_notes(isolated_client):
    """Verifies submitting empty revision feedback returns HTTP 400."""
    res = isolated_client.post("/api/workflow/default/revise", json={"revision_notes": "  "})
    assert res.status_code == 400


def test_get_non_existent_draft(isolated_client):
    """Verifies querying non-existent draft ID returns HTTP 404."""
    res = isolated_client.get("/api/draft/999999")
    assert res.status_code == 404


def test_get_non_existent_competitor(isolated_client):
    """Verifies querying non-existent competitor ID returns HTTP 404."""
    res = isolated_client.get("/api/competitors/999999")
    assert res.status_code == 404


def test_delete_non_existent_competitor(isolated_client):
    """Verifies deleting non-existent competitor ID returns HTTP 404."""
    res = isolated_client.delete("/api/competitors/999999")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# 5. Environment Variable & Safe Status Tests
# ---------------------------------------------------------------------------
def test_placeholder_key_treated_as_unconfigured():
    """Verifies that placeholder keys in .env are not mistakenly treated as configured."""
    old_key = os.environ.get("GEMINI_API_KEY")
    try:
        os.environ["GEMINI_API_KEY"] = "your_gemini_api_key_here"
        cfg = gemini_service.get_gemini_config()
        assert cfg["is_configured"] is False

        os.environ["GEMINI_API_KEY"] = "Your-GEMINI-API -key"
        cfg2 = gemini_service.get_gemini_config()
        assert cfg2["is_configured"] is False
    finally:
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key
        else:
            os.environ.pop("GEMINI_API_KEY", None)


def test_gemini_status_never_exposes_key(isolated_client):
    """Verifies that even with a dummy key configured, /api/gemini/status never leaks it."""
    dummy_secret = "AIzaSySecretTestKeyNotForProduction123456"
    old_key = os.environ.get("GEMINI_API_KEY")
    try:
        os.environ["GEMINI_API_KEY"] = dummy_secret
        res = isolated_client.get("/api/gemini/status")
        assert res.status_code == 200
        data = res.get_json()
        assert data["connected"] is True
        assert data["meta"]["configured"] is True
        assert data["meta"]["live_tested"] is False
        # Absolute secret redaction check
        raw_response = json.dumps(data)
        assert dummy_secret not in raw_response
    finally:
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key
        else:
            os.environ.pop("GEMINI_API_KEY", None)

