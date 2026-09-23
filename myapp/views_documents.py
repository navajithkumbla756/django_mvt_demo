from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .permissions import IsEmployerRole
from .services import DocumentAccessService


class ResumeDownloadURLView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEmployerRole]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resumes"

    @extend_schema(
        summary="Generate Pre-Signed S3 Resume Download URL",
        description="Generates an AWS SigV4 pre-signed URL with a 300-second expiration for authorized recruiters.",
        responses={
            200: OpenApiResponse(
                description="Pre-signed download URL generated successfully.",
                examples=[
                    OpenApiExample(
                        "Successful S3 Pre-sign Response",
                        value={
                            "application_id": 1,
                            "candidate_email": "candidate@example.com",
                            "download_url": "https://s3.eu-north-1.amazonaws.com/...",
                            "expires_in": 300,
                        },
                    )
                ],
            ),
            401: OpenApiResponse(description="Missing or invalid JWT Bearer token."),
            403: OpenApiResponse(description="Forbidden - You are not authorized to view candidates for this job."),
            404: OpenApiResponse(description="Application or resume snapshot not found."),
        },
    )
    def get(self, request, candidate_id=None, pk=None, *args, **kwargs):
        app_id = candidate_id if candidate_id is not None else pk
        data = DocumentAccessService.get_resume_download_url(app_id, request.user)
        return Response(data, status=status.HTTP_200_OK)
