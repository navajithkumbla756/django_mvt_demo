# myapp/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Job, Application, CustomUser
from .serializers import JobSerializer, ApplicationSerializer
from .permissions import IsAdminRole, IsEmployerRole, IsCandidateRole, IsJobOwner

# --- EMPLOYER COMPONENT: Job Board Controls ---

class JobDashboardAPIView(generics.ListCreateAPIView):
    """
    Endpoint: GET/POST /api/jobs/
    GET: Anyone authenticated can browse jobs.
    POST: Restricted to corporate EMPLOYERS only.
    """
    queryset = Job.objects.all().order_by('-posted_at')
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != 'EMPLOYER':
            raise PermissionDenied("Access Denied: Your account role does not permit posting job listings.")
        serializer.save(employer=self.request.user.employer_profile)


class JobDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint: GET/PUT/DELETE /api/jobs/<id>/
    PUT/DELETE: Restricted to the specific EMPLOYER owner who created the post.
    """
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsJobOwner]


# --- CANDIDATE COMPONENT: Submit Applications ---

class ApplicationCreateAPIView(generics.CreateAPIView):
    """
    Endpoint: POST /api/applications/
    POST: Restricted to CANDIDATES only. Auto-links the profile context.
    """
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsCandidateRole]

    def perform_create(self, serializer):
        # Prevent duplicate applications from the same candidate for the same job listing
        job_id = self.request.data.get('job')
        if Application.objects.filter(job_id=job_id, candidate=self.request.user.candidate_profile).exists():
            raise PermissionDenied("Security Flag: You have already submitted an application for this role.")
        
        serializer.save(candidate=self.request.user.candidate_profile)


# --- ADMIN COMPONENT: System Orchestration Control ---

class SystemAdminUserMetricsAPIView(generics.GenericAPIView):
    """
    Endpoint: GET /api/admin/metrics/
    GET: Restricted strictly to ADMIN accounts.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        total_users = CustomUser.objects.count()
        employers = CustomUser.objects.filter(role='EMPLOYER').count()
        candidates = CustomUser.objects.filter(role='CANDIDATE').count()
        
        return Response({
            "system_status": "Healthy",
            "metrics": {
                "total_registered_accounts": total_users,
                "employer_workspaces": employers,
                "active_job_seekers": candidates
            }
        }, status=status.HTTP_200_OK)