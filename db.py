"""DataForge Content Crew - Database Operations & SQLite Persistence
Phase 2: Database Layer
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.environ.get("DATABASE_PATH", "content_crew.db")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a connection to SQLite database with Row factory and WAL mode."""
    target_path = db_path or os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes tables for company profile, competitors, chat sessions, and drafts."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Company Profile (Singleton id=1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                company_name TEXT NOT NULL,
                description TEXT NOT NULL,
                products_services TEXT NOT NULL,
                industry TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                usp TEXT NOT NULL,
                website TEXT NOT NULL,
                tone TEXT NOT NULL,
                content_goals TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # 2. Competitors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                website_url TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # 3. Chat Sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # 4. Chat Messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            );
        """)

        # 5. Draft Articles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content_markdown TEXT NOT NULL,
                word_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'published')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # Ensure schema migrations for drafts table (version, session_id, company_name, published_at)
        cursor.execute("PRAGMA table_info(drafts);")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        if "version" not in existing_cols:
            cursor.execute("ALTER TABLE drafts ADD COLUMN version INTEGER DEFAULT 1;")
        if "session_id" not in existing_cols:
            cursor.execute("ALTER TABLE drafts ADD COLUMN session_id TEXT DEFAULT 'default';")
        if "company_name" not in existing_cols:
            cursor.execute("ALTER TABLE drafts ADD COLUMN company_name TEXT DEFAULT '';")
        if "published_at" not in existing_cols:
            cursor.execute("ALTER TABLE drafts ADD COLUMN published_at TEXT;")

        # 6. Workflow Runs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                run_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                status TEXT NOT NULL,
                user_request TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
        """)

        # 7. Workflow Events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                stage_id TEXT NOT NULL,
                stage_number INTEGER NOT NULL,
                label TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT NOT NULL,
                details_json TEXT DEFAULT '{}',
                started_at TEXT,
                completed_at TEXT,
                duration_ms INTEGER DEFAULT 0,
                FOREIGN KEY (run_id) REFERENCES workflow_runs(run_id) ON DELETE CASCADE
            );
        """)

        # Ensure a default chat session exists
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT OR IGNORE INTO chat_sessions (id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?);
            """,
            ("default", "Primary Editorial Chat", now, now)
        )

        conn.commit()


# ---------------------------------------------------------------------------
# Company Profile CRUD
# ---------------------------------------------------------------------------
def get_company_profile(db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves the configured company profile or returns None if not set."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM company_profile WHERE id = 1;")
        row = cursor.fetchone()
        return dict(row) if row else None


def save_company_profile(data: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """Upserts the singleton company profile."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO company_profile (
                id, company_name, description, products_services,
                industry, target_audience, usp, website, tone, content_goals,
                created_at, updated_at
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                company_name = excluded.company_name,
                description = excluded.description,
                products_services = excluded.products_services,
                industry = excluded.industry,
                target_audience = excluded.target_audience,
                usp = excluded.usp,
                website = excluded.website,
                tone = excluded.tone,
                content_goals = excluded.content_goals,
                updated_at = excluded.updated_at;
        """, (
            data["company_name"],
            data["description"],
            data["products_services"],
            data["industry"],
            data["target_audience"],
            data["usp"],
            data["website"],
            data["tone"],
            data["content_goals"],
            now,
            now
        ))
        conn.commit()
    profile = get_company_profile(db_path)
    assert profile is not None
    return profile


# ---------------------------------------------------------------------------
# Competitors CRUD
# ---------------------------------------------------------------------------
def list_competitors(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists all tracked competitors ordered by creation time descending."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM competitors ORDER BY id DESC;")
        return [dict(row) for row in cursor.fetchall()]


def get_competitor(competitor_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches a specific competitor by ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM competitors WHERE id = ?;", (competitor_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_competitor(name: str, website_url: str, notes: str = "", db_path: Optional[str] = None) -> Dict[str, Any]:
    """Adds a new competitor."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO competitors (name, website_url, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?);
        """, (name, website_url, notes, now, now))
        new_id = cursor.lastrowid
        conn.commit()
    return get_competitor(new_id, db_path)  # type: ignore


