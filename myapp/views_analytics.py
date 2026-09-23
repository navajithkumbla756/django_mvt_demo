from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsEmployerRole
from .services import AnalyticsService


class RecruiterFunnelAnalyticsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEmployerRole]

    @extend_schema(
        tags=["analytics"],
        summary="Recruiter Stage-to-Stage Application Funnel",
        description=(
            "Calculates conversion metrics (applied -> shortlisted -> " "interview -> selected) for a specific job."
        ),
        parameters=[
            OpenApiParameter(
                name="job_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter funnel by specific Job ID owned by recruiter.",
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Conversion funnel metrics calculated successfully.",
                examples=[
                    OpenApiExample(
                        "Sample Funnel Response",
                        value={
                            "job_id": 3,
                            "job_title": "Senior Python Developer",
                            "funnel": {
                                "applied": 10,
                                "shortlisted": 5,
                                "interview": 3,
                                "selected": 1,
                                "conversion_rate_percent": 10.0,
                            },
                        },
                    )
                ],
            ),
            403: OpenApiResponse(description="Forbidden - Recruiter does not own this job."),
            404: OpenApiResponse(description="Job not found."),
        },
    )
    def get(self, request, *args, **kwargs):
        job_id = request.query_params.get("job_id")
        data = AnalyticsService.get_funnel_metrics(request.user, job_id)
        return Response(data, status=status.HTTP_200_OK)


class RecruiterTrendsAnalyticsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEmployerRole]

    @extend_schema(
        tags=["analytics"],
        summary="Sliding Window Candidate Sourcing Trends",
        description=(
            "Provides candidate application volume grouped by job title " "over a configurable sliding day window."
        ),
        parameters=[
            OpenApiParameter(
                name="days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                default=30,
                description="Window duration in days (default: 30).",
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Candidate volume metrics grouped by job title.",
                examples=[
                    OpenApiExample(
                        "Sample Trends Response",
                        value={
                            "window_days": 30,
                            "start_date": "2026-08-24T12:00:00Z",
                            "end_date": "2026-09-23T12:00:00Z",
                            "trends": [
                                {
                                    "job__title": "Senior Python Developer",
                                    "applicant_count": 8,
                                },
                                {
                                    "job__title": "Frontend React Engineer",
                                    "applicant_count": 4,
                                },
                            ],
                        },
                    )
                ],
            )
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            days = int(request.query_params.get("days", 30))
        except ValueError:
            days = 30

        data = AnalyticsService.get_candidate_trends(request.user, days)
        return Response(data, status=status.HTTP_200_OK)
