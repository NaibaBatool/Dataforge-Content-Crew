"""Phase 6 Comprehensive Test Suite - DataForge Content Crew
Blogs Shared Shell, Topic Normalization, Regeneration Repair & Session Isolation
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
    save_draft,
    get_draft,
    list_drafts,
    list_blogs,
    add_message,
    get_session_messages,
    list_sessions,
    get_or_create_session
)
import services.gemini_service as gemini_service
from agents.supervisor_agent import normalize_topic, run_supervisor
from agents.generation_agent import run_generation_agent
from graph.workflow import (
    start_workflow,
    get_workflow_state,
    regenerate_workflow_draft,
    approve_workflow_draft
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


def test_topic_normalization_various_phrasings():
    """Verifies that command phrases and conversational boilerplate are cleanly stripped."""
    test_cases = [
        ("write blog on agentic AI", "agentic AI"),
        ("please can you write an article about Kubernetes security in 1000 words", "Kubernetes security"),
        ("draft a guide on LLM observability", "LLM observability"),
        ("explain multi-agent orchestration", "multi-agent orchestration"),
        ("tell me about prompt caching", "prompt caching"),
        ("create a post on data observability for enterprise", "data observability"),
        ("Autonomous Multi-Agent Architectures", "Autonomous Multi-Agent Architectures")
    ]
    for prompt, expected in test_cases:
        normalized = normalize_topic(prompt)
        assert normalized.lower() == expected.lower(), f"Failed for '{prompt}': got '{normalized}'"


def test_supervisor_uses_normalized_topic():
    """Verifies that supervisor agent extracts clean subject and generates editorial title."""
    gemini_service.set_mock_responder(lambda prompt, sys, jm: {
        "topic": "Agentic AI",
        "working_title": "Demystifying Agentic AI: Autonomous Design Patterns",
        "target_angle": "Architectural breakdown for enterprise teams",
        "steps": ["research", "analysis", "generation", "review"]
    })

    plan = run_supervisor("write blog on agentic AI", {"company_name": "DataForge Labs", "industry": "AI"})
    assert plan["topic"] == "Agentic AI"
    assert "write blog" not in plan["topic"].lower()
    assert "working_title" in plan
    assert "Agentic AI" in plan["working_title"]


def test_generation_agent_reader_first_structure():
    """Verifies that generation agent provides structured, reader-first content."""
    draft = run_generation_agent(
        topic="write blog on agentic AI",
        analysis_report={"summary": "Multi-agent systems require state coordination", "sources": []},
        company_profile={"company_name": "DataForge", "tone": "Technical", "target_audience": "Engineers"}
    )

    assert "write blog on" not in draft["title"].lower()
    assert len(draft["title"]) > 10
    assert "##" in draft["content_markdown"]
    assert draft["word_count"] > 100


def test_blogs_page_uses_shared_workspace_shell(isolated_client):
    """Verifies that /blogs renders using the same shared application shell as workspace."""
    res = isolated_client.get("/blogs")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Shared shell verification: ws-header, ws-logo, ws-main, ws-sidebar
    assert 'class="ws-header"' in html
    assert 'class="ws-logo"' in html
    assert 'class="ws-main"' in html
    assert 'class="ws-sidebar"' in html
    assert 'Brand Context' in html

    # Empty state exact wording verification
    assert 'No articles published yet' in html
    assert 'Your published articles will appear here. Start by researching a topic and creating your first blog.' in html
    assert 'Create a Blog' in html


def test_blogs_page_populated_grid(isolated_client):
    """Verifies that /api/blogs returns published articles for the card grid."""
    save_draft(
        title="Architecting Agentic Systems",
        content_markdown="## Core Foundations\nAutonomous feedback loops require strict state isolation.",
        status="published",
        company_name="DataForge Labs"
    )

    res = isolated_client.get("/api/blogs?status=published")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["blogs"]) == 1
    blog = data["blogs"][0]
    assert blog["title"] == "Architecting Agentic Systems"
    assert blog["status"] == "published"
    assert blog["company_name"] == "DataForge Labs"


def test_regenerate_workflow_draft_increments_version_and_clears_approval(isolated_client):
    """Verifies that regenerating a draft increments version number and resets approval."""
    session_id = "sess_regen_test_1"
    
    # 1. Start initial workflow
    final_state = start_workflow(
        session_id=session_id,
        user_request="Autonomous Agent Evaluation",
        company_profile={"company_name": "DataForge", "industry": "Software"},
        competitors=[]
    )
    initial_draft = final_state["draft"]
    initial_version = initial_draft.get("version", 1)
    assert initial_version == 1

    # 2. Approve draft version 1
    approve_res = approve_workflow_draft(session_id)
    assert approve_res["status"] == "approved"
    assert approve_res["version"] == 1

    # 3. Regenerate draft
    regen_res = isolated_client.post(f"/api/workflow/{session_id}/regenerate")
    assert regen_res.status_code == 200
    regen_data = regen_res.get_json()
    new_draft = regen_data["workflow"]["draft"]

    assert new_draft["version"] == 2
    # Approval must be invalidated
    approval_state = regen_data["workflow"]["approval_state"]
    assert approval_state["is_approved"] is False
    assert approval_state["approved_version"] is None

    # Prior draft preserved in SQLite
    all_drafts = list_drafts()
    assert len(all_drafts) >= 2


def test_session_isolation(isolated_client):
    """Verifies that chat messages are partitioned strictly by session_id."""
    session_a = "session_alpha"
    session_b = "session_beta"

    # Add message to Session A
    res_a = isolated_client.post(
        f"/api/chat/sessions/{session_a}/messages",
        json={"message": "Research vector embeddings", "async": False}
    )
    assert res_a.status_code == 200

    # Add message to Session B
    res_b = isolated_client.post(
        f"/api/chat/sessions/{session_b}/messages",
        json={"message": "Explain Kubernetes operators", "async": False}
    )
    assert res_b.status_code == 200

    # Retrieve messages for each session
    msgs_a = isolated_client.get(f"/api/chat/sessions/{session_a}/messages").get_json()["messages"]
    msgs_b = isolated_client.get(f"/api/chat/sessions/{session_b}/messages").get_json()["messages"]

    # Verify session separation
    a_contents = [m["content"] for m in msgs_a]
    b_contents = [m["content"] for m in msgs_b]

    assert any("vector embeddings" in c for c in a_contents)
    assert not any("Kubernetes operators" in c for c in a_contents)

    assert any("Kubernetes operators" in c for c in b_contents)
    assert not any("vector embeddings" in c for c in b_contents)


def test_workspace_page_contains_new_chat_and_history(isolated_client):
    """Verifies that /workspace renders New Chat, History button, and the clean welcome screen."""
    res = isolated_client.get("/workspace")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    assert 'id="btn-new-chat"' in html
    assert 'id="btn-chat-history"' in html
    assert 'id="chat-history-modal"' in html
    assert 'What would you like to write about?' in html
    assert 'e.g. Explain how agentic AI is changing customer support' in html