def update_competitor(competitor_id: int, name: str, website_url: str, notes: str = "", db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Updates an existing competitor."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE competitors
            SET name = ?, website_url = ?, notes = ?, updated_at = ?
            WHERE id = ?;
        """, (name, website_url, notes, now, competitor_id))
        if cursor.rowcount == 0:
            return None
        conn.commit()
    return get_competitor(competitor_id, db_path)


def delete_competitor(competitor_id: int, db_path: Optional[str] = None) -> bool:
    """Removes a competitor by ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM competitors WHERE id = ?;", (competitor_id,))
        conn.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Chat Sessions & Messages CRUD
# ---------------------------------------------------------------------------
def get_or_create_session(session_id: str = "default", title: str = "Primary Editorial Chat", db_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves an existing session or creates it."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_sessions WHERE id = ?;", (session_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?);",
                (session_id, title, now, now)
            )
            conn.commit()
            cursor.execute("SELECT * FROM chat_sessions WHERE id = ?;", (session_id,))
            row = cursor.fetchone()
        return dict(row)


def list_sessions(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all chat sessions."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_sessions ORDER BY updated_at DESC;")
        return [dict(row) for row in cursor.fetchall()]


def get_session_messages(session_id: str = "default", limit: int = 50, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns chronologically ordered messages for a given session."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            LIMIT ?;
            """,
            (session_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]


def add_message(session_id: str, role: str, content: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Appends a new message to the session."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Verify session exists
        cursor.execute("SELECT id FROM chat_sessions WHERE id = ?;", (session_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?);",
                (session_id, "Editorial Session", now, now)
            )

        cursor.execute("""
            INSERT INTO chat_messages (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?);
        """, (session_id, role, content, now))
        msg_id = cursor.lastrowid

        # Update session timestamp
        cursor.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?;", (now, session_id))
        conn.commit()

        cursor.execute("SELECT * FROM chat_messages WHERE id = ?;", (msg_id,))
        return dict(cursor.fetchone())


# ---------------------------------------------------------------------------
# Draft Articles CRUD
# ---------------------------------------------------------------------------
def get_latest_draft(db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Gets the most recently updated draft."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drafts ORDER BY updated_at DESC LIMIT 1;")
        row = cursor.fetchone()
        return dict(row) if row else None


def list_drafts(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists all drafts stored in the SQLite library ordered by updated_at descending."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, word_count, status, version, session_id, company_name, published_at, created_at, updated_at
            FROM drafts
            ORDER BY updated_at DESC;
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def list_blogs(
    status_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lists blog articles filtered by status or search keyword ordered by latest update."""
    query = "SELECT id, title, content_markdown, word_count, status, version, session_id, company_name, published_at, created_at, updated_at FROM drafts WHERE 1=1"
    params: List[Any] = []

    if status_filter and status_filter.lower() != "all":
        query += " AND status = ?"
        params.append(status_filter.lower())

    if search_query and search_query.strip():
        query += " AND (title LIKE ? OR content_markdown LIKE ?)"
        like_term = f"%{search_query.strip()}%"
        params.extend([like_term, like_term])

    query += " ORDER BY updated_at DESC;"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        return rows


def get_draft(draft_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Gets a specific draft by ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drafts WHERE id = ?;", (draft_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def save_draft(
    title: str,
    content_markdown: str,
    status: str = "draft",
    draft_id: Optional[int] = None,
    version: int = 1,
    session_id: str = "default",
    company_name: str = "",
    published_at: Optional[str] = None,
    create_new_row: bool = False,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a new draft or updates an existing draft."""
    now = datetime.now(timezone.utc).isoformat()
    # Compute word count
    clean_text = " ".join(content_markdown.split())
    word_count = len(clean_text.split()) if clean_text else 0

    if status == "published" and not published_at:
        published_at = now

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if create_new_row:
            # Explicitly create a new draft version record
            cursor.execute("""
                INSERT INTO drafts (
                    title, content_markdown, word_count, status,
                    version, session_id, company_name, published_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (title, content_markdown, word_count, status, version, session_id, company_name, published_at, now, now))
            target_id = cursor.lastrowid
        elif draft_id:
            cursor.execute("""
                UPDATE drafts
                SET title = ?, content_markdown = ?, word_count = ?, status = ?,
                    version = COALESCE(?, version),
                    session_id = COALESCE(?, session_id),
                    company_name = COALESCE(?, company_name),
                    published_at = COALESCE(?, published_at),
                    updated_at = ?
                WHERE id = ?;
            """, (title, content_markdown, word_count, status, version, session_id, company_name, published_at, now, draft_id))
            target_id = draft_id
        else:
            # Check if there is already an existing draft to update or insert new
            cursor.execute("SELECT id, version FROM drafts ORDER BY id DESC LIMIT 1;")
            existing = cursor.fetchone()
            if existing:
                target_id = existing["id"]
                target_version = version or existing["version"] or 1
                cursor.execute("""
                    UPDATE drafts
                    SET title = ?, content_markdown = ?, word_count = ?, status = ?,
                        version = ?, session_id = ?, company_name = ?, published_at = ?,
                        updated_at = ?
                    WHERE id = ?;
                """, (title, content_markdown, word_count, status, target_version, session_id, company_name, published_at, now, target_id))
            else:
                cursor.execute("""
                    INSERT INTO drafts (
                        title, content_markdown, word_count, status,
                        version, session_id, company_name, published_at,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (title, content_markdown, word_count, status, version, session_id, company_name, published_at, now, now))
                target_id = cursor.lastrowid
        conn.commit()

    saved = get_draft(target_id, db_path)
    assert saved is not None
    return saved


# ---------------------------------------------------------------------------
# Workflow Runs & Events Persistence
# ---------------------------------------------------------------------------
def create_workflow_run(
    run_id: str,
    session_id: str,
    user_request: str,
    status: str = "running",
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Persists a new workflow run record."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO workflow_runs (run_id, session_id, status, user_request, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, NULL)
            ON CONFLICT(run_id) DO UPDATE SET
                status = excluded.status,
                user_request = excluded.user_request;
        """, (run_id, session_id, status, user_request, now))
        conn.commit()
    run = get_workflow_run(run_id, db_path)
    assert run is not None
    return run


def update_workflow_run_status(
    run_id: str,
    status: str,
    completed_at: Optional[str] = None,
    db_path: Optional[str] = None
) -> None:
    """Updates status and completion timestamp for a run."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if completed_at:
            cursor.execute(
                "UPDATE workflow_runs SET status = ?, completed_at = ? WHERE run_id = ?;",
                (status, completed_at, run_id)
            )
        else:
            cursor.execute(
                "UPDATE workflow_runs SET status = ? WHERE run_id = ?;",
                (status, run_id)
            )
        conn.commit()


def record_workflow_event(
    run_id: str,
    session_id: str,
    stage_id: str,
    stage_number: int,
    label: str,
    status: str,
    description: str,
    details_json: str = "{}",
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
    duration_ms: int = 0,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Appends or updates a stage execution event for a workflow run."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Check if this stage event already exists for this run
        cursor.execute(
            "SELECT id FROM workflow_events WHERE run_id = ? AND stage_id = ?;",
            (run_id, stage_id)
        )
        existing = cursor.fetchone()
        if existing:
            event_id = existing["id"]
            cursor.execute("""
                UPDATE workflow_events
                SET status = ?, description = ?, details_json = ?,
                    started_at = COALESCE(?, started_at),
                    completed_at = COALESCE(?, completed_at),
                    duration_ms = ?, label = ?, stage_number = ?
                WHERE id = ?;
            """, (status, description, details_json, started_at, completed_at, duration_ms, label, stage_number, event_id))
        else:
            cursor.execute("""
                INSERT INTO workflow_events (
                    run_id, session_id, stage_id, stage_number, label,
                    status, description, details_json, started_at, completed_at, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (run_id, session_id, stage_id, stage_number, label, status, description, details_json, started_at, completed_at, duration_ms))
            event_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM workflow_events WHERE id = ?;", (event_id,))
        return dict(cursor.fetchone())


def get_workflow_run(run_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Gets run record by ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflow_runs WHERE run_id = ?;", (run_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_latest_workflow_run(session_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Gets latest run record for a session."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM workflow_runs WHERE session_id = ? ORDER BY created_at DESC LIMIT 1;",
            (session_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_workflow_events(run_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns chronological stage events for a given run ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM workflow_events WHERE run_id = ? ORDER BY stage_number ASC, id ASC;",
            (run_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_session_workflow_events(session_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns workflow events for the latest run in a session."""
    latest_run = get_latest_workflow_run(session_id, db_path)
    if not latest_run:
        return []
    return get_workflow_events(latest_run["run_id"], db_path)
