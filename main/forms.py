from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField

from .models import ProductType, QrItem, Shop

INPUT = (
    "w-full border border-gray-200 rounded-xl px-4 py-3 text-sm "
    "focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
)

DATE_INPUT_FORMATS = ["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"]


class WarrantySellForm(forms.ModelForm):
    warranty_until_date = forms.DateField(
        required=False,
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.TextInput(attrs={
            "class": INPUT + " date-input-mask",
            "placeholder": "__/__/____",
            "maxlength": "10",
        }),
    )

    class Meta:
        model = QrItem
        fields = [
            "custom_name", "custom_description", "sold_price",
            "client_phone", "warranty_until_date",
            "warranty_mileage",
        ]
        widgets = {
            "custom_name": forms.TextInput(attrs={
                "class": INPUT, "placeholder": "Mahsulot nomi",
            }),
            "custom_description": forms.Textarea(attrs={
                "class": INPUT, "rows": 3, "placeholder": "Tavsif (ixtiyoriy)",
            }),
            "sold_price": forms.NumberInput(attrs={
                "class": INPUT, "placeholder": "0", "step": "1", "min": "0",
            }),
            "client_phone": forms.TextInput(attrs={
                "class": INPUT, "placeholder": "+998 90 000 00 00", "type": "tel",
            }),
            "warranty_mileage": forms.NumberInput(attrs={
                "class": INPUT, "placeholder": "0",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["custom_name"].required = True
        self.fields["sold_price"].required = True
        self.fields["client_phone"].required = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.warranty_mileage:
            instance.mileage_unit = "km"
        else:
            instance.mileage_unit = ""
        if commit:
            instance.save()
        return instance


class RepairForm(forms.ModelForm):
    warranty_until_date = forms.DateField(
        required=False,
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.TextInput(attrs={
            "class": INPUT + " date-input-mask",
            "placeholder": "__/__/____",
            "maxlength": "10",
        }),
    )

    repair_deadline = forms.DateField(
        required=False,
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.TextInput(attrs={
            "class": INPUT + " date-input-mask",
            "placeholder": "__/__/____",
            "maxlength": "10",
        }),
    )

    class Meta:
        model = QrItem
        fields = [
            "custom_name", "custom_description", "repair_deadline",
            "warranty_until_date", "warranty_mileage",
            "repair_price", "client_phone",
        ]
        widgets = {
            "custom_name": forms.TextInput(attrs={
                "class": INPUT, "placeholder": "Mahsulot nomi",
            }),
            "custom_description": forms.Textarea(attrs={
                "class": INPUT, "rows": 3, "placeholder": "Tavsif (ixtiyoriy)",
            }),
            "repair_price": forms.NumberInput(attrs={
                "class": INPUT, "placeholder": "0", "step": "1", "min": "0",
            }),
            "client_phone": forms.TextInput(attrs={
                "class": INPUT, "placeholder": "+998 90 000 00 00", "type": "tel",
            }),
            "warranty_mileage": forms.NumberInput(attrs={
                "class": INPUT, "placeholder": "0",
            }),
        }

    def __init__(self, *args, **kwargs):
        repair_intake = kwargs.pop("repair_intake", False)
        super().__init__(*args, **kwargs)
        self._repair_intake = repair_intake
        self.fields["custom_name"].required = True
        self.fields["client_phone"].required = True
        # First QR scan (repair intake): planned completion date required
        self.fields["repair_deadline"].required = bool(repair_intake)
        if repair_intake:
            if not self.is_bound:
                self.fields["client_phone"].initial = "+998"
            ph = self.fields["client_phone"]
            ph.widget.attrs["placeholder"] = "90 123 45 67"
            ph.widget.attrs["maxlength"] = "17"
            ph.widget.attrs["autocomplete"] = "tel"

    def clean_client_phone(self):
        phone = (self.cleaned_data.get("client_phone") or "").strip()
        phone = "".join(phone.split())
        if getattr(self, "_repair_intake", False):
            digits = "".join(c for c in phone if c.isdigit())
            if digits.startswith("998"):
                digits = digits[3:]
            digits = digits[:9]
            if not digits:
                raise forms.ValidationError("Telefon raqamini kiriting (+998 dan keyin 9 raqam).")
            phone = "+998" + digits
        return phone

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.warranty_mileage:
            instance.mileage_unit = "km"
        else:
            instance.mileage_unit = ""
        if commit:
            instance.save()
        return instance


class RepairWarehouseEditForm(forms.ModelForm):
    """Ombor / ta'mirlash kartasida faqat asosiy ma'lumotlar (narx, kafolat, muddat tahrirsiz)."""

    class Meta:
        model = QrItem
        fields = ["custom_name", "custom_description", "client_phone"]
        widgets = {
            "custom_name": forms.TextInput(attrs={
                "class": INPUT, "placeholder": "Mahsulot nomi",
            }),
            "custom_description": forms.Textarea(attrs={
                "class": INPUT, "rows": 3, "placeholder": "Tavsif (ixtiyoriy)",
            }),
            "client_phone": forms.TextInput(attrs={
                "class": INPUT, "placeholder": "+998 90 000 00 00", "type": "tel",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["custom_name"].required = True
        self.fields["client_phone"].required = True


class ProductTypeForm(forms.ModelForm):
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
