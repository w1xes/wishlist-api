from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import Base, Wish, get_engine
from app.main import app, cors_origins

client = TestClient(app)


def test_health_without_database(monkeypatch):
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_list_and_delete_in_postgres():
    engine = get_engine()
    assert engine.dialect.name == "postgresql"
    Base.metadata.create_all(engine)

    response = client.post("/items", json={"title": "  Настільна лампа  "})
    assert response.status_code == 201
    item = response.json()
    try:
        assert item["title"] == "Настільна лампа"
        with Session(engine) as session:
            assert session.get(Wish, item["id"]).title == "Настільна лампа"

        response = client.get("/items")
        assert response.status_code == 200
        assert item in response.json()
    finally:
        assert client.delete(f"/items/{item['id']}").status_code == 204

    with Session(engine) as session:
        assert session.get(Wish, item["id"]) is None


def test_postgres_and_redis_are_ready():
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"postgres": "ok", "redis": "ok"}


def test_reject_blank_title():
    response = client.post("/items", json={"title": "   "})

    assert response.status_code == 422


def test_cors_origins_splits_and_trims_list():
    assert cors_origins(" http://localhost:8081, http://127.0.0.1:8081 ,,") == [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ]


def test_cors_origins_default_when_unset_or_blank():
    assert cors_origins(None) == ["http://127.0.0.1:5174"]
    assert cors_origins(" , ") == ["http://127.0.0.1:5174"]
