"""Tests for the Shop application."""

import re
from decimal import Decimal

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Order, OrderItem, Product, Profile, Review, Store


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class ShopTestCase(TestCase):
    """Test the main eCommerce checkout and review functionality."""

    def setUp(self):
        """Create users, a store, and a product for the tests."""
        self.buyer = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="TestPassword123!",
        )

        Profile.objects.create(
            user=self.buyer,
            role="BUYER",
        )

        self.non_purchaser = User.objects.create_user(
            username="reviewer",
            email="reviewer@example.com",
            password="TestPassword123!",
        )

        Profile.objects.create(
            user=self.non_purchaser,
            role="BUYER",
        )

        self.vendor = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            password="TestPassword123!",
        )

        Profile.objects.create(
            user=self.vendor,
            role="VENDOR",
            vendor=self.vendor,
        )

        self.store = Store.objects.create(
            vendor=self.vendor,
            name="Test Store",
            description="Store used for automated tests.",
        )

        self.product = Product.objects.create(
            store=self.store,
            name="Test Product",
            description="Product used for automated tests.",
            price=Decimal("100.00"),
            stock=10,
        )

        self.client.login(
            username="buyer",
            password="TestPassword123!",
        )

    def test_checkout_creates_order_and_order_item(self):
        """Checkout should create an order with the correct item details."""
        session = self.client.session
        session["cart"] = {
            str(self.product.id): 2,
        }
        session.save()

        response = self.client.post(reverse("checkout"))

        self.assertEqual(response.status_code, 302)

        order = Order.objects.get(buyer=self.buyer)

        self.assertEqual(
            order.total,
            Decimal("200.00"),
        )

        self.assertEqual(
            order.status,
            "PENDING",
        )

        item = OrderItem.objects.get(order=order)

        self.assertEqual(
            item.product,
            self.product,
        )
        self.assertEqual(
            item.quantity,
            2,
        )
        self.assertEqual(
            item.price,
            Decimal("100.00"),
        )

    def test_checkout_reduces_stock(self):
        """Checkout should reduce product stock by the purchased quantity."""
        session = self.client.session
        session["cart"] = {
            str(self.product.id): 3,
        }
        session.save()

        self.client.post(reverse("checkout"))

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock,
            7,
        )

    def test_checkout_clears_cart(self):
        """Successful checkout should empty the session cart."""
        session = self.client.session
        session["cart"] = {
            str(self.product.id): 1,
        }
        session.save()

        response = self.client.post(reverse("checkout"))

        self.assertEqual(response.status_code, 302)

        session = self.client.session

        self.assertEqual(
            session.get("cart"),
            {},
        )

    def test_checkout_sends_invoice_email_with_order_details(self):
        """Checkout should send an email with a PDF invoice attachment."""
        self.client.login(
            username="buyer",
            password="TestPassword123!",
        )

        session = self.client.session
        session["cart"] = {
            str(self.product.id): 2,
        }
        session.save()

        response = self.client.post(
            reverse("checkout"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

        invoice = mail.outbox[0]

        order = Order.objects.get(
            buyer=self.buyer,
        )

        self.assertEqual(
            invoice.subject,
            f"Invoice for Order #{order.id}",
        )

        self.assertIn(
            "Test Product",
            invoice.body,
        )

        self.assertIn(
            "x 2",
            invoice.body,
        )

        self.assertIn(
            "R100.00",
            invoice.body,
        )

        self.assertIn(
            "R200.00",
            invoice.body,
        )

        self.assertIn(
            "Total: R200.00",
            invoice.body,
        )

        self.assertIn(
            self.buyer.username,
            invoice.body,
        )

        self.assertIn(
            self.buyer.email,
            invoice.body,
        )

        pdf_attachments = [
            attachment
            for attachment in invoice.attachments
            if attachment[0].endswith(".pdf")
        ]

        self.assertEqual(
            len(pdf_attachments),
            1,
        )

        filename, pdf_content, mimetype = pdf_attachments[0]

        self.assertEqual(
            filename,
            f"invoice_order_{order.id}.pdf",
        )

        self.assertEqual(
            mimetype,
            "application/pdf",
        )

        self.assertTrue(
            pdf_content.startswith(b"%PDF"),
        )

    def test_purchaser_can_submit_verified_review(self):
        """A user who purchased a product should receive a verified review."""
        order = Order.objects.create(
            buyer=self.buyer,
            total=Decimal("100.00"),
            status="COMPLETED",
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )

        response = self.client.post(
            f"/products/{self.product.id}/review/",
            {
                "rating": 5,
                "comment": "Excellent product.",
            },
        )

        self.assertEqual(response.status_code, 302)

        review = Review.objects.get(
            buyer=self.buyer,
            product=self.product,
        )

        self.assertTrue(review.verified)

    def test_non_purchaser_can_submit_unverified_review(self):
        """An authenticated non-purchaser should be allowed to review."""
        self.client.logout()

        self.client.login(
            username="reviewer",
            password="TestPassword123!",
        )

        response = self.client.post(
            f"/products/{self.product.id}/review/",
            {
                "rating": 4,
                "comment": "Looks like a good product.",
            },
        )

        self.assertEqual(response.status_code, 302)

        review = Review.objects.get(
            buyer=self.non_purchaser,
            product=self.product,
        )

        self.assertFalse(review.verified)

    def test_api_non_purchaser_can_submit_unverified_review(self):
        """The review API should allow authenticated non-purchasers."""
        api_client = APIClient()

        api_client.force_authenticate(
            user=self.non_purchaser,
        )

        response = api_client.post(
            reverse(
                "store-reviews",
                args=[self.store.id],
            ),
            {
                "product": self.product.id,
                "rating": 4,
                "comment": "API review from a non-purchaser.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        review = Review.objects.get(
            buyer=self.non_purchaser,
            product=self.product,
        )

        self.assertFalse(
            review.verified,
        )

    def test_api_purchaser_can_submit_verified_review(self):
        """The review API should mark a purchaser's review as verified."""
        order = Order.objects.create(
            buyer=self.buyer,
            total=Decimal("100.00"),
            status="COMPLETED",
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )

        api_client = APIClient()

        api_client.force_authenticate(
            user=self.buyer,
        )

        response = api_client.post(
            reverse(
                "store-reviews",
                args=[self.store.id],
            ),
            {
                "product": self.product.id,
                "rating": 5,
                "comment": "Verified API purchase review.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        review = Review.objects.get(
            buyer=self.buyer,
            product=self.product,
        )

        self.assertTrue(
            review.verified,
        )

    def test_api_pending_order_review_is_unverified(self):
        """A pending order must not qualify a review as verified."""
        order = Order.objects.create(
            buyer=self.buyer,
            total=Decimal("100.00"),
            status="PENDING",
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )

        api_client = APIClient()
        api_client.force_authenticate(user=self.buyer)

        response = api_client.post(
            reverse("store-reviews", args=[self.store.id]),
            {
                "product": self.product.id,
                "rating": 5,
                "comment": "Review for a pending order.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        review = Review.objects.get(
            buyer=self.buyer,
            product=self.product,
        )
        self.assertFalse(review.verified)

    def test_api_cancelled_order_review_is_unverified(self):
        """A cancelled order must not qualify a review as verified."""
        order = Order.objects.create(
            buyer=self.buyer,
            total=Decimal("100.00"),
            status="CANCELLED",
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )

        api_client = APIClient()
        api_client.force_authenticate(user=self.buyer)

        response = api_client.post(
            reverse("store-reviews", args=[self.store.id]),
            {
                "product": self.product.id,
                "rating": 4,
                "comment": "Review for a cancelled order.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        review = Review.objects.get(
            buyer=self.buyer,
            product=self.product,
        )
        self.assertFalse(review.verified)

    def test_unauthenticated_api_user_cannot_create_review(self):
        """Unauthenticated users should not be able to create reviews."""
        api_client = APIClient()

        response = api_client.post(
            reverse(
                "store-reviews",
                args=[self.store.id],
            ),
            {
                "product": self.product.id,
                "rating": 5,
                "comment": "Unauthenticated review.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_password_reset_sends_email_with_reset_link(self):
        """Password reset should send an email containing a reset link."""
        self.client.logout()

        response = self.client.post(
            reverse("password_reset"),
            {
                "email": self.buyer.email,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("password_reset_done"),
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        email = mail.outbox[0]

        self.assertIn(
            self.buyer.email,
            email.to,
        )

        self.assertIn(
            "/password-reset/",
            email.body,
        )

        self.assertRegex(
            email.body,
            r"/password-reset/[^/\s]+/[^/\s]+/",
        )

    def test_password_reset_token_allows_password_change(self):
        """A valid password-reset link should allow the user
        to change password."""
        self.client.logout()

        response = self.client.post(
            reverse("password_reset"),
            {
                "email": self.buyer.email,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        match = re.search(
            r"/password-reset/([^/\s]+)/([^/\s]+)/",
            email.body,
        )

        self.assertIsNotNone(match)

        uidb64, token = match.groups()

        response = self.client.get(
            reverse(
                "password_reset_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        reset_form_url = response.request["PATH_INFO"]

        new_password = "NewSecurePassword456!"

        response = self.client.post(
            reset_form_url,
            {
                "new_password1": new_password,
                "new_password2": new_password,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("password_reset_complete"),
        )

        self.assertTrue(
            self.client.login(
                username="buyer",
                password=new_password,
            )
        )

        self.assertFalse(
            self.client.login(
                username="buyer",
                password="TestPassword123!",
            )
        )

    def create_test_order(self, status="PENDING", product=None):
        """Create an order and item for vendor status API tests."""
        product = product or self.product

        order = Order.objects.create(
            buyer=self.buyer,
            total=product.price,
            status=status,
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=product.price,
        )

        return order

    def test_vendor_can_mark_pending_order_paid(self):
        """A vendor can move an order from PENDING to PAID."""
        order = self.create_test_order(status="PENDING")
        client = APIClient()
        client.force_authenticate(user=self.vendor)

        response = client.patch(
            reverse(
                "vendor-order-status-api",
                kwargs={"order_id": order.id},
            ),
            {"status": "PAID"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, "PAID")

    def test_vendor_can_mark_paid_order_completed(self):
        """A vendor can move an order from PAID to COMPLETED."""
        order = self.create_test_order(status="PAID")
        client = APIClient()
        client.force_authenticate(user=self.vendor)

        response = client.patch(
            reverse(
                "vendor-order-status-api",
                kwargs={"order_id": order.id},
            ),
            {"status": "COMPLETED"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, "COMPLETED")

    def test_buyer_cannot_update_vendor_order_status(self):
        """A buyer cannot use the vendor status endpoint."""
        order = self.create_test_order(status="PENDING")
        client = APIClient()
        client.force_authenticate(user=self.buyer)

        response = client.patch(
            reverse(
                "vendor-order-status-api",
                kwargs={"order_id": order.id},
            ),
            {"status": "PAID"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, "PENDING")

    def test_vendor_cannot_update_another_vendors_order(self):
        """A vendor cannot update an order containing another vendor's
        product."""
        other_vendor = User.objects.create_user(
            username="other_vendor",
            email="other-vendor@example.com",
            password="TestPassword123!",
        )
        Profile.objects.create(
            user=other_vendor,
            role="VENDOR",
            vendor=other_vendor,
        )
        other_store = Store.objects.create(
            vendor=other_vendor,
            name="Other Store",
            description="Another vendor's store.",
        )
        other_product = Product.objects.create(
            store=other_store,
            name="Other Product",
            description="Another vendor's product.",
            price=Decimal("50.00"),
            stock=5,
        )
        order = self.create_test_order(
            status="PENDING",
            product=other_product,
        )

        client = APIClient()
        client.force_authenticate(user=self.vendor)

        response = client.patch(
            reverse(
                "vendor-order-status-api",
                kwargs={"order_id": order.id},
            ),
            {"status": "PAID"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        order.refresh_from_db()
        self.assertEqual(order.status, "PENDING")

    def test_vendor_cannot_update_cancelled_order(self):
        """A cancelled order cannot be moved to another status."""
        order = self.create_test_order(status="CANCELLED")
        client = APIClient()
        client.force_authenticate(user=self.vendor)

        response = client.patch(
            reverse(
                "vendor-order-status-api",
                kwargs={"order_id": order.id},
            ),
            {"status": "PAID"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, "CANCELLED")
