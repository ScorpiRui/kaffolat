from django.contrib import admin

from .models import Shop, ProductType, QrItem, WarehouseRecord


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "is_active")
    list_filter = ("shop", "is_active")
    search_fields = ("name",)


@admin.register(QrItem)
class QrItemAdmin(admin.ModelAdmin):
    list_display = ("display_name", "shop", "qr_id", "item_type", "is_completed", "client_phone")
    list_filter = ("shop", "item_type", "is_completed")
    search_fields = ("qr_id", "custom_name", "client_phone")


@admin.register(WarehouseRecord)
class WarehouseRecordAdmin(admin.ModelAdmin):
    list_display = ("item", "action", "created_at")
    list_filter = ("action",)
