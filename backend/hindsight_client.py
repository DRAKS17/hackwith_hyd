import os
import json
from hindsight_client import Hindsight
from dotenv import load_dotenv

load_dotenv()

def get_hindsight_client() -> Hindsight:
    """
    Initializes and returns a connection to the Hindsight API.
    Expects HINDSIGHT_API_KEY in the environment.
    HINDSIGHT_BASE_URL can be set if using a specific cloud endpoint or local docker.
    """
    api_key = os.environ.get("HINDSIGHT_API_KEY")
    # Default to vectorize.io cloud endpoint, or override for local server
    base_url = os.environ.get("HINDSIGHT_BASE_URL", "https://api.vectorize.io")
    
    return Hindsight(api_key=api_key, base_url=base_url)

def write_memory(contact_id: str, meeting_data: dict):
    """
    Writes a meeting record into the agent's Hindsight memory for a given contact.
    
    Args:
        contact_id (str): The unique identifier for the contact (used as the memory bank_id).
        meeting_data (dict): The meeting data to retain.
        
    Returns:
        The response from the Hindsight retain API.
    """
    client = get_hindsight_client()
    
    # Hindsight's retain method typically ingests string content.
    # We convert the structured meeting data into a JSON string.
    content = json.dumps(meeting_data)
    
    print(f"Retaining memory for contact {contact_id}...")
    response = client.retain(content=content, bank_id=contact_id)
    return response

def query_memory(contact_id: str, query: str):
    """
    Queries the past meeting memories for a given contact to help with meeting prep.
    
    Args:
        contact_id (str): The unique identifier for the contact (used as the memory bank_id).
        query (str): The question or topic to search for in their memory.
        
    Returns:
        The reflected/synthesized answer based on past meetings.
    """
    client = get_hindsight_client()
    
    print(f"Reflecting on memory for contact {contact_id} with query: '{query}'...")
    
    # reflect synthesizes an answer from the recalled memories, which is perfect for prep briefings.
    response = client.reflect(query=query, bank_id=contact_id)
    return response
