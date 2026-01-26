from django import forms
from .models import WorkOrder


class WorkOrderCreateForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = ["kind", "plate_text", "complaint", "km", "payment_method"]
        widgets = {
            "complaint": forms.Textarea(attrs={"rows": 3}),
        }
