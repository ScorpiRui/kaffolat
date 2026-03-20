from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ProductTypeForm, RepairForm, ShopProfileForm, ShopRegistrationForm, WarrantySellForm
from .models import ProductType, QrItem, Shop, WarehouseRecord


def _get_shop_for_request(request) -> Shop:
    shop, _ = Shop.objects.get_or_create(
        user=request.user,
        defaults={"name": request.user.get_username() or "My Shop"},
    )
    return shop


# -- Scanner / home --

@login_required
def shop_home(request):
    shop = _get_shop_for_request(request)
    return render(request, "main/shop_home.html", {"shop": shop})


# -- QR handler --
# Accepts ?mode=warranty (default) or ?mode=repair
# New QR -> show appropriate form
# Existing QR -> go to item detail

@login_required
def qr_handler(request, qr_id: str):
    shop = _get_shop_for_request(request)
    mode = request.GET.get("mode", "warranty")
    if mode not in ("warranty", "repair"):
        mode = "warranty"

    existing = QrItem.objects.filter(shop=shop, qr_id=qr_id).first()
    if existing:
        return redirect("main:item_detail", pk=existing.pk)

    warranty_presets = [
        ("3 kun", 3),
        ("7 kun", 7),
        ("15 kun", 15),
        ("1 oy", 30),
        ("3 oy", 90),
        ("6 oy", 180),
        ("1 yil", 365),
    ]

    if mode == "repair":
        if request.method == "POST":
            form = RepairForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.shop = shop
                item.qr_id = qr_id
                item.item_type = QrItem.TYPE_REPAIR
                item.is_completed = False
                item.purchase_date = timezone.localdate()
                item.save()
                WarehouseRecord.objects.create(
                    item=item,
                    action=WarehouseRecord.ACTION_CREATED,
                    note="Ta'mirlash uchun qabul qilindi",
                )
                return redirect("main:item_detail", pk=item.pk)
        else:
            form = RepairForm()
        return render(request, "main/qr_item_form.html", {
            "shop": shop,
            "qr_id": qr_id,
            "form": form,
            "mode": "repair",
            "warranty_presets": warranty_presets,
        })
    else:
        if request.method == "POST":
            form = WarrantySellForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.shop = shop
                item.qr_id = qr_id
                item.item_type = QrItem.TYPE_WARRANTY
                item.purchase_date = timezone.localdate()
                item.save()
                WarehouseRecord.objects.create(
                    item=item,
                    action=WarehouseRecord.ACTION_CREATED,
                    note="Kafolat bilan sotildi",
                )
                return redirect("main:item_detail", pk=item.pk)
        else:
            form = WarrantySellForm()
        return render(request, "main/qr_item_form.html", {
            "shop": shop,
            "qr_id": qr_id,
            "form": form,
            "mode": "warranty",
            "warranty_presets": warranty_presets,
        })


# -- Warehouse (repair items not yet completed) --

@login_required
def warehouse_list(request):
    shop = _get_shop_for_request(request)
    items = (
        QrItem.objects
        .filter(shop=shop, item_type=QrItem.TYPE_REPAIR, is_completed=False)
        .select_related("product_type")
    )
    return render(request, "main/warehouse_list.html", {"shop": shop, "items": items})


# -- Item detail --

@login_required
def item_detail(request, pk: int):
    shop = _get_shop_for_request(request)
    item = get_object_or_404(QrItem, pk=pk, shop=shop)
    warranty_presets = [
        ("3 kun", 3),
        ("7 kun", 7),
        ("15 kun", 15),
        ("1 oy", 30),
        ("3 oy", 90),
        ("6 oy", 180),
        ("1 yil", 365),
    ]
    return render(request, "main/item_detail.html", {
        "shop": shop,
        "item": item,
        "warranty_presets": warranty_presets,
    })


# -- Edit item (warehouse repair or history warranty / completed repair) --

