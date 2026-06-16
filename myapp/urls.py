# myapp/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationAPIView, 
    CustomTokenObtainPairView, 
    UserLogoutAPIView,
    JobDashboardAPIView
)

urlpatterns = [
    # Core Authentication Operations Pipeline
    path('api/auth/signup/', UserRegistrationAPIView.as_view(), name='jwt-signup'),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='jwt-login'),
    path('api/auth/logout/', UserLogoutAPIView.as_view(), name='jwt-logout'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),

    # Sample Protected Core Business Logic Operations
    path('api/jobs/', JobDashboardAPIView.as_view(), name='protected-jobs'),
]