from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField

from .models import QrItem, Shop


class QrItemForm(forms.ModelForm):
    class Meta:
        model = QrItem
        fields = [
            "product_type",
            "custom_name",
            "custom_description",
            "buy_price",
            "purchase_date",
            "client_phone",
            "warranty_until_date",
            "warranty_mileage",
            "mileage_unit",
        ]
        widgets = {
            "product_type": forms.Select(attrs={"class": "w-full border rounded px-3 py-2 text-sm"}),
            "custom_name": forms.TextInput(attrs={"class": "w-full border rounded px-3 py-2 text-sm"}),
            "custom_description": forms.Textarea(
                attrs={"class": "w-full border rounded px-3 py-2 text-sm", "rows": 3}
            ),
            "buy_price": forms.NumberInput(attrs={"class": "w-full border rounded px-3 py-2 text-sm"}),
            "purchase_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full border rounded px-3 py-2 text-sm"}
            ),
            "client_phone": forms.TextInput(attrs={"class": "w-full border rounded px-3 py-2 text-sm"}),
            "warranty_until_date": forms.DateInput(
                attrs={"type": "date", "class": "w-full border rounded px-3 py-2 text-sm"}
            ),
            "warranty_mileage": forms.NumberInput(attrs={"class": "w-full border rounded px-3 py-2 text-sm"}),
            "mileage_unit": forms.TextInput(attrs={"class": "w-full border rounded px-3 py-2 text-sm"}),
        }


User = get_user_model()


class ShopRegistrationForm(forms.ModelForm):
    username = UsernameField(
        label="Login",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "class": "w-full border rounded px-3 py-2 text-sm",
                "placeholder": "Login kiriting",
            }
        ),
    )
    password1 = forms.CharField(
        label="Parol",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "w-full border rounded px-3 py-2 text-sm",
                "placeholder": "Parol kiriting",
            }
        ),
    )
    password2 = forms.CharField(
        label="Parolni tasdiqlang",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "class": "w-full border rounded px-3 py-2 text-sm",
                "placeholder": "Parolni qayta kiriting",
            }
        ),
    )

    class Meta:
        model = Shop
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full border rounded px-3 py-2 text-sm",
                    "placeholder": "Masalan: AutoServis 1",
                }
            ),
        }

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Bu login band.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Parollar mos emas.")
        return cleaned_data

    def save(self, commit=True):
        shop = super().save(commit=False)
        username = self.cleaned_data["username"]
        password = self.cleaned_data["password1"]
        user = User.objects.create_user(username=username, password=password)
        shop.user = user
        if commit:
            shop.save()
        return shop


