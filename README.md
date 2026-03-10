# Google_APIGEE_Bot

A customized **RAG (Retrieval-Augmented Generation) bot** that answers queries related to **Google Apigee**.  
It combines:
- a **vector knowledge base** (ChromaDB) built from Apigee docs/content,
- **LLM reasoning** (Groq / OpenAI via LangChain),
- and an optional **proxy configuration generator** that can produce **Apigee API proxy XML previews** (ProxyEndpoint/TargetEndpoint/Policies) from natural-language requests.

---

## Features

- **Ask mode (Q&A / consultant mode)**  
  Uses RAG over the knowledge base to answer Apigee questions and provide best-practice guidance.

- **Agent mode (proxy creation assistant)**  
  Detects “create/build/generate proxy” type requests and generates a **configuration preview** including:
  - API proxy name, base path, target URL
  - suggested/detected policies (e.g., `VerifyAPIKey`, `CORS`, `Quota`, `SpikeArrest`, `AssignMessage`, `JavaScript`)
  - XML snippets for the proxy + endpoints + policies
  - optional JavaScript transformation code when requested

- **Vector store persistence**  
  If a vector DB already exists on disk, it is re-used; otherwise it can be created after ingestion.

---

## Tech Stack

- **Python**
- **LangChain** (agents + retrieval QA)
- **ChromaDB** (vector database)
- **HuggingFace embeddings** (Sentence Transformers)
- **Groq** (primary chat model integration)
- (Optional) **OpenAI** integration (dependency present)
- **FastAPI** + **Uvicorn**
- **Streamlit** (UI dependency present)

---

## Repository Structure (high level)

- `services/`
  - `llm.py` — initializes Groq LLMs + HuggingFace embeddings
  - `knowledge_base.py` — Chroma vector store + RetrievalQA chain
  - `apigee_service.py` — parses requests + generates configuration previews
  - `template_generator.py` — creates Apigee XML templates and JS transformation code
- `agents/`
  - `ask_mode.py` — “AskAgent” for Q&A and guidance
  - `agent_mode.py` — “AgentMode” for proxy creation workflows
  - `few_shot_prompts.py` — few-shot prompt templates for strict JSON parsing / XML generation
- `common/`
  - `parsers.py` — request parsing helpers (proxy name, base path, target URL, policies, transforms)
  - `tools.py` — shared LangChain tools (doc search, policy suggestions)
- `requirements.txt` — pinned dependency versions

---

## Setup

### 1) Clone the repo
```bash
git clone https://github.com/Tejaswini-41/Google_APIGEE_Bot.git
cd Google_APIGEE_Bot
```

### 2) Create and activate a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

---

## Configuration (Environment Variables)

This project expects API keys and runtime settings via environment variables.

### Required (for LLM)
- `GROQ_API_KEY` — required to enable Groq models (the LLM service warns and won’t fully initialize without it)

### Common Apigee-related defaults
These are used with defaults if not set:
- `APIGEE_ORG` (default seen in code: `apigee-non-prod-crjb`)
- `APIGEE_ENVIRONMENT` (default seen in code: `apim-dev`)

### Other settings
There is a `config` module imported across services/agents (e.g., model name, temperatures, paths like vector DB directory, processed docs path).  
If you don’t see a `config.py` in the repo root, create one to define values such as:
- model name (Groq model)
- embedding model name
- temperatures / token limits
- paths for:
  - processed docs JSON
  - Chroma persistence directory

Example (illustrative only — adjust to your project):
```python
# config.py (example)
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.1-70b-versatile")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

TEMPERATURE_CREATIVE = float(os.getenv("TEMPERATURE_CREATIVE", "0.7"))
TEMPERATURE_PRECISE = float(os.getenv("TEMPERATURE_PRECISE", "0.2"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))

MEMORY_WINDOW = int(os.getenv("MEMORY_WINDOW", "6"))

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vector_db")
PROCESSED_DOCS_PATH = os.getenv("PROCESSED_DOCS_PATH", "./data/processed_docs.json")
```

---

## Knowledge Base / Ingestion

`KnowledgeService` will:
- load an existing Chroma DB from `VECTOR_DB_PATH` if present, OR
- attempt to create one from `PROCESSED_DOCS_PATH` (a JSON file of processed documents)

If your vector DB is not building, ensure:
- the embeddings model can download (network access / HuggingFace model availability)
- `PROCESSED_DOCS_PATH` exists and contains valid JSON documents

---

## Usage

### Example: Ask mode (Apigee Q&A)
Typical questions:
- “How do I apply SpikeArrest in Apigee?”
- “Explain VerifyAPIKey policy and how to attach it to PreFlow.”
- “What’s the difference between Quota and SpikeArrest?”

### Example: Agent mode (proxy configuration preview)
You can provide prompts like:
- “Create an Apigee API proxy named `booking-api` with base path `/booking` pointing to `https://backend.example.com/api`. Add VerifyAPIKey.”
- “Create an Apigee API proxy named `googledemo` with base path `/google` pointing to `https://www.google.com`. Add routes /getuser (GET) ... and attach SpikeArrest with 4ps.”
- “Create a proxy that combines firstName and lastName into fullName in response using JavaScript.”

The service can generate a preview containing:
- `APIProxy` XML
- `ProxyEndpoint` XML
- `TargetEndpoint` XML
- policy XML snippets
- optional `transformation.js` code (Apigee JavaScript policy)

---

## Notes / Limitations

- If `GROQ_API_KEY` is not set, the LLM service will not fully initialize and agents may not run.
- The vector DB requires embeddings initialization; if embeddings fail, the knowledge base won’t be available.
- Some policy suggestions are keyword-based (simple heuristics) and may need refinement depending on your use cases.

---


