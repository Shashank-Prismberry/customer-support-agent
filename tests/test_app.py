from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI
from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import SecretStr

from support_agent.core.config import settings
from support_agent.api.dependencies import get_current_user
from support_agent.main import app, create_app
from support_agent.schemas.context import AuthenticatedUser
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


def make_access_token(**claims) -> str:
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "customer_id": "10000000-0000-0000-0000-000000000001",
        "org_id": "20000000-0000-0000-0000-000000000001",
        "role": "Org_Admin",
        "email": "alice@example.com",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    payload.update(claims)
    secret = settings.jwt_secret_key
    assert secret is not None
    return jwt.encode(payload, secret.get_secret_value(), algorithm="HS256")


def test_authentication_dependency_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        SecretStr("test-jwt-secret-at-least-32-bytes"),
    )
    application = create_app()

    @application.get("/auth-test")
    def auth_test(user: AuthenticatedUser = Depends(get_current_user)):
        return {"user_id": str(user.user_id), "org_id": str(user.org_id)}

    token = make_access_token()
    with TestClient(application) as client:
        response = client.get("/auth-test", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["user_id"] == "00000000-0000-0000-0000-000000000001"


def test_authentication_dependency_rejects_missing_token():
    application = create_app()

    @application.get("/auth-test")
    def auth_test(user: AuthenticatedUser = Depends(get_current_user)):
        return {"user_id": str(user.user_id)}

    with TestClient(application) as client:
        response = client.get("/auth-test")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_authentication_dependency_rejects_invalid_token():
    application = create_app()

    @application.get("/auth-test")
    def auth_test(user: AuthenticatedUser = Depends(get_current_user)):
        return {"user_id": str(user.user_id)}

    with TestClient(application) as client:
        response = client.get(
            "/auth-test",
            headers={"Authorization": "Bearer not-a-jwt"},
        )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_authentication_dependency_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        SecretStr("test-jwt-secret-at-least-32-bytes"),
    )
    application = create_app()

    @application.get("/auth-test")
    def auth_test(user: AuthenticatedUser = Depends(get_current_user)):
        return {"user_id": str(user.user_id)}

    token = make_access_token(exp=datetime.now(timezone.utc) - timedelta(minutes=1))
    with TestClient(application) as client:
        response = client.get(
            "/auth-test",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"
