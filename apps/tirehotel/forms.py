from django import forms
from .models import TireHotelEntry


class TireHotelCreateForm(forms.ModelForm):
    class Meta:
        model = TireHotelEntry
        fields = [
            "plate_text",
            "brand",
            "size",
            "season",
            "qty",
            "rack_code",
            "slot_code",
            "price",
            "received_at",
            "due_at",
            "notes",
            "photo",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "received_at": forms.DateInput(attrs={"type": "date"}),
            "due_at": forms.DateInput(attrs={"type": "date"}),
        }
