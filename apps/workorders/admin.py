from django.contrib import admin
from .models import WorkOrder, WorkOrderItem


class WorkOrderItemInline(admin.TabularInline):
    model = WorkOrderItem
    extra = 1


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "kind", "status", "plate_text", "customer", "grand_total", "is_paid", "created_at")
    list_filter = ("branch", "kind", "status", "is_paid")
    search_fields = ("plate_text", "customer__full_name", "vehicle__plate")
    inlines = [WorkOrderItemInline]


@admin.register(WorkOrderItem)
class WorkOrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "title", "is_part", "qty", "unit_price")
