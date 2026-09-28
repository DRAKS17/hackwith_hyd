import json
from fastapi.testclient import TestClient
from api import app
import time

client = TestClient(app)

def verify_item1():
    print("--- RAW JSON FOR CONTACT C1 ---")
    with open('../data/meetings.json') as f:
        data = json.load(f)
    c1 = next(c for c in data['contacts'] if c['contact_id'] == 'c2')
    print(json.dumps(c1, indent=2))
    
    print("\n--- EXTRACTED PROMISES & STATUS ---")
    all_promises = {} # promise text -> final status
    for m in c1['meetings']:
        # register new promises
        for p in m.get('promises', []):
            all_promises[p] = "unknown"
        # check follow ups
        for f in m.get('follow_ups', []):
            all_promises[f['promise']] = f['status']
            
    for p, s in all_promises.items():
        print(f"- '{p}' => {s}")
        
    print("\n--- RUNNING SIMULATE 4 & PREP ---")
    # run simulate 4
    res = client.post("/simulate", json={"contact_id": "c2", "meeting_number": 4})
    print("Simulate 4:", res.json())
    time.sleep(3) # allow ingestion to complete, polling will handle the rest in API but extra sleep helps tests
    
    # run prep
    res = client.post("/prep", json={"contact_id": "c2", "context": ""})
    print("\nPREP RESPONSE:")
    print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    verify_item1()
