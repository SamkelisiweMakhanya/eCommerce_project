"""API views for the eCommerce application.

This module provides REST API endpoints for authentication, stores,
products, reviews, orders, payments, and Reddit posts.
"""

from decimal import Decimal
from typing import ClassVar

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
from functions.reddit import get_reddit_posts
from rest_framework import generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem, Product, Review, Store
from .serializers import (
    CreateOrderSerializer,
    LoginSerializer,
    OrderSerializer,
    ProductSerializer,
    ReviewSerializer,
    StoreSerializer,
    VendorOrderStatusSerializer,
)


@extend_schema(
    auth=[],
    request=LoginSerializer,
    responses={
        200: {
            "type": "object",
        },
    },
)
class LoginAPIView(APIView):
    """Authenticate users and return an authentication token."""

    permission_classes = []  # noqa: RUF012

    def post(self, request):
        """Authenticate a user using the supplied username and password.

        Args:
            request: The HTTP request containing login credentials.

        Returns:
            A response containing the authentication token and user
            information, or an error response for invalid credentials.
        """
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(
            username=username,
            password=password,
        )

        if user is None:
            return Response(
                {"error": "Invalid username or password."},
                status=400,
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
        })


class StoreCreateView(generics.ListCreateAPIView):
    """List existing stores and allow vendors to create new stores."""

    serializer_class = StoreSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Return all stores with their associated vendor information.

        Returns:
            A queryset containing all stores with vendor data loaded.
        """
        return Store.objects.all().select_related("vendor")

    def perform_create(self, serializer):
        """Create a store for the authenticated vendor.

        Args:
            serializer: The serializer containing the submitted store data.

        Raises:
            PermissionDenied: If the user has no profile or is not a vendor.
        """
        if not hasattr(self.request.user, "profile"):
            raise PermissionDenied("You do not have a profile.")

        if self.request.user.profile.role != "VENDOR":
            raise PermissionDenied(
                "Only vendors can create stores."
            )

        serializer.save(vendor=self.request.user)


class ProductCreateView(generics.ListCreateAPIView):
    """List products for a store and allow its vendor to add products."""

    serializer_class = ProductSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Return products belonging to the requested store.

        An optional search parameter filters products by name.

        Returns:
            A queryset containing products for the selected store.
        """
        store = generics.get_object_or_404(
            Store,
            id=self.kwargs["store_id"],
        )

        search = self.request.query_params.get("search")

        queryset = Product.objects.filter(
            store=store
        ).select_related("store")

        if search:
            queryset = queryset.filter(
                name__icontains=search
            )

        return queryset

    def perform_create(self, serializer):
        """Create a product in a store owned by the authenticated vendor.

        Args:
            serializer: The serializer containing the submitted product data.

        Raises:
            PermissionDenied: If the authenticated user does not own
                the selected store.
        """
        store = generics.get_object_or_404(
            Store,
            id=self.kwargs["store_id"],
        )

        if store.vendor != self.request.user:
            raise PermissionDenied(
                "You can only add products to your own store."
            )

        serializer.save(store=store)


class VendorStoresView(generics.ListAPIView):
    """List all stores belonging to a specified vendor."""

    serializer_class = StoreSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        """Return stores belonging to the requested vendor.

        Returns:
            A queryset containing stores owned by the specified vendor.
        """
        vendor = generics.get_object_or_404(
            User,
            id=self.kwargs["vendor_id"],
        )

        return Store.objects.filter(
            vendor=vendor
        ).select_related("vendor")


class StoreReviewsView(generics.ListCreateAPIView):
    """List reviews for a store and allow eligible buyers to create reviews."""

    serializer_class = ReviewSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        """Return reviews associated with products in the requested store.

        Returns:
            A queryset containing store reviews with buyer and product
            information loaded.
        """
        store = generics.get_object_or_404(
            Store,
            id=self.kwargs["store_id"],
        )

        return Review.objects.filter(
            product__store=store
        ).select_related(
            "buyer",
            "product",
        )

    def perform_create(self, serializer):
        """Create a verified review for a purchased product.

        Args:
            serializer: The serializer containing the submitted review data.

        Raises:
            PermissionDenied: If the product is missing, does not belong
                to the store, has not been purchased by the user, or has
                already been reviewed by the user.
        """
        product_id = self.request.data.get("product")

        if not product_id:
            raise PermissionDenied(
                "A product is required for a review."
            )

        product = generics.get_object_or_404(
            Product,
            id=product_id,
        )

        store = generics.get_object_or_404(
            Store,
            id=self.kwargs["store_id"],
        )

        if product.store_id != store.id:
            raise PermissionDenied(
                "That product does not belong to this store."
            )

        if not OrderItem.objects.filter(
            order__buyer=self.request.user,
            product=product,
        ).exists():
            raise PermissionDenied(
                "You can only review products you have purchased."
            )

        if Review.objects.filter(
            buyer=self.request.user,
            product=product,
        ).exists():
            raise PermissionDenied(
                "You have already reviewed this product."
            )

        serializer.save(
            buyer=self.request.user,
            product=product,
            verified=True,
        )


