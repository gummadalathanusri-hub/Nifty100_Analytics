from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Nifty 100 Analytics API is running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["rows"] == 100
    assert data["companies"] == 100


def test_screener_presets():
    response = client.get("/screener/presets")
    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert len(data["presets"]) == 6


def test_value_pick():
    response = client.get("/screener/value_pick")
    assert response.status_code == 200
    data = response.json()
    assert data["preset"] == "value_pick"
    assert data["rows"] == 2
    assert data["companies"] == 2
    assert "results" in data


def test_quality_compounder():
    response = client.get("/screener/quality_compounder")
    assert response.status_code == 200
    data = response.json()
    assert data["preset"] == "quality_compounder"
    assert "results" in data


def test_growth_accelerator():
    response = client.get("/screener/growth_accelerator")
    assert response.status_code == 200
    data = response.json()
    assert data["preset"] == "growth_accelerator"
    assert "results" in data


def test_dividend_champion():
    response = client.get("/screener/dividend_champion")
    assert response.status_code == 200
    data = response.json()
    assert data["preset"] == "dividend_champion"
    assert "results" in data


def test_debt_free_blue_chip():
    response = client.get("/screener/debt_free_blue_chip")
    assert response.status_code == 200
    data = response.json()
    assert data["preset"] == "debt_free_blue_chip"
    assert "results" in data


def test_turnaround_watch():
    response = client.get("/screener/turnaround_watch")
    assert response.status_code == 200
    data = response.json()
    assert data["preset"] == "turnaround_watch"
    assert "results" in data