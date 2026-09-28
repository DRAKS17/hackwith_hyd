import json
import os
from fastapi.testclient import TestClient

from api import app
from hindsight_client import clear_memory, write_memory

client = TestClient(app)

def run_test():
    # Load synthetic meetings data
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'meetings.json')
    if not os.path.exists(data_path):
        print(f"Data file not found at {data_path}. Please run generate_data.py first.")
        return
        
    with open(data_path, 'r') as f:
        data = json.load(f)
        
    # Pick the first contact for the demo
    contact = data.get('contacts', [])[0]
    contact_id = contact['contact_id']
    meetings = contact.get('meetings', [])
    
    # Sort just to be safe
    meetings.sort(key=lambda x: x.get('date', ''))
    
    print(f"--- Starting Meeting Prep Agent Demo for {contact.get('name')} ({contact_id}) ---")
    
    # 1. Clear memory to start fresh
    print("\n[*] Resetting memory for a clean slate...")
    clear_memory(contact_id)
    
    # ---------------------------------------------------------
    # TEST 1: 1st Meeting (0 Past Meetings in Memory)
    # ---------------------------------------------------------
    print("\n==================================================")
    print("[Test 1] Generating prep for the 1st Meeting (No History)")
    print("==================================================")
    res1 = client.post("/prep", json={"contact_id": contact_id, "context": "Introductory discovery call."})
    print(json.dumps(res1.json(), indent=2))
    
    # Ingest the first 2 meetings
    if len(meetings) >= 2:
        print("\n[*] Simulating time passing... Ingesting 2 past meetings into Hindsight...")
        for meeting in meetings[:2]:
            date = meeting.get('date')
            for m_type in ['topics', 'objections', 'promises', 'personal_details']:
                content = meeting.get(m_type)
                if content:
                    payload = {"contact_id": contact_id, "date": date, "type": m_type, "content": content}
                    metadata = {"contact_id": contact_id, "date": date, "type": m_type}
                    write_memory(contact_id, payload, metadata)
                    
    # ---------------------------------------------------------
    # TEST 2: 3rd Meeting (2 Past Meetings in Memory)
    # ---------------------------------------------------------
    print("\n==================================================")
    print("[Test 2] Generating prep for the 3rd Meeting (2 Past Meetings)")
    print("==================================================")
    res2 = client.post("/prep", json={"contact_id": contact_id, "context": "Follow up on the product demo."})
    print(json.dumps(res2.json(), indent=2))
    
    # Ingest the next 2 meetings (total 4)
    if len(meetings) >= 4:
        print("\n[*] Simulating more time passing... Ingesting 2 more past meetings into Hindsight...")
        for meeting in meetings[2:4]:
            date = meeting.get('date')
            for m_type in ['topics', 'objections', 'promises', 'personal_details']:
                content = meeting.get(m_type)
                if content:
                    payload = {"contact_id": contact_id, "date": date, "type": m_type, "content": content}
                    metadata = {"contact_id": contact_id, "date": date, "type": m_type}
                    write_memory(contact_id, payload, metadata)
                    
    # ---------------------------------------------------------
    # TEST 3: 5th Meeting (4 Past Meetings in Memory)
    # ---------------------------------------------------------
    print("\n==================================================")
    print("[Test 3] Generating prep for the 5th Meeting (4 Past Meetings)")
    print("==================================================")
    res3 = client.post("/prep", json={"contact_id": contact_id, "context": "Pricing negotiation and trying to close the deal."})
    print(json.dumps(res3.json(), indent=2))

if __name__ == "__main__":
    run_test()
