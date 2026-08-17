import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_success():
    user = User.objects.create_user(
        email="ali@example.com",
        password="strongpass123",
        display_name="Ali Khan"
    )
    assert user.email == "ali@example.com"
    assert user.display_name == "Ali Khan"
    assert user.check_password("strongpass123")
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_user_without_email_raises_error():
    with pytest.raises(ValueError):
        User.objects.create_user(
            email="",
            password="somepass",
            display_name="No Email"
        )


@pytest.mark.django_db
def test_username_auto_generated_from_email():
    user = User.objects.create_user(
        email="test.user@example.com",
        password="pass123",
        display_name="Test User"
    )
    assert user.username == "test_user"


@pytest.mark.django_db
def test_duplicate_username_gets_suffix():
    User.objects.create_user(
        email="ahmed@example.com",
        password="pass123",
        display_name="Ahmed"
    )
    user2 = User.objects.create_user(
        email="ahmed@other.com",
        password="pass456",
        display_name="Ahmed Two"
    )
    assert user2.username != "ahmed"
    assert user2.username.startswith("ahmed_")


@pytest.mark.django_db
def test_email_is_normalized():
    user = User.objects.create_user(
        email="Ali@EXAMPLE.com",
        password="pass123",
        display_name="Ali"
    )
    assert user.email == "Ali@example.com"


@pytest.mark.django_db
def test_create_superuser_success():
    admin = User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass123",
        display_name="Admin"
    )
    assert admin.is_staff is True
    assert admin.is_superuser is True


@pytest.mark.django_db
def test_create_superuser_with_is_staff_false_raises_error():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="admin2@example.com",
            password="adminpass123",
            display_name="Admin2",
            is_staff=False
        )


@pytest.mark.django_db
def test_display_name_is_stripped():
    user = User.objects.create_user(
        email="spacey@example.com",
        password="pass123",
        display_name="   Spacey Name   "
    )
    assert user.display_name == "Spacey Name"

@pytest.mark.django_db
def test_this_will_fail():
    user = User.objects.create_user(
        email="fail@example.com",
        password="pass123",
        display_name="Fail Test"
    )
    assert user.email == "wrong@example.com"


# ---------------------------------------------------------------------------
# Signup + OTP + Login API tests
# ---------------------------------------------------------------------------

import json
import re
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone


def _extract_otp(email_body: str) -> str:
    match = re.search(r"Your OTP is: (\d+)", email_body)
    assert match, f"Could not find OTP in email body: {email_body}"
    return match.group(1)


def _post_json(client, url_name, payload):
    return client.post(
        reverse(url_name),
        data=json.dumps(payload),
        content_type="application/json",
    )


SIGNUP_PAYLOAD = {
    "email": "signuptest@example.com",
    "password": "StrongPass123!",
    "display_name": "Signup Test",
}


@pytest.mark.django_db
def test_signup_creates_inactive_user_and_sends_otp(client, mailoutbox):
    resp = _post_json(client, "signup", SIGNUP_PAYLOAD)

    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["email"] == SIGNUP_PAYLOAD["email"]

    user = User.objects.get(email=SIGNUP_PAYLOAD["email"])
    assert user.is_active is False
    assert "otp" in user.metadata
    assert "otp_expires_at" in user.metadata

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [SIGNUP_PAYLOAD["email"]]


@pytest.mark.django_db
def test_signup_fails_with_short_password(client, mailoutbox):
    resp = _post_json(client, "signup", {**SIGNUP_PAYLOAD, "password": "123"})

    assert resp.status_code == 400
    assert resp.json()["success"] is False
    assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_signup_fails_if_active_user_already_exists(client, mailoutbox):
    User.objects.create_user(
        email=SIGNUP_PAYLOAD["email"],
        password="somepass123",
        display_name="Existing",
        is_active=True,
    )

    resp = _post_json(client, "signup", SIGNUP_PAYLOAD)

    assert resp.status_code == 400
    assert resp.json()["success"] is False
    assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_signup_twice_reuses_pending_inactive_account(client, mailoutbox):
    _post_json(client, "signup", SIGNUP_PAYLOAD)
    _post_json(client, "signup", {**SIGNUP_PAYLOAD, "display_name": "Updated Name"})

    users = User.objects.filter(email=SIGNUP_PAYLOAD["email"])
    assert users.count() == 1
    assert users.first().display_name == "Updated Name"
    assert len(mailoutbox) == 2  # one OTP email per signup call


