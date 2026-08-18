# utils/response.py

import random
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

OTP_LENGTH = 4
OTP_EXPIRY_SECONDS = getattr(settings, "OTP_EXPIRY_SECONDS", 120)


def generate_otp(length: int = OTP_LENGTH) -> str:
    """Generate a numeric OTP string, e.g. '482913'."""
    return "".join(random.choices("0123456789", k=length))


def set_user_otp(user) -> str:
    """
    Generate a fresh OTP, store its hash + timestamps on user.metadata,
    save the user, and return the PLAIN otp (only for sending in the email —
    never store or return the plain value anywhere else).
    """
    otp = generate_otp()
    now = timezone.now()
    expires_at = now + timedelta(seconds=OTP_EXPIRY_SECONDS)

    user.metadata = user.metadata or {}
    user.metadata["otp"] = make_password(otp)
    user.metadata["otp_created_at"] = now.isoformat()
    user.metadata["otp_expires_at"] = expires_at.isoformat()
    user.save(update_fields=["metadata"])

    return otp


def verify_user_otp(user, otp_input: str):
    """
    Validate the submitted OTP against what's stored on user.metadata.
    Returns (is_valid: bool, message: str).
    """
    metadata = user.metadata or {}
    stored_hash = metadata.get("otp")
    expires_at_str = metadata.get("otp_expires_at")

    if not stored_hash or not expires_at_str:
        return False, "No OTP was requested for this account."

    expires_at = timezone.datetime.fromisoformat(expires_at_str)
    if timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(expires_at)

    if timezone.now() > expires_at:
        return False, "OTP has expired. Please request a new one."

    if not check_password(otp_input, stored_hash):
        return False, "Invalid OTP."

    return True, "OTP verified successfully."


def clear_user_otp(user):
    """Remove OTP data from user.metadata after successful verification."""
    metadata = user.metadata or {}
    metadata.pop("otp", None)
    metadata.pop("otp_created_at", None)
    metadata.pop("otp_expires_at", None)
    user.metadata = metadata
    user.save(update_fields=["metadata"])


def send_otp_email(user, otp: str):
    """Send the OTP to the user's email via configured SMTP backend."""
    subject = "Your verification code"
    message = (
        f"Hi {user.display_name or user.username},\n\n"
        f"Your OTP is: {otp}\n"
        f"It will expire in {OTP_EXPIRY_SECONDS} seconds.\n\n"
        f"If you didn't request this, you can ignore this email."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )