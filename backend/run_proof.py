import json
import time
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

contact_id = "c3"  # Maria Garcia

def run_proof():
    with open("../docs/sample_briefings.md", "w", encoding="utf-8") as f:
        f.write("# Sample Briefings (Learning Curve Proof)\n\n")
        
        for meeting_number in [1, 3, 5]:
            print(f"Simulating before meeting {meeting_number}...")
            
            # Simulate timeline
            sim_res = client.post("/simulate", json={"contact_id": contact_id, "meeting_number": meeting_number})
            assert sim_res.status_code == 200
            
            # Add a slight delay to ensure Hindsight indexes it
            time.sleep(3)
            
            # Generate prep
            prep_res = client.post("/prep", json={"contact_id": contact_id, "context": "Discussing next steps for deployment."})
            assert prep_res.status_code == 200
            
            data = prep_res.json()
            briefing = data.get("briefing", {})
            model_used = data.get("model_used", "unknown")
            
            f.write(f"## Before meeting {meeting_number}\n")
            f.write(f"**Model Used:** `{model_used}`\n\n")
            f.write("```json\n")
            f.write(json.dumps(briefing, indent=2))
            f.write("\n```\n\n")

if __name__ == "__main__":
    run_proof()
    print("Done")
