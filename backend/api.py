import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from groq import Groq

from ingest import ingest_data
from hindsight_client import query_memory

app = FastAPI(title="Meeting Prep Agent API")

class IngestResponse(BaseModel):
    status: str
    summary: List[Dict[str, Any]]

class PrepRequest(BaseModel):
    contact_id: str
    context: Optional[str] = None

class PrepResponse(BaseModel):
    briefing: Dict[str, Any]

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
    """
    contact_id = req.contact_id
    context = req.context or ""
    
    # 1. Pull relevant past memories
    query = "Summarize all past meetings, specifically detailing topics discussed, unresolved promises, objections raised, and any personal details."
    
    try:
        memory_result = query_memory(contact_id, query)
        memory_text = str(memory_result)
        
        # Checking if Hindsight effectively returned no memories
        if not memory_text or "no memories" in memory_text.lower() or "don't know" in memory_text.lower() or memory_text.strip() == "{}":
            memory_text = ""
    except Exception:
        # If the bank doesn't exist yet or another error occurs during recall
        memory_text = ""

    # 3. Handle the case where a contact has no memory yet
    if not memory_text or len(memory_text) < 15:
        return PrepResponse(briefing={
            "What you discussed last time": "No past meetings on record.",
            "Promises you haven't followed up on": "None.",
            "Concerns to address": "None.",
            "Personal touch to mention": "This is your first meeting. Focus on building rapport."
        })
        
    # 2. Pass to LLM to generate structured briefing
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
    
    # 4. Add basic error handling for LLM function-calling failures
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
            
            # Verify structure
            expected_keys = [
                "What you discussed last time",
                "Promises you haven't followed up on",
                "Concerns to address",
                "Personal touch to mention"
            ]
            if not all(k in briefing for k in expected_keys):
                raise ValueError("Missing expected keys in JSON")
                
            return PrepResponse(briefing=briefing)
            
        except Exception as e:
            if attempt == 1:
                # Fall back to a plain-text response
                try:
                    fallback_response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a helpful meeting prep assistant."},
                            {"role": "user", "content": prompt + "\nProvide the answer in plain text with clear headings instead of JSON."}
                        ]
                    )
                    return PrepResponse(briefing={
                        "Fallback Plain Text": fallback_response.choices[0].message.content
                    })
                except Exception as inner_e:
                    raise HTTPException(status_code=500, detail="LLM generation failed completely.")
            # If attempt == 0 fails, loop continues to attempt 1
            
# Run with: uvicorn api:app --reload
