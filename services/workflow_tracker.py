"""DataForge Content Crew - Workflow Execution Tracker
Phase 5: Real-time Multi-Stage Workflow Tracking & Event Persistence
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from db import (
    create_workflow_run,
    update_workflow_run_status,
    record_workflow_event,
    get_workflow_run,
    get_latest_workflow_run,
    get_workflow_events
)

# Standardized 10 Stages of the Content Crew Pipeline
WORKFLOW_STAGES = [
    {
        "stage_id": "stage_1_understanding",
        "stage_number": 1,
        "label": "Understanding Request & Brand Context",
        "default_desc": "Analyzing editorial topic, target audience, brand voice, and content goals."
    },
    {
        "stage_id": "stage_2_planning",
        "stage_number": 2,
        "label": "Creating Content Execution Plan",
        "default_desc": "Supervisor agent determining editorial angles, structure, and required research."
    },
    {
        "stage_id": "stage_3_search",
        "stage_number": 3,
        "label": "Searching Google / Web Sources",
        "default_desc": "Searching the web for relevant articles and competitor information."
    },
    {
        "stage_id": "stage_4_sources",
        "stage_number": 4,
        "label": "Reviewing & Extracting Source Information",
        "default_desc": "Reviewing and extracting evidence, data points, and context from retrieved sources."
    },
    {
        "stage_id": "stage_5_competitors",
        "stage_number": 5,
        "label": "Comparing Relevant Competitors & Content",
        "default_desc": "Benchmarking tracked competitors to identify industry positioning and overlap."
    },
    {
        "stage_id": "stage_6_analysis",
        "stage_number": 6,
        "label": "Analyzing Search Intent & Content Gaps",
        "default_desc": "Synthesizing keyword relevance, user search intent, and unique differentiation angles."
    },
    {
        "stage_id": "stage_7_outline",
        "stage_number": 7,
        "label": "Preparing Article Outline",
        "default_desc": "Constructing structured semantic headings (H1, H2, H3), flow, and core arguments."
    },
    {
        "stage_id": "stage_8_generation",
        "stage_number": 8,
        "label": "Generating Blog Article",
        "default_desc": "Writing complete article with engaging intro, sections, practical examples, and conclusion."
    },
    {
        "stage_id": "stage_9_review",
        "stage_number": 9,
        "label": "Reviewing Structure, Claims & Citations",
        "default_desc": "Auditing headings, readability, word count, and citation linkage."
    },
    {
        "stage_id": "stage_10_draft_ready",
        "stage_number": 10,
        "label": "Preparing Final Draft for Editorial Review",
        "default_desc": "Saving version in library and loading interactive editor for review."
    }
]

# In-memory stage timers: (run_id, stage_id) -> start_timestamp
_stage_start_times: Dict[str, float] = {}


def initialize_workflow_run(session_id: str, user_request: str, run_id: Optional[str] = None) -> str:
    """Creates a new workflow run and initializes all 10 stages in Pending state."""
    if not run_id:
        timestamp_ms = int(time.time() * 1000)
        run_id = f"run_{session_id}_{timestamp_ms}"

    create_workflow_run(
        run_id=run_id,
        session_id=session_id,
        user_request=user_request,
        status="running"
    )

    now = datetime.now(timezone.utc).isoformat()
    for stage in WORKFLOW_STAGES:
        record_workflow_event(
            run_id=run_id,
            session_id=session_id,
            stage_id=stage["stage_id"],
            stage_number=stage["stage_number"],
            label=stage["label"],
            status="pending",
            description=stage["default_desc"],
            details_json="{}",
            started_at=None,
            completed_at=None,
            duration_ms=0
        )

    return run_id


def start_stage(run_id: str, stage_id: str, description: Optional[str] = None) -> None:
    """Marks a stage as In Progress."""
    key = f"{run_id}:{stage_id}"
    _stage_start_times[key] = time.time()
    now = datetime.now(timezone.utc).isoformat()

    stage_meta = next((s for s in WORKFLOW_STAGES if s["stage_id"] == stage_id), None)
    if not stage_meta:
        return

    record_workflow_event(
        run_id=run_id,
        session_id="default",
        stage_id=stage_id,
        stage_number=stage_meta["stage_number"],
        label=stage_meta["label"],
        status="in_progress",
        description=description or stage_meta["default_desc"],
        started_at=now
    )


def complete_stage(
    run_id: str,
    stage_id: str,
    description: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Marks a stage as Completed with elapsed duration and result details."""
    key = f"{run_id}:{stage_id}"
    start_time = _stage_start_times.pop(key, None)
    duration_ms = int((time.time() - start_time) * 1000) if start_time else 0
    now = datetime.now(timezone.utc).isoformat()

    stage_meta = next((s for s in WORKFLOW_STAGES if s["stage_id"] == stage_id), None)
    if not stage_meta:
        return

    details_str = json.dumps(details or {})

    record_workflow_event(
        run_id=run_id,
        session_id="default",
        stage_id=stage_id,
        stage_number=stage_meta["stage_number"],
        label=stage_meta["label"],
        status="completed",
        description=description or stage_meta["default_desc"],
        details_json=details_str,
        completed_at=now,
        duration_ms=duration_ms
    )


def fail_stage(
    run_id: str,
    stage_id: str,
    error_message: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Marks a stage as Failed with failure explanation."""
    key = f"{run_id}:{stage_id}"
    start_time = _stage_start_times.pop(key, None)
    duration_ms = int((time.time() - start_time) * 1000) if start_time else 0
    now = datetime.now(timezone.utc).isoformat()

    stage_meta = next((s for s in WORKFLOW_STAGES if s["stage_id"] == stage_id), None)
    label = stage_meta["label"] if stage_meta else stage_id
    stage_num = stage_meta["stage_number"] if stage_meta else 0

    record_workflow_event(
        run_id=run_id,
        session_id="default",
        stage_id=stage_id,
        stage_number=stage_num,
        label=label,
        status="failed",
        description=error_message,
        details_json=json.dumps(details or {"error": error_message}),
        completed_at=now,
        duration_ms=duration_ms
    )

    update_workflow_run_status(run_id, "failed", completed_at=now)


def finalize_workflow_run(run_id: str, status: str = "completed") -> None:
    """Marks the entire workflow run completed or failed."""
    now = datetime.now(timezone.utc).isoformat()
    update_workflow_run_status(run_id, status, completed_at=now)


def get_formatted_workflow_events(run_id: str) -> List[Dict[str, Any]]:
    """Retrieves and parses workflow events for client consumption."""
    raw_events = get_workflow_events(run_id)
    formatted = []
    for ev in raw_events:
        try:
            parsed_details = json.loads(ev.get("details_json") or "{}")
        except Exception:
            parsed_details = {}

        formatted.append({
            "stage_id": ev["stage_id"],
            "stage_number": ev["stage_number"],
            "label": ev["label"],
            "status": ev["status"],
            "description": ev["description"],
            "details": parsed_details,
            "started_at": ev.get("started_at"),
            "completed_at": ev.get("completed_at"),
            "duration_ms": ev.get("duration_ms", 0)
        })
    return formatted
