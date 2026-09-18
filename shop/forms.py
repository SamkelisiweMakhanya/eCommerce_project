"""Forms for user registration, products, and product reviews."""

from typing import ClassVar

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Product, Profile, Review


class RegistrationForm(UserCreationForm):
    """Provide a form for registering new users as buyers or vendors."""

    email = forms.EmailField(required=True)

    role = forms.ChoiceField(
        choices=[
            ("BUYER", "Buyer"),
            ("VENDOR", "Vendor"),
        ],
        widget=forms.RadioSelect,
    )

    class Meta:
        """Define the model and fields used by the registration form."""

        model = User
        fields: ClassVar[list[str]] = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        """Create the user and associated profile.

        Args:
            commit: Whether to save the user and create the profile
                immediately.

        Returns:
            The newly created User instance.
        """
        user = super().save(commit=False)

        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

            Profile.objects.create(
                user=user,
                role=self.cleaned_data["role"]
            )

        return user


class ProductForm(forms.ModelForm):
    """Provide a form for creating and updating products."""

    class Meta:
        """Define the model and fields used by the product form."""

        model = Product
        fields: ClassVar[list[str]] = [
            "name",
            "description",
            "price",
            "stock",
        ]


class ReviewForm(forms.ModelForm):
    """Provide a form for submitting and validating product reviews."""

    class Meta:
        """Define the model, fields, and widgets used by the review form."""

        model = Review
        fields: ClassVar[list[str]] = ["rating", "comment"]
        widgets: ClassVar[dict[str, forms.Widget]] = {
            "rating": forms.Select(
                choices=[
                    (5, "★★★★★ - Excellent"),
                    (4, "★★★★☆ - Very Good"),
                    (3, "★★★☆☆ - Good"),
                    (2, "★★☆☆☆ - Fair"),
                    (1, "★☆☆☆☆ - Poor"),
                ],
                attrs={"class": "form-control"},
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Write your review...",
                }
            ),
        }

    def clean_rating(self):
        """Validate that the review rating is between 1 and 5 stars.

        Returns:
            The validated rating value.

        Raises:
            forms.ValidationError: If the rating is outside the range
                of 1 to 5.
        """
        rating = self.cleaned_data["rating"]
        if rating < 1 or rating > 5:
            raise forms.ValidationError(
                "Rating must be between 1 and 5 stars."
            )
        return rating
