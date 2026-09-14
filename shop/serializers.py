from typing import ClassVar

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Order, OrderItem, Product, Profile, Review, Store


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
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
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
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
    buyer_username = serializers.CharField(
        source="buyer.username",
        read_only=True,
    )

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    class Meta:
        model = Review
        fields = (
            "id",
            "buyer",
            "buyer_username",
            "product",
            "product_name",
            "rating",
            "comment",
            "verified",
            "created_at",
        )
        read_only_fields: ClassVar[list[str]] = [
            "buyer",
            "verified",
            "created_at",
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )

        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )

        Profile.objects.create(
            user=user,
            role="BUYER",
        )

        return user


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    store_name = serializers.CharField(
        source="product.store.name",
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "product_name",
            "store_name",
            "quantity",
            "price",
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "buyer",
            "created_at",
            "total",
            "status",
            "items",
        )
        read_only_fields = (
            "buyer",
            "created_at",
            "total",
            "status",
            "items",
        )


class CreateOrderItemSerializer(serializers.Serializer):
    product = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    items = CreateOrderItemSerializer(many=True)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()


class VendorOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["PAID", "COMPLETED", "CANCELLED"]
    )
