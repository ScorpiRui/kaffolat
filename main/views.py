from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ProductTypeForm, QrItemAddForm, QrItemSellForm, ShopProfileForm, ShopRegistrationForm
from .models import ProductType, QrItem, Shop, WarehouseRecord


def _get_shop_for_request(request) -> Shop:
    shop, _ = Shop.objects.get_or_create(
        user=request.user,
        defaults={"name": request.user.get_username() or "My Shop"},
    )
    return shop


# ── Scanner / home ─────────────────────────────────────────────────────────────

@login_required
def shop_home(request):
    shop = _get_shop_for_request(request)
    return render(request, "main/shop_home.html", {"shop": shop})


# ── QR handler ─────────────────────────────────────────────────────────────────
# New QR          → show "Add to warehouse" form (type, name, desc, price, date)
# Existing QR     → go straight to item detail

@login_required
def qr_handler(request, qr_id: str):
    shop = _get_shop_for_request(request)

    existing = QrItem.objects.filter(shop=shop, qr_id=qr_id).first()
    if existing:
        return redirect("main:item_detail", pk=existing.pk)

    # New QR — add to warehouse
    if request.method == "POST":
        form = QrItemAddForm(request.POST, shop=shop)
        if form.is_valid():
            item = form.save(commit=False)
            item.shop = shop
            item.qr_id = qr_id
            if not item.purchase_date:
                item.purchase_date = timezone.localdate()
            item.save()
            WarehouseRecord.objects.create(
                item=item,
                action=WarehouseRecord.ACTION_CREATED,
                note="Yangi mahsulot omborga qo'shildi",
            )
            return redirect("main:item_detail", pk=item.pk)
    else:
        form = QrItemAddForm(shop=shop)

    warranty_presets = [
        ("3 kun", 3),
        ("7 kun", 7),
        ("15 kun", 15),
        ("1 oy", 30),
        ("3 oy", 90),
        ("6 oy", 180),
        ("1 yil", 365),
    ]
    return render(request, "main/qr_item_form.html", {
        "shop": shop,
        "qr_id": qr_id,
        "form": form,
        "is_new": True,
        "warranty_presets": warranty_presets,
    })


# ── Quick sell new QR (create item + sell in one step) ────────────────────────

@login_required
def qr_quick_sell(request, qr_id: str):
    shop = _get_shop_for_request(request)
    if request.method != "POST":
        return redirect("main:qr_handler", qr_id=qr_id)

    # Create the item first using warehouse form data
    add_form = QrItemAddForm(request.POST, shop=shop)
    if add_form.is_valid():
        item = add_form.save(commit=False)
        item.shop = shop
        item.qr_id = qr_id
        if not item.purchase_date:
            item.purchase_date = timezone.localdate()
        # Apply sell fields from POST
        item.sold_price = request.POST.get("sold_price") or None
        item.client_phone = request.POST.get("client_phone", "")
        # Parse warranty date
        from django.utils.dateparse import parse_date
        raw_date = request.POST.get("warranty_until_date", "").strip()
        for fmt in ["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"]:
            try:

                item.warranty_until_date = datetime.strptime(raw_date, fmt).date()
                break
            except (ValueError, TypeError):
                pass
        if request.POST.get("warranty_mileage"):
            try:
                item.warranty_mileage = int(request.POST.get("warranty_mileage"))
                item.mileage_unit = request.POST.get("mileage_unit", "km")
            except (ValueError, TypeError):
                pass
        item.save()
        WarehouseRecord.objects.create(
            item=item,
            action=WarehouseRecord.ACTION_CREATED,
            note="Yangi mahsulot qo'shildi va sotildi",
        )
        WarehouseRecord.objects.create(
            item=item,
            action=WarehouseRecord.ACTION_UPDATED,
            note="Mahsulot sotildi, kafolat ma'lumotlari kiritildi",
        )
    return redirect("main:item_detail", pk=item.pk)


# ── Warehouse (all registered products) ────────────────────────────────────────

@login_required
def warehouse_list(request):
    shop = _get_shop_for_request(request)
    items = (
        QrItem.objects
        .filter(shop=shop)
        .filter(client_phone="")
        .select_related("product_type")
    )
    return render(request, "main/warehouse_list.html", {"shop": shop, "items": items})


# ── Item detail ────────────────────────────────────────────────────────────────

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
    return render(request, "main/item_detail.html", {"shop": shop, "item": item, "warranty_presets": warranty_presets})


# ── Sell item (modal POST) ─────────────────────────────────────────────────────

@login_required
def sell_item(request, pk: int):
    shop = _get_shop_for_request(request)
    item = get_object_or_404(QrItem, pk=pk, shop=shop)
    if request.method == "POST":
        form = QrItemSellForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            WarehouseRecord.objects.create(
                item=item,
                action=WarehouseRecord.ACTION_UPDATED,
                note="Mahsulot sotildi, kafolat ma'lumotlari kiritildi",
            )
    return redirect("main:item_detail", pk=pk)


