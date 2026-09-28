import os
import time
from fastapi.testclient import TestClient
from api import app, get_hindsight_client

client = TestClient(app)

def test_edge_cases():
    print("=== TEST 1: IDEMPOTENCY ===")
    res1 = client.post("/simulate", json={"contact_id": "c1", "meeting_number": 3})
    time.sleep(3)
    hs = get_hindsight_client()
    r1 = hs.recall(query="topics", bank_id="c1")
    count1 = len(r1.results) if hasattr(r1, 'results') and r1.results else 0
    print(f"Run 1 count: {count1}")
    
    res2 = client.post("/simulate", json={"contact_id": "c1", "meeting_number": 3})
    time.sleep(3)
    r2 = hs.recall(query="topics", bank_id="c1")
    count2 = len(r2.results) if hasattr(r2, 'results') and r2.results else 0
    print(f"Run 2 count: {count2}")
    
    print("\n=== TEST 2: INVALID GROQ API KEY ===")
    old_key = os.environ.get("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = "invalid_key_123"
    try:
        prep_res = client.post("/prep", json={"contact_id": "c1", "context": "test"})
        print(f"Status Code: {prep_res.status_code}")
        print("Briefing text:", prep_res.json()["briefing"])
    finally:
        os.environ["GROQ_API_KEY"] = old_key
        
    print("\n=== TEST 3: ZERO MEMORY ===")
    client.post("/simulate", json={"contact_id": "c2", "meeting_number": 1}) # No past meetings
    prep_res2 = client.post("/prep", json={"contact_id": "c2", "context": "test"})
    print(f"Status Code: {prep_res2.status_code}")
    print("Briefing:", prep_res2.json()["briefing"])

if __name__ == "__main__":
    test_edge_cases()
