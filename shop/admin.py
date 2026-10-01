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
admin.site.register(Store)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)
