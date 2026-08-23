import random
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

OTP_LENGTH = 4
OTP_EXPIRY_SECONDS = getattr(settings, "OTP_EXPIRY_SECONDS", 120)

# Subjects/messages per purpose. Add a new entry here to support a new
# OTP-gated action without touching the core generate/verify/clear logic.
OTP_EMAIL_COPY = {
    "signup": {
        "subject": "Your verification code",
        "intro": "",
    },
    "password_reset": {
        "subject": "Your password reset code",
        "intro": "We received a request to reset your password.\n",
    },
}


def generate_otp(length: int = OTP_LENGTH) -> str:
    """Generate a numeric OTP string, e.g. '4829'."""
    return "".join(random.choices("0123456789", k=length))


def _otp_keys(purpose: str):
    """Metadata key names for a given purpose."""
    prefix = "otp" if purpose == "signup" else f"{purpose}_otp"
    return prefix, f"{prefix}_created_at", f"{prefix}_expires_at"


def set_otp(user, purpose: str = "signup") -> str:
    """
    Generate a fresh OTP for the given purpose.
    """
    otp_key, created_key, expires_key = _otp_keys(purpose)

    otp = generate_otp()
    now = timezone.now()
    expires_at = now + timedelta(seconds=OTP_EXPIRY_SECONDS)

    user.metadata = user.metadata or {}
    user.metadata[otp_key] = make_password(otp)
    user.metadata[created_key] = now.isoformat()
    user.metadata[expires_key] = expires_at.isoformat()
    user.save(update_fields=["metadata"])

    return otp


def verify_otp(user, otp_input: str, purpose: str = "signup"):
    """
    Validate the submitted OTP against what's stored on user.metadata for
    the given purpose.
    """
    otp_key, _, expires_key = _otp_keys(purpose)
    metadata = user.metadata or {}
    stored_hash = metadata.get(otp_key)
    expires_at_str = metadata.get(expires_key)

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


def clear_otp(user, purpose: str = "signup"):
    """Remove OTP data for the given purpose from user.metadata."""
    otp_key, created_key, expires_key = _otp_keys(purpose)
    metadata = user.metadata or {}
    metadata.pop(otp_key, None)
    metadata.pop(created_key, None)
    metadata.pop(expires_key, None)
    user.metadata = metadata
    user.save(update_fields=["metadata"])


def send_otp_by_email(user, otp: str, purpose: str = "signup"):
    """Send the OTP to the user's email via configured SMTP backend."""
    # otp = otp
    # if settings.DEBUG:
    #     print(f"OTP for {user.email}: {otp}")
    copy = OTP_EMAIL_COPY.get(purpose, OTP_EMAIL_COPY["signup"])
    message = (
        f"Hi {user.display_name or user.username}\n\n"
        f"{copy['intro']}"
        f"Your OTP is: {otp}\n"
        f"It will expire in {OTP_EXPIRY_SECONDS} seconds.\n\n"
        f"If you didn't request this, you can ignore this email."
    )
    send_mail(
        subject=copy["subject"],
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


# ---------------------------------------------------------------------------
# Thin, purpose-bound wrappers.
#
# These just call the generic functions above with a fixed `purpose`, so
# existing call sites (views.py) don't need to pass "signup" /
# "password_reset" everywhere and read a bit more naturally.
# ---------------------------------------------------------------------------

def set_user_otp(user) -> str:
    return set_otp(user, purpose="signup")


def verify_user_otp(user, otp_input: str):
    return verify_otp(user, otp_input, purpose="signup")


def clear_user_otp(user):
    return clear_otp(user, purpose="signup")


def send_otp_email(user, otp: str):
    return send_otp_by_email(user, otp, purpose="signup")


def set_password_reset_otp(user) -> str:
    return set_otp(user, purpose="password_reset")


def verify_password_reset_otp(user, otp_input: str):
    return verify_otp(user, otp_input, purpose="password_reset")


def clear_password_reset_otp(user):
    return clear_otp(user, purpose="password_reset")


def send_password_reset_otp_email(user, otp: str):
    return send_otp_by_email(user, otp, purpose="password_reset")