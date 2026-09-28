import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from groq import Groq

from ingest import ingest_data
from hindsight_client import query_memory, clear_memory, write_memory, get_hindsight_client

app = FastAPI(title="Meeting Prep Agent API")

# Add CORS to allow frontend to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestResponse(BaseModel):
    status: str
    summary: List[Dict[str, Any]]

class PrepRequest(BaseModel):
    contact_id: str
    context: Optional[str] = None

class PrepResponse(BaseModel):
    briefing: Dict[str, Any]
    raw_memory: str

class SimulateRequest(BaseModel):
    contact_id: str
    meeting_number: int  # 1, 3, or 5

def load_meetings_data():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'meetings.json')
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            return json.load(f)
    return {"contacts": []}

@app.get("/contacts")
def get_contacts():
    """
    Returns the list of contacts for the frontend dropdown.
    """
    data = load_meetings_data()
    return [{"contact_id": c["contact_id"], "name": c["name"]} for c in data.get("contacts", [])]

@app.post("/simulate")
def simulate_timeline(req: SimulateRequest):
    """
    Clears memory and ingests a specific number of past meetings to simulate a point in time.
    """
    data = load_meetings_data()
    contact = next((c for c in data.get("contacts", []) if c["contact_id"] == req.contact_id), None)
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    clear_memory(req.contact_id)
    
    meetings_to_ingest = req.meeting_number - 1
    meetings = contact.get("meetings", [])
    meetings.sort(key=lambda x: x.get("date", ""))
    
    ingested_count = 0
    for meeting in meetings[:meetings_to_ingest]:
        date = meeting.get('date')
        for m_type in ['topics', 'objections', 'promises', 'personal_details']:
            content = meeting.get(m_type)
            if content:
                payload = {"contact_id": req.contact_id, "date": date, "type": m_type, "content": content}
                metadata = {"contact_id": req.contact_id, "date": date, "type": m_type}
                write_memory(req.contact_id, payload, metadata)
                ingested_count += 1
                
    return {"status": "success", "message": f"Memory reset. Ingested {meetings_to_ingest} past meetings ({ingested_count} snippets)."}

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

@app.post("/prep", response_model=PrepResponse)
def generate_prep(req: PrepRequest):
    """
    Generates a personalized meeting prep briefing based on past memories.
    Also returns the raw memory retrieved for transparency.
    """
    contact_id = req.contact_id
    context = req.context or ""
    
    query = "Summarize all past meetings, specifically detailing topics discussed, unresolved promises, objections raised, and any personal details."
    
    raw_memory_display = "No memory found."
    memory_text = ""
    
    try:
        memory_result = query_memory(contact_id, query)
        memory_text = str(memory_result)
        
        # Try to pull exact recall nodes if the client supports it for transparency, 
        # otherwise use the reflect text as our "raw memory" snippet
        try:
            client = get_hindsight_client()
            recall_result = client.recall(query=query, bank_id=contact_id)
            raw_memory_display = str(recall_result)
        except:
            raw_memory_display = memory_text
        
        if not memory_text or "no memories" in memory_text.lower() or "don't know" in memory_text.lower() or memory_text.strip() == "{}":
            memory_text = ""
            raw_memory_display = "No past memory history found."
    except Exception:
        pass

    if not memory_text or len(memory_text) < 15:
        return PrepResponse(
            briefing={
                "What you discussed last time": "No past meetings on record.",
                "Promises you haven't followed up on": "None.",
                "Concerns to address": "None.",
                "Personal touch to mention": "This is your first meeting. Focus on building rapport."
            },
            raw_memory=raw_memory_display
        )
        
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured in environment.")
        
    client = Groq(api_key=api_key)
    model = "openai/gpt-oss-120b"
    
    prompt = f"""
    You are an expert meeting prep assistant. Based on the following memories of past interactions 
    with contact {contact_id}, generate a structured briefing for the upcoming meeting.
    
    Memories:
    {memory_text}
    
    Upcoming meeting context:
    {context}
    
    Return ONLY a JSON object with EXACTLY the following string keys:
    - "What you discussed last time"
    - "Promises you haven't followed up on"
    - "Concerns to address"
    - "Personal touch to mention"
    """
    
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a structured data generator. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            briefing = json.loads(content)
            
            expected_keys = [
                "What you discussed last time",
                "Promises you haven't followed up on",
                "Concerns to address",
                "Personal touch to mention"
            ]
            if not all(k in briefing for k in expected_keys):
                raise ValueError("Missing expected keys in JSON")
                
            return PrepResponse(briefing=briefing, raw_memory=raw_memory_display)
            
        except Exception:
            if attempt == 1:
                try:
                    fallback_response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a helpful meeting prep assistant."},
                            {"role": "user", "content": prompt + "\nProvide the answer in plain text with clear headings instead of JSON."}
                        ]
                    )
                    return PrepResponse(
                        briefing={"Fallback Plain Text": fallback_response.choices[0].message.content},
                        raw_memory=raw_memory_display
                    )
                except Exception:
                    raise HTTPException(status_code=500, detail="LLM generation failed completely.")