@pytest.mark.django_db
def test_verify_otp_with_wrong_code_fails(client, mailoutbox):
    _post_json(client, "signup", SIGNUP_PAYLOAD)

    resp = _post_json(client, "verify-signup-otp", {
        "email": SIGNUP_PAYLOAD["email"],
        "otp": "00000000",
    })

    assert resp.status_code == 400
    assert resp.json()["success"] is False

    user = User.objects.get(email=SIGNUP_PAYLOAD["email"])
    assert user.is_active is False


@pytest.mark.django_db
def test_verify_otp_with_correct_code_activates_user_and_returns_tokens(client, mailoutbox):
    _post_json(client, "signup", SIGNUP_PAYLOAD)
    otp = _extract_otp(mailoutbox[0].body)

    resp = _post_json(client, "verify-signup-otp", {
        "email": SIGNUP_PAYLOAD["email"],
        "otp": otp,
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "access" in body["data"]["tokens"]
    assert "refresh" in body["data"]["tokens"]

    user = User.objects.get(email=SIGNUP_PAYLOAD["email"])
    assert user.is_active is True
    assert "otp" not in user.metadata


@pytest.mark.django_db
def test_verify_otp_fails_when_no_pending_signup(client):
    resp = _post_json(client, "verify-signup-otp", {
        "email": "nosignup@example.com",
        "otp": "123456",
    })

    assert resp.status_code == 404
    assert resp.json()["success"] is False


@pytest.mark.django_db
def test_verify_otp_fails_when_expired(client, mailoutbox):
    _post_json(client, "signup", SIGNUP_PAYLOAD)
    otp = _extract_otp(mailoutbox[0].body)

    # Force the OTP to look expired
    user = User.objects.get(email=SIGNUP_PAYLOAD["email"])
    user.metadata["otp_expires_at"] = (timezone.now() - timedelta(seconds=5)).isoformat()
    user.save(update_fields=["metadata"])

    resp = _post_json(client, "verify-signup-otp", {
        "email": SIGNUP_PAYLOAD["email"],
        "otp": otp,
    })

    assert resp.status_code == 400
    assert "expired" in resp.json()["message"].lower()


@pytest.mark.django_db
def test_resend_otp_issues_new_code(client, mailoutbox):
    _post_json(client, "signup", SIGNUP_PAYLOAD)
    first_otp = _extract_otp(mailoutbox[0].body)

    resp = _post_json(client, "resend-otp", {"email": SIGNUP_PAYLOAD["email"]})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert len(mailoutbox) == 2

    second_otp = _extract_otp(mailoutbox[1].body)

    # old otp should no longer work
    resp = _post_json(client, "verify-signup-otp", {
        "email": SIGNUP_PAYLOAD["email"],
        "otp": first_otp,
    })
    assert resp.status_code == 400

    # new otp should work
    resp = _post_json(client, "verify-signup-otp", {
        "email": SIGNUP_PAYLOAD["email"],
        "otp": second_otp,
    })
    assert resp.status_code == 200


@pytest.mark.django_db
def test_resend_otp_fails_when_no_pending_signup(client):
    resp = _post_json(client, "resend-otp", {"email": "nosignup@example.com"})
    assert resp.status_code == 404
    assert resp.json()["success"] is False


@pytest.mark.django_db
def test_login_succeeds_for_verified_user(client):
    user = User.objects.create_user(
        email="logintest@example.com",
        password="LoginPass123!",
        display_name="Login Test",
        is_active=True,
    )

    resp = _post_json(client, "login", {
        "email": "logintest@example.com",
        "password": "LoginPass123!",
    })

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "access" in body["data"]["tokens"]


@pytest.mark.django_db
def test_login_fails_with_wrong_password(client):
    User.objects.create_user(
        email="logintest2@example.com",
        password="LoginPass123!",
        display_name="Login Test 2",
        is_active=True,
    )

    resp = _post_json(client, "login", {
        "email": "logintest2@example.com",
        "password": "WrongPass!",
    })

    assert resp.status_code == 401
    assert resp.json()["success"] is False


@pytest.mark.django_db
def test_login_fails_for_unverified_user(client):
    User.objects.create_user(
        email="unverified@example.com",
        password="LoginPass123!",
        display_name="Unverified",
        is_active=False,
    )

    resp = _post_json(client, "login", {
        "email": "unverified@example.com",
        "password": "LoginPass123!",
    })

    assert resp.status_code == 403
    assert resp.json()["success"] is False


@pytest.mark.django_db
def test_login_fails_for_nonexistent_email(client):
    resp = _post_json(client, "login", {
        "email": "doesnotexist@example.com",
        "password": "whatever123",
    })

    assert resp.status_code == 401
    assert resp.json()["success"] is False