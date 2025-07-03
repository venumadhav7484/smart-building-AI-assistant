import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from backend import main as backend

# Ensure health endpoint finds sensors
dummy_sensors = {"temperature": 70, "vibration": 0.2}
backend.fetch_live_data = lambda *_: dummy_sensors  # type: ignore
backend.__dict__["fetch_live_data"] = backend.fetch_live_data  # ensure global ref updated

client = TestClient(backend.app)

def test_health_endpoint():
    resp = client.get("/health/HVAC-01")
    assert resp.status_code == 200
    data = resp.json()
    assert "failure_probability" in data
    assert 0 <= data["failure_probability"] <= 1 