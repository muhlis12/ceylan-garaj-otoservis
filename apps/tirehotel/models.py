from django.db import models
from apps.core.models import Branch
from apps.customers.models import Customer, Vehicle


class TireHotelEntry(models.Model):
    SEASON_SUMMER = "SUMMER"
    SEASON_WINTER = "WINTER"
    SEASON_CHOICES = [(SEASON_SUMMER, "Yazlik"), (SEASON_WINTER, "Kislik")]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    plate_text = models.CharField(max_length=20, blank=True)

    brand = models.CharField(max_length=60, blank=True)
    size = models.CharField(max_length=40, blank=True, help_text="Orn: 205/55R16")
    season = models.CharField(max_length=10, choices=SEASON_CHOICES, default=SEASON_WINTER)
    qty = models.PositiveIntegerField(default=4)

    rack_code = models.CharField(max_length=10, help_text="Raf kodu: orn R3")
    slot_code = models.CharField(max_length=10, help_text="Goz kodu: orn G12")

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    received_at = models.DateField(null=True, blank=True)
    due_at = models.DateField(null=True, blank=True)
    released_at = models.DateField(null=True, blank=True)

    photo = models.ImageField(upload_to="tirehotel", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        plate = self.plate_text or (self.vehicle.plate if self.vehicle else "-")
        return f"{plate} - {self.season} ({self.rack_code}/{self.slot_code})"
