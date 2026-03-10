# Google Apigee Bot

A customized **Retrieval-Augmented Generation (RAG) assistant** designed to answer questions related to **Google Apigee** and assist in **API proxy configuration generation**.

The bot combines a **vector knowledge base**, **LLM reasoning**, and **automated configuration generation** to help developers understand Apigee concepts and quickly generate proxy configuration previews.

---

# Key Features

## 1. Ask Mode – Apigee Q&A

Allows users to ask questions about **Google Apigee concepts, policies, and best practices**.

The bot retrieves relevant information from the knowledge base and generates contextual answers.

Example queries:

* How does **SpikeArrest** work in Apigee?
* Explain the **VerifyAPIKey policy**
* Difference between **Quota and SpikeArrest**

---

## 2. Agent Mode – Proxy Configuration Assistant

Detects requests related to **creating API proxies** and generates a **configuration preview**.

The generated preview may include:

* API proxy name
* Base path
* Target endpoint URL
* Suggested policies
* XML configuration snippets

Supported policies include:

* VerifyAPIKey
* CORS
* Quota
* SpikeArrest
* AssignMessage
* JavaScript transformation

Example request:

```
Create an Apigee API proxy named booking-api with base path /booking
pointing to https://backend.example.com/api and add VerifyAPIKey.
```

Generated preview includes:

* `APIProxy.xml`
* `ProxyEndpoint.xml`
* `TargetEndpoint.xml`
* Policy XML snippets
* Optional JavaScript transformation code

---

# Tech Stack

* **Python**
* **LangChain**
* **ChromaDB**
* **HuggingFace Sentence Transformers**
* **Groq LLM**
* **FastAPI**
* **Uvicorn**
* **Streamlit (optional UI)**

---

# Project Structure

```
Google_APIGEE_Bot/
│
├── agents/
│   ├── ask_mode.py
│   ├── agent_mode.py
│   └── few_shot_prompts.py
│
├── services/
│   ├── llm.py
│   ├── knowledge_base.py
│   ├── apigee_service.py
│   └── template_generator.py
│
├── common/
│   ├── parsers.py
│   └── tools.py
│
├── requirements.txt
└── README.md
```

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Tejaswini-41/Google_APIGEE_Bot.git
cd Google_APIGEE_Bot
```

---

## 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate it:

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Configuration

The application requires a **Groq API key** for LLM inference.

Set the environment variable:

```
GROQ_API_KEY=your_api_key
```

Optional environment variables:

| Variable            | Description                        |
| ------------------- | ---------------------------------- |
| APIGEE_ORG          | Apigee organization                |
| APIGEE_ENVIRONMENT  | Apigee environment                 |
| VECTOR_DB_PATH      | Path to ChromaDB                   |
| PROCESSED_DOCS_PATH | Processed knowledge base documents |

---

# Knowledge Base

The system uses **ChromaDB** as the vector database.

At runtime the system will:

1. Load an existing vector database if available.
2. Otherwise build the vector database from processed Apigee documents.

Ensure that the **processed documents JSON file** exists before building the knowledge base.

---

# Example Usage

## Ask Mode

```
How do I attach a SpikeArrest policy in Apigee?
```

## Agent Mode

```
Create an Apigee proxy named user-api with base path /users
pointing to https://backend.example.com and add VerifyAPIKey.
```

---

# Limitations

* Requires a valid **Groq API key**
* Policy detection currently uses **heuristics and prompts**
* Vector database must be built before RAG can be used

---

# Future Improvements

* Improved policy recommendation engine
* Apigee deployment integration
* Enhanced UI for proxy generation
* Expanded Apigee documentation coverage

---

# License

This project is intended for **learning and experimentation with Apigee automation and RAG-based assistants**.

---

# Author

**Tejaswini Durge**

GitHub:
https://github.com/Tejaswini-41
