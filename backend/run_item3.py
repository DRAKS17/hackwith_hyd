import time
from fastapi.testclient import TestClient
from api import app, get_hindsight_client

client = TestClient(app)

def run_item3():
    contact_id = "c2" # Marcus Thorne
    print("=== ITEM 3: IDEMPOTENCY TABLE ===")
    print("Past Meetings | Run 1 Count | Run 2 Count")
    print("---|---|---")
    
    hs = get_hindsight_client()
    
    for meetings in [0, 2, 4]:
        counts = []
        for run in [1, 2]:
            client.post("/simulate", json={"contact_id": contact_id, "meeting_number": meetings})
            # the simulate endpoint now polls for up to 30s so we know it's done indexing
            res = hs.recall(query="topics", bank_id=contact_id)
            c = len(res.results) if hasattr(res, 'results') and res.results else 0
            counts.append(c)
        print(f"{meetings} | {counts[0]} | {counts[1]}")
        
    print("\n--- Testing recall after delete_bank ---")
    hs.delete_bank(bank_id=contact_id)
    time.sleep(2)
    res2 = hs.recall(query="topics", bank_id=contact_id)
    c2 = len(res2.results) if hasattr(res2, 'results') and res2.results else 0
    print(f"Count after delete: {c2}")

if __name__ == "__main__":
    run_item3()
