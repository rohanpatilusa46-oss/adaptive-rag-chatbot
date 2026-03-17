# Adaptive RAG Chatbot (FastAPI + LangGraph + Streamlit)

An end-to-end, adaptive Retrieval-Augmented Generation (RAG) chatbot with an agentic architecture. The system:

- Uses **LangChain + LangGraph** for orchestration
- Routes queries adaptively between:
  - **Document RAG** (uploaded PDFs / text)
  - **General LLM knowledge**
  - **Web search via Tavily**
- Stores vectors in **Qdrant** (with **FAISS** fallback)
- Stores chat history in **MongoDB**
- Exposes a **FastAPI** backend and a **Streamlit** frontend

---

## 1. Project Structure

```text
.
├── backend
│   ├── main.py              # FastAPI app & API routes
│   ├── config.py            # Configuration & environment
│   ├── logging_config.py    # Logging setup
│   ├── schemas.py           # Pydantic models
│   ├── vectorstore.py       # Qdrant + FAISS management
│   ├── memory.py            # MongoDB chat history
│   ├── ingestion.py         # Document parsing & ingestion
│   └── graph
│       ├── state.py         # LangGraph state definition
│       └── graph_builder.py # Adaptive routing graph
├── frontend
│   └── app.py               # Streamlit UI
├── requirements.txt
└── README.md
```

---

## 2. Setup

### 2.1. Python environment

```bash
cd /Users/rohan/ai-live-assistant
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2.2. Environment variables

Set these in your shell or a `.env` file in the project root:

- **Core**
  - `OPENAI_API_KEY` – OpenAI API key
  - `TAVILY_API_KEY` – Tavily API key
- **Qdrant (optional; FAISS used if Qdrant fails)**
  - `QDRANT_URL` – e.g. `http://localhost:6333`
  - `QDRANT_API_KEY` – if your Qdrant instance requires auth
  - `QDRANT_COLLECTION` – defaults to `documents`
- **MongoDB (optional; memory disabled if missing)**
  - `MONGODB_URI` – e.g. `mongodb://localhost:27017`
  - `MONGODB_DB_NAME` – e.g. `adaptive_rag`
  - `MONGODB_COLLECTION_NAME` – e.g. `conversations`

---

## 3. Running the backend (FastAPI)

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

FastAPI will be available at `http://localhost:8000`.

- Docs: `http://localhost:8000/docs`
- Health check: `GET /health`

---

## 4. Running the frontend (Streamlit)

In a separate terminal:

```bash
cd frontend
streamlit run app.py
```

The Streamlit UI will open in your browser (usually `http://localhost:8501`).

---

## 5. Usage

- **Upload documents** (PDF or `.txt`) in the sidebar.
- **Chat** with the assistant; each browser tab is a separate session.
- The backend will:
  - Classify each query (documents vs general LLM vs web search).
  - Build the appropriate context using RAG, general LLM, or Tavily.
  - Use conversation history from MongoDB (if available) to maintain continuity.

---

## 6. Fault Tolerance

- If **Qdrant** is unavailable, the system falls back to an in-process **FAISS** index.
- If **MongoDB** is unavailable, conversation history is not stored, but the chatbot continues to function.
- Clear logging is provided for:
  - Query classification decisions
  - Retrieval steps and scores
  - Web search usage
  - Errors and degraded modes (e.g. missing services)

---

## 7. Notes

- This project intentionally omits authentication and complex user management to keep the focus on the **adaptive RAG core**.
- All configuration is done via environment variables for easy deployment to different environments.

