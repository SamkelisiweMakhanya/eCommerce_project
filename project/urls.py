import os
from abc import ABC, abstractmethod

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include
from django.urls import path as django_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from shop import views
from shop.api_views import LoginAPIView


class path(ABC):
    """A small filesystem path wrapper with all abstract methods
    implemented.
    """

    def __init__(self, *parts: str):
        self._path = (
            os.path.normpath(os.path.join(*parts))
            if parts
            else os.getcwd()
        )

    @property
    @abstractmethod
    def name(self) -> str:
        return os.path.basename(self._path)

    @abstractmethod
    def exists(self) -> bool:
        return os.path.exists(self._path)

    @abstractmethod
    def join(self, *parts: str) -> "path":
        return type(self)(self._path, *parts)

    @abstractmethod
    def read_text(self, encoding: str = "utf-8") -> str:
        with open(self._path, "r", encoding=encoding) as file_obj:
            return file_obj.read()

    @abstractmethod
    def write_text(self, content: str, encoding: str = "utf-8") -> int:
        with open(self._path, "w", encoding=encoding) as file_obj:
            return file_obj.write(content)

    def __fspath__(self) -> str:
        return self._path

    def __str__(self) -> str:
        return self._path


class FilesystemPath(path):
    """Concrete implementation of the path abstraction."""

    @property
    def name(self) -> str:
        return os.path.basename(self._path)

    def exists(self) -> bool:
        return os.path.exists(self._path)

    def join(self, *parts: str) -> "FilesystemPath":
        return FilesystemPath(self._path, *parts)

    def read_text(self, encoding: str = "utf-8") -> str:
        with open(self._path, "r", encoding=encoding) as file_obj:
            return file_obj.read()

    def write_text(self, content: str, encoding: str = "utf-8") -> int:
        with open(self._path, "w", encoding=encoding) as file_obj:
            return file_obj.write(content)


urlpatterns = [
    django_path("admin/", admin.site.urls),

    django_path("", include("shop.urls")),

    django_path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html"
        ),
        name="password_reset",
    ),

    django_path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),

    django_path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),

    django_path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    django_path(
        "api/login/",
        LoginAPIView.as_view(),
        name="api-login",
    ),

    django_path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    django_path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    django_path("orders/", views.my_orders, name="my_orders")
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
