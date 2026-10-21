# DataForge Content Crew

**DataForge Content Crew** is an intelligent content creation workspace for modern B2B editorial teams. It orchestrates company onboarding, competitor intelligence tracking, Google Gemini API & LangGraph multi-agent workflows, and blog draft management.

---

## 1. Supported Environment & Prerequisites

- **Python Version:** Python 3.10 to Python 3.15+ (tested on Windows 10/11)
- **Database:** SQLite (built into Python, zero external database setup needed)
- **Package Manager:** `pip`

---

## 2. Quick Setup & Virtual Environment (Windows)

Open PowerShell in the project directory (`Content_Crew`):

```powershell
# 1. Create a Python virtual environment
python -m venv .venv

# 2. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Configuration (`.env`)

Copy the environment template:
```powershell
Copy-Item .env.example .env
```

Open `.env` in your text editor:
```env
# Server Configuration
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000
DATABASE_PATH=content_crew.db

# Google Gemini API Settings (Optional for automated tests, required for live AI)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Optional Web Search Provider
TAVILY_API_KEY=
```

### Enabling Live Integrations

| Integration | Required Env Var | How to Obtain Credentials | Status If Unset |
|---|---|---|---|
| **Google Gemini API** | `GEMINI_API_KEY` | Visit [Google AI Studio](https://aistudio.google.com/), click **Get API key**, and paste your key. | Operates in deterministic fallback mode with full workflow state transitions. |
| **Web Search** | `TAVILY_API_KEY` | Register at [Tavily](https://tavily.com/) for a search key. | Truthfully reports search is unconfigured; does not fabricate search results or citations. |

> [!NOTE]
> Automated unit and integration tests do **not** require live API keys. All provider tests run offline using mocks and deterministic evaluation.

---

## 4. Starting the Application

Run the Flask server:
```powershell
python app.py
```

The application automatically starts at:
👉 **`http://127.0.0.1:5000`**

*(Note: If port 5000 is occupied by another local service on your machine, the server automatically detects the collision and safely binds to `http://127.0.0.1:5001`).*

---

## 5. Running Automated Tests

Run the complete 42-test automated verification suite:
```powershell
python -m pytest -v
```

This verifies:
- All pages and UI static assets
- Company onboarding validation & SQLite persistence
- Competitor management CRUD
- LangGraph state transitions (`planning -> research -> analysis -> generation -> review`)
- Revision version bumping and approval invalidation
- Server-side publishing security safeguards (unapproved publishing rejected with HTTP 403)
- Gemini error handling (missing keys, invalid keys, rate limits, timeouts, empty responses)
- Idempotent demo publishing and duplicate prevention

---

## 6. Available Application Routes & API Endpoints

### User Interface Routes
- `GET /`: Product landing page featuring value proposition, feature breakdown, and workflow.
- `GET /workspace`: Unified 3-column editorial workspace (Brand Context, Crew Chat, and Blog Editor).
- `GET /onboarding`: Dedicated company profile configuration form.

### REST API Endpoints

| Route | Method | Purpose |
|---|---|---|
| `/api/health` | `GET` | Health check reporting service status, SQLite connectivity, and Gemini status. |
| `/api/gemini/status` | `GET` | Tests Gemini connectivity without leaking API secrets. |
| `/api/company-profile` | `GET`, `POST` | Retrieves or saves the company profile in SQLite. |
| `/api/competitors` | `GET`, `POST` | Lists or adds tracked competitors. |
| `/api/competitors/<id>` | `GET`, `PUT`, `DELETE` | Retrieves, updates, or deletes a competitor. |
| `/api/draft` | `GET`, `POST` | Loads or saves blog draft content (manual edits invalidate prior approvals). |
| `/api/workflow/start` | `POST` | Triggers the LangGraph agent workflow for a given user prompt. |
| `/api/workflow/<session_id>/status` | `GET` | Polls progress, findings, draft, and approval status for a session. |
| `/api/workflow/<session_id>/revise` | `POST` | Submits revision notes, increments version, and invalidates previous approvals. |
| `/api/workflow/<session_id>/approve` | `POST` | Explicitly approves the exact draft version and signs an approval token. |
| `/api/workflow/<session_id>/publish` | `POST` | Publishes draft to local demo store after server-side version verification. |
| `/api/chat/sessions/<id>/messages` | `GET`, `POST` | Retrieves or appends messages in persistent SQLite chat history. |

---

## 7. Approval & Publishing Safety Architecture

DataForge Content Crew enforces publishing safety on the **backend**, not just via frontend disabled buttons:

1. **Version-Locked Human Approval**:
   - The workflow pauses at `review_pending`.
   - Approval generates a cryptographically signed approval token bound strictly to the active draft version (`version 1`).
2. **Revision Invalidation**:
   - Requesting a revision (`POST /api/workflow/<session_id>/revise`) generates a new draft, increments the version (`version 2`), and resets `approval_state["is_approved"] = False`.
   - Outdated approval tokens cannot authorize newer draft versions.
3. **Manual Edit Protection**:
   - Direct edits saved via `POST /api/draft` automatically invalidate existing workflow approvals.
4. **Publishing Protection**:
   - Direct requests to `POST /api/workflow/<session_id>/publish` without version-matched approval are rejected with **HTTP 403 Forbidden**.
5. **Idempotent Demo Store**:
   - Repeated publishing calls return confirmation without creating duplicate database records.
   - The system clearly informs the user that content is saved to the local demo database, not a public CMS.

---

## 8. Experiments Jupyter Notebook

A Jupyter notebook is provided in [`notebooks/gemini_agent_experiments.ipynb`](file:///c:/Users/HP/Documents/AI%20Projects/Content_Crew/notebooks/gemini_agent_experiments.ipynb) to experiment with direct Gemini API calls and structured JSON generation:

```powershell
jupyter notebook notebooks/gemini_agent_experiments.ipynb
```

---

## 9. Troubleshooting & FAQ

### Port Already in Use
- **Issue:** Flask reports `Address already in use` on port 5000.
- **Solution:** The application includes an automatic port fallback. If port 5000 is occupied, it automatically starts on port 5001. You can also specify a custom port by setting `$env:PORT=5002; python app.py`.

### Gemini API Key Errors
- **Issue:** `/api/gemini/status` reports unconfigured or invalid key.
- **Solution:** Verify that your key is correctly pasted in `.env` as `GEMINI_API_KEY=...` with no surrounding quotation marks or spaces. Ensure the key was created in [Google AI Studio](https://aistudio.google.com/).

### SQLite Database Locks
- **Issue:** `sqlite3.OperationalError: database is locked`.
- **Solution:** `db.py` enables SQLite WAL mode (`PRAGMA journal_mode = WAL;`) by default, allowing concurrent readers and writers without lock contention.
