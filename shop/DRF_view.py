"""API views for managing stores, products, and reviews."""

# flake8: noqa: N999

from rest_framework import status  # pyright: ignore[reportMissingImports]
from rest_framework.permissions import (  # pyright: ignore[reportMissingImports]
    IsAuthenticated,
)
from rest_framework.response import (  # pyright: ignore[reportMissingImports]
    Response,
)
from rest_framework.views import (  # pyright: ignore[reportMissingImports]
    APIView,
)

from .models import Product, Review, Store
from .serializers import ProductSerializer, ReviewSerializer, StoreSerializer


class StoreCreateView(APIView):
    """Provide an API endpoint for creating a new store."""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Create a store belonging to the authenticated user.

        Args:
            request: The HTTP request containing the store data.

        Returns:
            A response containing the created store data, or validation
            errors if the submitted data is invalid.
        """
        serializer = StoreSerializer(data=request.data)

        if serializer.is_valid():
            store = serializer.save(vendor=request.user)
            return Response(
                StoreSerializer(store).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProductCreateView(APIView):
    """Provide an API endpoint for creating products in a store."""

    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def post(self, request, store_id):
        """Create a product in a store owned by the authenticated user.

    Args:
        request: The HTTP request containing product data.
        store_id: The database ID of the store receiving the product.

    Returns:
        A response containing the created product data, or an error
        response if the user does not own the store or validation fails.
        """
        store = Store.objects.get(id=store_id)

        if store.vendor != request.user:
            return Response(
                {"error": "You do not own this store."},
                status=403,
            )

        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.save(store=store)

            return Response(
                ProductSerializer(product).data,
                status=201,
            )

        return Response(serializer.errors, status=400)

class VendorStoresView(APIView):
    """Provide an API endpoint for retrieving a vendor's stores."""

    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get(self, request, vendor_id):
        """Return all stores belonging to a specified vendor.

    Args:
        request: The HTTP request received from the client.
        vendor_id: The database ID of the vendor.

    Returns:
        A response containing the serialized vendor stores.
        """
        stores = Store.objects.filter(vendor_id=vendor_id)
        serializer = StoreSerializer(stores, many=True)

        return Response(serializer.data)

class StoreProductsView(APIView):
    """Provide an API endpoint for retrieving products in a store."""

    def get(self, request, store_id):
        """Return all products belonging to a specified store.

    Args:
        request: The HTTP request received from the client.
        store_id: The database ID of the store.

    Returns:
        A response containing the serialized store products.
        """
        products = Product.objects.filter(store_id=store_id)
        serializer = ProductSerializer(products, many=True)

        return Response(serializer.data)


class StoreReviewsView(APIView):
    """Provide an API endpoint for retrieving reviews for a store."""


    def get(self, request, store_id):
        """Return all reviews associated with a specified store.

    Args:
        request: The HTTP request received from the client.
        store_id: The database ID of the store.

    Returns:
        A response containing the serialized store reviews.
        """
        reviews = Review.objects.filter(store_id=store_id)
        serializer = ReviewSerializer(reviews, many=True)

        return Response(serializer.data)
