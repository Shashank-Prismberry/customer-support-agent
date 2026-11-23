from typing import Any

import jwt
from pydantic import ValidationError
from jwt import InvalidTokenError

from support_agent.core.config import Settings
from support_agent.schemas.context import AuthenticatedUser


class JWTVerificationError(Exception):
    pass


def verify_jwt(token: str, config: Settings) -> dict[str, Any]:
    if config.jwt_secret_key is None:
        raise JWTVerificationError("JWT secret is not configured")
    if not config.jwt_issuer or not config.jwt_audience:
        raise JWTVerificationError("JWT issuer and audience must be configured")

    try:
        return jwt.decode(
            token,
            config.jwt_secret_key.get_secret_value(),
            algorithms=["HS256"],
            issuer=config.jwt_issuer,
            audience=config.jwt_audience,
            options={
                "require": ["exp", "iss", "aud"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
    except InvalidTokenError as exc:
        raise JWTVerificationError("JWT verification failed") from exc


def authenticated_user_from_claims(claims: dict[str, Any]) -> AuthenticatedUser:
    try:
        return AuthenticatedUser(
            user_id=claims["sub"],
            customer_id=claims["customer_id"],
            org_id=claims["org_id"],
            role=claims["role"],
            email=claims["email"],
        )
    except KeyError as exc:
        raise JWTVerificationError(f"Missing identity claim: {exc.args[0]}") from exc
    except ValidationError as exc:
        raise JWTVerificationError("Invalid identity claims") from exc
