from django.contrib.auth.base_user import BaseUserManager

from common.phone import normalize_phone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone, name, email=""):
        """Customer: normalized phone, unusable password."""
        user = self.model(
            phone=normalize_phone(phone), name=name, email=self.normalize_email(email)
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, name, password):
        user = self.model(
            phone=normalize_phone(phone),
            name=name,
            is_staff=True,
            is_superuser=True,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
