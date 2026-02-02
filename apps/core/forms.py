from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class AdminUserCreateForm(UserCreationForm):
    """Admin panel icin kullanici olusturma formu."""

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
        label="Yetki Grupları",
        help_text="Örn: ADMIN, USTA",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k in ["username", "first_name", "last_name", "email"]:
            self.fields[k].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

        self.fields["first_name"].required = False
        self.fields["last_name"].required = False
        self.fields["email"].required = False


class AdminUserUpdateForm(forms.ModelForm):
    """Admin panel icin kullanici guncelleme formu.

    Not: Sifre degistirmek istersen yeni sifre alanlarini doldur.
    """

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
        label="Yetki Grupları",
    )

    new_password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Yeni Şifre",
    )
    new_password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Yeni Şifre (Tekrar)",
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
        labels = {
            "is_active": "Aktif",
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if (p1 or p2) and p1 != p2:
            raise forms.ValidationError("Yeni şifreler eşleşmiyor.")
        return cleaned