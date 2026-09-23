from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    ApplicationCreateAPIView,
    JobDashboardAPIView,
    JobDetailAPIView,
    SystemAdminUserMetricsAPIView,
)
from .views_analytics import (
    RecruiterFunnelAnalyticsAPIView,
    RecruiterTrendsAnalyticsAPIView,
)
from .views_documents import ResumeDownloadURLView

urlpatterns = [
    # System Telemetry & Admin
    path("api/admin/metrics/", SystemAdminUserMetricsAPIView.as_view(), name="admin_metrics"),
    # JWT Authentication Endpoints
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    # Job Endpoints
    path("api/jobs/", JobDashboardAPIView.as_view(), name="job_list_create"),
    path("api/jobs/<int:pk>/", JobDetailAPIView.as_view(), name="job_detail"),
    # Candidate Applications
    path("api/applications/", ApplicationCreateAPIView.as_view(), name="application_create"),
    # Recruiter Pre-Signed Resume Access
    path("api/resumes/<int:candidate_id>/download-url/", ResumeDownloadURLView.as_view(), name="resume_download_url"),
    # Recruiter Analytics
    path("api/analytics/funnel/", RecruiterFunnelAnalyticsAPIView.as_view(), name="analytics_funnel"),
    path("api/analytics/trends/", RecruiterTrendsAnalyticsAPIView.as_view(), name="analytics_trends"),
]