class MyOrdersAPIView(generics.ListAPIView):
    """Return the authenticated buyer's orders."""

    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Return orders belonging to the authenticated buyer.

        Returns:
            A queryset containing the buyer's orders ordered from newest
            to oldest.
        """
        return Order.objects.filter(
            buyer=self.request.user
        ).prefetch_related(
            "items__product"
        ).order_by("-created_at")


class MyOrderDetailAPIView(generics.RetrieveAPIView):
    """Return details for a single order belonging to the buyer."""

    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_url_kwarg = "order_id"

    def get_queryset(self):
        """Return orders belonging to the authenticated buyer.

        Returns:
            A queryset containing the buyer's orders and their products.
        """
        return Order.objects.filter(
            buyer=self.request.user
        ).prefetch_related(
            "items__product"
        )


@extend_schema(
    request=None,
    responses=OrderSerializer,
)
class CancelOrderAPIView(APIView):
    """Cancel a pending order and restore its product stock."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, order_id):
        """Cancel the specified pending order.

        Args:
            request: The HTTP request from the authenticated buyer.
            order_id: The database ID of the order to cancel.

        Returns:
            A response containing the cancelled order or an error message.
        """
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().prefetch_related(
                    "items__product"
                ).get(
                    id=order_id,
                    buyer=request.user,
                )
            except Order.DoesNotExist:
                return Response(
                    {"error": "Order not found."},
                    status=404,
                )

            if order.status != "PENDING":
                return Response(
                    {
                        "error": (
                            "Only pending orders can be cancelled."
                        )
                    },
                    status=400,
                )

            for item in order.items.all():
                product = Product.objects.select_for_update().get(
                    id=item.product_id
                )

                product.stock += item.quantity
                product.save(update_fields=["stock"])

            order.status = "CANCELLED"
            order.save(update_fields=["status"])

        return Response(
            OrderSerializer(order).data,
            status=200,
        )


