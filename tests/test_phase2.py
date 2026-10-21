"""Automated test suite for DataForge Content Crew - Phase 2 Backend & Onboarding
Tests SQLite database persistence, validation rules, and REST API behavior.
"""

import os
import sys
import tempfile
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from db import init_db


@pytest.fixture
def test_client():
    """Configures a temporary SQLite database and Flask test client."""
    db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    os.environ["DATABASE_PATH"] = temp_db_path

    # Initialize the temporary database schema
    init_db(temp_db_path)

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

    # Cleanup temporary test database
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Health Check Tests
# ---------------------------------------------------------------------------
def test_health_check_with_db(test_client):
    """Verifies that /api/health confirms SQLite database connectivity."""
    res = test_client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["phase"] in (2, 3)
    assert data["database"] == "connected"


# ---------------------------------------------------------------------------
# Onboarding & Company Profile Tests
# ---------------------------------------------------------------------------
def test_onboarding_page_render(test_client):
    """Verifies that GET /onboarding serves the profile form."""
    res = test_client.get("/onboarding")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Company Profile &amp; Editorial Context" in html
    assert "company_name" in html
    assert "products_services" in html
    assert "target_audience" in html
    assert "usp" in html
    assert "content_goals" in html
    assert "Your Business Profile" in html


def test_company_profile_unconfigured_initially(test_client):
    """Verifies that GET /api/company-profile returns null profile before configuration."""
    res = test_client.get("/api/company-profile")
    assert res.status_code == 200
    data = res.get_json()
    assert data["is_configured"] is False
    assert data["profile"] is None


def test_company_profile_validation_errors(test_client):
    """Verifies that submitting missing/invalid profile fields returns 400 with details."""
    res = test_client.post("/api/company-profile", json={
        "company_name": "Acme Inc"
        # Missing description, website, products, etc.
    })
    assert res.status_code == 400
    data = res.get_json()
    assert data["status"] == "error"
    assert "details" in data
    assert "description" in data["details"]
    assert "website" in data["details"]


