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
    permission_classes = (IsAuthenticated,)

    def post(self, request):
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
        permission_classes = [IsAuthenticated]  # noqa: RUF012

    def post(self, request, store_id):  # noqa: F811
        store = Store.objects.get(id=store_id)

        if store.vendor != request.user:
            return Response(
                {"error": "You do not own this store."},
                status=403
            )

        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.save(store=store)

            return Response(
                ProductSerializer(product).data,
                status=201
            )

        return Response(serializer.errors, status=400)

class VendorStoresView(APIView):
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get(self, request, vendor_id):
        stores = Store.objects.filter(vendor_id=vendor_id)
        serializer = StoreSerializer(stores, many=True)

        return Response(serializer.data)


class StoreProductsView(APIView):

    def get(self, request, store_id):
        products = Product.objects.filter(store_id=store_id)
        serializer = ProductSerializer(products, many=True)

        return Response(serializer.data)


class StoreReviewsView(APIView):

    def get(self, request, store_id):
        reviews = Review.objects.filter(store_id=store_id)
        serializer = ReviewSerializer(reviews, many=True)

        return Response(serializer.data)
    