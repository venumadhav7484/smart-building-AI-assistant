# Smart Building AI Assistant

A full-stack reference implementation of an **AI co-pilot for facility managers**.  
It combines Retrieval-Augmented Generation (RAG) over building manuals, real-time sensor analytics, and predictive-maintenance ML models behind a FastAPI backend and Streamlit UI.

---

## ✨  Features

| Capability | Details |
|------------|---------|
| RAG over docs | Ingest PDFs & CSVs → chunk & embed (FAISS locally or **pgvector** in Postgres) → semantic search & answer generation |
| Live sensor data | Pluggable MCP integration (mock data in `backend/services/mcp.py`) |
| Predictive maintenance | Lightweight heuristic or H2O MOJO model in `backend/predictive/` |
| Multi-tool agent | LangChain agent that can call: `vector_search`, `sensor_live_data`, `predict_failure`, `sql_query` |
| Observability | Optional Prometheus & OpenTelemetry collectors (see `infrastructure/`) |
| Docker-ready | One‐shot `docker compose up` for local demo; ECS/RDS guidance in docs |
| Confidential-mode | Toggle **CONFIDENTIAL_MODE=true** to switch to local embeddings + local LLM, disable outbound calls |

---

## 🚀 Quick Start (local dev)
```bash
# clone your fork / this repo
cd smart-building-AI-assistant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start backend (FastAPI)
export LOCAL_MODE=true             # enables Swagger & CORS
python backend/main.py             # → http://localhost:8000/docs

# In a second terminal – launch UI
streamlit run frontend/app.py      # → http://localhost:8501
```

### Ingest a document
```bash
curl -F file=@data/pdf/M52.pdf http://localhost:8000/upload-document
```
Then ask a question in the Streamlit chat box.

---

## 🔐 Confidential deployments
Setting `CONFIDENTIAL_MODE=true` :
1. uses `sentence-transformers/all-MiniLM-L6-v2` embeddings locally
2. routes all LLM calls to a local model (Mistral-7B or similar)
3. summarises chunks before agent prompts
4. blocks non-SELECT SQL via the pre-push hook

See `backend/llm_factory.py` for implementation guidance.

---

## 🗂️ Repo layout
```
backend/      FastAPI service & LangChain logic
frontend/     Streamlit-based UI
scripts/      CLI helpers (faiss→pgvector, create_dummy_docs, …)
data/         Sample manuals & sensor CSVs (small)
indexes/      Local FAISS store (ignored by .gitignore)
```

---

## 📦 Docker / Compose
```
docker compose -f infrastructure/docker-compose.yml up --build
```
This spins up:
* api (FastAPI)
* ui  (Streamlit)
* postgres-vector (with pgvector extension)
* prometheus + otel-collector

---

## 🛣️ Roadmap
- [ ] Replace heuristic predictor with real MOJO & example dataset
- [ ] Add OAuth2 (Auth0) and role-based access in UI
- [ ] Streaming responses with Server-Sent Events
- [ ] CI: pytest + ruff + docker build in GitHub Actions

---

## License
MIT © 2025 Venu Madhav 