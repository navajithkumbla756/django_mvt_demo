# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from django.shortcuts import get_object_or_404
# from .models import Job
# from .serializers import JobSerializer

# # 1. For handling multiple items (List and Create)
# @api_view(['GET', 'POST'])
# def job_list(request):
#     if request.method == 'GET':
#         jobs = Job.objects.all()
#         serializer = JobSerializer(jobs, many=True)
#         return Response(serializer.data)
        
#     elif request.method == 'POST':
#         serializer = JobSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # 2. For handling a single specific item (Get individual, Update, and Delete)
# @api_view(['GET', 'PUT', 'DELETE'])
# def job_detail(request, pk):  # pk is the ID of the job passed in the URL
#     job = get_object_or_404(Job, pk=pk)

#     if request.method == 'GET':
#         serializer = JobSerializer(job)
#         return Response(serializer.data)

#     elif request.method == 'PUT':
#         serializer = JobSerializer(job, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     elif request.method == 'DELETE':
#         job.delete()
#         return Response({'message': 'Job deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)

# myapp/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import UserRegistrationSerializer

class UserRegistrationAPIView(generics.CreateAPIView):
    """Public registration endpoint for creating custom users."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    # myapp/views.py (Append to bottom)
from rest_framework.permissions import IsAuthenticated
from .models import Job, Application
from .serializers import JobSerializer, ApplicationSerializer
from .permissions import IsEmployerRole, IsCandidateRole

class JobListCreateAPIView(generics.ListCreateAPIView):
    """Lists jobs for anyone, but restricts new creations to verified Employers."""
    queryset = Job.objects.all().order_by('-posted_at')
    serializer_class = JobSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsEmployerRole()]
        return [AllowAny()]

    def perform_create(self, serializer):
        # Automatically hooks the posting job to the active logged-in user's Employer profile
        serializer.save(employer=self.request.user.employer_profile)


class ApplicationCreateAPIView(generics.CreateAPIView):
    """Enables candidates to apply to open jobs securely via authentication keys."""
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsCandidateRole]

    def perform_create(self, serializer):
        # Automatically connects the application to the active logged-in Candidate profile
        serializer.save(candidate=self.request.user.candidate_profile)