class VendorOrdersAPIView(generics.ListAPIView):
    """Return orders containing the authenticated vendor's products."""

    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Return orders associated with the authenticated vendor's products.

        Raises:
            PermissionDenied: If the user has no profile or is not a vendor.

        Returns:
            A queryset containing the vendor's relevant orders.
        """
        if not hasattr(self.request.user, "profile"):
            raise PermissionDenied("You do not have a profile.")

        if self.request.user.profile.role != "VENDOR":
            raise PermissionDenied(
                "Only vendors can view vendor orders."
            )

        return Order.objects.filter(
            items__product__store__vendor=self.request.user
        ).prefetch_related(
            "items__product"
        ).distinct().order_by("-created_at")


class VendorOrderDetailAPIView(generics.RetrieveAPIView):
    """Return details of an order associated with the authenticated vendor."""

    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_url_kwarg = "order_id"

    def get_queryset(self):
        """Return orders containing products from the vendor's stores.

        Raises:
            PermissionDenied: If the user has no profile or is not a vendor.

        Returns:
            A queryset containing orders associated with the vendor.
        """
        if not hasattr(self.request.user, "profile"):
            raise PermissionDenied("You do not have a profile.")

        if self.request.user.profile.role != "VENDOR":
            raise PermissionDenied(
                "Only vendors can view vendor orders."
            )

        return (
            Order.objects.filter(
                items__product__store__vendor=self.request.user
            )
            .prefetch_related("items__product__store")
            .distinct()
        )


@extend_schema(
    request=VendorOrderStatusSerializer,
    responses=OrderSerializer,
)
class VendorOrderStatusAPIView(APIView):
    """Allow vendors to update the status of their orders."""

    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, order_id):
        """Update the status of an order belonging to the vendor.

    Args:
        request: The HTTP request containing the new order status.
        order_id: The database ID of the order to update.

    Returns:
        A response containing the updated order or an error message.

    Raises:
        PermissionDenied: If the authenticated user is not a vendor.
        """
        if not hasattr(request.user, "profile"):
            raise PermissionDenied("You do not have a profile.")

        if request.user.profile.role != "VENDOR":
            raise PermissionDenied(
                "Only vendors can update order status."
            )

        new_status = request.data.get("status")

        allowed_statuses = ["PAID", "COMPLETED", "CANCELLED"]

        if new_status not in allowed_statuses:
            return Response(
                {
                    "error": (
                        "Status must be PAID, COMPLETED, or CANCELLED."
                    )
                },
                status=400,
            )

        try:
            order = Order.objects.get(
                id=order_id,
                items__product__store__vendor=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=404,
            )

        if order.status == "CANCELLED":
            return Response(
                {"error": "Cancelled orders cannot be updated."},
                status=400,
            )

        if order.status == "COMPLETED":
            return Response(
                {"error": "Completed orders cannot be updated."},
                status=400,
            )

        if order.status == "PENDING" and new_status == "COMPLETED":
            return Response(
                {
                    "error": (
                        "A pending order must be marked PAID "
                        "before it can be completed."
                    )
                },
                status=400,
            )

        order.status = new_status
        order.save(update_fields=["status"])

        return Response(
            OrderSerializer(order).data,
            status=200,
        )


@extend_schema(
    request=CreateOrderSerializer,
    responses=OrderSerializer,
)
class CreateOrderAPIView(APIView):
    """Create an order for the authenticated buyer."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """Create an order from the submitted products and quantities.

        Args:
            request: The HTTP request containing order data.

        Returns:
            A response containing the created order or an error message.
        """
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data["items"]
        product_ids = [item["product"] for item in items]

        if len(product_ids) != len(set(product_ids)):
            return Response(
                {
                    "error": "The same product cannot appear more than once."
                },
                status=400,
            )

        if not items:
            return Response(
                {"error": "Your order must contain at least one product."},
                status=400,
            )

        with transaction.atomic():
            total = Decimal("0.00")
            order_items = []

            for item in items:
                try:
                    product = Product.objects.select_for_update().get(
                        id=item["product"]
                    )
                except Product.DoesNotExist:
                    return Response(
                        {
                            "error": (
                                f"Product {item['product']} does not exist."
                            )
                        },
                        status=400,
                    )

                quantity = item["quantity"]

                if product.stock < quantity:
                    return Response(
                        {
                            "error": (
                                f"Not enough stock for {product.name}. "
                                f"Available: {product.stock}."
                            )
                        },
                        status=400,
                    )

                item_total = product.price * quantity
                total += item_total

                order_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                        "price": product.price,
                    }
                )

            order = Order.objects.create(
                buyer=request.user,
                total=total,
                status="PENDING",
            )

            for item in order_items:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    quantity=item["quantity"],
                    price=item["price"],
                )

                item["product"].stock -= item["quantity"]
                item["product"].save(update_fields=["stock"])

        return Response(
            OrderSerializer(order).data,
            status=201,
        )


@extend_schema(
    request=None,
    responses=OrderSerializer,
)
class PayOrderAPIView(APIView):
    """Allow an authenticated buyer to pay for a pending order."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, order_id):
        """Mark a pending order as paid.

        Args:
            request: The HTTP request from the authenticated buyer.
            order_id: The database ID of the order to pay.

        Returns:
            A response containing the updated order or an error message.
        """
        try:
            order = Order.objects.get(
                id=order_id,
                buyer=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=404,
            )

        if order.status != "PENDING":
            return Response(
                {
                    "error": (
                        "Only pending orders can be paid."
                    )
                },
                status=400,
            )

        order.status = "PAID"
        order.save(update_fields=["status"])

        return Response(
            OrderSerializer(order).data,
            status=200,
        )


@extend_schema(
    responses={
        200: OpenApiResponse(
            description="Reddit posts from r/django."
        ),
        503: OpenApiResponse(
            description="Reddit is unavailable."
        ),
    }
)
class RedditPostsAPIView(APIView):
    """Provide an API endpoint for retrieving Django Reddit posts."""

    permission_classes: ClassVar[list] = [permissions.AllowAny]

    def get(self, request):
        """Retrieve and return posts from the Django subreddit.

        Args:
            request: The HTTP request received from the API client.

        Returns:
            A response containing Reddit posts, or a 503 response when
            Reddit is unavailable.
        """
        data = get_reddit_posts("django")

        if "error" in data:
            return Response(data, status=503)

        return Response(data)
