from decimal import Decimal
from django.conf import settings
from django.db import models
from apps.core.models import Branch
from apps.customers.models import Customer, Vehicle


class WorkOrder(models.Model):
    KIND_CAR_WASH = "CAR_WASH"
    KIND_VEHICLE_REPAIR = "VEHICLE_REPAIR"
    KIND_TIRE_REPAIR = "TIRE_REPAIR"

    KIND_CHOICES = [
        (KIND_CAR_WASH, "Oto Yıkama"),
        (KIND_TIRE_REPAIR, "Lastik Tamir"),
        (KIND_VEHICLE_REPAIR, "Araç Tamir"),
    ]

    STATUS_WAITING = "WAITING"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_WAITING_ADMIN = "WAITING_ADMIN"
    STATUS_DONE = "DONE"
    STATUS_CHOICES = [
        (STATUS_WAITING, "Beklemede"),
        (STATUS_IN_PROGRESS, "İşlemde"),
        (STATUS_WAITING_ADMIN, "Admin Bekliyor"),
        (STATUS_DONE, "Teslim"),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING)

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    plate_text = models.CharField(max_length=20, blank=True, help_text="Araç kaydı yoksa plaka")

    complaint = models.TextField(blank=True, default="")
    km = models.PositiveIntegerField(null=True, blank=True)

    # Admin fiyatları
    labor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    parts_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payment_method = models.CharField(max_length=20, blank=True, default="", help_text="NAKIT/KART/HAVALE")
    is_paid = models.BooleanField(default=False)

    # Admin not
    staff_note = models.TextField(blank=True, default="")

    # USTA / KALFA AKIŞI (fiyat görmez)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_workorders"
    )
    worker_services = models.TextField(blank=True, default="")  # "İç Yıkama|Motor Yıkama"
    worker_note = models.TextField(blank=True, default="")
    worker_finished_at = models.DateTimeField(null=True, blank=True)
    worker_finished_by_name = models.CharField(max_length=120, blank=True, default="")

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    subject = models.CharField(max_length=120, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        plate = (self.plate_text or "").strip() or (self.vehicle.plate if self.vehicle else "-")
        return f"{plate} - {self.get_kind_display()}"


class WorkOrderItem(models.Model):
    order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=120)
    is_part = models.BooleanField(default=False)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # müşteriye görünecek başlık
    subject = models.CharField(max_length=120, blank=True, default="")

    # tahmini fiyatlar (müşteri onayı için)
    estimate_labor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimate_parts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimate_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def line_total(self):
        return (self.qty or Decimal("0")) * (self.unit_price or Decimal("0"))

    def __str__(self):
        return self.title
