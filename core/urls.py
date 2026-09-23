from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import serializers
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

User = get_user_model()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.username_field in self.fields:
            pass
        elif "username" in self.fields:
            self.fields[self.username_field] = self.fields.pop("username")


class ThrottledTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_burst"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path(
        "api/auth/token/",
        ThrottledTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("", include("myapp.urls")),
]
