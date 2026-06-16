# myapp/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserRegistrationAPIView, JobListCreateAPIView, ApplicationCreateAPIView

urlpatterns = [
    # Identity Management Paths
    path('api/auth/register/', UserRegistrationAPIView.as_view(), name='auth-register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='auth-login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),

    # Core ATS Application Tracking Operations Paths
    path('api/jobs/', JobListCreateAPIView.as_view(), name='jobs-list-create'),
    path('api/applications/', ApplicationCreateAPIView.as_view(), name='applications-create'),
]