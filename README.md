# AI Intelligence Hub (Web Dashboard)

A Python-based autonomous agent that aggregates, analyzes, and catalogs news on new AI technologies, model releases, and benchmarks. 

This project features a **Web Dashboard** built with FastAPI and Vanilla JS/CSS, serving a **Local-First Architecture** background agent that uses local LLM inference (Ollama).

## Architecture

1.  **FastAPI Backend (`app.py`)**: Serves the web interface and handles the background agent orchestration.
2.  **Agent Runner (`core/agent_runner.py`)**: Runs asynchronously in the background. It implements a 6-hour continuous loop that **only executes if the laptop is plugged into AC power**.
3.  **Scout (`core/scout.py`)**: Fetches raw links from RSS feeds and Serper.dev.
4.  **Librarian (`core/librarian.py`)**: Uses Firecrawl to scrape full content.
5.  **Analyst (`core/analyst.py`)**: The logic handler interfacing with local Ollama (`gemma4:e4b`).
6.  **Reporter (`core/reporter.py`)**: Saves structured JSON to `ai_intelligence_report.xlsx` and handles deduplication via Semantic Hashing.
7.  **Web Frontend (`static/`)**: A premium dark-mode glassmorphism dashboard to view data and control the agent.

## Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com/) installed and running locally.
- Free-tier API keys for [Serper.dev](https://serper.dev/) and [Firecrawl](https://firecrawl.dev/).

## Setup Instructions

1.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment Variables:**
    Open the `.env` file and add your API keys:
    ```env
    SERPER_API_KEY=your_serper_api_key
    FIRECRAWL_API_KEY=your_firecrawl_api_key
    OLLAMA_BASE_URL=http://localhost:11434
    ```

3.  **Pull the Local LLM:**
    ```bash
    ollama run gemma4:e4b
    ```

4.  **Start the Dashboard:**
    Start the FastAPI server using Uvicorn:
    ```bash
    uvicorn app:app --reload
    ```
    Then, open your browser and navigate to `http://localhost:8000`. You can start the background agent directly from the web interface!
