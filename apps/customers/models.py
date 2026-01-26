from django.db import models
from apps.core.models import Branch


class Customer(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.phone})"

    @property
    def wa_phone(self) -> str:
        """0555xxxxxxx -> 90555xxxxxxx"""
        if not self.phone:
            return ""
        p = (
            self.phone.strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
            .replace("+", "")
        )
        if p.startswith("0"):
            p = "9" + p
        if p.startswith("5"):
            p = "90" + p
        return p


class Vehicle(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="vehicles")
    plate = models.CharField(max_length=15)
    brand = models.CharField(max_length=60, blank=True, default="")
    model = models.CharField(max_length=60, blank=True, default="")
    year = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("branch", "plate")
        indexes = [models.Index(fields=["branch", "plate"])]

    def __str__(self):
        return self.plate
