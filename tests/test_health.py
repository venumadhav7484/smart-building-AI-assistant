import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from backend import main as backend

# monkeypatch
backend.fetch_live_data = lambda *_: {"temperature": 70, "vibration": 0.1}  # type: ignore

def test_health():
    client = TestClient(backend.app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok" 