from django.contrib import admin
from .models import Part, StockMove, WorkOrderPart

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("id","name","brand","sku","barcode","sale_price","is_active","branch")
    search_fields = ("name","sku","barcode","brand")

@admin.register(StockMove)
class StockMoveAdmin(admin.ModelAdmin):
    list_display = ("id","part","move_type","qty","unit_cost","branch","workorder","created_at")
    search_fields = ("part__name","note")

@admin.register(WorkOrderPart)
class WorkOrderPartAdmin(admin.ModelAdmin):
    list_display = ("id","order","part","qty","unit_price","line_total","created_at")
