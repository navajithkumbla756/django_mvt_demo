# myapp/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserRegistrationSerializer, CustomTokenObtainPairSerializer

class UserRegistrationAPIView(generics.CreateAPIView):
    """Public Registration Endpoint."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom Login Endpoint injecting user profiles."""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class UserLogoutAPIView(generics.GenericAPIView):
    """Stateless Logout endpoint invalidating the current Refresh Token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist() # Invalidate token inside the centralized database register
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"detail": "Invalid or expired refresh token payload."}, status=status.HTTP_400_BAD_REQUEST)
        

# myapp/views.py (Append to bottom)
from rest_framework.exceptions import PermissionDenied
from .models import Job
from .serializers import JobSerializer

class JobDashboardAPIView(generics.ListCreateAPIView):
    """Protected API pipeline where only authenticated profiles can view, and only EMPLOYERS can create."""
    queryset = Job.objects.all().order_by('-posted_at')
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated] # Global fallback verification check

    def perform_create(self, serializer):
        # Enforce strict role-based permission checks manually
        if self.request.user.role != 'EMPLOYER':
            raise PermissionDenied("Access Denied: Only corporate employers can post job openings.")
        serializer.save(employer=self.request.user.employer_profile)