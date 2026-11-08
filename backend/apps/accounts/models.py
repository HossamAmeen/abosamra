from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField("الموبايل", max_length=11, unique=True)
    name = models.CharField("الاسم", max_length=80)
    email = models.EmailField("الإيميل", blank=True)
    default_address = models.TextField("العنوان الافتراضي", blank=True)
    area = models.CharField("المنطقة", max_length=80, blank=True)
    is_staff = models.BooleanField("موظف", default=False)
    is_active = models.BooleanField("نشط", default=True)
    date_joined = models.DateTimeField("تاريخ التسجيل", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمين"

    def __str__(self):
        return f"{self.name} ({self.phone})"
