"""Automated verification tests for DataForge Content Crew - Phase 1 Foundation
"""

import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_static_assets_exist():
    """Verify that all required static assets and templates are present."""
    required_files = [
        "static/images/dataforge_logo.jpeg",
        "static/css/base.css",
        "static/css/landing.css",
        "static/css/workspace.css",
        "static/js/api.js",
        "static/js/landing.js",
        "static/js/workspace.js",
        "templates/base.html",
        "templates/index.html",
        "templates/workspace.html",
    ]
    for rel_path in required_files:
        assert os.path.exists(rel_path), f"Missing required file: {rel_path}"


def test_landing_page(client):
    """Verify GET / landing page response and essential elements."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Required Hero heading
    assert "Research smarter." in html
    assert "Write with purpose." in html

    # Logo and product name
    assert "dataforge_logo.jpeg" in html
    assert "Content Crew" in html

    # Navigation & CTA links to workspace
    assert "/workspace" in html
    assert "Open Workspace" in html

    # Features & Workflow
    assert "Features" in html
    assert "How It Works" in html
    assert "Research" in html
    assert "Analyze" in html
    assert "Write" in html
    assert "Review" in html
    assert "Publish" in html

    # Health indicator pill present
    assert "landing-health-indicator" in html


def test_workspace_page(client):
    """Verify GET /workspace page response and visual components."""
    response = client.get("/workspace")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Header branding
    assert "dataforge_logo.jpeg" in html
    assert "DataForge Content Crew" in html

    # Sidebar sections
    assert "Company Profile" in html
    assert "Tracked Competitors" in html

    # Chat Panel
    assert "Crew Chat" in html
    assert "prompt-chip" in html
    assert "chat-messages" in html

    # Blog Preview / Editor with clean Empty State
    assert "No blog generated yet" in html
    assert "word-count" in html
    assert "read-time" in html
    assert "btn-toggle-edit" in html
    assert "Request Revision" in html
    assert "Approve" in html
    assert "Publish" in html


def test_api_health(client):
    """Verify GET /api/health endpoint returns healthy status JSON."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "DataForge Content Crew"
    assert data["phase"] in (1, 2, 3)
    assert "version" in data


def test_api_contracts(client):
    """Verify GET /api/contracts provides specifications for future phases."""
    response = client.get("/api/contracts")
    assert response.status_code == 200
    data = response.get_json()
    assert "contracts" in data
    assert "chat" in data["contracts"]
    assert "company_profile" in data["contracts"]
    assert "draft" in data["contracts"]


def test_demo_chat(client):
    """Verify POST /api/chat provides a functional demo response."""
    payload = {"message": "Hello Content Crew"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "reply" in data
    assert data["is_demo"] is True
