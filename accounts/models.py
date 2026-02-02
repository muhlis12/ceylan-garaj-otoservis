from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_ADMIN = "ADMIN"
    ROLE_WORKER = "WORKER"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_WORKER, "Usta"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_WORKER)
