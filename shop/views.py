import json
from decimal import Decimal
from urllib.request import Request, urlopen

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem, Product, Profile, Review, Store
from .serializers import RegisterSerializer


def get_reddit_posts(subreddit):
    """Return Reddit posts without depending on a missing local module."""
    request = Request(
        f"https://www.reddit.com/r/{subreddit}/new.json?limit=10",
        headers={"User-Agent": "ecommerce-project/1.0"},
    )

    try:
        with urlopen(request, timeout=5) as response:
            data = json.load(response)
    except (OSError, ValueError, json.JSONDecodeError):
        return []

    return [
        item.get("data", {})
        for item in data.get("data", {}).get("children", [])
    ]

# ============================================================
# HOME / PRODUCTS
# ============================================================


# views.py

def home(request):
    return render(request, 'shop/home.html')


def product_list(request):
    products = Product.objects.all()

    return render(
        request,
        'shop/product_list.html',
        {'products': products}
    )


def product_detail(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
    )

    reviews = product.reviews.select_related("buyer").all()

    return render(
        request,
        "shop/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
        },
    )


# ============================================================
# REVIEWS
# ============================================================

@login_required
def submit_review(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
    )

    if request.method != "POST":
        return redirect(
            "product_detail",
            product_id=product.id,
        )

    rating = request.POST.get("rating", "").strip()
    comment = request.POST.get("comment", "").strip()

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        messages.error(
            request,
            "Please select a rating between 1 and 5.",
        )
        return redirect(
            "product_detail",
            product_id=product.id,
        )

    if rating < 1 or rating > 5:
        messages.error(
            request,
            "Rating must be between 1 and 5.",
        )
        return redirect(
            "product_detail",
            product_id=product.id,
        )

    if not comment:
        messages.error(
            request,
            "Please enter a comment.",
        )
        return redirect(
            "product_detail",
            product_id=product.id,
        )

    existing_review = Review.objects.filter(
        buyer=request.user,
        product=product,
    ).first()

    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        existing_review.save()

        messages.success(
            request,
            "Your review has been updated.",
        )
    else:
        Review.objects.create(
            buyer=request.user,
            product=product,
            rating=rating,
            comment=comment,
            verified=False,
        )

        messages.success(
            request,
            "Your review has been submitted.",
        )

    return redirect(
        "product_detail",
        product_id=product.id,
    )


# ============================================================
# LOGIN / REGISTER / LOGOUT
# ============================================================

def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)

            messages.success(
                request,
                "You have successfully logged in.",
            )

            try:
                role = user.profile.role
            except Profile.DoesNotExist:
                role = "BUYER"

            if role == "VENDOR":
                return redirect("vendor_dashboard")

            return redirect("home")

        messages.error(
            request,
            "Invalid username or password.",
        )

    return render(
        request,
        "shop/login.html",
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        role = request.POST.get("role", "BUYER").upper()

        if not username:
            messages.error(
                request,
                "Username is required.",
            )
            return render(request, "shop/register.html")

        if not password:
            messages.error(
                request,
                "Password is required.",
            )
            return render(request, "shop/register.html")

        if password != password2:
            messages.error(
                request,
                "Passwords do not match.",
            )
            return render(request, "shop/register.html")

        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "That username is already taken.",
            )
            return render(request, "shop/register.html")

        if role not in {"BUYER", "VENDOR"}:
            role = "BUYER"

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        Profile.objects.create(
            user=user,
            role=role,
            vendor=user if role == "VENDOR" else None,
        )

        login(
            request,
            user,
        )

        messages.success(
            request,
            "Your account has been created.",
        )

        if role == "VENDOR":
            return redirect("vendor_dashboard")

        return redirect("buyer_dashboard")

    return render(
        request,
        "shop/register.html",
    )


@login_required
def user_logout(request):
    logout(request)

    messages.success(
        request,
        "You have been logged out.",
    )

    return redirect("home")


# ============================================================
# BUYER DASHBOARD
# ============================================================

@login_required
def buyer_dashboard(request):
    orders = Order.objects.filter(
        buyer=request.user,
    ).order_by("-created_at")

    return render(
        request,
        "shop/buyer_dashboard.html",
        {
            "orders": orders,
        },
    )


# ============================================================
# VENDOR DASHBOARD
# ============================================================

@login_required
def vendor_dashboard(request):
    profile = Profile.objects.get(user=request.user)

    store = Store.objects.filter(
        vendor=request.user
    ).first()

    products = Product.objects.filter(
        store__vendor=request.user
    ).select_related("store")

    context = {
        "profile": profile,
        "store": store,
        "products": products,
    }

    return render(
        request,
        "shop/vendor_dashboard.html",
        context,
    )

# ============================================================
# CREATE PRODUCT
# ============================================================


@login_required
def product_create(request, store_id):
    store = get_object_or_404(
        Store,
        id=store_id,
        vendor=request.user,
    )

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        price = request.POST.get("price")
        image = request.FILES.get("image")

        Product.objects.create(
            store=store,
            name=name,
            description=description,
            price=price,
            image=image,
        )

        return redirect("vendor_dashboard")

    return render(
        request,
        "shop/product_create.html",
        {"store": store},
    )

