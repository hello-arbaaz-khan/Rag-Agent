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