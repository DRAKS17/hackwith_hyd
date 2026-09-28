import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from groq import Groq

from ingest import ingest_data
from hindsight_service import query_memory, clear_memory, write_memory, get_hindsight_client

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
    model_used: str

class SimulateRequest(BaseModel):
    contact_id: str
    meeting_number: int  # 1, 3, or 5

def load_meetings_data():
    """
    Helper function to load the mock meeting data from JSON.
    """
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
                
    # Poll Vectorize Hindsight for indexing completion
    import time
    if ingested_count > 0:
        client_hs = get_hindsight_client()
        start_time = time.time()
        while time.time() - start_time < 30:
            try:
                res = client_hs.recall(query="*", bank_id=req.contact_id)
                if hasattr(res, 'results') and len(res.results) > 0:
                    break
            except Exception:
                pass
            time.sleep(1.5)
        else:
            return {"status": "warning", "message": f"Memory reset. Ingested {meetings_to_ingest} past meetings ({ingested_count} snippets). Warning: Memory indexing timed out after 30s."}
                
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
        memory_text = getattr(memory_result, 'text', str(memory_result))
        
        # Try to pull exact recall nodes if the client supports it for transparency
        try:
            client_hs = get_hindsight_client()
            recall_result = client_hs.recall(query=query, bank_id=contact_id)
            if hasattr(recall_result, 'results') and recall_result.results:
                count = len(recall_result.results)
                lines = [f"### Hindsight recalled {count} memories:"]
                for i, r in enumerate(recall_result.results, 1):
                    date_val = r.metadata.get('date', 'Unknown date') if getattr(r, 'metadata', None) else 'Unknown date'
                    type_val = r.metadata.get('type', 'fact') if getattr(r, 'metadata', None) else 'fact'
                    lines.append(f"{i}. **[{date_val} | {type_val}]** {r.text}")
                raw_memory_display = "\n\n".join(lines)
            else:
                raw_memory_display = "No specific memory nodes recalled."
        except Exception:
            raw_memory_display = memory_text
        
        if not memory_text or "no memories" in memory_text.lower() or "don't know" in memory_text.lower() or memory_text.strip() == "{}":
            memory_text = ""
            raw_memory_display = "No past memory history found."
    except Exception:
        pass

    if not memory_text or len(memory_text) < 15:
        return PrepResponse(
            briefing={
                "What you discussed last time": f"This is your first meeting with {contact_id}. No history yet.",
                "Open commitments": "No previous promises to track.",
                "Concerns to address": "Are there any immediate roadblocks preventing them from moving forward?",
                "Personal touch to mention": "Ask about their role, their company's current main focus, and how they like their current tech stack. The agent will start remembering after this meeting."
            },
            raw_memory=raw_memory_display,
            model_used="static-no-memory"
        )
        
    api_key = os.environ.get("GROQ_API_KEY", "dummy_key")  # Provide a fallback so it doesn't 500 immediately if env missing
        
    client = Groq(api_key=api_key)
    primary_model = "openai/gpt-oss-120b"
    fallback_model = "qwen/qwen3.8-27b"
    
    prompt = f"""
    You are an expert meeting prep assistant. Based on the following memories of past interactions 
    with contact {contact_id}, generate a highly specific, structured briefing for the upcoming meeting.
    
    Memories:
    {memory_text}
    
    Upcoming meeting context:
    {context}
    
    INSTRUCTIONS:
    - Summarize past topics discussed.
    - Open commitments: You MUST list ONLY promises that have NO later delivery recorded in memory. Do not invent delivery status. If the memory doesn't say it was delivered, assume it is open. If all promises are explicitly marked delivered, state "No open commitments."
    - Extract and name any personal details (e.g., hobbies, family, trips) to build rapport.
    
    Return ONLY a valid JSON object with EXACTLY these string keys:
    - "What you discussed last time"
    - "Open commitments"
    - "Concerns to address"
    - "Personal touch to mention"
    """
    
    for attempt in range(2):
        try:
            model = primary_model if attempt == 0 else fallback_model
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
                "Open commitments",
                "Concerns to address",
                "Personal touch to mention"
            ]
            if not all(k in briefing for k in expected_keys):
                raise ValueError("Missing expected keys in JSON")
                
            return PrepResponse(briefing=briefing, raw_memory=raw_memory_display, model_used=model)
            
        except Exception as e:
            if attempt == 1:
                try:
                    # Final fallback: plain text with the fallback model
                    fallback_response = client.chat.completions.create(
                        model=fallback_model,
                        messages=[
                            {"role": "system", "content": "You are a helpful meeting prep assistant."},
                            {"role": "user", "content": prompt + "\nProvide the answer in plain text with clear headings instead of JSON."}
                        ]
                    )
                    return PrepResponse(
                        briefing={"Fallback Plain Text": fallback_response.choices[0].message.content},
                        raw_memory=raw_memory_display,
                        model_used=f"{fallback_model}-plaintext"
                    )
                except Exception:
                    # NEVER a 500. Return a graceful fallback.
                    return PrepResponse(
                        briefing={"System Notice": "The LLM service (Groq) is currently unavailable. Please review the raw memories below instead."},
                        raw_memory=raw_memory_display,
                        model_used="system-fallback-error"
                    )