@login_required
def item_edit(request, pk: int):
    shop = _get_shop_for_request(request)
    item = get_object_or_404(QrItem, pk=pk, shop=shop)

    warranty_presets = [
        ("3 kun", 3),
        ("7 kun", 7),
        ("15 kun", 15),
        ("1 oy", 30),
        ("3 oy", 90),
        ("6 oy", 180),
        ("1 yil", 365),
    ]

    if item.is_repair:
        if request.method == "POST":
            form = RepairForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
                WarehouseRecord.objects.create(
                    item=item,
                    action=WarehouseRecord.ACTION_UPDATED,
                    note="Ma'lumotlar tahrirlandi",
                )
                messages.success(request, "O'zgarishlar saqlandi.")
                return redirect("main:item_detail", pk=item.pk)
        else:
            form = RepairForm(instance=item)
        mode = "repair"
    else:
        if request.method == "POST":
            form = WarrantySellForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
                WarehouseRecord.objects.create(
                    item=item,
                    action=WarehouseRecord.ACTION_UPDATED,
                    note="Ma'lumotlar tahrirlandi",
                )
                messages.success(request, "O'zgarishlar saqlandi.")
                return redirect("main:item_detail", pk=item.pk)
        else:
            form = WarrantySellForm(instance=item)
        mode = "warranty"

    form.fields["warranty_until_date"].widget.attrs["id"] = "warrantyDateInput"

    return render(request, "main/item_edit.html", {
        "shop": shop,
        "item": item,
        "form": form,
        "mode": mode,
        "warranty_presets": warranty_presets,
    })


# -- Complete repair (mark repair as done) --

@login_required
def complete_repair(request, pk: int):
    shop = _get_shop_for_request(request)
    item = get_object_or_404(QrItem, pk=pk, shop=shop)
    if request.method == "POST" and item.is_repair and not item.is_completed:
        item.is_completed = True
        item.save()
        WarehouseRecord.objects.create(
            item=item,
            action=WarehouseRecord.ACTION_COMPLETED,
            note="Ta'mirlash yakunlandi, mijozga topshirildi",
        )
    return redirect("main:item_detail", pk=pk)


# -- Revert completion (move back to warehouse) --

@login_required
def revert_complete(request, pk: int):
    shop = _get_shop_for_request(request)
    item = get_object_or_404(QrItem, pk=pk, shop=shop)
    if request.method == "POST" and item.is_repair and item.is_completed:
        item.is_completed = False
        item.save()
        WarehouseRecord.objects.create(
            item=item,
            action=WarehouseRecord.ACTION_REVERTED,
            note="Ta'mirlash qaytarildi, mahsulot omborga qaytdi",
        )
    return redirect("main:item_detail", pk=pk)


# -- History (warranty items + completed repairs) --

@login_required
def warranty_history(request):
    shop = _get_shop_for_request(request)
    items = (
        QrItem.objects
        .filter(shop=shop)
        .filter(
            Q(item_type=QrItem.TYPE_WARRANTY) |
            Q(item_type=QrItem.TYPE_REPAIR, is_completed=True)
        )
        .select_related("product_type")
    )

    search_q = request.GET.get("q", "").strip()
    date_from_str = request.GET.get("from", "").strip()
    date_to_str = request.GET.get("to", "").strip()

    if search_q:
        items = items.filter(
            Q(custom_name__icontains=search_q)
            | Q(custom_description__icontains=search_q)
            | Q(client_phone__icontains=search_q)
            | Q(qr_id__icontains=search_q)
        )

    _date_formats = ["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"]

    def _parse_date(s):
        if not s:
            return None
        for fmt in _date_formats:
            try:
                return datetime.strptime(s, fmt).date()
            except (ValueError, TypeError):
                pass
        return None

    date_from = _parse_date(date_from_str)
    date_to = _parse_date(date_to_str)

    if date_from:
        items = items.filter(created_at__date__gte=date_from)
    if date_to:
        items = items.filter(created_at__date__lte=date_to)

    items = items.order_by("-created_at")

    return render(request, "main/warranty_history.html", {
        "shop": shop,
        "items": items,
        "search_q": search_q,
        "date_from": date_from_str,
        "date_to": date_to_str,
    })


