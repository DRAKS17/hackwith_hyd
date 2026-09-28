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

5. **Start the API Server**
   Start the FastAPI server to expose the HTTP endpoints to the frontend:
   ```bash
   cd backend
   uvicorn api:app --reload
   ```

6. **Open the Frontend UI**
   Open the `frontend/index.html` file directly in your browser, or serve it via a simple HTTP server:
   ```bash
   cd frontend
   python -m http.server 8080
   ```
   Then navigate to `http://localhost:8080`.

## How Hindsight Memory Powers This

Unlike traditional RAG (Retrieval-Augmented Generation) which simply retrieves chunks of text, this agent uses Vectorize's **Hindsight** memory engine to structurally "remember" past interactions. 

1. **Retain**: Past meeting notes are ingested and categorized.
2. **Recall & Reflect**: When prepping for a new meeting, the backend queries Hindsight. Hindsight navigates its internal graph of the contact (World, Experience, and Observation networks) to synthesize raw historical snippets into a consolidated memory context.
3. **Generate**: We pass Hindsight's synthesis into an LLM (Groq / Llama / GPT) to cleanly format the final briefing ("Promises you haven't followed up on," "Concerns to address," etc.).

This allows the agent's briefing to get exponentially smarter and more contextualized as more meetings occur!

## Hindsight API Connection

The file `backend/hindsight_client.py` contains the connection layer to Hindsight.
- `write_memory(contact_id, meeting_data, metadata)`: Retains meeting notes into a Hindsight memory bank specific to that contact. Now supports tagging by meeting component (topics, promises, etc.).
- `query_memory(contact_id, query)`: Uses Hindsight to reflect on past interactions and retrieve insights to build personalized prep briefings.
- `clear_memory(contact_id)`: Completely resets a contact's memory bank.
