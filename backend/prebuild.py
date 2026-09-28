import os
import json
import time
from hindsight_service import get_hindsight_client

def ingest_stage(contact_id, contact_name, meetings_to_ingest, bank_id, hs):
    print(f"\\n--- Building Bank {bank_id} ---")
    try:
        hs.delete_bank(bank_id=bank_id)
        time.sleep(2)
    except Exception:
        pass # Not found
        
    for idx, meeting in enumerate(meetings_to_ingest):
        date = meeting.get('date')
        for m_type in ['topics', 'objections', 'promises', 'follow_ups', 'personal_details']:
            content = meeting.get(m_type)
            if content:
                if isinstance(content, list):
                    content_str = ", ".join(json.dumps(c) if isinstance(c, dict) else str(c) for c in content)
                else:
                    content_str = str(content)
                
                # Use real name instead of "contact cX"
                payload = {
                    "contact_id": contact_id, 
                    "date": date, 
                    "type": m_type, 
                    "content": f"{contact_name}: {content_str}"
                }
                metadata = {"contact_id": contact_id, "date": date, "type": m_type}
                
                retries = 3
                for attempt in range(retries):
                    start_t = time.time()
                    try:
                        hs.retain(content=json.dumps(payload), bank_id=bank_id, metadata=metadata)
                        dur = time.time() - start_t
                        print(f"Retained {date} {m_type} | Dur: {dur:.2f}s | Status: Success")
                        break
                    except Exception as e:
                        dur = time.time() - start_t
                        print(f"Retained {date} {m_type} | Dur: {dur:.2f}s | Attempt {attempt+1} failed: {e}")
                        if attempt == retries - 1:
                            raise e
                        time.sleep(2 ** attempt)

def poll_stable_count(contact_id, stage_num, bank_id, hs):
    stable_checks = 0
    last_count = -1
    timeout = 60
    start_t = time.time()
    
    print(f"Polling {bank_id}...")
    while time.time() - start_t < timeout:
        try:
            res = hs.recall(query="*", bank_id=bank_id)
            count = len(res.results) if hasattr(res, 'results') and res.results else 0
        except Exception:
            count = 0
            
        if count > 0 and count == last_count:
            stable_checks += 1
            if stable_checks >= 2:
                print(f"{bank_id:15} | {stage_num:17} | {count:12} | yes")
                return
        else:
            stable_checks = 0
            
        last_count = count
        time.sleep(2)
        
    print(f"{bank_id:15} | {stage_num:17} | {last_count:12} | no (timeout)")

def prebuild_banks():
    hs = get_hindsight_client()
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "meetings.json")
    with open(data_path, "r") as f:
        data = json.load(f)
        
    print(f"{'bank':15} | {'expected meetings':17} | {'memory count':12} | stable (yes/no)")
    print("-" * 65)
        
    for contact in data.get("contacts", [])[:2]:
        contact_id = contact.get('contact_id')
        contact_name = contact.get('name')
        meetings = contact.get('meetings', [])
        
        for stage in [1, 3, 5]:
            bank_id = f"{contact_id}_before{stage}"
            m_count = stage - 1
            to_ingest = meetings[:m_count]
            if to_ingest:
                ingest_stage(contact_id, contact_name, to_ingest, bank_id, hs)
                poll_stable_count(contact_id, m_count, bank_id, hs)
            else:
                # 0 meetings, empty bank
                try:
                    hs.delete_bank(bank_id=bank_id)
                except Exception:
                    pass
                print(f"{bank_id:15} | {m_count:17} | {0:12} | yes")

if __name__ == "__main__":
    prebuild_banks()
