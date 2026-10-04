from __future__ import annotations

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "core.settings",
)

import django

django.setup()

from django.contrib.auth import get_user_model

from rest_framework_simplejwt.exceptions import (
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken

security = HTTPBearer(
    scheme_name="Django JWT",
    bearerFormat="JWT",
)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
) -> int:
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = AccessToken(
            credentials.credentials
        )

        user_id = token.get(
            api_settings.USER_ID_CLAIM
        )

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user identifier.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = get_user_model().objects.filter(
            pk=user_id,
            is_active=True,
        ).only("pk").first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return int(user.pk)

    except (
        InvalidToken,
        TokenError,
        ValueError,
        TypeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc