from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from support_agent.core.config import settings
from support_agent.core.security import (
    JWTVerificationError,
    authenticated_user_from_claims,
    verify_jwt,
)
from support_agent.schemas.context import AuthenticatedUser


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer authentication required")

    try:
        claims = verify_jwt(credentials.credentials, settings)
        return authenticated_user_from_claims(claims)
    except JWTVerificationError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired bearer token") from exc
