"""Phase 5 Comprehensive Test Suite - DataForge Content Crew
Agent Workflow Visibility, In-App Blogs Library, Regeneration & UX Upgrades
"""

import os
import sys
import json
import tempfile
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from db import (
    init_db,
    get_draft,
    save_draft,
    list_drafts,
    list_blogs,
    get_workflow_events,
    get_latest_workflow_run
)
import services.gemini_service as gemini_service
from services.workflow_tracker import (
    initialize_workflow_run,
    start_stage,
    complete_stage,
    fail_stage,
    get_formatted_workflow_events
)
from tools.web_search import search_web
from tools.content_analyzer import analyze_content
from tools.demo_publisher import publish_draft_to_demo_store
from graph.workflow import (
    start_workflow,
    get_workflow_state,
    regenerate_workflow_draft,
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

    gemini_service.set_mock_responder(None)
    if old_db:
        os.environ["DATABASE_PATH"] = old_db
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass


def test_workflow_all_ten_stages_execution(isolated_client):
    """Verifies that all 10 LangGraph stages execute and record genuine events in SQLite."""
    session_id = "test_ten_stages_sess"
    final_state = start_workflow(
        session_id=session_id,
        user_request="Autonomous Multi-Agent Architectures",
        company_profile={"company_name": "DataForge Labs", "tone": "Technical", "industry": "AI Software"},
        competitors=[{"name": "CompetitorA", "website_url": "https://competitor-a.com"}]
    )

    assert "events" in final_state
    events = final_state["events"]
    assert len(events) == 10

    expected_stage_ids = [
        "stage_1_understanding",
        "stage_2_planning",
        "stage_3_search",
        "stage_4_sources",
        "stage_5_competitors",
        "stage_6_analysis",
        "stage_7_outline",
        "stage_8_generation",
        "stage_9_review",
        "stage_10_draft_ready"
    ]

    actual_stage_ids = [ev["stage_id"] for ev in events]
    assert actual_stage_ids == expected_stage_ids

    # All stages completed successfully
    for ev in events:
        assert ev["status"] == "completed"
        assert len(ev["label"]) > 0
        assert len(ev["description"]) > 0
        assert ev["completed_at"] is not None

    # Verify persisted in SQLite
    run_id = final_state["run_id"]
    db_events = get_workflow_events(run_id)
    assert len(db_events) == 10


def test_stage_failure_recording(isolated_client):
    """Verifies that stage failures are honestly recorded with error details."""
    run_id = initialize_workflow_run("fail_test_sess", "Testing error capture")
    start_stage(run_id, "stage_3_search", "Connecting to search provider...")
    fail_stage(run_id, "stage_3_search", "Provider connection timed out after 6000ms.")

    events = get_formatted_workflow_events(run_id)
    search_ev = next(e for e in events if e["stage_id"] == "stage_3_search")
    assert search_ev["status"] == "failed"
    assert "timed out" in search_ev["description"]


def test_web_search_honesty_and_no_fabrication(isolated_client):
    """Verifies that when search is unconfigured, it reports honestly without fabricating fake sources."""
    res = search_web("Enterprise Kubernetes Security")
    # In test environment, Tavily is unconfigured
    if not res.get("is_available"):
        assert res["provider"] == "None"
        assert len(res["results"]) == 0
        assert "unconfigured" in res["message"].lower()


def test_regeneration_increments_version_and_invalidates_approval(isolated_client):
    """Verifies that Regenerate Article creates a fresh version, invalidates approval, and keeps history."""
    session_id = "regen_test_session"

    # 1. Start initial workflow
    start_res = isolated_client.post("/api/workflow/start", json={
        "message": "Distributed Message Queues in Fintech",
        "session_id": session_id
    })
    assert start_res.status_code == 200
    start_data = start_res.get_json()
    assert start_data["workflow"]["draft"]["version"] == 1

    # 2. Approve draft version 1
    app_res = isolated_client.post(f"/api/workflow/{session_id}/approve")
    assert app_res.status_code == 200
    assert app_res.get_json()["approval"]["version"] == 1

    # 3. Call Regenerate Article endpoint
    regen_res = isolated_client.post(f"/api/workflow/{session_id}/regenerate")
    assert regen_res.status_code == 200
    regen_data = regen_res.get_json()

    # Draft version must be incremented to 2
    new_draft = regen_data["workflow"]["draft"]
    assert new_draft["version"] == 2

    # Prior approval must be invalidated
    assert regen_data["workflow"]["approval_state"]["is_approved"] is False
    assert regen_data["workflow"]["approval_state"]["approved_version"] is None

    # Check database persistence: both version records exist in history
    all_drafts = list_drafts()
    assert len(all_drafts) >= 2


def test_publishing_to_in_app_blogs_library_requires_exact_version_approval(isolated_client):
    """Verifies that publishing requires explicit approval for the exact version and populates /blogs."""
    session_id = "pub_blogs_test_session"

    # 1. Start workflow
    isolated_client.post("/api/workflow/start", json={
        "message": "GraphQL Federation Patterns",
        "session_id": session_id
    })

    # 2. Attempt to publish unapproved draft -> Must fail with HTTP 403
    pub_fail = isolated_client.post(f"/api/workflow/{session_id}/publish")
    assert pub_fail.status_code == 403
    assert "not been explicitly approved" in pub_fail.get_json()["error"]

    # 3. Approve draft version 1
    app_res = isolated_client.post(f"/api/workflow/{session_id}/approve")
    assert app_res.status_code == 200

    # 4. Publish approved draft
    pub_res = isolated_client.post(f"/api/workflow/{session_id}/publish")
    assert pub_res.status_code == 200
    pub_data = pub_res.get_json()
    assert "Content Crew Blogs library" in pub_data["message"]
    assert pub_data["is_public_publish"] is False

    # 5. Check in-app Blogs catalog endpoint
    blogs_res = isolated_client.get("/api/blogs")
    assert blogs_res.status_code == 200
    blogs = blogs_res.get_json()["blogs"]
    assert len(blogs) >= 1
    published_entry = next(b for b in blogs if b["title"] == pub_data["publish_result"]["draft"]["title"])
    assert published_entry["status"] == "published"
    assert published_entry["published_at"] is not None


def test_editing_draft_invalidates_approval_and_blocks_publication(isolated_client):
    """Verifies that manual draft edits invalidate prior approvals and prevent publishing until re-approved."""
    session_id = "edit_guard_test_session"

    isolated_client.post("/api/workflow/start", json={
        "message": "Zero Trust IAM in Multi-Cloud",
        "session_id": session_id
    })

    # Approve v1
    isolated_client.post(f"/api/workflow/{session_id}/approve")

    # User manually edits draft in editor (POST /api/draft with status="draft")
    draft = isolated_client.get("/api/draft").get_json()["draft"]
    isolated_client.post("/api/draft", json={
        "draft_id": draft["id"],
        "title": draft["title"],
        "content_markdown": draft["content_markdown"] + "\n\nAdded critical security disclaimer.",
        "status": "draft"
    })

    # Publication attempt must be blocked
    pub_blocked = isolated_client.post(f"/api/workflow/{session_id}/publish")
    assert pub_blocked.status_code == 403

    # Re-approve
    re_app = isolated_client.post(f"/api/workflow/{session_id}/approve")
    assert re_app.status_code == 200

    # Publishing succeeds after re-approval
    pub_ok = isolated_client.post(f"/api/workflow/{session_id}/publish")
    assert pub_ok.status_code == 200


def test_blogs_page_rendering_and_query_filters(isolated_client):
    """Verifies GET /blogs page response and /api/blogs search/status filtering."""
    # Check HTML page render
    page_res = isolated_client.get("/blogs")
    assert page_res.status_code == 200
    html = page_res.get_data(as_text=True)
    assert "Content Crew Published Articles" in html
    assert "blogs-search" in html
    assert "status-filter" in html
    assert "theme-toggle" in html

    # Populate two test articles
    save_draft("React Server Components Architecture", "Deep dive into RSC...", status="published", company_name="TechCorp", create_new_row=True)
    save_draft("Legacy Python 2 to 3 Migration Guide", "Step by step migration...", status="draft", company_name="DataForge", create_new_row=True)

    # Test filtering by status
    pub_res = isolated_client.get("/api/blogs?status=published")
    assert pub_res.status_code == 200
    pub_blogs = pub_res.get_json()["blogs"]
    assert all(b["status"] == "published" for b in pub_blogs)

    # Test search query
    search_res = isolated_client.get("/api/blogs?q=React")
    assert search_res.status_code == 200
    search_blogs = search_res.get_json()["blogs"]
    assert any("React" in b["title"] for b in search_blogs)


def test_content_analyzer_structure_and_citations(isolated_client):
    """Verifies content analyzer checks semantic headings, title, and citation linkages."""
    markdown_sample = """## 1. Executive Overview
This is a comprehensive strategy for modern cloud infrastructure.

## 2. Platform Implementation
Key implementation best practices are outlined below.

Refer to the official architecture guide at [AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/).

## Conclusion
Final strategic takeaways for engineering leaders.
"""
    result = analyze_content(
        title="Modern Cloud Architecture Strategy",
        content_markdown=markdown_sample,
        target_keyword="strategy"
    )

    assert result["is_valid"] is True
    assert result["headings_count"] >= 2
    assert result["citations_count"] == 1
    assert result["citations"][0]["url"] == "https://aws.amazon.com/architecture/well-architected/"
