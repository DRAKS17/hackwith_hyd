import os
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_fallback():
    print("=== Testing Primary Fallback ===")
    res = client.post("/prep", json={"contact_id": "c1", "context": "test"})
    print("Status:", res.status_code)
    print("Model Used:", res.json().get("model_used"))
    
    print("\n=== Testing Complete Fallback (Invalid API Key) ===")
    old_key = os.environ.get("GROQ_API_KEY")
    os.environ["GROQ_API_KEY"] = "invalid_key_123"
    try:
        res2 = client.post("/prep", json={"contact_id": "c1", "context": "test"})
        print("Status:", res2.status_code)
        print("Model Used:", res2.json().get("model_used"))
        print("Briefing:", res2.json().get("briefing"))
    finally:
        os.environ["GROQ_API_KEY"] = old_key

if __name__ == "__main__":
    test_fallback()
