"""Django admin configuration for the store application."""

from django.contrib import admin

from .models import (
    Order,
    OrderItem,
    Product,
    Profile,
    Review,
    Store,
)

admin.site.register(Profile)
"""Register the Profile model with the Django admin site."""

admin.site.register(Store)
"""Register the Store model with the Django admin site."""

admin.site.register(Product)
"""Register the Product model with the Django admin site."""

admin.site.register(Order)
"""Register the Order model with the Django admin site."""

admin.site.register(OrderItem)
"""Register the OrderItem model with the Django admin site."""

admin.site.register(Review)
"""Register the Review model with the Django admin site."""