def test_company_profile_invalid_url(test_client):
    """Verifies that an invalid website URL is rejected."""
    payload = {
        "company_name": "Acme Cloud",
        "description": "Provider of enterprise cloud infrastructure.",
        "products_services": "Cloud storage and container engines",
        "industry": "B2B SaaS",
        "target_audience": "CTOs and engineering directors",
        "usp": "30% faster multi-cloud builds",
        "website": "invalid-url-without-domain",
        "tone": "Authoritative & Technical",
        "content_goals": "Organic search ranking and lead generation"
    }
    res = test_client.post("/api/company-profile", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert "website" in data["details"]


def test_company_profile_save_and_retrieve(test_client):
    """Verifies that a valid company profile is successfully saved and retrieved."""
    payload = {
        "company_name": "NovaSphere AI",
        "description": "Automated data ingestion and pipeline platform for modern enterprises.",
        "products_services": "NovaIngest, NovaTransform, NovaObservability",
        "industry": "Data Engineering",
        "target_audience": "Data Architects and VP Analytics",
        "usp": "Zero-code ETL pipelines setup in under 5 minutes",
        "website": "https://novasphere.io",
        "tone": "Authoritative & Technical",
        "content_goals": "Drive technical buyer awareness and newsletter signups"
    }
    res = test_client.post("/api/company-profile", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["profile"]["company_name"] == "NovaSphere AI"
    assert data["profile"]["website"] == "https://novasphere.io"

    # Verify retrieval
    get_res = test_client.get("/api/company-profile")
    assert get_res.status_code == 200
    get_data = get_res.get_json()
    assert get_data["is_configured"] is True
    assert get_data["profile"]["company_name"] == "NovaSphere AI"


# ---------------------------------------------------------------------------
# Competitor CRUD Tests
# ---------------------------------------------------------------------------
def test_competitor_crud_lifecycle(test_client):
    """Tests full add, view, update, and delete lifecycle for competitors."""
    # 1. Initial list should be empty
    res = test_client.get("/api/competitors")
    assert res.status_code == 200
    assert res.get_json()["count"] == 0

    # 2. Add competitor with invalid URL fails
    bad_res = test_client.post("/api/competitors", json={
        "name": "BadComp",
        "website_url": "not_a_valid_url"
    })
    assert bad_res.status_code == 400

    # 3. Add valid competitor
    add_res = test_client.post("/api/competitors", json={
        "name": "CloudPulse Systems",
        "website_url": "https://cloudpulse.io",
        "notes": "Primary competitor in cloud monitoring"
    })
    assert add_res.status_code == 201
    comp = add_res.get_json()["competitor"]
    comp_id = comp["id"]
    assert comp["name"] == "CloudPulse Systems"
    assert comp["website_url"] == "https://cloudpulse.io"

    # 4. Get single competitor
    single_res = test_client.get(f"/api/competitors/{comp_id}")
    assert single_res.status_code == 200
    assert single_res.get_json()["competitor"]["name"] == "CloudPulse Systems"

    # 5. Update competitor
    update_res = test_client.put(f"/api/competitors/{comp_id}", json={
        "name": "CloudPulse Analytics",
        "website_url": "https://cloudpulse.io",
        "notes": "Updated keyword notes"
    })
    assert update_res.status_code == 200
    assert update_res.get_json()["competitor"]["name"] == "CloudPulse Analytics"

    # 6. Delete competitor
    del_res = test_client.delete(f"/api/competitors/{comp_id}")
    assert del_res.status_code == 200

    # 7. Confirm deleted
    confirm_res = test_client.get(f"/api/competitors/{comp_id}")
    assert confirm_res.status_code == 404


# ---------------------------------------------------------------------------
# Blog Draft Persistence Tests
# ---------------------------------------------------------------------------
def test_draft_persistence_and_metrics(test_client):
    """Verifies that blog drafts are persisted with word count in SQLite."""
    # Initially no draft
    init_res = test_client.get("/api/draft")
    assert init_res.status_code == 200
    assert init_res.get_json()["has_draft"] is False

    # Save a draft
    content = "## Introduction\n\nThis is a test article with nine distinct words."
    save_res = test_client.post("/api/draft", json={
        "title": "Scaling Multi-Cloud Architectures",
        "content_markdown": content,
        "status": "draft"
    })
    assert save_res.status_code == 200
    draft = save_res.get_json()["draft"]
    assert draft["title"] == "Scaling Multi-Cloud Architectures"
    assert draft["word_count"] > 0
    assert draft["status"] == "draft"

    # Update draft to approved
    approve_res = test_client.post("/api/draft", json={
        "id": draft["id"],
        "title": "Scaling Multi-Cloud Architectures",
        "content_markdown": content,
        "status": "approved"
    })
    assert approve_res.status_code == 200
    assert approve_res.get_json()["draft"]["status"] == "approved"

    # Retrieve latest draft
    fetch_res = test_client.get("/api/draft")
    assert fetch_res.status_code == 200
    assert fetch_res.get_json()["draft"]["status"] == "approved"


# ---------------------------------------------------------------------------
# Chat Session & Message Persistence Tests
# ---------------------------------------------------------------------------
def test_chat_session_message_history(test_client):
    """Verifies chat message persistence and honest Phase 2 demo responses."""
    # Post a message to default session
    res = test_client.post("/api/chat/sessions/default/messages", json={
        "message": "Analyze competitor keywords for Kubernetes deployment"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["is_demo"] is True
    assert "user_message" in data
    assert "assistant_message" in data
    assert "Phase 2 Backend Stored" in data["reply"] or "synthesized" in data["reply"].lower()

    # Verify messages are in session history
    hist_res = test_client.get("/api/chat/sessions/default/messages")
    assert hist_res.status_code == 200
    hist = hist_res.get_json()
    assert hist["count"] >= 2  # user message and assistant message
    roles = [m["role"] for m in hist["messages"]]
    assert "user" in roles
    assert "assistant" in roles
