from django.conf import settings
from django.db import models
from django.utils import timezone


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
    language = models.CharField(max_length=10, default="uz")
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
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="items")
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )
    qr_id = models.CharField(max_length=128, unique=True)
    custom_name = models.CharField(max_length=255, blank=True)
    custom_description = models.TextField(blank=True)
    buy_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateField(default=timezone.now)
    client_phone = models.CharField(max_length=32, blank=True)
    warranty_until_date = models.DateField(null=True, blank=True)
    warranty_mileage = models.PositiveIntegerField(null=True, blank=True)
    mileage_unit = models.CharField(max_length=16, blank=True)
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


class WarehouseRecord(models.Model):
    ACTION_CREATED = "created"
    ACTION_UPDATED = "updated"
    ACTION_WARRANTY_CHECK = "warranty_check"

    ACTION_CHOICES = [
        (ACTION_CREATED, "Created"),
        (ACTION_UPDATED, "Updated"),
        (ACTION_WARRANTY_CHECK, "Warranty check"),
    ]

    item = models.ForeignKey(QrItem, on_delete=models.CASCADE, related_name="history")
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.item.display_name} - {self.action}"

