from django.urls import path

from . import views


app_name = "main"

urlpatterns = [
    path("", views.shop_home, name="shop_home"),
    path("qr/<str:qr_id>/", views.qr_handler, name="qr_handler"),
    path("warehouse/", views.warehouse_list, name="warehouse_list"),
    path("item/<int:pk>/", views.item_detail, name="item_detail"),
    path("p/<str:qr_id>/", views.public_item_detail, name="public_item_detail"),
    path("qr", views.public_item_from_query, name="public_item_from_query"),
    path("shops/register/", views.shop_register, name="shop_register"),
]

