import json
import re
from decimal import Decimal
from functools import wraps
from io import BytesIO
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Avg, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import ProductForm, RegistrationForm, StoreForm
from .models import Order, OrderItem, Product, Profile, Review, Store
from .serializers import RegisterSerializer


def role_required(required_role):
    """Require the user to be logged in and have the specified role."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            profile = Profile.objects.filter(
                user=request.user
            ).first()

            role = profile.role if profile else "BUYER"

            if role != required_role:
                messages.error(
                    request,
                    "You do not have permission to access this page."
                )

                if role == "VENDOR":
                    return redirect("vendor_dashboard")

                return redirect("home")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def get_reddit_posts(subreddit, limit=10):
    """
    Fetch recent posts from a Reddit subreddit.

    Args:
        subreddit: The name of the Reddit subreddit.
        limit: Maximum number of posts to retrieve.

    Returns:
        A list of Reddit post data dictionaries. Returns an empty
        list if Reddit is unavailable or the response is invalid.
    """
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    request = Request(
        url,
        headers={"User-Agent": "ecommerce-project/1.0"},
    )

    try:
        with urlopen(request, timeout=5) as response:
            data = json.load(response)

    except (OSError, ValueError, json.JSONDecodeError):
        return []

    return [
        child.get("data", {})
        for child in data.get("data", {}).get("children", [])
    ]


# ============================================================
# HOME / PRODUCTS
# ============================================================


def home(request):
    """
    Display the SAMKY TECH SHOP home page.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        Rendered home page response.
    """
    return render(
        request,
        "shop/home.html",
    )


def product_list(request):
    """
    Display products with optional search and sorting.

    Products can be searched by name, description, or store name.
    The results can also be sorted by price or product name.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        Rendered product list page containing the filtered products.
    """
    search_query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "").strip()

    products = Product.objects.all()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(store__name__icontains=search_query)
        )

    if sort == "price_low":
        products = products.order_by("price")

    elif sort == "price_high":
        products = products.order_by("-price")

    elif sort == "name_az":
        products = products.order_by("name")

    elif sort == "name_za":
        products = products.order_by("-name")

    else:
        products = products.order_by("id")

    return render(
        request,
        "shop/product_list.html",
        {
            "products": products,
            "search_query": search_query,
            "sort": sort,
        },
    )


def product_detail(request, product_id):
    """
    Display details, reviews, and rating information for a product.

    Args:
        request: The incoming Django HTTP request.
        product_id: ID of the product to display.

    Returns:
        Rendered product detail page.
    """
    product = get_object_or_404(
        Product,
        id=product_id,
    )

    reviews = product.reviews.select_related(
        "buyer"
    ).all()

    average_rating = reviews.aggregate(
        average=Avg("rating")
    )["average"]

    review_count = reviews.count()

    return render(
        request,
        "shop/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "average_rating": average_rating,
            "review_count": review_count,
        },
    )


# ============================================================
# REVIEWS
# ============================================================

@require_POST
@role_required("BUYER")
def submit_review(request, product_id):
    """
    Create or update the authenticated user's review for a product.

    Only POST requests are accepted. Ratings must be between 1 and 5,
    and a comment is required.

    Args:
        request: The incoming Django HTTP request.
        product_id: ID of the product being reviewed.

    Returns:
        Redirect to the product detail page.
    """
    product = get_object_or_404(Product, id=product_id)

    rating_value = request.POST.get("rating", "").strip()
    comment = request.POST.get("comment", "").strip()

    if not rating_value:
        messages.error(request, "Please select a rating.")
        return redirect("product_detail", product_id=product_id)

    try:
        rating = int(rating_value)
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid rating.")
        return redirect("product_detail", product_id=product_id)

    if rating < 1 or rating > 5:
        messages.error(request, "Rating must be between 1 and 5.")
        return redirect("product_detail", product_id=product_id)

    if not comment:
        messages.error(request, "Please enter a review comment.")
        return redirect("product_detail", product_id=product_id)

    purchased = OrderItem.objects.filter(
        order__buyer=request.user,
        order__status__in=["PAID", "COMPLETED"],
        product=product,
    ).exists()

    _, created = Review.objects.update_or_create(
        buyer=request.user,
        product=product,
        defaults={
            "rating": rating,
            "comment": comment,
            "verified": purchased,
        },
    )

    if created:
        messages.success(request, "Your review has been submitted.")
    else:
        messages.success(request, "Your review has been updated.")

    return redirect("product_detail", product_id=product_id)

# ============================================================
# LOGIN / REGISTER / LOGOUT
# ============================================================


def user_login(request):
    """
    Authenticate a user and redirect them based on their role.

    Authenticated users are redirected to the home page. Vendors are
    redirected to the vendor dashboard, while buyers are redirected
    to the home page.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        Rendered login page or redirect response.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get(
            "username",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

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

            return redirect(
                "vendor_dashboard"
                if role == "VENDOR"
                else "home"
            )

        messages.error(
            request,
            "Invalid username or password.",
        )

    return render(
        request,
        "shop/login.html",
    )


def register(request):
    """
    Register a new buyer or vendor account.

    Uses RegistrationForm to validate and create the account.
    The user is automatically logged in after successful registration.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        Rendered registration page or redirect to the appropriate
        dashboard after successful registration.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(
                request,
                user,
            )

            messages.success(
                request,
                "Your account has been created.",
            )

            return redirect(
                "vendor_dashboard"
                if form.cleaned_data["role"] == "VENDOR"
                else "buyer_dashboard"
            )

    else:
        form = RegistrationForm()

    return render(
        request,
        "shop/register.html",
        {
            "form": form,
        },
    )


@login_required
def user_logout(request):
    """
    Log out the currently authenticated user.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        Redirect to the home page after logout.
    """
    logout(request)

    messages.success(
        request,
        "You have been logged out.",
    )

    return redirect("home")


# ============================================================
# BUYER DASHBOARD
# ============================================================


@role_required("BUYER")
def buyer_dashboard(request):
    """
    Display the authenticated buyer's orders.

    Orders are displayed with the newest orders first.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        Rendered buyer dashboard page.
    """
    orders = (
        Order.objects
        .filter(buyer=request.user)
        .order_by("-created_at")
    )

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


@role_required("VENDOR")
def vendor_dashboard(request):
    """Display all stores and products belonging to the vendor."""
    profile = Profile.objects.filter(
        user=request.user
    ).first()

    stores = Store.objects.filter(
        vendor=request.user
    ).order_by("-created_at")

    products = (
        Product.objects
        .filter(store__vendor=request.user)
        .select_related("store")
        .order_by("-id")
    )

    available_products = products.filter(
        stock__gt=0
    ).count()

    return render(
        request,
        "shop/vendor_dashboard.html",
        {
            "profile": profile,
            "stores": stores,
            "products": products,
            "available_products": available_products,
        },
    )


# ============================================================
# STORE MANAGEMENT
# ============================================================


@role_required("VENDOR")
def store_create(request):
    """Create a store for the authenticated vendor."""

    profile = Profile.objects.filter(
        user=request.user
    ).first()

    if profile is None or profile.role != "VENDOR":
        messages.error(
            request,
            "You do not have permission to create a store.",
        )
        return redirect("home")

    if request.method == "POST":
        form = StoreForm(request.POST)

        if form.is_valid():
            store = form.save(commit=False)
            store.vendor = request.user
            store.save()

            messages.success(
                request,
                f"{store.name} was created successfully.",
            )

            return redirect("vendor_dashboard")

    else:
        form = StoreForm()

    return render(
        request,
        "shop/store_form.html",
        {
            "form": form,
            "title": "Create Store",
        },
    )


@role_required("VENDOR")
def store_edit(request, store_id):
    """Edit a store owned by the authenticated vendor."""

    store = get_object_or_404(
        Store,
        id=store_id,
        vendor=request.user,
    )

    if request.method == "POST":
        form = StoreForm(
            request.POST,
            instance=store,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                f"{store.name} was updated successfully.",
            )

            return redirect("vendor_dashboard")

    else:
        form = StoreForm(instance=store)

    return render(
        request,
        "shop/store_form.html",
        {
            "form": form,
            "title": "Edit Store",
            "store": store,
        },
    )


@role_required("VENDOR")
def store_delete(request, store_id):
    """Delete a store owned by the authenticated vendor."""

    store = get_object_or_404(
        Store,
        id=store_id,
        vendor=request.user,
    )

    if request.method == "POST":
        store_name = store.name
        store.delete()

        messages.success(
            request,
            f"{store_name} was deleted successfully.",
        )

        return redirect("vendor_dashboard")

    return render(
        request,
        "shop/store_confirm_delete.html",
        {
            "store": store,
        },
    )


# ============================================================
# PRODUCT MANAGEMENT
# ============================================================


@role_required("VENDOR")
def product_edit(request, product_id):
    """Edit a product belonging to the authenticated vendor."""

    product = get_object_or_404(
        Product,
        id=product_id,
        store__vendor=request.user,
    )

    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                f"{product.name} was updated successfully.",
            )

            return redirect("vendor_dashboard")

    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "shop/product_edit.html",
        {
            "form": form,
            "product": product,
        },
    )


@role_required("VENDOR")
def product_delete(request, product_id):
    """Delete a product belonging to the authenticated vendor."""

    product = get_object_or_404(
        Product,
        id=product_id,
        store__vendor=request.user,
    )

    if request.method == "POST":
        product_name = product.name

        try:
            product.delete()

        except ProtectedError:
            messages.error(
                request,
                "This product cannot be deleted because it is "
                "associated with an existing order.",
            )

            return redirect("vendor_dashboard")

        messages.success(
            request,
            f"{product_name} was deleted successfully.",
        )

        return redirect("vendor_dashboard")

    return render(
        request,
        "shop/product_confirm_delete.html",
        {
            "product": product,
        },
    )


# ============================================================
# CREATE PRODUCT
# ============================================================


@role_required("VENDOR")
def product_create(request, store_id):
    """
    Create a new product for a store owned by the current vendor.

    Args:
        request: The incoming Django HTTP request.
        store_id: ID of the vendor's store.

    Returns:
        Rendered product creation form or redirect to vendor dashboard
        after successful product creation.
    """
    store = get_object_or_404(
        Store,
        id=store_id,
        vendor=request.user,
    )

    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            product = form.save(
                commit=False
            )

            product.store = store
            product.save()

            messages.success(
                request,
                f"{product.name} was added successfully.",
            )

            return redirect(
                "vendor_dashboard"
            )

    else:
        form = ProductForm()

    return render(
        request,
        "shop/product_create.html",
        {
            "store": store,
            "form": form,
        },
    )


# ============================================================
# CART HELPERS
# ============================================================


def _get_cart(request):
    """
    Retrieve the shopping cart from the user's session.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        A dictionary containing product IDs and quantities.
        Returns an empty dictionary if the stored cart is invalid.
    """
    cart_data = request.session.get(
        "cart",
        {}
    )

    return (
        cart_data
        if isinstance(cart_data, dict)
        else {}
    )


def _save_cart(request, cart_data):
    """
    Save the shopping cart dictionary to the user's session.

    Args:
        request: The incoming Django HTTP request.
        cart_data: Dictionary containing product IDs and quantities.
    """
    request.session["cart"] = cart_data
    request.session.modified = True


def _get_cart_items(request):
    """
    Build cart items and calculate the cart's total price.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        A tuple containing a list of cart items and the total price.
    """
    cart_data = _get_cart(request)

    product_ids = []

    for product_id in cart_data:
        try:
            product_ids.append(
                int(product_id)
            )

        except (TypeError, ValueError):
            continue

    products = Product.objects.filter(
        id__in=product_ids
    )

    product_map = {
        str(product.id): product
        for product in products
    }

    items = []
    total = Decimal("0.00")

    for product_id, quantity in cart_data.items():

        product = product_map.get(
            str(product_id)
        )

        if product is None:
            continue

        try:
            quantity = int(quantity)

        except (TypeError, ValueError):
            quantity = 1

        quantity = max(
            quantity,
            1,
        )

        item_total = (
            product.price * quantity
        )

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

@role_required("BUYER")
def cart(request):
    """
    Display the shopping cart stored in the user's session.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        Rendered shopping cart page.
    """
    items, total = _get_cart_items(request)

    context = {
        "items": items,
        "cart_items": items,
        "total": total,
        "cart_total": total,
    }

    return render(
        request,
        "shop/cart.html",
        context,
    )


@role_required("BUYER")
@require_POST
def cart_add(request, product_id):
    """
        Add one unit of a product to the shopping cart.

        The quantity cannot exceed the product's available stock.

        Args:
            request: The incoming Django HTTP request.
            product_id: ID of the product to add.

        Returns:
            Redirect to the cart or product list.
        """
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, "This product is out of stock.")
        return redirect("store_detail", store_id=product.store_id)

    cart = _get_cart(request)
    product_key = str(product.id)
    current_quantity = int(cart.get(product_key, 0))

    if current_quantity >= product.stock:
        messages.warning(
            request,
            "You cannot add more than the available stock.",
        )
        return redirect("cart")

    # Add one item to the cart.
    cart[product_key] = current_quantity + 1
    _save_cart(request, cart)

    messages.success(
        request,
        f"{product.name} was added to your cart.",
    )

    # Take the buyer to the cart.
    return redirect("cart")


@role_required("BUYER")
def cart_remove(request, product_id):
    """
    Remove a product completely from the shopping cart.

    Args:
        request: The incoming Django HTTP request.
        product_id: ID of the product to remove.

    Returns:
        Redirect to the cart page.
    """
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


@role_required("BUYER")
def update_cart(request, product_id):
    """
    Update the quantity of a product in the shopping cart.

    A quantity of zero removes the product. The requested quantity
    cannot exceed the product's current stock.

    Args:
        request: The incoming Django HTTP request.
        product_id: ID of the product to update.

    Returns:
        Redirect to the cart page.
    """
    if request.method != "POST":
        return redirect("cart")

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    cart_data = _get_cart(request)
    key = str(product_id)

    try:
        quantity = int(
            request.POST.get(
                "quantity",
                0,
            )
        )

    except (TypeError, ValueError):
        messages.error(
            request,
            "Invalid quantity.",
        )

        return redirect("cart")

    if quantity < 0:
        messages.error(
            request,
            "Quantity cannot be negative.",
        )

        return redirect("cart")

    if quantity == 0:

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

    if product.stock <= 0:
        messages.error(
            request,
            "This product is out of stock.",
        )

        return redirect("cart")

    if quantity > product.stock:
        messages.warning(
            request,
            f"Only {product.stock} item(s) are available.",
        )

        return redirect("cart")

    cart_data[key] = quantity

    _save_cart(
        request,
        cart_data,
    )

    messages.success(
        request,
        "Cart updated.",
    )

    return redirect("cart")


# ============================================================
# CHECKOUT
# ============================================================
def build_invoice_pdf(order):
    """Build a PDF invoice containing the order and its item details."""
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, height = A4

    y = height - 50

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "INVOICE")

    y -= 35

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Order ID: {order.id}")

    y -= 18
    pdf.drawString(50, y, f"Customer: {order.buyer.username}")

    y -= 18
    pdf.drawString(50, y, f"Email: {order.buyer.email}")

    y -= 30

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Items")

    y -= 20

    pdf.setFont("Helvetica", 10)

    for item in order.items.select_related("product").all():
        subtotal = item.price * item.quantity

        line = (
            f"{item.product.name} x {item.quantity} "
            f"@ R{item.price:.2f} = R{subtotal:.2f}"
        )

        pdf.drawString(50, y, line)

        y -= 18

        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)

    y -= 10

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(
        50,
        y,
        f"Total: R{order.total:.2f}",
    )

    y -= 20

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        50,
        y,
        f"Status: {order.status}",
    )

    pdf.save()

    buffer.seek(0)

    return buffer.getvalue()


@role_required("BUYER")
def checkout(request):
    """
    Process the shopping cart and create a new order.
    Validate the customer's email and South African cellphone number.
    """
    items, total = _get_cart_items(request)

    if not items:
        messages.warning(request, "Your cart is empty.")
        return redirect("cart")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()

        # Validate the email address.
        try:
            validate_email(email)
        except ValidationError:
            messages.error(
                request,
                "Please enter a valid email address, "
                "such as customer@example.com.",
            )
            return redirect("checkout")

        # Remove spaces, brackets, and hyphens from the phone number.
        phone = re.sub(r"[\s()-]", "", phone)

        # Convert international South African format to local format.
        if phone.startswith("+27"):
            phone = "0" + phone[3:]

        # Validate a South African cellphone number.
        if not re.fullmatch(r"0(?:6\d|7\d|8[1-9])\d{7}", phone):
            messages.error(
                request,
                "Please enter a valid South African cellphone number, "
                "such as 0821234567 or +27821234567.",
            )
            return redirect("checkout")

        cart_data = _get_cart(request)

        with transaction.atomic():
            products = (
                Product.objects
                .select_for_update()
                .filter(
                    id__in=[
                        int(product_id)
                        for product_id in cart_data
                        if str(product_id).isdigit()
                    ]
                )
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
                validated_items.append((product, quantity))

            if not validated_items:
                messages.warning(request, "Your cart is empty.")
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
                product.save(update_fields=["stock"])

            invoice_lines = [
                "INVOICE",
                "=======",
                f"Order ID: {order.id}",
                f"Customer: {request.user.username}",
                f"Email: {email}",
                "",
                "Items:",
            ]

            for item in order.items.select_related("product").all():
                subtotal = item.price * item.quantity
                invoice_lines.append(
                    f"- {item.product.name} x {item.quantity} "
                    f"@ R{item.price:.2f} = R{subtotal:.2f}"
                )

            invoice_lines.extend(
                [
                    "",
                    f"Total: R{order.total:.2f}",
                    f"Status: {order.status}",
                ]
            )

            invoice_pdf = build_invoice_pdf(order)

            invoice = EmailMessage(
                subject=f"Invoice for Order #{order.id}",
                body="\n".join(invoice_lines),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )

            invoice.attach(
                f"invoice_order_{order.id}.pdf",
                invoice_pdf,
                "application/pdf",
            )

            invoice.send(fail_silently=False)

            request.session["cart"] = {}
            request.session.modified = True

            return redirect("checkout_success", order_id=order.id)

    total_quantity = sum(item["quantity"] for item in items)

    return render(
        request,
        "shop/checkout.html",
        {
            "items": items,
            "total": total,
            "cart_total": total,
            "total_quantity": total_quantity,
        },
    )


# ============================================================
# CHECKOUT SUCCESS
# ============================================================


@role_required("BUYER")
def checkout_success(request, order_id):
    """
    Display the successful checkout page for an order.

    The order must belong to the currently authenticated buyer.

    Args:
        request: The incoming Django HTTP request.
        order_id: ID of the completed order.

    Returns:
        Rendered checkout success page.
    """
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


@role_required("BUYER")
def my_orders(request):
    """
    Display all orders belonging to the authenticated buyer.

    Orders are displayed with the newest orders first.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        Rendered order history page.
    """
    orders = (
        Order.objects
        .filter(
            buyer=request.user,
        )
        .prefetch_related(
            "items__product",
        )
        .order_by(
            "-created_at",
        )
    )

    return render(
        request,
        "shop/my_orders.html",
        {
            "orders": orders,
        },
    )


@role_required("BUYER")
def order_detail(request, order_id):
    """
    Display the details and invoice information for an order.

    Only the buyer who owns the order can access it.

    Args:
        request: The incoming Django HTTP request.
        order_id: ID of the order to display.

    Returns:
        Rendered order detail page.
    """
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product",
        ),
        id=order_id,
        buyer=request.user,
    )

    invoice_items = []

    for item in order.items.all():
        item.subtotal = (
            item.price * item.quantity
        )

        invoice_items.append(item)

    return render(
        request,
        "shop/order_detail.html",
        {
            "order": order,
            "invoice_items": invoice_items,
        },
    )


def store_list(request):
    """Show stores that buyers can browse."""
    stores = Store.objects.order_by("name")

    return render(
        request,
        "shop/store_list.html",
        {"stores": stores},
    )


def store_detail(request, store_id):
    """Show the products belonging to a selected store."""
    store = get_object_or_404(Store, id=store_id)

    products = Product.objects.filter(
        store=store
    ).order_by("name")

    return render(
        request,
        "shop/store_detail.html",
        {
            "store": store,
            "products": products,
        },
    )


# ============================================================
# REDDIT FEED
# ============================================================


def reddit_feed(request):
    """
    Display recent posts from the Django subreddit.

    Args:
        request: The incoming Django HTTP request.

    Returns:
        Rendered Reddit feed page.
    """
    posts = get_reddit_posts(
        "django"
    )

    return render(
        request,
        "shop/reddit_feed.html",
        {
            "posts": posts or [],
        },
    )


# ============================================================
# REST API
# ============================================================


class RegisterAPIView(APIView):
    """
    API endpoint for registering a new user.
    """

    def post(self, request):
        """
        Register a new user through the REST API.

        Args:
            request: Django REST Framework request containing
                registration data.

        Returns:
            HTTP 201 with user information when registration succeeds,
            or HTTP 400 with validation errors when it fails.
        """
        serializer = RegisterSerializer(
            data=request.data
        )

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": (
                        "User registered successfully."
                    ),
                    "username": user.username,
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )
