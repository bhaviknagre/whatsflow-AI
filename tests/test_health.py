from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "database": "healthy",
        },
    }


def test_health_reports_unhealthy_database() -> None:
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise SQLAlchemyError("connection refused")

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    try:
        response = client.get("/api/v1/health")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "database": "unhealthy",
        },
    }