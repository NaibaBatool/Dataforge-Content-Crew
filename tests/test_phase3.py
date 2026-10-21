"""Automated test suite for DataForge Content Crew - Phase 3 LangGraph & Gemini
Tests multi-agent workflows, state transitions, tool safety, revision flow, and publishing guards.
"""

import os
import sys
import json
import tempfile
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from db import init_db
from services.gemini_service import test_gemini_connection as check_gemini_conn, set_mock_responder
from tools.web_search import search_web
from tools.webpage_reader import read_webpage
from tools.keyword_analyzer import analyze_keywords
from tools.content_analyzer import analyze_content
from graph.workflow import (
    start_workflow,
    get_workflow_state,
    request_workflow_revision,
    approve_workflow_draft,
    publish_workflow_draft
)


@pytest.fixture
def test_client():
    """Configures a temporary SQLite database and Flask test client."""
    db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    old_db = os.environ.get("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = temp_db_path

    # Initialize SQLite schema
    init_db(temp_db_path)

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

    # Cleanup temporary test database
    if old_db is not None:
        os.environ["DATABASE_PATH"] = old_db
    else:
        os.environ.pop("DATABASE_PATH", None)
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# 1. Gemini Configuration & Missing Credentials Tests
# ---------------------------------------------------------------------------
def test_gemini_connection_function():
    """Verifies that test_gemini_connection returns a valid (bool, str, dict) tuple."""
    res = check_gemini_conn()
    assert isinstance(res, tuple)
    assert len(res) == 3
    assert isinstance(res[0], bool)
    assert isinstance(res[1], str)
    assert isinstance(res[2], dict)


def test_gemini_unconfigured_behavior():
    """Verifies that missing GEMINI_API_KEY is handled cleanly without crashing or false claims."""
    # Temporarily unset key
    old_key = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = ""

    is_connected, msg, meta = check_gemini_conn()
    assert is_connected is False
    assert "not configured" in msg
    assert meta["configured"] is False

    # Restore key if existed
    if old_key is not None:
        os.environ["GEMINI_API_KEY"] = old_key


def test_gemini_status_endpoint(test_client):
    """Verifies GET /api/gemini/status returns configuration metadata without leaking secrets."""
    res = test_client.get("/api/gemini/status")
    assert res.status_code in (200, 400)
    data = res.get_json()
    assert "connected" in data
    assert "meta" in data
    assert "model" in data["meta"]
    # Ensure no secret key is exposed in JSON
    raw_str = json.dumps(data)
    assert "AIza" not in raw_str


# ---------------------------------------------------------------------------
# 2. Research Tools Safety Tests
# ---------------------------------------------------------------------------
def test_web_search_unconfigured_honesty():
    """Verifies that unconfigured search provider truthfully reports unavailability without fake URLs."""
    old_tavily = os.environ.get("TAVILY_API_KEY")
    try:
        os.environ["TAVILY_API_KEY"] = ""
        res = search_web("Kubernetes Cost Optimization")
        assert res["is_available"] is False
        assert len(res["results"]) == 0
        assert "unconfigured" in res["message"]
    finally:
        if old_tavily is not None:
            os.environ["TAVILY_API_KEY"] = old_tavily
        else:
            os.environ.pop("TAVILY_API_KEY", None)


def test_webpage_reader_scheme_guard():
    """Verifies webpage reader rejects non-http schemes."""
    res = read_webpage("file:///etc/passwd")
    assert res["success"] is False
    assert "Invalid URL scheme" in res["error"]


def test_keyword_analyzer_no_fabricated_metrics():
    """Verifies keyword analyzer extracts semantic terms without fabricating fake search volumes."""
    res = analyze_keywords("Cloud Security Posture Management", "Drive inbound signups", "DevOps")
    assert res["primary_keyword"] is not None
    assert len(res["secondary_keywords"]) > 0
    assert "No third-party search volume metrics fabricated" in res["honesty_notice"]


def test_content_analyzer():
    """Verifies content quality and structure analyzer checks headings and length."""
    content = "## Section 1\n\nContent paragraph.\n\n## Section 2\n\nAnother paragraph."
    res = analyze_content("Scalable Cloud Architectures", content, "Cloud")
    assert res["headings_count"] == 2
    assert "Section 1" in res["h2_sections"]


# ---------------------------------------------------------------------------
# 3. LangGraph Workflow State Transitions & Approval Guard Tests
# ---------------------------------------------------------------------------
def test_langgraph_full_workflow_lifecycle(test_client):
    """Verifies execution through planning -> research -> generation -> review."""
    session_id = "test_session_lifecycle"
    profile = {
        "company_name": "TestCloud Systems",
        "industry": "DevOps",
        "target_audience": "VP of Infrastructure",
        "tone": "Authoritative & Technical",
        "usp": "Multi-cloud Kubernetes federation in minutes",
        "content_goals": "Thought leadership"
    }
    competitors = [{"name": "CompetitorX", "website_url": "https://comp-x.io", "notes": "Leader"}]

    final_state = start_workflow(
        session_id=session_id,
        user_request="Best practices for Kubernetes multi-cloud deployment",
        company_profile=profile,
        competitors=competitors
    )

    # 1. State assertions
    assert final_state["status"] == "review_pending"
    assert "plan" in final_state
    assert "analysis_report" in final_state
    assert "draft" in final_state
    assert final_state["draft"]["version"] == 1
    assert final_state["draft"]["word_count"] > 50
    assert final_state["approval_state"]["is_approved"] is False

    # 2. Test Revision Flow (Increments version & invalidates approval)
    revised_state = request_workflow_revision(session_id, "Emphasize security governance in Section 2")
    assert revised_state["draft"]["version"] == 2
    assert revised_state["approval_state"]["is_approved"] is False

    # 3. Test Publishing Guard (Cannot publish unapproved draft)
    unapproved_publish = publish_workflow_draft(session_id)
    assert unapproved_publish["status"] == "error"
    assert "explicitly approved" in unapproved_publish["error"]

    # 4. Explicit Approval (Binds to exact version 2)
    approval_info = approve_workflow_draft(session_id)
    assert approval_info["status"] == "approved"
    assert approval_info["version"] == 2
    assert approval_info["approval_token"] is not None

    # 5. Successful Demo Publishing after version-verified approval
    published_state = publish_workflow_draft(session_id)
    assert published_state["status"] == "published"
    assert published_state["publish_result"]["success"] is True
    assert published_state["publish_result"]["is_public_publish"] is False


# ---------------------------------------------------------------------------
# 4. API Endpoints Integration Tests
# ---------------------------------------------------------------------------
def test_workflow_api_endpoints(test_client):
    """Verifies /api/workflow endpoints for starting, polling, revising, approving, and publishing."""
    # 1. Start workflow
    start_res = test_client.post("/api/workflow/start", json={
        "session_id": "api_test_session",
        "message": "CI/CD Pipeline Governance"
    })
    assert start_res.status_code == 200
    start_data = start_res.get_json()
    assert start_data["status"] == "success"
    assert start_data["workflow"]["status"] == "review_pending"
    assert start_data["workflow"]["draft"]["version"] == 1

    # 2. Check workflow status polling
    poll_res = test_client.get("/api/workflow/api_test_session/status")
    assert poll_res.status_code == 200
    poll_data = poll_res.get_json()
    assert poll_data["workflow"]["draft"]["title"] is not None

    # 3. Revision endpoint
    rev_res = test_client.post("/api/workflow/api_test_session/revise", json={
        "revision_notes": "Add actionable checklist"
    })
    assert rev_res.status_code == 200
    assert rev_res.get_json()["workflow"]["draft"]["version"] == 2

    # 4. Publishing without approval fails with 403
    pub_fail = test_client.post("/api/workflow/api_test_session/publish")
    assert pub_fail.status_code == 403

    # 5. Approval endpoint
    app_res = test_client.post("/api/workflow/api_test_session/approve")
    assert app_res.status_code == 200
    assert app_res.get_json()["approval"]["version"] == 2

    # 6. Publishing succeeds after explicit approval
    pub_success = test_client.post("/api/workflow/api_test_session/publish")
    assert pub_success.status_code == 200
    assert pub_success.get_json()["status"] == "success"


# ---------------------------------------------------------------------------
# 5. Jupyter Notebook Validation Test
# ---------------------------------------------------------------------------
def test_notebook_exists_and_is_valid_json():
    """Verifies that the experiments Jupyter notebook is a valid .ipynb document."""
    notebook_path = os.path.join(os.path.dirname(__file__), "..", "notebooks", "gemini_agent_experiments.ipynb")
    assert os.path.exists(notebook_path), "Notebook file missing."
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    assert nb["nbformat"] == 4
    assert len(nb["cells"]) >= 4
