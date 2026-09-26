from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from drf_spectacular.utils import extend_schema
from .models import InterviewRescheduleRequest


ACTION_CHOICES = (
    ('APPROVE', 'Approve'),
    ('REJECT', 'Reject'),
)

class InterviewActionInputSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=ACTION_CHOICES, required=True)
    reviewer_notes = serializers.CharField(required=False, allow_blank=True)


class InterviewRescheduleSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='application.candidate.user.name', read_only=True)
    job_title = serializers.CharField(source='application.job.title', read_only=True)

    class Meta:
        model = InterviewRescheduleRequest
        fields = [
            'id', 'application', 'candidate_name', 'job_title',
            'requested_by', 'current_slot', 'proposed_slot',
            'reason', 'status', 'reviewer_notes', 'reviewed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'reviewer_notes', 'reviewed_at', 'created_at', 'updated_at', 'requested_by']

    def validate_proposed_slot(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Proposed slot must be in the future.")
        return value

    def validate(self, attrs):
        app = attrs.get('application')
        if InterviewRescheduleRequest.objects.filter(application=app, status='PENDING').exists():
            raise serializers.ValidationError("A pending reschedule request already exists for this application.")
        return attrs


class InterviewRescheduleListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=InterviewRescheduleSerializer(many=True))
    def get(self, request):
        user = request.user
        if user.is_staff or getattr(user, 'role', None) in ['RECRUITER', 'EMPLOYER']:
            qs = InterviewRescheduleRequest.objects.select_related('application', 'application__job', 'application__candidate__user').all()
        else:
            qs = InterviewRescheduleRequest.objects.filter(application__candidate__user=user).select_related('application', 'application__job')
        serializer = InterviewRescheduleSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=InterviewRescheduleSerializer, responses=InterviewRescheduleSerializer)
    def post(self, request):
        serializer = InterviewRescheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(requested_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InterviewRescheduleActionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=InterviewRescheduleSerializer, request=InterviewActionInputSerializer)
    def post(self, request, pk=None):
        user = request.user
        if not (user.is_staff or getattr(user, 'role', None) in ['RECRUITER', 'EMPLOYER']):
            return Response({'detail': 'Only recruiters or staff can review reschedule requests.'}, status=status.HTTP_403_FORBIDDEN)

        input_serializer = InterviewActionInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        try:
            req_obj = InterviewRescheduleRequest.objects.select_related('application').get(pk=pk)
        except InterviewRescheduleRequest.DoesNotExist:
            return Response({'detail': 'Reschedule request not found.'}, status=status.HTTP_404_NOT_FOUND)


        if req_obj.status != 'PENDING':
            return Response({'detail': f'Request is already marked as {req_obj.status}.'}, status=status.HTTP_400_BAD_REQUEST)

        decision = input_serializer.validated_data['action']
        notes = input_serializer.validated_data.get('reviewer_notes', '')

        with transaction.atomic():
            req_obj.status = 'APPROVE' if decision == 'APPROVE' else 'REJECTED'
            req_obj.rWiewer_notes = notes
            req_obj.rWiewed_at = timezone.now()
            req_obj.save()

        result = InterviewRescheduleSerializer(req_obj)
        return Response(result.data, status=status.HTTP_200_OK)
