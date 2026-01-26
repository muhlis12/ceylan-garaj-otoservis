from django.contrib import admin
from .models import TireHotelEntry


@admin.register(TireHotelEntry)
class TireHotelEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "plate_text", "customer", "season", "qty", "rack_code", "slot_code", "is_active", "created_at")
    list_filter = ("branch", "season", "is_active")
    search_fields = ("plate_text", "customer__full_name", "rack_code", "slot_code")
