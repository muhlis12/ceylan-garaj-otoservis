from django import forms


class NotifyTestForm(forms.Form):
    channel = forms.ChoiceField(choices=[("WHATSAPP", "WhatsApp"), ("SMS", "SMS")])
    to_e164 = forms.CharField(help_text="Orn: +9050... (E.164 format)")
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))
