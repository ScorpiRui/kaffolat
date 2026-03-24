from django.conf import settings
from django.db import models
from django.utils import timezone

_UZ_MONTH_NAMES = (
    "yanvar",
    "fevral",
    "mart",
    "aprel",
    "may",
    "iyun",
    "iyul",
    "avgust",
    "sentyabr",
    "oktyabr",
    "noyabr",
    "dekabr",
)


def _format_date_uz(d) -> str:
    """Masalan: 12-Dekabr, 2026-yil (vaqtsiz)."""
    if d is None:
        return ""
    month = _UZ_MONTH_NAMES[d.month - 1].capitalize()
    return f"{d.day}-{month}, {d.year}-yil"


class Shop(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shop",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="shop_logos/", blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True)
    location = models.CharField(max_length=255, blank=True)
    language = models.CharField(max_length=10, default="uz")
    warranty_mileage_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class ProductType(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="product_types")
    name = models.CharField(max_length=255)
    default_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.shop.name} - {self.name}"


class QrItem(models.Model):
    TYPE_WARRANTY = "warranty"
    TYPE_REPAIR = "repair"
    TYPE_CHOICES = [
        (TYPE_WARRANTY, "Kafolat"),
        (TYPE_REPAIR, "Ta'mirlash"),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="items")
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )
    qr_id = models.CharField(max_length=128, unique=True)
    item_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=TYPE_WARRANTY)
    custom_name = models.CharField(max_length=255, blank=True)
    custom_description = models.TextField(blank=True)
    buy_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sold_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    repair_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    repair_deadline = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    # Ta'mirlash: False = ombor "Jarayonda", True = "Tayyor" (yakunlash mumkin)
    repair_ready_to_finish = models.BooleanField(default=False)
    purchase_date = models.DateField(default=timezone.now)
    client_phone = models.CharField(max_length=32, blank=True)
    warranty_until_date = models.DateField(null=True, blank=True)
    warranty_mileage = models.PositiveIntegerField(null=True, blank=True)
    mileage_unit = models.CharField(max_length=16, blank=True)
    debt_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        if self.custom_name:
            return self.custom_name
        if self.product_type:
            return self.product_type.name
        return self.qr_id

    def warranty_is_valid(self) -> bool:
        today = timezone.localdate()
        if self.warranty_until_date and self.warranty_until_date < today:
            return False
        return True

    @property
    def is_warranty(self):
        return self.item_type == self.TYPE_WARRANTY

    @property
    def is_repair(self):
        return self.item_type == self.TYPE_REPAIR

    @property
    def created_at_uz(self) -> str:
        """Qabul sanasi — lokal kun, o'zbekcha oy nomi, vaqtsiz."""
        if self.created_at is None:
            return ""
        return _format_date_uz(timezone.localdate(self.created_at))


class WarehouseRecord(models.Model):
    ACTION_CREATED = "created"
    ACTION_UPDATED = "updated"
    ACTION_WARRANTY_CHECK = "warranty_check"
    ACTION_REVERTED = "reverted"
    ACTION_COMPLETED = "completed"
    ACTION_WAREHOUSE_READY = "warehouse_ready"
    ACTION_CHOICES = [
        (ACTION_CREATED, "Created"),
        (ACTION_UPDATED, "Updated"),
        (ACTION_WARRANTY_CHECK, "Warranty check"),
        (ACTION_REVERTED, "Reverted"),
        (ACTION_COMPLETED, "Completed"),
        (ACTION_WAREHOUSE_READY, "Warehouse ready"),
    ]

    item = models.ForeignKey(QrItem, on_delete=models.CASCADE, related_name="history")
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.item.display_name} - {self.action}"