# ── Revert sell (unsell — move back to warehouse) ──────────────────────────────

@login_required
def revert_sell(request, pk: int):
    shop = _get_shop_for_request(request)
    item = get_object_or_404(QrItem, pk=pk, shop=shop)
    if request.method == "POST":
        item.client_phone = ""
        item.sold_price = None
        item.warranty_until_date = None
        item.warranty_mileage = None
        item.mileage_unit = ""
        item.save()
        WarehouseRecord.objects.create(
            item=item,
            action=WarehouseRecord.ACTION_REVERTED,
            note="Sotuv bekor qilindi, mahsulot omborga qaytarildi",
        )
    return redirect("main:item_detail", pk=pk)


# ── History (sold products — items that have a client phone) ───────────────────

@login_required
def warranty_history(request):
    shop = _get_shop_for_request(request)
    # "sold" = items that have a client phone registered
    items = (
        QrItem.objects
        .filter(shop=shop)
        .exclude(client_phone="")
        .select_related("product_type")
    )
    return render(request, "main/warranty_history.html", {"shop": shop, "items": items})


# ── Profit detail (management) ────────────────────────────────────────────────

@login_required
def profit_detail(request):
    shop = _get_shop_for_request(request)

    date_from_str = request.GET.get("from", "").strip()
    date_to_str = request.GET.get("to", "").strip()

    items = (
        QrItem.objects
        .filter(shop=shop)
        .exclude(client_phone="")
        .exclude(buy_price__isnull=True)
        .exclude(sold_price__isnull=True)
        .select_related("product_type")
        .order_by("-purchase_date", "-created_at")
    )

    _date_formats = ["%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"]

    def _parse_date(s):
        for fmt in _date_formats:
            try:
                return datetime.strptime(s, fmt).date()
            except (ValueError, TypeError):
                pass
        return None

    date_from = None
    date_to = None

    if date_from_str:
        date_from = _parse_date(date_from_str)
        if date_from:
            items = items.filter(purchase_date__gte=date_from)

    if date_to_str:
        date_to = _parse_date(date_to_str)
        if date_to:
            items = items.filter(purchase_date__lte=date_to)

    profit_data = items.aggregate(total_sold=Sum("sold_price"), total_cost=Sum("buy_price"))
    total_profit = (profit_data["total_sold"] or 0) - (profit_data["total_cost"] or 0)

    items_with_profit = []
    for item in items:
        item.item_profit = (item.sold_price or 0) - (item.buy_price or 0)
        items_with_profit.append(item)

    return render(request, "main/profit_detail.html", {
        "shop": shop,
        "items": items_with_profit,
        "total_profit": total_profit,
        "date_from": date_from_str,
        "date_to": date_to_str,
        "item_count": len(items_with_profit),
    })


# ── Product types CRUD ────────────────────────────────────────────────────────

@login_required
def product_type_list(request):
    shop = _get_shop_for_request(request)
    product_types = shop.product_types.all().order_by("name")

    today = timezone.localdate()

    warehouse_total = (
        QrItem.objects
        .filter(shop=shop, client_phone="")
        .aggregate(total=Sum("buy_price"))["total"] or 0
    )

    sold_with_active_warranty = (
        QrItem.objects
        .filter(shop=shop)
        .exclude(client_phone="")
        .filter(Q(warranty_until_date__isnull=True) | Q(warranty_until_date__gte=today))
        .count()
    )

    profit_data = (
        QrItem.objects
        .filter(shop=shop)
        .exclude(client_phone="")
        .exclude(buy_price__isnull=True)
        .exclude(sold_price__isnull=True)
        .aggregate(total_sold=Sum("sold_price"), total_cost=Sum("buy_price"))
    )
    total_profit = (profit_data["total_sold"] or 0) - (profit_data["total_cost"] or 0)

    return render(request, "main/product_type_list.html", {
        "shop": shop,
        "product_types": product_types,
        "warehouse_total": warehouse_total,
        "sold_with_active_warranty": sold_with_active_warranty,
        "total_profit": total_profit,
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


# ── Profile / Settings ─────────────────────────────────────────────────────────

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


# ── Public customer page (/qr?id=…) ───────────────────────────────────────────

def public_item_from_query(request):
    qr_id = request.GET.get("id", "").strip()
    if not qr_id:
        raise Http404("QR id is required")
    item = get_object_or_404(QrItem.objects.select_related("shop", "product_type"), qr_id=qr_id)
    return render(request, "main/public_item_detail.html", {"item": item, "shop": item.shop})


# legacy path-based URL kept for backward compat
def public_item_detail(request, qr_id: str):
    item = get_object_or_404(QrItem.objects.select_related("shop", "product_type"), qr_id=qr_id)
    return render(request, "main/public_item_detail.html", {"item": item, "shop": item.shop})


# ── Shop registration (staff only) ────────────────────────────────────────────

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
