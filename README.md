# Meeting Prep Agent

An AI agent that uses [Hindsight](https://hindsight.vectorize.io/) to remember past meetings with contacts and generate personalized meeting prep briefings.

## Project Structure

- `/backend`: Contains the API clients, specifically the Hindsight connection layer.
- `/data`: Scripts for data generation and the resulting synthetic JSON mock data.
- `/docs`: Documentation and architecture guidelines.

## Setup Instructions

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GROQ_API_KEY="your_groq_api_key_here"
   HINDSIGHT_API_KEY="your_hindsight_api_key_here"
   # Optional: Set base URL if using a local Docker Hindsight instance
   HINDSIGHT_BASE_URL="http://localhost:8888" 
   ```

3. **Generate Synthetic Data**
   To populate the mock meeting data for your contacts, run the data generation script:
   ```bash
   python data/generate_data.py
   ```
   This uses Groq (model `openai/gpt-oss-120b`) to generate 5 realistic contacts with 4-5 past meetings each. The output will be saved to `data/meetings.json`.

4. **Run Data Ingestion (CLI)**
   To ingest the generated data into Hindsight memory, use the `ingest.py` script:
   ```bash
   python backend/ingest.py
   ```
   To clear a contact's memory before re-ingesting (useful for testing), use the `--reset` flag:
   ```bash
   python backend/ingest.py --reset
   ```

5. **Run the API Server**
   Start the FastAPI server to expose the HTTP endpoints:
   ```bash
   cd backend
   uvicorn api:app --reload
   ```
   You can trigger the ingestion pipeline via the API by sending a POST request to `/ingest`.

## Hindsight Integration

The file `backend/hindsight_client.py` contains the connection layer to Hindsight.
- `write_memory(contact_id, meeting_data, metadata)`: Retains meeting notes into a Hindsight memory bank specific to that contact. Now supports tagging by meeting component (topics, promises, etc.).
- `query_memory(contact_id, query)`: Uses Hindsight to reflect on past interactions and retrieve insights to build personalized prep briefings.
- `clear_memory(contact_id)`: Completely resets a contact's memory bank.
