from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from common.fields import PhoneField

from .models import User
from .tokens import AppRefreshToken


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "phone", "email", "default_address", "area", "is_staff"]
        read_only_fields = ["id", "phone", "is_staff"]
        extra_kwargs = {
            "name": {
                "min_length": 2,
                "error_messages": {
                    "min_length": "الاسم لازم يكون حرفين على الأقل",
                    "max_length": "الاسم طويل أوي (80 حرف بحد أقصى)",
                    "required": "اكتب اسمك",
                    "blank": "اكتب اسمك",
                },
            },
            "email": {"error_messages": {"invalid": "اكتب إيميل صحيح"}},
        }


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(
        min_length=2,
        max_length=80,
        error_messages={
            "min_length": "الاسم لازم يكون حرفين على الأقل",
            "max_length": "الاسم طويل أوي (80 حرف بحد أقصى)",
            "required": "اكتب اسمك",
            "blank": "اكتب اسمك",
        },
    )
    phone = PhoneField()
    email = serializers.EmailField(
        required=False, allow_blank=True, error_messages={"invalid": "اكتب إيميل صحيح"}
    )


class LoginSerializer(serializers.Serializer):
    phone = PhoneField()


class AdminLoginSerializer(serializers.Serializer):
    # Plain strings on purpose: any failure returns the same 401.
    phone = serializers.CharField(allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False, allow_blank=True)


class AuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class RefreshSerializer(TokenRefreshSerializer):
    token_class = AppRefreshToken


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