# ============================================================
# CART HELPERS
# ============================================================


def _get_cart(request):
    cart_data = request.session.get("cart", {})

    if not isinstance(cart_data, dict):
        cart_data = {}

    return cart_data


def _save_cart(request, cart_data):
    request.session["cart"] = cart_data
    request.session.modified = True


def _get_cart_items(request):
    cart_data = _get_cart(request)

    product_ids = []

    for product_id in cart_data:
        try:
            product_ids.append(int(product_id))
        except (TypeError, ValueError):
            continue

    products = Product.objects.filter(
        id__in=product_ids,
    )

    product_map = {
        str(product.id): product
        for product in products
    }

    items = []
    total = Decimal("0.00")

    for product_id, quantity in cart_data.items():
        product = product_map.get(str(product_id))

        if product is None:
            continue

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 1

        quantity = max(quantity, 1)

        item_total = product.price * quantity
        total += item_total

        items.append(
            {
                "product": product,
                "quantity": quantity,
                "total": item_total,
            }
        )

    return items, total


# ============================================================
# CART
# ============================================================

def cart(request):
    items, total = _get_cart_items(request)

    return render(
        request,
        "shop/cart.html",
        {
            "items": items,
            "cart_items": items,
            "total": total,
            "cart_total": total,
        },
    )


def cart_add(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
    )

    if product.stock <= 0:
        messages.error(
            request,
            "This product is out of stock.",
        )
        return redirect("product_list")

    cart_data = _get_cart(request)

    key = str(product.id)

    try:
        current_quantity = int(cart_data.get(key, 0))
    except (TypeError, ValueError):
        current_quantity = 0

    if current_quantity >= product.stock:
        messages.warning(
            request,
            "You cannot add more than the available stock.",
        )
        return redirect("cart")

    cart_data[key] = current_quantity + 1

    _save_cart(
        request,
        cart_data,
    )

    messages.success(
        request,
        f"{product.name} was added to your cart.",
    )

    return redirect("cart")


def cart_remove(request, product_id):
    cart_data = _get_cart(request)

    key = str(product_id)

    if key in cart_data:
        del cart_data[key]

        _save_cart(
            request,
            cart_data,
        )

        messages.success(
            request,
            "Product removed from your cart.",
        )

    return redirect("cart")


# ============================================================
# CHECKOUT
# ============================================================

@login_required
def checkout(request):
    items, total = _get_cart_items(request)

    if not items:
        messages.warning(
            request,
            "Your cart is empty.",
        )
        return redirect("cart")

    if request.method == "POST":
        cart_data = _get_cart(request)

        with transaction.atomic():
            products = Product.objects.select_for_update().filter(
                id__in=[
                    int(product_id)
                    for product_id in cart_data
                    if str(product_id).isdigit()
                ]
            )

            product_map = {
                str(product.id): product
                for product in products
            }

            order_total = Decimal("0.00")
            validated_items = []

            for product_id, quantity in cart_data.items():
                product = product_map.get(str(product_id))

                if product is None:
                    continue

                try:
                    quantity = int(quantity)
                except (TypeError, ValueError):
                    quantity = 1

                quantity = max(quantity, 1)

                if quantity > product.stock:
                    messages.error(
                        request,
                        f"Not enough stock available for {product.name}.",
                    )
                    return redirect("cart")

                item_total = product.price * quantity
                order_total += item_total

                validated_items.append(
                    (
                        product,
                        quantity,
                    )
                )

            if not validated_items:
                messages.warning(
                    request,
                    "Your cart is empty.",
                )
                return redirect("cart")

            order = Order.objects.create(
                buyer=request.user,
                total=order_total,
                status="PENDING",
            )

            for product, quantity in validated_items:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                )

                product.stock -= quantity
                product.save(
                    update_fields=["stock"]
                )

        request.session["cart"] = {}
        request.session.modified = True

        return redirect(
            "checkout_success",
            order_id=order.id,
        )

    return render(
        request,
        "shop/checkout.html",
        {
            "items": items,
            "total": total,
            "cart_total": total,
        },
    )


# ============================================================
# CHECKOUT SUCCESS
# ============================================================

@login_required
def checkout_success(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        buyer=request.user,
    )

    return render(
        request,
        "shop/checkout_success.html",
        {
            "order": order,
        },
    )


# ============================================================
# ORDERS
# ============================================================

@login_required
def my_orders(request):
    orders = Order.objects.filter(
        buyer=request.user,
    ).prefetch_related(
        "items__product",
    ).order_by("-created_at")

    return render(
        request,
        "shop/my_orders.html",
        {
            "orders": orders,
        },
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product",
        ),
        id=order_id,
        buyer=request.user,
    )

    return render(
        request,
        "shop/order_detail.html",
        {
            "order": order,
        },
    )


def reddit_feed(request):
    # Call our helper function to fetch posts
    posts = get_reddit_posts("python")
    # Pass the posts into the template
    return render(request, "reddit_feed.html", {"posts": posts})


@extend_schema(
    auth=[],
    request=RegisterSerializer,
    responses={
        201: {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "username": {"type": "string"},
                "email": {"type": "string"},
            },
        },
    },
)
class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "User registered successfully.",
                    "username": user.username,
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
