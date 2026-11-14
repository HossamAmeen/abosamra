from rest_framework import status

from common.exceptions import ApiError

from .models import User
from .tokens import issue_tokens  # noqa: F401  (re-exported for views)


def phone_exists_error():
    return ApiError("الرقم ده عنده حساب، ادخل بيه", "phone_exists", status.HTTP_409_CONFLICT)


def register_customer(name, phone, email=""):
    if User.objects.filter(phone=phone).exists():
        raise phone_exists_error()
    return User.objects.create_user(phone=phone, name=name, email=email)


def staff_phone_exists_error():
    return ApiError("الرقم ده مسجل قبل كده", "phone_exists", status.HTTP_409_CONFLICT)


def create_staff(name, phone, password):
    """New dashboard admin, with the same rights as the seeded owner account."""
    if User.objects.filter(phone=phone).exists():
        raise staff_phone_exists_error()
    return User.objects.create_superuser(phone=phone, name=name, password=password)


def get_customer_by_phone(phone):
    user = User.objects.filter(phone=phone, is_active=True, is_staff=False).first()
    if user is None:
        raise ApiError("مفيش حساب بالرقم ده", "not_found", status.HTTP_404_NOT_FOUND)
    return user
