from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField

from .models import QrItem, Shop

INPUT = (
    "w-full border border-gray-200 rounded-xl px-4 py-3 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
)


class QrItemAddForm(forms.ModelForm):
    """Step 1 — New QR: add product to warehouse.
    Fields: product type, name, description, buy price, purchase date."""

    class Meta:
        model = QrItem
        fields = ["product_type", "custom_name", "custom_description", "buy_price", "purchase_date"]
        widgets = {
            "product_type": forms.Select(attrs={"class": INPUT}),
            "custom_name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Ixtiyoriy nom"}),
            "custom_description": forms.Textarea(attrs={"class": INPUT, "rows": 3, "placeholder": "Tavsif (ixtiyoriy)"}),
            "buy_price": forms.NumberInput(attrs={"class": INPUT, "placeholder": "0.00"}),
            "purchase_date": forms.DateInput(attrs={"type": "date", "class": INPUT}),
        }

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        if shop is not None:
            self.fields["product_type"].queryset = shop.product_types.filter(is_active=True)
        else:
            self.fields["product_type"].queryset = QrItem.objects.none()
        self.fields["product_type"].required = False
        self.fields["product_type"].empty_label = "— Mahsulot tanlang (ixtiyoriy)"


# Keep old name as alias so other imports don't break
QrItemForm = QrItemAddForm


class QrItemSellForm(forms.ModelForm):
    """Step 2 — Sell: add client phone, sold price + warranty to an existing warehouse item."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sold_price"].required = True

    class Meta:
        model = QrItem
        fields = ["client_phone", "sold_price", "warranty_until_date", "warranty_mileage", "mileage_unit"]
        widgets = {
            "client_phone": forms.TextInput(attrs={
                "class": INPUT, "placeholder": "+998 90 000 00 00", "type": "tel",
            }),
            "sold_price": forms.NumberInput(attrs={
                "class": INPUT, "placeholder": "0.00", "step": "0.01",
            }),
            "warranty_until_date": forms.DateInput(attrs={
                "type": "date", "class": INPUT,
            }),
            "warranty_mileage": forms.NumberInput(attrs={
                "class": INPUT, "placeholder": "0",
            }),
            "mileage_unit": forms.TextInput(attrs={
                "class": INPUT, "placeholder": "km",
            }),
        }


User = get_user_model()


class ShopRegistrationForm(forms.ModelForm):
    username = UsernameField(
        label="Login",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "class": INPUT,
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
                "class": INPUT,
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
                "class": INPUT,
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
                    "class": INPUT,
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


LANGUAGE_CHOICES = [
    ("uz", "O'zbek"),
    ("ru", "Русский"),
    ("en", "English"),
]


class ShopProfileForm(forms.ModelForm):
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        label="Til",
        widget=forms.Select(attrs={"class": INPUT}),
    )

    class Meta:
        model = Shop
        fields = ["name", "phone", "location", "logo", "language", "warranty_mileage_enabled"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Do'kon nomi"}),
            "phone": forms.TextInput(attrs={"class": INPUT, "placeholder": "+998 90 000 00 00", "type": "tel"}),
            "location": forms.TextInput(attrs={"class": INPUT, "placeholder": "Shahar, ko'cha, uy raqami"}),
        }
