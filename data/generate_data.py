import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# We will use prompt engineering to enforce JSON structure.
# Model specified by user: openai/gpt-oss-120b
MODEL_NAME = "openai/gpt-oss-120b"

PROMPT = """
You are a synthetic data generator. 
Generate realistic synthetic data for 5 contacts. 
For each contact, generate 4-5 past meetings. 
Each meeting record MUST include:
- date (YYYY-MM-DD)
- topics discussed (list of strings)
- objections/concerns raised (list of strings)
- promises made (list of strings)
- personal details mentioned (string)

Return ONLY valid JSON. The output should follow this format:
{
  "contacts": [
    {
      "contact_id": "c1",
      "name": "Jane Doe",
      "company": "Tech Corp",
      "meetings": [
        {
          "date": "2023-10-15",
          "topics": ["Product demo", "Pricing"],
          "objections": ["Price is too high", "Missing feature X"],
          "promises": ["Send custom proposal", "Check with engineering about feature X"],
          "personal_details": "Mentioned her daughter is starting college next month"
        }
      ]
    }
  ]
}
"""

def generate_data():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY is not set in the environment. Please set it in a .env file.")
        return

    client = Groq(api_key=api_key)
    
    print(f"Generating synthetic data using {MODEL_NAME} on Groq...")
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output valid JSON."},
                {"role": "user", "content": PROMPT}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        try:
            data = json.loads(content)
            # Ensure data directory exists
            output_dir = os.path.dirname(os.path.abspath(__file__))
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = os.path.join(output_dir, "meetings.json")
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
                
            print(f"Successfully generated data and saved to {output_file}")
        except json.JSONDecodeError:
            print("Error: The model did not return valid JSON.")
            print("Raw output:", content)
            
    except Exception as e:
        print(f"An error occurred during generation: {e}")

if __name__ == "__main__":
    generate_data()
