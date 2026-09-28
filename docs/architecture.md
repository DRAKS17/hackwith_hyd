# Architecture Guidelines

This directory contains documentation for the Meeting Prep Agent's overall architecture.

## Overview
- **Data Layer**: Synthetic JSON generation via Groq API.
- **Memory Layer**: Vectorize Hindsight API for memory retention, recall, and reflection.
- **Application Layer**: FastAPI backend and HTML/JS frontend.

## Architecture Diagram

```mermaid
flowchart TD
    A[data/meetings.json] -->|backend/ingest.py| B(Hindsight retain)
    B --> C[(Hindsight Memory Graph)]
    C -->|Hindsight reflect/recall| D(backend/api.py /prep)
    D --> E(Groq LLM)
    E --> F[Structured Briefing JSON]
    F --> G(frontend/index.html UI)
```
