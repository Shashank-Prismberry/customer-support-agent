from datetime import datetime, timedelta, timezone

import jwt
import pytest

from support_agent.core.config import Settings
from support_agent.core.security import (
    JWTVerificationError,
    authenticated_user_from_claims,
    verify_jwt,
)
from support_agent.schemas.context import UserRole


SECRET = "test-jwt-secret-at-least-32-bytes"
ISSUER = "support-ai-backend"
AUDIENCE = "support-ai-services"


def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        jwt_secret_key=SECRET,
        jwt_issuer=ISSUER,
        jwt_audience=AUDIENCE,
    )


def make_token(**claims) -> str:
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "customer_id": "10000000-0000-0000-0000-000000000001",
        "org_id": "20000000-0000-0000-0000-000000000001",
        "role": "Org_Admin",
        "email": "alice@example.com",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    payload.update(claims)
    return jwt.encode(payload, SECRET, algorithm="HS256")


def make_token_without_claim(claim: str) -> str:
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    payload.pop(claim)
    return jwt.encode(payload, SECRET, algorithm="HS256")


def test_verify_jwt_accepts_valid_hs256_token():
    claims = verify_jwt(make_token(), make_settings())

    assert claims["sub"] == "00000000-0000-0000-0000-000000000001"
    assert claims["org_id"] == "20000000-0000-0000-0000-000000000001"
    assert claims["role"] == "Org_Admin"


def test_verify_jwt_rejects_wrong_signature():
    token = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "wrong-jwt-secret-at-least-32-bytes",
        algorithm="HS256",
    )

    with pytest.raises(JWTVerificationError):
        verify_jwt(token, make_settings())


def test_verify_jwt_rejects_expired_token():
    token = make_token(exp=datetime.now(timezone.utc) - timedelta(minutes=1))

    with pytest.raises(JWTVerificationError):
        verify_jwt(token, make_settings())


def test_verify_jwt_rejects_wrong_issuer():
    with pytest.raises(JWTVerificationError):
        verify_jwt(make_token(iss="wrong-issuer"), make_settings())


def test_verify_jwt_rejects_wrong_audience():
    with pytest.raises(JWTVerificationError):
        verify_jwt(make_token(aud="wrong-audience"), make_settings())


def test_verify_jwt_rejects_non_hs256_algorithm():
    token = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "different-key-used-only-for-rejecting-non-hs256-algorithm",
        algorithm="HS384",
    )

    with pytest.raises(JWTVerificationError):
        verify_jwt(token, make_settings())


def test_verify_jwt_requires_configured_secret():
    config = Settings(_env_file=None, jwt_secret_key=None)

    with pytest.raises(JWTVerificationError, match="secret is not configured"):
        verify_jwt(make_token(), config)


@pytest.mark.parametrize("claim", ["exp", "iss", "aud"])
def test_verify_jwt_rejects_missing_required_claim(claim):
    with pytest.raises(JWTVerificationError):
        verify_jwt(make_token_without_claim(claim), make_settings())


def test_verify_jwt_rejects_malformed_token():
    with pytest.raises(JWTVerificationError):
        verify_jwt("not-a-jwt", make_settings())


def test_verify_jwt_rejects_none_algorithm():
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    token = jwt.encode(payload, key="", algorithm="none")

    with pytest.raises(JWTVerificationError):
        verify_jwt(token, make_settings())


def test_verify_jwt_requires_configured_issuer_and_audience():
    config = Settings(
        _env_file=None,
        jwt_secret_key=SECRET,
        jwt_issuer="",
        jwt_audience="",
    )

    with pytest.raises(JWTVerificationError, match="issuer and audience"):
        verify_jwt(make_token(), config)


def test_authenticated_user_maps_verified_claims():
    claims = verify_jwt(make_token(), make_settings())

    user = authenticated_user_from_claims(claims)

    assert str(user.user_id) == "00000000-0000-0000-0000-000000000001"
    assert str(user.customer_id) == "10000000-0000-0000-0000-000000000001"
    assert str(user.org_id) == "20000000-0000-0000-0000-000000000001"
    assert user.role == UserRole.ORG_ADMIN
    assert user.email == "alice@example.com"


@pytest.mark.parametrize("claim", ["sub", "customer_id", "org_id", "role", "email"])
def test_authenticated_user_rejects_missing_identity_claim(claim):
    claims = verify_jwt(make_token(), make_settings())
    claims.pop(claim)

    with pytest.raises(JWTVerificationError, match="Missing identity claim"):
        authenticated_user_from_claims(claims)


@pytest.mark.parametrize(
    ("claim", "value"),
    [
        ("sub", "not-a-uuid"),
        ("customer_id", "not-a-uuid"),
        ("org_id", "not-a-uuid"),
        ("role", "Unknown_Role"),
    ],
)
def test_authenticated_user_rejects_invalid_identity_claim(claim, value):
    claims = verify_jwt(make_token(), make_settings())
    claims[claim] = value

    with pytest.raises(JWTVerificationError, match="Invalid identity claims"):
        authenticated_user_from_claims(claims)
