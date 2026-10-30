import os

os.environ["DATABASE_URL"] = "sqlite:///./test_evolutia_test.db"
os.environ["EVOLUTIA_ADMIN_TOKEN"] = "test-token-not-for-production"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
AUTH = {"Authorization": "Bearer test-token-not-for-production"}


def test_root_and_health():
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["name"] == "EVOLUTIA AI"
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["database"] == "connected"


def test_research_requires_admin_and_can_be_listed():
    denied = client.post("/research", json={"question": "Como melhorar a plataforma?"})
    assert denied.status_code == 401

    created = client.post(
        "/research",
        headers=AUTH,
        json={"question": "Como melhorar a plataforma?", "context": "Teste automatizado"},
    )
    assert created.status_code == 201
    assert created.json()["status"] == "received"

    listed = client.get("/research")
    assert listed.status_code == 200
    assert any(item["question"] == "Como melhorar a plataforma?" for item in listed.json())


def test_improvement_can_be_created_and_approved():
    created = client.post(
        "/improvements",
        headers=AUTH,
        json={"title": "Adicionar testes", "description": "Criar testes automatizados para a API."},
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    denied = client.post(f"/improvements/{item_id}/approve")
    assert denied.status_code == 401

    approved = client.post(f"/improvements/{item_id}/approve", headers=AUTH)
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["reviewed_at"] is not None


def test_ai_analysis_requires_admin(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    denied = client.post("/ai/analyze", json={"question": "Como melhorar a plataforma?"})
    assert denied.status_code == 401


def test_ai_analysis_reports_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/ai/analyze",
        headers=AUTH,
        json={"question": "Como melhorar a plataforma?"},
    )
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_dashboard_page_is_available():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "EVOLUTIA AI" in response.text
