from django.contrib import admin
from .models import Customer, Vehicle


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "full_name", "phone", "email", "created_at")
    search_fields = ("full_name", "phone", "email")
    list_filter = ("branch",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "plate", "customer", "brand", "model", "year", "created_at")
    search_fields = ("plate", "brand", "model", "customer__full_name")
    list_filter = ("branch",)
