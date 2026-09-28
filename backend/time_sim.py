import time
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def time_simulate():
    print("Timing /simulate runs for contact c3...")
    for meetings in [0, 2, 4]:
        start = time.time()
        res = client.post("/simulate", json={"contact_id": "c3", "meeting_number": meetings})
        end = time.time()
        duration = end - start
        
        status = res.json().get("status")
        msg = res.json().get("message")
        print(f"Meetings: {meetings} | Time: {duration:.2f}s | Status: {status} | Msg: {msg}")

if __name__ == "__main__":
    time_simulate()
