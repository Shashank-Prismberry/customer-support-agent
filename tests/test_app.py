from fastapi import FastAPI
from fastapi.testclient import TestClient

from support_agent.core.config import settings
from support_agent.main import app, create_app


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
