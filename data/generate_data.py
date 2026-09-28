import os
import json
from groq import Groq

def generate_meetings():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not found. Please set it.")
        return
        
    client = Groq(api_key=api_key)
    
    prompt = """
    Generate a JSON object containing synthetic meeting history for 5 diverse, realistic B2B contacts.
    DO NOT use placeholder names like 'Jane Doe' or 'John Smith'. Use realistic names (e.g., 'Elena Rostova', 'Marcus Thorne').
    Include a mix of industries for the companies.
    
    For each contact, generate an array of 4 to 5 meetings.
    ALL meeting dates MUST be in the year 2026, strictly between January 2026 and September 2026.
    The meetings must be chronological.
    
    SCHEMA for each meeting:
    {
      "date": "YYYY-MM-DD",
      "topics": "summary of what was discussed",
      "objections": "any concerns raised",
      "promises": ["list of promises made by either party"],
      "follow_ups": [
         {
           "promise": "exact text of a promise from a PREVIOUS meeting",
           "status": "delivered" or "not delivered",
           "owner": "us" or "contact"
         }
      ],
      "personal_details": "any personal notes (e.g. vacations, family)"
    }
    
    RULES:
    1. The first meeting has an empty "follow_ups" array.
    2. Subsequent meetings MUST have "follow_ups" referring to promises made in earlier meetings.
    3. Make sure SOME promises are delivered, but at least 2 contacts MUST have a promise that is NEVER delivered across all meetings.
    4. At least 2 contacts MUST have a personal detail revealed in a LATE meeting (meeting 3, 4, or 5).
    
    Return ONLY a valid JSON object with a "contacts" array.
    Each contact should have: "contact_id" (e.g. "c1", "c2"), "name", "title", "company", and "meetings".
    """
    
    print("Generating synthetic data using openai/gpt-oss-120b on Groq...")
    res = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a JSON data generator. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    data = json.loads(res.choices[0].message.content)
    
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), "meetings.json"), "w") as f:
        json.dump(data, f, indent=2)
        
    print("Successfully generated data and saved to data/meetings.json")

if __name__ == "__main__":
    generate_meetings()
