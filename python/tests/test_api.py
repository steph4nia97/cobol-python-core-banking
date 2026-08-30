from fastapi.testclient import TestClient

from banking_pipeline.api import app


def test_health_and_oracle_endpoints():
    client = TestClient(app)
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    oracle = client.get("/api/oracle")
    assert oracle.status_code == 200
    assert oracle.json()["accounts"] == 5
    assert oracle.json()["exceptions"] == 5

    home = client.get("/")
    assert home.status_code == 200
    assert "Andean Ledger" in home.text
