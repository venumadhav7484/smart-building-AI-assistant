import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from backend import main as backend
from langchain.schema import Document

# Patch LLM and doc assistant to avoid external calls
class DummyLLM:
    def __init__(self, *_, **__):
        pass

    def predict(self, prompt: str) -> str:
        return "dummy answer"

backend.ChatOpenAI = DummyLLM  # type: ignore
backend.doc_assist.ingest_pdf = lambda *_: 1  # type: ignore

dummy_doc = Document(page_content="dummy context", metadata={"source": "test.pdf", "page": 1})
backend.doc_assist.similarity_search_docs = lambda *_, **__: [dummy_doc]  # type: ignore

client = TestClient(backend.app)

def test_ask_endpoint():
    ans = client.post("/ask", json={"query": "test"})
    assert ans.status_code == 200
    data = ans.json()
    assert data["answer"] == "dummy answer"
    assert data["citations"][0]["source"] == "test.pdf" 