from typing import ClassVar

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Product, Profile, Review


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    role = forms.ChoiceField(
        choices=[
            ("BUYER", "Buyer"),
            ("VENDOR", "Vendor"),
        ],
        widget=forms.RadioSelect,
    )

    class Meta:
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
    class Meta:
        model = Product
        fields: ClassVar[list[str]] = [
            "name",
            "description",
            "price",
            "stock",
        ]


class ReviewForm(forms.ModelForm):
    class Meta:
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
        rating = self.cleaned_data["rating"]
        if rating < 1 or rating > 5:
            raise forms.ValidationError(
                "Rating must be between 1 and 5 stars."
            )
        return rating
