import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from backend import main as backend

# Inject dummy agent executor so no OpenAI key needed
after = getattr(backend, "_agent_executor", None)

class _Dummy:
    def invoke(self, *_, **__):
        return {"output": "dummy answer"}

backend._agent_executor = _Dummy()

client = TestClient(backend.app)


def test_agent_endpoint():
    resp = client.post("/agent", json={"question": "What is HVAC?"})
    assert resp.status_code == 200
    assert resp.json().get("answer") == "dummy answer" 