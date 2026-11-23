from fastapi import FastAPI
from fastapi.testclient import TestClient

from support_agent.core.config import settings
from support_agent.main import app, create_app
from support_agent.schemas.requests import ChatRequest


def test_create_app_returns_fastapi_instance():
    application = create_app()

    assert isinstance(application, FastAPI)
    assert application.title == settings.app_name


def test_application_entry_point_is_initialized():
    assert isinstance(app, FastAPI)
    assert app.title == settings.app_name


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_structured_not_found_error():
    with TestClient(app) as client:
        response = client.get("/unknown")

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert response.json()["message"] == "Not Found"


def test_validation_error_returns_structured_response():
    application = create_app()

    @application.post("/validation-test")
    def validation_test(request: ChatRequest):
        return {"message": request.message}

    with TestClient(application) as client:
        response = client.post("/validation-test", json={"message": " "})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "Request validation failed"
    assert body["details"]
