# DataForge Content Crew

**An AI-powered research and content creation workflow by DataForge.**

DataForge Content Crew is a web application designed to help turn a content idea into a researched, structured blog article. It combines AI-assisted planning, research, analysis, generation, and human review in one workspace.

## Overview

Creating quality content involves more than generating text. It requires understanding the topic, researching relevant information, organizing ideas, drafting an article, and reviewing the result.

DataForge Content Crew brings these steps into a single workflow to make content creation more organized and efficient.

## Key Features

- **AI-assisted planning:** Organizes the content task into a workflow.
- **Research and analysis:** Supports gathering and analyzing information relevant to the topic.
- **Blog generation:** Creates a structured first draft from the research workflow.
- **Review and revision:** Allows the user to review and improve generated content.
- **Content workspace:** Provides a web interface for working with generated articles.
- **Blogs page:** Provides an in-app place to view published demo articles.
- **Modular architecture:** Separates agents, workflow nodes, routes, services, and UI assets.

*Note: Research availability and results depend on the configured search provider and API access. In-app demo publishing does not mean that an article is automatically published to an external website.*

## Technology Stack

- Python
- Flask
- LangGraph
- Google Gemini API
- SQLite
- HTML, CSS, and JavaScript
- pytest

## Project Structure

```text
Content_Crew/
├── agents/        # AI agent logic
├── graph/         # Workflow and state
├── nodes/         # Workflow steps
├── routes/        # Application API routes
├── services/      # Supporting services
├── static/        # CSS, JavaScript, images
├── templates/     # HTML templates
├── tests/         # Automated tests
├── tools/         # Research and content tools
├── app.py         # Flask application entry point
├── db.py          # Database functionality
├── requirements.txt
├── .env.example
└── README.md
```

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/NaibaBatool/Dataforge-Content-Crew.git
cd Dataforge-Content-Crew
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file based on `.env.example`. Add your own API credentials using the exact variable names expected by the project.

**Never commit your `.env` file or expose API keys in source code, screenshots, or public repositories.**

### 5. Start the application

```bash
python app.py
```

Open the local URL printed by Flask in your terminal. If your configuration uses port 5001, the address will typically be `http://127.0.0.1:5001`.

## Testing

Run the automated tests with:

```bash
pytest
```

Some tests or application workflows may require environment variables or API access. Review the test setup before running integration tests.

## Current Scope and Limitations

- The application requires the appropriate API configuration to use AI functionality.
- Research quality and source availability depend on the configured provider.
- The local SQLite database is intended for the current local setup; a hosted deployment may require a persistent database service.
- In-app demo publishing is separate from publishing to an external blogging platform.
- Public deployment and external publishing integrations should be considered available only after they have been implemented and tested.

## Future Improvements

Potential improvements include hosted database support, production deployment, additional publishing integrations, and expanded automated testing.

## About DataForge

DataForge explores AI-powered automation and data-driven solutions to help businesses work more efficiently.

**Project:** DataForge Content Crew  
**Repository:** https://github.com/NaibaBatool/Dataforge-Content-Crew

*Built as a project to explore agentic AI workflows for research and content creation.*
