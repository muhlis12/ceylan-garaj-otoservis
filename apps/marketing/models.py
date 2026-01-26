from django.db import models
from django.conf import settings
from apps.core.models import Branch

class WhatsAppClickLog(models.Model):
    TYPE_OPEN = "OPEN"
    TYPE_CAMPAIGN = "CAMPAIGN"
    TYPE_CHOICES = [
        (TYPE_OPEN, "Tek Tık Aç"),
        (TYPE_CAMPAIGN, "Toplu Mesaj"),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    message = models.TextField()

    # ✅ EKLENENLER
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_OPEN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone} - {self.message_type} - {self.created_at:%d.%m.%Y %H:%M}"
