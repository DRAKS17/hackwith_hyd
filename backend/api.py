from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from ingest import ingest_data

app = FastAPI(title="Meeting Prep Agent API")

class IngestResponse(BaseModel):
    status: str
    summary: List[Dict[str, Any]]

@app.post("/ingest", response_model=IngestResponse)
def trigger_ingestion(reset: bool = False):
    """
    Triggers the ingestion pipeline to read meetings.json and load into Hindsight.
    Optional 'reset' query parameter clears existing memory before re-ingesting.
    """
    try:
        summary = ingest_data(reset=reset)
        return IngestResponse(status="success", summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn api:app --reload