# -- Management page --

@login_required
def product_type_list(request):
    shop = _get_shop_for_request(request)
    product_types = shop.product_types.all().order_by("name")

    today = timezone.localdate()

    repair_in_progress = (
        QrItem.objects
        .filter(shop=shop, item_type=QrItem.TYPE_REPAIR, is_completed=False)
        .count()
    )

    warranty_active = (
        QrItem.objects
        .filter(shop=shop, item_type=QrItem.TYPE_WARRANTY)
        .filter(Q(warranty_until_date__isnull=True) | Q(warranty_until_date__gte=today))
        .count()
    )

    total_warranty_items = QrItem.objects.filter(shop=shop, item_type=QrItem.TYPE_WARRANTY).count()
    total_repair_items = QrItem.objects.filter(shop=shop, item_type=QrItem.TYPE_REPAIR).count()
    completed_repairs = QrItem.objects.filter(shop=shop, item_type=QrItem.TYPE_REPAIR, is_completed=True).count()

    return render(request, "main/product_type_list.html", {
        "shop": shop,
        "product_types": product_types,
        "repair_in_progress": repair_in_progress,
        "warranty_active": warranty_active,
        "total_warranty_items": total_warranty_items,
        "total_repair_items": total_repair_items,
        "completed_repairs": completed_repairs,
    })


@login_required
def product_type_create(request):
    shop = _get_shop_for_request(request)
    if request.method == "POST":
        form = ProductTypeForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.shop = shop
            obj.save()
            messages.success(request, "Mahsulot turi qo'shildi.")
            return redirect("main:product_type_list")
    else:
        form = ProductTypeForm()
    return render(request, "main/product_type_form.html", {
        "shop": shop,
        "form": form,
        "is_edit": False,
    })


@login_required
def product_type_edit(request, pk: int):
    shop = _get_shop_for_request(request)
    obj = get_object_or_404(ProductType, pk=pk, shop=shop)
    if request.method == "POST":
        form = ProductTypeForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "O'zgarishlar saqlandi.")
            return redirect("main:product_type_list")
    else:
        form = ProductTypeForm(instance=obj)
    return render(request, "main/product_type_form.html", {
        "shop": shop,
        "form": form,
        "product_type": obj,
        "is_edit": True,
    })


@login_required
def product_type_delete(request, pk: int):
    shop = _get_shop_for_request(request)
    obj = get_object_or_404(ProductType, pk=pk, shop=shop)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Mahsulot turi o'chirildi.")
        return redirect("main:product_type_list")
    return redirect("main:product_type_list")


# -- Profile / Settings --

@login_required
def shop_profile(request):
    shop = _get_shop_for_request(request)
    if request.method == "POST":
        form = ShopProfileForm(request.POST, request.FILES, instance=shop)
        if form.is_valid():
            form.save()
            messages.success(request, "Ma'lumotlar saqlandi.")
            return redirect("main:shop_profile")
    else:
        form = ShopProfileForm(instance=shop)
    return render(request, "main/shop_profile.html", {"shop": shop, "form": form})


# -- Public customer page --

def public_item_from_query(request):
    qr_id = request.GET.get("id", "").strip()
    if not qr_id:
        raise Http404("QR id is required")
    item = get_object_or_404(QrItem.objects.select_related("shop", "product_type"), qr_id=qr_id)
    return render(request, "main/public_item_detail.html", {"item": item, "shop": item.shop})


def public_item_detail(request, qr_id: str):
    item = get_object_or_404(QrItem.objects.select_related("shop", "product_type"), qr_id=qr_id)
    return render(request, "main/public_item_detail.html", {"item": item, "shop": item.shop})


# -- Shop registration (staff only) --

@staff_member_required
def shop_register(request):
    if request.method == "POST":
        form = ShopRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = ShopRegistrationForm()
    return render(request, "main/shop_register.html", {"form": form})
