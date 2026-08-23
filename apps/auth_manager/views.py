from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from apps.auth_manager.permission import IsAuthenticatedAndVerified
from apps.shared.json_response import response_json
from apps.auth_manager.serializers import (
    SignupSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    VerifyOtpGenericSerializer,
)
from apps.auth_manager.utils import (
    set_otp,
    verify_otp,
    clear_otp,
    send_otp_email,
    set_password_reset_otp,
    verify_password_reset_otp,
    clear_password_reset_otp,
    send_password_reset_otp_email,
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

        otp = set_otp(user)  # <-- shared OTP function, purpose="signup"

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

        is_valid, message = verify_otp(user, otp)  # <-- shared OTP function
        if not is_valid:
            return response_json(success=False, message=message, status=400)

        user.is_active = True
        user.save(update_fields=["is_active"])
        clear_otp(user)  # <-- shared OTP function (single-use)

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

        otp = set_otp(user)  # <-- shared OTP function

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

class LogoutView(APIView):
    permission_classes = [IsAuthenticatedAndVerified]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return response_json(
                success=True,
                message="Logout successful.",
                status=200,
            )
        except Exception:
            return response_json(
                success=False,
                message="Invalid refresh token.",
                status=400,
            )

class ForgotPasswordView(APIView):
    """
    Step 1 of the forgot-password flow: given an email, send an OTP.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status=400,
            )

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email, is_active=True).first()

        if user:
            otp = set_password_reset_otp(user)  # <-- shared OTP function, purpose="password_reset"
            try:
                send_password_reset_otp_email(user, otp)
            except Exception:
                return response_json(
                    success=False,
                    message="Could not send OTP email. Please try again.",
                    status=502,
                )

        return response_json(
            success=True,
            message="If an account with that email exists, an OTP has been sent.",
            data={"email": email},
            status=200,
        )


class ResetPasswordView(APIView):
    """
    Step 2 of the forgot-password flow: verify the OTP and set a new password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status=400,
            )

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        user = User.objects.filter(email=email, is_active=True).first()
        if not user:
            return response_json(
                success=False,
                message="No account found for this email.",
                status=404,
            )

        is_valid, message = verify_password_reset_otp(user, otp)  # <-- shared OTP function
        if not is_valid:
            return response_json(success=False, message=message, status=400)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        clear_password_reset_otp(user)  # <-- shared OTP function (single-use)

        return response_json(
            success=True,
            message="Password has been reset successfully. Please log in with your new password.",
            status=200,
        )


class ChangePasswordView(APIView):
    """
    For an authenticated user to change their password by supplying
    their current password and a new one.
    """
    permission_classes = [IsAuthenticatedAndVerified]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status=400,
            )

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]
        confirm_new_password = serializer.validated_data["confirm_new_password"]
        if new_password != confirm_new_password:
            return response_json(
                success=False,
                message="New password and confirm new password do not match.",
                status=400,
            )

        user = request.user

        if not user.check_password(old_password):
            return response_json(
                success=False,
                message="Old password is incorrect.",
                status=400,
            )

        if old_password == new_password:
            return response_json(
                success=False,
                message="New password must be different from the old password.",
                status=400,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return response_json(
            success=True,
            message="Password changed successfully.",
            status=200,
        )

class VerifyOtpGenericView(APIView):
    """
    Generic "is this OTP valid" check for {email, purpose, otp}.
    """
    permission_classes = [AllowAny]
 
    def post(self, request):
        serializer = VerifyOtpGenericSerializer(data=request.data)
        if not serializer.is_valid():
            return response_json(
                success=False,
                message="Validation failed",
                errors=serializer.errors,
                status=400,
            )
 
        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]
        otp = serializer.validated_data["otp"]
 
        if purpose == "signup":
            # Signup OTPs belong to accounts that are not yet activated.
            user = User.objects.filter(email=email, is_active=False).first()
        else:
            # password_reset OTPs belong to already-active accounts.
            user = User.objects.filter(email=email, is_active=True).first()
 
        if not user:
            return response_json(
                success=False,
                message="No account found for this email and purpose.",
                status=404,
            )
 
        is_valid, message = verify_otp(user, otp, purpose=purpose)
        if not is_valid:
            return response_json(success=False, message=message, status=400)
 
        return response_json(
            success=True,
            message="OTP verified successfully.",
            data={"email": email, "purpose": purpose},
            status=200,
        )