from django.conf import settings
from django.db import models


class Branch(models.Model):
    """Sube"""

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BranchMembership(models.Model):
    """Kullanicinin hangi subelerde calisacagini belirler."""

    ROLE_ADMIN = "ADMIN"
    ROLE_MANAGER = "MANAGER"
    ROLE_TECH = "TECH"
    ROLE_WASH = "WASH"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_MANAGER, "Yonetici"),
        (ROLE_TECH, "Usta"),
        (ROLE_WASH, "Personel (Yikama)"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_WASH)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "branch")

    def __str__(self):
        return f"{self.user} @ {self.branch}"
