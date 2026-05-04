"""
AI Intelligence Dashboard — FastAPI Application
------------------------------------------------
Serves the web frontend and exposes REST endpoints to control the
background agent and retrieve scraped news data.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import os

from core.agent_runner import AgentRunner

# Load environment variables from .env
load_dotenv()

app = FastAPI(title="AI Intelligence Dashboard")

# Initialise the background agent (singleton for the process lifetime)
agent = AgentRunner()

# Ensure the static directory exists before mounting
os.makedirs("static", exist_ok=True)

# Mount static assets — must come AFTER specific routes are defined,
# but FastAPI handles path priority correctly with mount.
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Routes ──────────────────────────────────────────────────────────────

@app.get("/")
async def read_index():
    """Serve the main dashboard HTML page."""
    index_path = os.path.join("static", "index.html")
    if not os.path.exists(index_path):
        return JSONResponse(
            {"error": "index.html not found in static/"}, status_code=404
        )
    return FileResponse(index_path)


@app.get("/api/status")
async def get_status():
    """Return current agent status and power-plug state."""
    return await agent.get_status()


@app.post("/api/start")
async def start_agent():
    """Start the background scraping agent."""
    await agent.start()
    return {"message": "Agent started successfully"}


@app.post("/api/stop")
async def stop_agent():
    """Stop the background scraping agent gracefully."""
    await agent.stop()
    return {"message": "Agent stopped successfully"}


@app.get("/api/news")
async def get_news():
    """Read the Excel report and return all rows as JSON."""
    file_path = "ai_intelligence_report.csv"
    if not os.path.exists(file_path):
        return {"data": []}

    try:
        df = pd.read_csv(file_path)
        # Replace NaN, Inf, -Inf, and NaT with None for JSON serialisation
        df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
        df = df.where(df.notna(), None)
        records = df.to_dict(orient="records")
        return {"data": records}
    except Exception as exc:
        print(f"[App] Error reading report: {exc}")
        return {"data": [], "error": str(exc)}


# ── Entry Point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("Starting AI Intelligence Dashboard on http://127.0.0.1:8000 ...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
