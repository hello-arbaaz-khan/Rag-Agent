from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from apps.shared.json_response import response_json
from apps.auth_manager.serializers import (
    SignupSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    LoginSerializer,
)
from apps.auth_manager.utils import (
    set_user_otp,
    verify_user_otp,
    clear_user_otp,
    send_otp_email,
)

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class SignupView(APIView):
    """
    Step 1 of signup: create an INACTIVE user and email them an OTP.
    If the email already has a pending (inactive) signup, reuse that
    account and just issue a fresh OTP instead of erroring out.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status=400,
            )

        data = serializer.validated_data
        email = data["email"]

        user = User.objects.filter(email=email, is_active=False).first()
        if user:
            # Pending signup exists — update password/display_name and resend OTP
            user.set_password(data["password"])
            user.display_name = data.get("display_name", user.display_name)
            user.save(update_fields=["password", "display_name"])
        else:
            user = User.objects.create_user(
                email=email,
                password=data["password"],
                display_name=data.get("display_name", ""),
                is_active=False,
            )

        otp = set_user_otp(user)

        try:
            send_otp_email(user, otp)
        except Exception:
            return response_json(
                success=False,
                message="Could not send OTP email. Please try again.",
                status=502,
            )

        return response_json(
            success=True,
            message="OTP sent to your email. Please verify to complete signup.",
            data={"email": user.email},
            status=201,
        )


class VerifySignupOTPView(APIView):
    """
    Step 2 of signup: verify the OTP, activate the user, and return JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status=400,
            )

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        user = User.objects.filter(email=email, is_active=False).first()
        if not user:
            return response_json(
                success=False,
                message="No pending signup found for this email.",
                status=404,
            )

        is_valid, message = verify_user_otp(user, otp)
        if not is_valid:
            return response_json(success=False, message=message, status=400)

        user.is_active = True
        user.save(update_fields=["is_active"])
        clear_user_otp(user)

        tokens = get_tokens_for_user(user)

        return response_json(
            success=True,
            message="Account verified successfully.",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "display_name": user.display_name,
                },
                "tokens": tokens,
            },
            status=200,
        )


class ResendOTPView(APIView):
    """Resend a fresh OTP for a pending (inactive) signup."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status=400,
            )

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email, is_active=False).first()
        if not user:
            return response_json(
                success=False,
                message="No pending signup found for this email.",
                status=404,
            )

        otp = set_user_otp(user)

        try:
            send_otp_email(user, otp)
        except Exception:
            return response_json(
                success=False,
                message="Could not send OTP email. Please try again.",
                status=502,
            )

        return response_json(
            success=True,
            message="A new OTP has been sent to your email.",
            data={"email": user.email},
            status=200,
        )


class LoginView(APIView):
    """Login with email + password, returns JWT access & refresh tokens."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status=400,
            )

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            return response_json(
                success=False,
                message="Invalid email or password.",
                status=401,
            )

        if not user.is_active:
            return response_json(
                success=False,
                message="Account not verified. Please complete OTP verification.",
                status=403,
            )

        tokens = get_tokens_for_user(user)

        return response_json(
            success=True,
            message="Login successful.",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "display_name": user.display_name,
                },
                "tokens": tokens,
            },
            status=200,
        )