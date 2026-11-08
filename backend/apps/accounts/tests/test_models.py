import pytest

from apps.accounts.models import User


@pytest.mark.django_db
def test_create_user_normalizes_phone_and_unusable_password():
    u = User.objects.create_user("+201012345678", "أحمد")
    assert u.phone == "01012345678"
    assert not u.has_usable_password()
    assert not u.is_staff and u.is_active


@pytest.mark.django_db
def test_create_superuser_has_password_and_flags():
    u = User.objects.create_superuser("٠١١١٢٣٤٥٦٧٨", "Admin", "pw-12345")
    assert u.phone == "01112345678"
    assert u.is_staff and u.is_superuser and u.check_password("pw-12345")


def test_username_field_is_phone():
    assert User.USERNAME_FIELD == "phone"


@pytest.mark.django_db
def test_create_user_rejects_bad_phone():
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        User.objects.create_user("123", "x")


@pytest.mark.django_db
def test_str(customer):
    assert "01012345678" in str(customer)
