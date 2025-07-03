"""Week 3 – Smart Building Assistant (skeleton backend).

Run locally with:
    LOCAL_MODE=true python backend/main.py
"""
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Instrumentation libraries are optional in local dev / test
try:
    from prometheus_fastapi_instrumentator import Instrumentator  # type: ignore
except ImportError:  # pragma: no cover
    Instrumentator = None  # type: ignore

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
except ImportError:  # pragma: no cover
    FastAPIInstrumentor = None  # type: ignore

from backend.rag.manager import DocumentAssistant
from backend.agent.builder import get_agent

# Load env vars
load_dotenv()

# RAG helper
doc_assist = DocumentAssistant()

# Predictive maintenance
from backend.predictive.maintenance import HealthPredictor
from backend.services.mcp import fetch_live_data as _fetch_live_data

# Expose fetch_live_data at module level so tests can monkey-patch it easily
fetch_live_data = _fetch_live_data  # type: ignore

# Single predictor instance (lightweight heuristic / MOJO)
predictor = HealthPredictor()

# Lazily create agent (uses same doc_assist via underlying tool singleton)
_agent_executor = None

app = FastAPI(title="Smart Building AI – Backend", docs_url="/docs" if os.getenv("LOCAL_MODE") else None)

# Allow localhost JS during dev only
if os.getenv("LOCAL_MODE"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Simple health-check used by ALB / CI tests."""
    return {"status": "ok"}


# ---------------- RAG endpoints ----------------


@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    fname = file.filename.lower()
    if not (fname.endswith(".pdf") or fname.endswith(".csv")):
        raise HTTPException(status_code=400, detail="PDF or CSV only")

    suffix = ".pdf" if fname.endswith(".pdf") else ".csv"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(await file.read())
    tmp.flush()

    if suffix == ".pdf":
        num_chunks = doc_assist.ingest_pdf(tmp.name)
    else:
        num_chunks = doc_assist.ingest_csv(tmp.name)

    return {"status": "success", "chunks": num_chunks, "file_type": suffix}


class AskRequest(BaseModel):
    query: str
    k: int = 4


@app.post("/ask")
async def ask(req: AskRequest):
    # Quick heuristic: for short greetings/one-word queries just respond politely without citations
    if len(req.query.split()) < 3:
        return {"answer": "Hello! How can I assist you today?", "citations": []}

    doc_objs = doc_assist.similarity_search_docs(req.query, k=req.k)
    if not doc_objs:
        return {"answer": "No documents ingested yet."}

    context = "\n".join([d.page_content for d in doc_objs])

    prompt = (
        "You are a helpful building-ops assistant.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {req.query}\n\nANSWER:"
    )
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
    resp = llm.predict(prompt)

    citations = []
    for d in doc_objs:
        meta = d.metadata or {}
        citations.append({
            "source": os.path.basename(meta.get("source", "")),
            "page": meta.get("page", -1),
            "snippet": d.page_content[:160].replace("\n", " ")
        })

    return {"answer": resp, "citations": citations}


# ---------------- Predictive maintenance endpoint ----------------


@app.get("/health/{equipment_id}")
async def equipment_health(equipment_id: str):
    """Return probability of failure for a given piece of equipment.

    The endpoint fetches live sensor data via the MCP integration, then feeds it
    into the `HealthPredictor`. If the equipment ID is unknown it returns 404.
    """
    sensors = fetch_live_data(equipment_id)

    if not sensors:
        raise HTTPException(status_code=404, detail="Unknown equipment_id")

    prob = predictor.predict(sensors)

    return {
        "equipment_id": equipment_id,
        "sensors": sensors,
        "failure_probability": prob,
    }


# ---------------- Agent endpoint ----------------


class AgentRequest(BaseModel):
    question: str


@app.post("/agent")
async def agent_endpoint(req: AgentRequest):
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = get_agent()
    result = _agent_executor.invoke({"input": req.question, "chat_history": []})
    return {"answer": result["output"]}


if __name__ == "__main__":
    import uvicorn

    if os.getenv("LOCAL_MODE"):
        # Use import string so reload works without warning
        uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

# ------------ Instrumentation (after app definition) ------------

# Prometheus metrics
if Instrumentator is not None:  # pragma: no cover
    Instrumentator().instrument(app).expose(app, include_in_schema=False)

# OpenTelemetry tracing (no-op exporter unless configured)
if FastAPIInstrumentor is not None:  # pragma: no cover
    FastAPIInstrumentor().instrument_app(app) 