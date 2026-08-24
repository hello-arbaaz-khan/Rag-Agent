from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=4, max_length=4)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ForgotPasswordSerializer(serializers.Serializer):
    """Step 1 of the forgot-password flow: request an OTP by email."""
    email = serializers.EmailField()
 
 
class ResetPasswordSerializer(serializers.Serializer):
    """Step 2 of the forgot-password flow: verify OTP and set a new password."""
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=4, max_length=4)
    new_password = serializers.CharField(write_only=True, min_length=8)
 
    def validate_new_password(self, value):
        validate_password(value)
        return value
 
 
class ChangePasswordSerializer(serializers.Serializer):
    """For an already-authenticated user changing their own password."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True, min_length=8)
 
    def validate_new_password(self, value):
        validate_password(value)
        return value
    
class VerifyOtpGenericSerializer(serializers.Serializer):
    """
    Generic OTP-check serializer.
    """
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=["signup", "password_reset"], default="password_reset")
    otp = serializers.CharField(min_length=4, max_length=4)

class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()