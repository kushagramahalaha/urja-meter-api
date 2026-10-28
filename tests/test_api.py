
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.clients.portal_client import PortalClient


@pytest.fixture
def client(monkeypatch):
    """Use mocked portal responses so tests do not call the live portal."""

    def fake_login(self):
        pass

    def fake_search_meters(self, query="", page=1):
        return {
            "data": [
                {
                    "meterId": "J100000",
                    "serialNo": "SE33962",
                    "make": "HPL",
                    "phaseType": "single",
                    "installStatus": "Decommissioned",
                    "dtCode": "DT-001",
                }
            ],
            "total": 1,
            "page": page,
            "pageSize": 20,
        }

    def fake_geo(self, meter_id):
        return {
            "data": {
                "latitude": "26.938961",
                "longitude": "75.830957",
            }
        }

    def fake_energy(self, meter_id):
        return {
            "data": [
                {
                    "timestamp": "23/06/2026 23:30",
                    "kwh": "48438.74",
                    "kvah": "52313.84",
                    "voltR": "226",
                }
            ]
        }

    def fake_transformers(self, page=1):
        return {
            "data": [
                {
                    "code": "DT-001",
                    "name": "Malviya Nagar DT 1",
                    "feederCode": "F-001",
                    "capacityKva": 100,
                }
            ],
            "total": 40,
            "page": page,
            "pageSize": 20,
        }

    monkeypatch.setattr(PortalClient, "login", fake_login)
    monkeypatch.setattr(PortalClient, "close", lambda self: None)
    monkeypatch.setattr(
        PortalClient, "search_meters", fake_search_meters
    )
    monkeypatch.setattr(PortalClient, "get_meter_geo", fake_geo)
    monkeypatch.setattr(
        PortalClient, "get_meter_energy", fake_energy
    )
    monkeypatch.setattr(
        PortalClient, "list_transformers", fake_transformers
    )

    with TestClient(app) as test_client:
        yield test_client


def test_meter_search(client):
    response = client.get(
        "/api/v1/meters",
        params={"q": "J100000", "page": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"][0]["meterId"] == "J100000"
    assert body["total"] == 1


def test_meter_geo(client):
    response = client.get("/api/v1/meters/J100000/geo")

    assert response.status_code == 200
    body = response.json()["data"]
    assert isinstance(body["latitude"], (int, float))
    assert isinstance(body["longitude"], (int, float))


def test_meter_energy(client):
    response = client.get("/api/v1/meters/J100000/energy")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["kwh"] == pytest.approx(48438.74)


def test_transformer_list(client):
    response = client.get(
        "/api/v1/transformers",
        params={"page": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"][0]["code"] == "DT-001"
    assert body["total"] == 40


def test_invalid_page_returns_422(client):
    response = client.get(
        "/api/v1/meters",
        params={"page": 0},
    )

    assert response.status_code == 422
