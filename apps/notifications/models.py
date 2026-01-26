from django.db import models
from apps.core.models import Branch


class NotificationLog(models.Model):
    CHANNEL_SMS = "SMS"
    CHANNEL_WHATSAPP = "WHATSAPP"
    CHANNEL_CHOICES = [(CHANNEL_SMS, "SMS"), (CHANNEL_WHATSAPP, "WhatsApp")]

    STATUS_PENDING = "PENDING"
    STATUS_SENT = "SENT"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [(STATUS_PENDING, "Beklemede"), (STATUS_SENT, "Gonderildi"), (STATUS_FAILED, "Basarisiz")]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    to = models.CharField(max_length=80)
    message = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    provider = models.CharField(max_length=40, blank=True)
    provider_message_id = models.CharField(max_length=120, blank=True)
    error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.channel} -> {self.to} ({self.status})"
