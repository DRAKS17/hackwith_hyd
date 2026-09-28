import os
import json
import requests
from hindsight_client import Hindsight
from dotenv import load_dotenv

load_dotenv()

def get_hindsight_client() -> Hindsight:
    """
    Initializes and returns a connection to the Hindsight API.
    Expects HINDSIGHT_API_KEY in the environment.
    """
    api_key = os.environ.get("HINDSIGHT_API_KEY")
    base_url = os.environ.get("HINDSIGHT_BASE_URL", "https://api.vectorize.io")
    return Hindsight(api_key=api_key, base_url=base_url)

def write_memory(contact_id: str, meeting_data: dict, metadata: dict = None):
    """
    Writes a meeting record into the agent's Hindsight memory for a given contact.
    
    Args:
        contact_id (str): The unique identifier for the contact (used as the memory bank_id).
        meeting_data (dict): The meeting data to retain.
        metadata (dict, optional): Tags to categorize the memory (e.g., date, type).
        
    Returns:
        The response from the Hindsight retain API.
    """
    client = get_hindsight_client()
    
    # Enrich meeting data with metadata if provided so it's queryable via content
    # In case the Hindsight client doesn't directly support a metadata kwarg in retain.
    if metadata:
        meeting_data["_tags"] = metadata

    content = json.dumps(meeting_data)
    
    print(f"Retaining memory for contact {contact_id}...")
    # Attempting to pass metadata if supported by retain; otherwise fallback.
    try:
        response = client.retain(content=content, bank_id=contact_id, metadata=metadata)
    except TypeError:
        # If metadata kwarg is not supported by retain signature
        response = client.retain(content=content, bank_id=contact_id)
        
    return response

def query_memory(contact_id: str, query: str):
    """
    Queries the past meeting memories for a given contact to help with meeting prep.
    """
    client = get_hindsight_client()
    print(f"Reflecting on memory for contact {contact_id} with query: '{query}'...")
    response = client.reflect(query=query, bank_id=contact_id)
    return response

def clear_memory(contact_id: str):
    """
    Clears all memories for a given contact bank.
    """
    client = get_hindsight_client()
    print(f"Clearing memory for contact {contact_id}...")
    
    # Try built-in methods if they exist
    if hasattr(client, 'delete_memories'):
        return client.delete_memories(bank_id=contact_id)
    elif hasattr(client, 'delete_bank'):
        return client.delete_bank(bank_id=contact_id)
    else:
        # Fallback to direct HTTP request based on known endpoint
        base_url = getattr(client, 'base_url', "https://api.vectorize.io").rstrip('/')
        url = f"{base_url}/v1/default/banks/{contact_id}/memories"
        headers = {"Authorization": f"Bearer {client.api_key}"}
        response = requests.delete(url, headers=headers)
        if response.status_code >= 400:
            print(f"Warning: Failed to clear memory via HTTP. Status code: {response.status_code}")
        return response.json() if response.text else {}
