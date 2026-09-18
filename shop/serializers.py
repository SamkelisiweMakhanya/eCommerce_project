"""Serializers for the eCommerce application's REST API.

This module defines serializers for products, stores, reviews, users,
orders, authentication, and order status data.
"""

from typing import ClassVar

from django.contrib.auth.models import User
from rest_framework import serializers  # type: ignore[reportMissingImports]

from .models import Order, OrderItem, Product, Profile, Review, Store


class ProductSerializer(serializers.ModelSerializer):
    """Serialize product information for API requests and responses."""

    class Meta:
        """Define the model and fields used by ProductSerializer."""

        model = Product
        fields: ClassVar[list[str]] = [
            "id",
            "store",
            "name",
            "description",
            "price",
            "stock",
            "image",
        ]
        read_only_fields: ClassVar[list[str]] = ["store"]


class StoreSerializer(serializers.ModelSerializer):
    """Serialize store information and its associated products."""

    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        """Define the model and fields used by StoreSerializer."""

        model = Store
        fields = (
            "id",
            "vendor",
            "name",
            "description",
            "created_at",
            "updated_at",
            "products",
        )
        read_only_fields = (
            "vendor",
            "created_at",
            "updated_at",
            "products",
        )


class ReviewSerializer(serializers.ModelSerializer):
    """Serialize product reviews with buyer and product information."""

    buyer_username = serializers.CharField(
        source="buyer.username",
        read_only=True,
    )

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    class Meta:
        """Define the model and fields used by ReviewSerializer."""

        model = Review
        fields = (
            "id", "buyer", "buyer_username", "product", "product_name",
            "rating", "comment", "verified", "created_at",
        )
        read_only_fields: ClassVar[list[str]] = [
            "buyer", "verified", "created_at",
        ]

    def validate_rating(self, value):
        """Validate that a review rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """Serialize data required to register a new user."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        """Define the model and fields used during user registration."""

        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        """Create a new user and assign the default buyer role."""
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        Profile.objects.create(user=user, role="BUYER")
        return user


class OrderItemSerializer(serializers.ModelSerializer):
    """Serialize individual order items with product and store details."""

    product_name = serializers.CharField(source="product.name", read_only=True)

    store_name = serializers.CharField(
        source="product.store.name",
        read_only=True,
    )

    class Meta:
        """Define the model and fields used by OrderItemSerializer."""

        model = OrderItem
        fields = (
            "id", "product", "product_name", "store_name", "quantity", "price",
        )


class OrderSerializer(serializers.ModelSerializer):
    """Serialize order information and its associated order items."""

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        """Define the model and fields used by OrderSerializer."""

        model = Order
        fields = ("id", "buyer", "created_at", "total", "status", "items")
        read_only_fields = ("buyer", "created_at", "total", "status", "items")


class CreateOrderItemSerializer(serializers.Serializer):
    """Validate product and quantity data for a new order item."""

    product = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    """Validate the list of items submitted when creating an order."""

    items = CreateOrderItemSerializer(many=True)


class LoginSerializer(serializers.Serializer):
    """Validate username and password data for API authentication."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    """Define the response structure returned after successful login."""

    token = serializers.CharField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()


class VendorOrderStatusSerializer(serializers.Serializer):
    """Validate order status updates submitted by vendors."""

    status = serializers.ChoiceField(
        choices=["PAID", "COMPLETED", "CANCELLED"]
    )
