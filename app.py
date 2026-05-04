from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import pandas as pd
import os
import math

from core.agent_runner import AgentRunner

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Intelligence Dashboard")

# Initialize the background agent
agent = AgentRunner()

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/api/status")
async def get_status():
    return await agent.get_status()

@app.post("/api/start")
async def start_agent():
    await agent.start()
    return {"message": "Agent started successfully"}

@app.post("/api/stop")
async def stop_agent():
    await agent.stop()
    return {"message": "Agent stopped successfully"}

@app.get("/api/news")
async def get_news():
    file_path = "ai_intelligence_report.xlsx"
    if not os.path.exists(file_path):
        return {"data": []}
        
    try:
        df = pd.read_excel(file_path)
        # Convert nan/float values to string or None for JSON serialization
        df = df.replace({float('nan'): None})
        records = df.to_dict(orient="records")
        return {"data": records}
    except Exception as e:
        return {"data": []}

if __name__ == "__main__":
    import uvicorn
    print("Starting AI Intelligence Dashboard...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
