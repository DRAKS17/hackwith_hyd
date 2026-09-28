import os, json
from fastapi.testclient import TestClient
from api import app, get_hindsight_client

client = TestClient(app)

def run_item2():
    # Insert a dummy memory so it passes the < 15 chars check
    hs = get_hindsight_client()
    hs.retain(content="dummy memory for fallback test so length is greater than 15", bank_id="c_fallback")
    import time
    time.sleep(3)
    
    print("=== TEST A: PRIMARY INVALID, FALLBACK VALID ===")
    res = client.post("/prep", json={"contact_id": "c_fallback", "context": "test"})
    print("Status:", res.status_code)
    print("Model Used:", res.json().get("model_used"))
    print("Briefing:", res.json().get("briefing"))
    
    print("\n=== TEST B: BOTH MODELS INVALID ===")
    old_key = os.environ.get("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = "invalid_key_123"
    try:
        res2 = client.post("/prep", json={"contact_id": "c_fallback", "context": "test"})
        print("Status:", res2.status_code)
        print("Model Used:", res2.json().get("model_used"))
        print("Briefing:", res2.json().get("briefing"))
    finally:
        os.environ["GROQ_API_KEY"] = old_key

if __name__ == "__main__":
    run_item2()
