from typing import Any

import jwt
from jwt import InvalidTokenError

from support_agent.core.config import Settings


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
