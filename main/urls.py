from django.urls import path

from . import views


app_name = "main"

urlpatterns = [
    path("", views.shop_home, name="shop_home"),
    path("qr/<str:qr_id>/", views.qr_handler, name="qr_handler"),
    path("warehouse/", views.warehouse_list, name="warehouse_list"),
    path("product-types/", views.product_type_list, name="product_type_list"),
    path("product-types/create/", views.product_type_create, name="product_type_create"),
    path("product-types/<int:pk>/edit/", views.product_type_edit, name="product_type_edit"),
    path("product-types/<int:pk>/delete/", views.product_type_delete, name="product_type_delete"),
    path("item/<int:pk>/", views.item_detail, name="item_detail"),
    path("item/<int:pk>/sell/", views.sell_item, name="sell_item"),
    path("item/<int:pk>/revert/", views.revert_sell, name="revert_sell"),
    path("history/", views.warranty_history, name="warranty_history"),
    path("profile/", views.shop_profile, name="shop_profile"),
    path("p/<str:qr_id>/", views.public_item_detail, name="public_item_detail"),
    path("qr", views.public_item_from_query, name="public_item_from_query"),
    path("shops/register/", views.shop_register, name="shop_register"),
]

