from decimal import Decimal
from django.db import models
from apps.core.models import Branch
from apps.workorders.models import WorkOrder


class Part(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    sku = models.CharField(max_length=50, blank=True, default="")
    barcode = models.CharField(max_length=80, blank=True, default="")
    name = models.CharField(max_length=160)
    brand = models.CharField(max_length=80, blank=True, default="")
    unit = models.CharField(max_length=20, blank=True, default="adet")

    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["branch", "name"]),
            models.Index(fields=["branch", "barcode"]),
            models.Index(fields=["branch", "sku"]),
        ]
        unique_together = ("branch", "sku")

    def __str__(self):
        return self.name

    def ensure_barcode(self):
        """
        Barkod yoksa otomatik üret:
        OS-{branch_id}-{part_id}
        """
        if not self.barcode:
            self.barcode = f"OS-{self.branch_id}-{self.id}"
            self.save(update_fields=["barcode"])


class StockMove(models.Model):
    TYPE_IN = "IN"
    TYPE_OUT = "OUT"
    TYPE_CHOICES = [(TYPE_IN, "Giriş (+)"), (TYPE_OUT, "Çıkış (-)")]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name="moves")
    move_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    note = models.CharField(max_length=200, blank=True, default="")

    workorder = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name="stock_moves")
    created_at = models.DateTimeField(auto_now_add=True)

    def signed_qty(self):
        return self.qty if self.move_type == self.TYPE_IN else -self.qty

    def __str__(self):
        return f"{self.part.name} {self.move_type} {self.qty}"


class WorkOrderPart(models.Model):
    order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="parts")
    part = models.ForeignKey(Part, on_delete=models.PROTECT)

    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def recalc(self):
        self.line_total = (self.qty or Decimal("0")) * (self.unit_price or Decimal("0"))

    def __str__(self):
        return f"{self.part.name} x{self.qty}"
