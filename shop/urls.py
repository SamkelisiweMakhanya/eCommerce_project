from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("products/", views.product_list, name="product_list"),

    path(
        "products/<int:product_id>/",
        views.product_detail,
        name="product_detail",
    ),

    path(
        "products/<int:product_id>/review/",
        views.submit_review,
        name="submit_review",
    ),

    path("login/", views.user_login, name="login"),

    path("register/", views.register, name="register"),

    path(
        "buyer/",
        views.buyer_dashboard,
        name="buyer_dashboard",
    ),

    path(
        "vendor/",
        views.vendor_dashboard,
        name="vendor_dashboard",
    ),

    path(
        "logout/",
        views.user_logout,
        name="logout",
    ),

    path(
        "store/<int:store_id>/product/create/",
        views.product_create,
        name="product_create",
    ),

    path(
        "cart/",
        views.cart,
        name="cart",
    ),

    path(
        "cart/add/<int:product_id>/",
        views.cart_add,
        name="cart_add",
    ),

    path(
        "cart/remove/<int:product_id>/",
        views.cart_remove,
        name="cart_remove",
    ),

    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),

    path(
        "checkout/success/<int:order_id>/",
        views.checkout_success,
        name="checkout_success",
    ),

    path(
        "orders/",
        views.my_orders,
        name="my_orders",
    ),

    path(
        "orders/<int:order_id>/",
        views.order_detail,
        name="order_detail",
    ),

]
