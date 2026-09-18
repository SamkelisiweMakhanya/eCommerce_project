"""URL configuration for the eCommerce application.

This module maps browser and API URL patterns to their corresponding
Django views and REST API class-based views.
"""

from django.urls import path

from . import views
from .api_views import (
    CancelOrderAPIView,
    CreateOrderAPIView,
    LoginAPIView,
    MyOrderDetailAPIView,
    MyOrdersAPIView,
    PayOrderAPIView,
    ProductCreateView,
    RedditPostsAPIView,
    StoreCreateView,
    StoreReviewsView,
    VendorOrderDetailAPIView,
    VendorOrdersAPIView,
    VendorOrderStatusAPIView,
    VendorStoresView,
)

# ============================================================

# URL PATTERNS

# ============================================================

urlpatterns = [
    # Home and product pages.
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

    # Authentication and user account pages.
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

    # Vendor product management.
    path(
        "store/<int:store_id>/product/create/",
        views.product_create,
        name="product_create",
    ),

    # Shopping cart.
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

    # Checkout and order pages.
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

    # Reddit feed.
    path("reddit/", views.reddit_feed, name="reddit_feed"),

    # Store and vendor API endpoints.
    path(
        "api/stores/",
        StoreCreateView.as_view(),
        name="store-create",
    ),

    path(
        "api/stores/<int:store_id>/products/",
        ProductCreateView.as_view(),
        name="store-products",
    ),

    path(
        "api/vendors/<int:vendor_id>/stores/",
        VendorStoresView.as_view(),
        name="vendor-stores",
    ),

    path(
        "api/stores/<int:store_id>/reviews/",
        StoreReviewsView.as_view(),
        name="store-reviews",
    ),

    # Authentication API endpoints.
    path(
        "api/register/",
        views.RegisterAPIView.as_view(),
        name="api-register",
    ),

    path(
        "api/login/",
        LoginAPIView.as_view(),
        name="api-login",
    ),

    # Reddit API endpoint.
    path(
        "api/reddit/django/",
        RedditPostsAPIView.as_view(),
        name="reddit-django",
    ),

    # Buyer order API endpoints.
    path(
        "api/orders/",
        MyOrdersAPIView.as_view(),
        name="api-orders",
    ),

    path(
        "api/orders/create/",
        CreateOrderAPIView.as_view(),
        name="create-order-api",
    ),

    path(
        "api/orders/<int:order_id>/",
        MyOrderDetailAPIView.as_view(),
        name="my-order-detail-api",
    ),

    path(
        "api/orders/<int:order_id>/cancel/",
        CancelOrderAPIView.as_view(),
        name="cancel-order-api",
    ),

    path(
        "api/orders/<int:order_id>/pay/",
        PayOrderAPIView.as_view(),
        name="pay-order-api",
    ),

    # Vendor order API endpoints.
    path(
        "api/vendor/orders/",
        VendorOrdersAPIView.as_view(),
        name="vendor-orders-api",
    ),

    path(
        "api/vendor/orders/<int:order_id>/status/",
        VendorOrderStatusAPIView.as_view(),
        name="vendor-order-status-api",
    ),

    path(
        "api/vendor/orders/<int:order_id>/",
        VendorOrderDetailAPIView.as_view(),
        name="vendor-order-detail-api",
    ),

    # Note:
    # The original file contained a second Reddit URL with a different
    # URL name. It is preserved here to avoid changing functionality.
    path(
        "reddit/",
        views.reddit_feed,
        name="reddit-feed",
    ),

]
