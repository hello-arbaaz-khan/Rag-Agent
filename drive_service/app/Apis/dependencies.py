from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import get_current_user_id


bearer_scheme = HTTPBearer(
    scheme_name="Django JWT",
    bearerFormat="JWT",
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
):
    """
    Resolve the Django user from the existing Django-issued JWT.

    Django remains responsible for creating the token.
    FastAPI is responsible for validating the request and
    resolving the authenticated user.
    """

    return get_current_user_id(credentials)