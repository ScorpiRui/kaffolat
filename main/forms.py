from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField

from .models import ProductType, QrItem, Shop

INPUT = (
    "w-full border border-gray-200 rounded-xl px-4 py-3 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
)


DATE_INPUT_FORMATS = ["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"]


class ProductTypeChoiceField(forms.ModelChoiceField):
    """Show only product type name, not shop name."""

    def label_from_instance(self, obj):
        return obj.name


class QrItemAddForm(forms.ModelForm):
    """Step 1 — New QR: add product to warehouse.
    Fields: product type, name, description, buy price, purchase date."""

    product_type = ProductTypeChoiceField(
        queryset=ProductType.objects.none(),
        required=False,
        empty_label="— Mahsulot tanlang (ixtiyoriy)",
        widget=forms.Select(attrs={"class": INPUT}),
    )

    purchase_date = forms.DateField(
        required=False,
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.TextInput(attrs={"class": INPUT + " date-input-mask", "placeholder": "__/__/____", "maxlength": "10"}),
    )

    class Meta:
        model = QrItem
        fields = ["product_type", "custom_description", "buy_price", "purchase_date"]
        widgets = {
            "custom_description": forms.Textarea(attrs={"class": INPUT, "rows": 3, "placeholder": "Tavsif (ixtiyoriy)"}),
            "buy_price": forms.NumberInput(attrs={"class": INPUT, "placeholder": "0.00"}),
        }

    def __init__(self, *args, shop=None, **kwargs):
        super().__init__(*args, **kwargs)
        if shop is not None:
            self.fields["product_type"].queryset = shop.product_types.filter(is_active=True)
        else:
            self.fields["product_type"].queryset = ProductType.objects.none()
        # Pre-fill purchase_date with today if not already set
        if not self.initial.get("purchase_date") and not self.data.get("purchase_date"):
            from django.utils import timezone
            self.fields["purchase_date"].initial = timezone.localdate().strftime("%d/%m/%Y")


# Keep old name as alias so other imports don't break
QrItemForm = QrItemAddForm


class QrItemSellForm(forms.ModelForm):
    """Step 2 — Sell: add client phone, sold price + warranty to an existing warehouse item."""

    warranty_until_date = forms.DateField(
        required=False,
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.TextInput(attrs={"class": INPUT + " date-input-mask", "placeholder": "__/__/____", "maxlength": "10"}),
    )

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
            "warranty_mileage": forms.NumberInput(attrs={
                "class": INPUT, "placeholder": "0",
            }),
            "mileage_unit": forms.TextInput(attrs={
                "class": INPUT, "placeholder": "km",
            }),
        }


class ProductTypeForm(forms.ModelForm):
    """Form for creating/editing product types."""

    class Meta:
        model = ProductType
        fields = ["name", "default_description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Masalan: Avtomobil"}),
            "default_description": forms.Textarea(
                attrs={"class": INPUT, "rows": 3, "placeholder": "Tavsif (ixtiyoriy)"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
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


class ShopProfileForm(forms.ModelForm):
    warranty_mileage_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"id": "id_warranty_mileage_enabled"}),
    )

    class Meta:
        model = Shop
        fields = ["name", "phone", "location", "logo", "warranty_mileage_enabled"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT, "placeholder": "Do'kon nomi"}),
            "phone": forms.TextInput(attrs={"class": INPUT, "placeholder": "+998 90 000 00 00", "type": "tel"}),
            "location": forms.TextInput(attrs={"class": INPUT, "placeholder": "Shahar, ko'cha, uy raqami"}),
            "logo": forms.FileInput(attrs={"id": "id_logo", "class": "hidden", "accept": "image/*"}),
        }
