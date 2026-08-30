from fastapi.testclient import TestClient

from banking_pipeline.api import app


def test_login_and_operator_cannot_run_batch():
    client = TestClient(app)
    assert client.get("/api/accounts").status_code == 401

    admin = client.post("/api/auth/login-json", json={"username": "admin", "password": "admin"})
    assert admin.status_code == 200

    operator = client.post("/api/auth/login-json", json={"username": "operator", "password": "operator"})
    headers = {"Authorization": f"Bearer {operator.json()['access_token']}"}
    assert client.post("/api/batch/run", headers=headers).status_code == 403
    assert client.get("/api/accounts", headers=headers).status_code == 200


def test_home_dashboard():
    client = TestClient(app)
    home = client.get("/")
    assert home.status_code == 200
    assert "Batch Control" in home.text
