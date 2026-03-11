from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import QrItemForm, ShopRegistrationForm
from .models import QrItem, Shop


def _get_shop_for_request(request) -> Shop:
    if request.user.is_authenticated:
        shop, _ = Shop.objects.get_or_create(
            user=request.user,
            defaults={"name": request.user.get_username() or "My Shop"},
        )
        return shop
    shop, _ = Shop.objects.get_or_create(name="Default Shop")
    return shop


@login_required
def shop_home(request):
    shop = _get_shop_for_request(request)
    context = {
        "shop": shop,
    }
    return render(request, "main/shop_home.html", context)


@login_required
def qr_handler(request, qr_id: str):
    shop = _get_shop_for_request(request)
    try:
        item = QrItem.objects.get(shop=shop, qr_id=qr_id)
        return redirect("main:item_detail", pk=item.pk)
    except QrItem.DoesNotExist:
        pass

    if request.method == "POST":
        form = QrItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.shop = shop
            item.qr_id = qr_id
            item.save()
            return redirect("main:item_detail", pk=item.pk)
    else:
        form = QrItemForm()

    context = {
        "shop": shop,
        "qr_id": qr_id,
        "form": form,
    }
    return render(request, "main/qr_item_form.html", context)


@login_required
def warehouse_list(request):
    shop = _get_shop_for_request(request)
    items = QrItem.objects.filter(shop=shop)
    context = {
        "shop": shop,
        "items": items,
    }
    return render(request, "main/warehouse_list.html", context)


@login_required
def item_detail(request, pk: int):
    shop = _get_shop_for_request(request)
    item = get_object_or_404(QrItem, pk=pk, shop=shop)
    context = {
        "shop": shop,
        "item": item,
    }
    return render(request, "main/item_detail.html", context)


def public_item_detail(request, qr_id: str):
    item = get_object_or_404(QrItem, qr_id=qr_id)
    context = {
        "item": item,
        "shop": item.shop,
    }
    return render(request, "main/public_item_detail.html", context)


def public_item_from_query(request):
    qr_id = request.GET.get("id")
    if not qr_id:
        raise Http404("QR id is required")
    item = get_object_or_404(QrItem, qr_id=qr_id)
    context = {
        "item": item,
        "shop": item.shop,
    }
    return render(request, "main/public_item_detail.html", context)


@staff_member_required
def shop_register(request):
    if request.method == "POST":
        form = ShopRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = ShopRegistrationForm()

    context = {"form": form}
    return render(request, "main/shop_register.html", context)
