import os
import json
import argparse
from typing import Dict, Any

from hindsight_service import write_memory, clear_memory

def load_data(filepath: str) -> Dict[str, Any]:
    """
    Loads JSON data from the specified filepath.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def ingest_data(reset: bool = False):
    """
    Ingests meeting data into Hindsight.
    """
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'meetings.json')
    data = load_data(data_path)
    
    contacts = data.get('contacts', [])
    summary = []
    
    for contact in contacts:
        contact_id = contact.get('contact_id')
        name = contact.get('name')
        meetings = contact.get('meetings', [])
        
        if not contact_id:
            continue
            
        if reset:
            clear_memory(contact_id)
            print(f"Memory reset for {name} ({contact_id})")
            
        # Sort meetings chronologically
        meetings.sort(key=lambda x: x.get('date', ''))
        
        memories_written = 0
        for meeting in meetings:
            date = meeting.get('date')
            
            # We break down the meeting into different memory types for better filterability
            components = {
                'topics': meeting.get('topics'),
                'objections': meeting.get('objections'),
                'promises': meeting.get('promises'),
                'personal_notes': meeting.get('personal_details')
            }
            
            for m_type, content in components.items():
                if not content:
                    continue
                    
                # Prepare payload
                payload = {
                    "contact_id": contact_id,
                    "date": date,
                    "type": m_type,
                    "content": content
                }
                
                metadata = {
                    "contact_id": contact_id,
                    "date": date,
                    "type": m_type
                }
                
                # Write to Hindsight
                write_memory(contact_id, payload, metadata)
                memories_written += 1
                
            print(f"Ingested meeting on {date} for {name}")
            
        summary.append({"contact_id": contact_id, "name": name, "memories_written": memories_written})
        
    print("\n--- Ingestion Complete ---")
    for s in summary:
        print(f"{s['name']}: {s['memories_written']} memory segments written.")
        
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest mock meeting data into Hindsight.")
    parser.add_argument("--reset", action="store_true", help="Clear contact's memory before re-ingesting")
    args = parser.parse_args()
    
    ingest_data(reset=args.reset)
