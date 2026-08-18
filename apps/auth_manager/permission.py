from rest_framework.permissions import BasePermission


class IsAuthenticatedAndVerified(BasePermission):
    """
    Allows access only to users who are:
      1. Authenticated (valid JWT access token), AND
      2. Active (is_active=True — i.e. they completed OTP verification).

    Use this instead of DRF's plain IsAuthenticated wherever an endpoint
    should be blocked for users who signed up but never verified their OTP.
    Unverified users technically don't have valid JWT tokens yet (tokens are
    only issued after verify-otp), so this is mostly a defence-in-depth
    check in case a token somehow exists for an inactive account.
    """

    message = "You must be logged in with a verified account to access this."

    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        user = request.user
        return bool(user and user.is_authenticated and user.is_active)