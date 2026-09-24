from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nifty100 Analytics API"
    assert data["version"] == "1.0.0"
    assert data["health"] == "/api/v1/health"


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert data["db_row_counts"]["companies"] == 92


def test_screener():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_screener_min_roe():
    response = client.get("/api/v1/screener", params={"min_roe": 15})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == len(data["results"])
    for row in data["results"]:
        assert row["roe_pct"] >= 15


def test_screener_sector():
    response = client.get(
        "/api/v1/screener", params={"sector": "Information Technology"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == len(data["results"])
    for row in data["results"]:
        assert row["broad_sector"] == "Information Technology"


def test_screener_max_pe():
    response = client.get("/api/v1/screener", params={"max_pe": 20})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == len(data["results"])
    for row in data["results"]:
        if row["pe_ratio"] is not None:
            assert row["pe_ratio"] <= 20


def test_screener_invalid_numeric_filter():
    response = client.get("/api/v1/screener", params={"min_roe": "abc"})
    assert response.status_code == 400


def test_screener_invalid_infinite_filter():
    response = client.get("/api/v1/screener", params={"min_roe": "nan"})
    assert response.status_code == 400
