# Week 3 – Smart Building Operations Assistant (Scaffold)

This directory starts the Week-3 project that will cover the remaining Nemetschek AI-Developer gaps:

* MCP-enabled multi-tool agent (docs, SQL, sensor API, code-gen)
* Lightweight fine-tuned GPT-3.5 reranker
* Predictive maintenance with H2O MOJO
* OAuth2 auth, observability, CI/CD to AWS

## Run locally (dev mode)
```bash
export LOCAL_MODE=true   # enables CORS & docs
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python backend/main.py        # Terminal 1
streamlit run frontend/app.py # Terminal 2
```
Then open http://localhost:8501 and click "Ping backend".

## Folder layout
```text
backend/   – FastAPI service (currently just /healthz)
frontend/  – Streamlit UI scaffold
tests/     – pytest suite (health endpoint only for now)
```

## Next milestones
1. Add RAG ingestion & query (reuse Week-2 code).
2. Wire LangChain Agent + MCP tool calls.
3. Integrate PGVector for scalable embeddings.
4. Add MOJO predictor + fake sensor data.
5. CI workflow & Docker compose.

Stay tuned! ☕️ 