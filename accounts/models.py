import re
import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager, PermissionsMixin

# Create your models here.

def generate_user_name_from_email(email:str) -> str:
    """
    generate safe username from email.
    Allowed chars A-Z and 1-9  underscore
    """
    base = email.split('@')[0]
    base = re.sub(r'[^A-Za-z0-9_]', '_', base)
    base = base.strip('_')

    if not base:
        base = "user"

    while User.objects.filter(username=base).exists():
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"{base}_{suffix}"
        base = username

    return base     

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, display_name=None, **extra_fileds):
        if not email:
            raise ValueError("Email is required")
        
        email = self.normalize_email(email)
        username = generate_user_name_from_email(email)

        user = self.model(
            email = email,
            username = username,
            display_name=(display_name or "").strip(), **extra_fileds
        )
       
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, display_name=None, **extra_fileds):
        extra_fileds.setdefault('is_staff', True)
        extra_fileds.setdefault('is_superuser', True)
        extra_fileds.setdefault('is_active', True)

        if extra_fileds.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff True")
        if extra_fileds.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser True")
        
        return self.create_user(email, password, display_name, **extra_fileds)

class User(AbstractUser, PermissionsMixin):

    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, blank=True)
    display_name = models.CharField(max_length=150, blank=False)
    metadata = models.JSONField(
        blank = True,
        default=dict,
        help_text='Arbitrary json; signup OTP use key: otp, otp_created_at, otp_expired_at'
    )

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    def save(self, *args, **kwargs):
        if self.display_name:
            self.display_name = self.display_name.strip()
        
        if not self.username:
            self.username = generate_user_name_from_email(self.email)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name or self.username or self.email