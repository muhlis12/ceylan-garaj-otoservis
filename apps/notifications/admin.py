from django.contrib import admin
from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "channel", "to", "status", "provider", "created_at")
    list_filter = ("branch", "channel", "status", "provider")
    search_fields = ("to", "message", "error")
