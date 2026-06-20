# myapp/urls.py
from django.urls import path
from .views import (
    JobDashboardAPIView,
    JobDetailAPIView,
    ApplicationCreateAPIView,
    SystemAdminUserMetricsAPIView
)

urlpatterns = [
    # Job Board Resource Mappings
    path('api/jobs/', JobDashboardAPIView.as_view(), name='jobs-list-create'),
    path('api/jobs/<intpk>/', JobDetailAPIView.as_view(), name='jobs-detail-mutate'),

    # Application Tracking Lifecycle Mappings
    path('api/applications/', ApplicationCreateAPIView.as_view(), name='candidate-apply'),

    # Admin Control Operations Mappings
    path('api/admin/metrics/', SystemAdminUserMetricsAPIView.as_view(), name='admin-system-metrics'),
]