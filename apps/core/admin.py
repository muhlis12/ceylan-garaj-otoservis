from django.contrib import admin
from .models import Branch, BranchMembership


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "is_active", "created_at")
    search_fields = ("name", "phone")


@admin.register(BranchMembership)
class BranchMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "branch", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("user__username", "user__email", "branch__name")
