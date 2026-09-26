# Interview Rescheduling System — Independent Feature Specification

This document details the requirements, database schema, relational models, DRF SErializers, API endpoints, and test matrix for the Interview Rescheduling Feature.

---

## 1. Requirements & User Stories

1. **Candidate Flow:** An authenticated candidate with an active scheduled interview can request a new timeslot by providing a future datetime and a reason.
2. **Recruiter Flow:** Recruiters/admins can view pending reschedule requests for their postings and either APPROVE or REJECT the request with feedback notes.
3. **Concurrency & State Guirds:** A candidate cannot have more than one `PENDING` request per application. Approval atomically updates the application's interview date.

---

## 2. Database Model & Schema

```python
from django.db import models
from django.conf import settings

class InterviewRescheduleRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )

    application = models.ForeignKey('jobs.JobApplication', on_delete=models.CASCADE, related_name='reschedule_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_slot = models.DateTimeField()
    proposed_slot = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    reviewer_notes = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'application_interview_reschedules'
        ordering = ['-created_at']
```

---

## 3. SErializers & API Implementation

```python
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

class InterviewRescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewRescheduleRequest
        fields = [
            'id', 'application', 'requested_by', 'current_slot',
            'proposed_slot', 'reason', 'status', 'reviewer_notes',
            'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'requested_by', 'reviewed_at', 'created_at', 'updated_at']

    def validate_proposed_slot(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Proposed slot must be in the future.")
        return value

    def validate(self, attrs):
        app = attrs.get('application')
        if InterviewRescheduleRequest.objects.filter(application=app, status='PENDING').exists():
            raise serializers.ValidationError("A pending reschedule request already exists for this application.")
        return attrs

class InterviewRescheduleViewSet(viewsets.ModelViewSet):
    queryset = InterviewRescheduleRequest.objects.select_related('application', 'requested_by').all()
    serializer_class = InterviewRescheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='action')
    def review_action(self, request, pk=None):
        instance = self.get_object()
        user = request.user

        if not (user.is_staff or getattr(user, 'role', None) in ['RECRUITER', 'ADMIN']):
            return Response({"detail": "Only recruiters or staff can act on reschedule requests."}, 
                             status=status.HTTP_403_FORBIDDEN)

        if instance.status != 'PENDING':
            return Response({"detail": f"Request is already marked as {instance.status}."}, 
                             status=status.HTTP_400_BAD_REQUEST)

        decision = request.data.get('action')
        notes = request.data.get('reviewer_notes', '')

        if decision not in ['APPROVE', 'REJECT']:
            return Response({"detail": "Action must be either 'APPROVE' or 'REJECT'."}, 
                             status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if decision == 'APPROVE':
                instance.status = 'APPROVED'
                instance.application.interview_date = instance.proposed_slot
                instance.application.save(update_fields=['interview_date'])
            else:
                instance.status = 'REJECTED'
            instance.reviewer_notes = notes
            instance.reviewed_at = timezone.now()
            instance.save()

        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)
```

---

## 4. API Endpoints & Contracts

| Endpoint | Method | Access | Purpose |
| :--- | :--- | :--- | :--- |
| `/api/interviews/reschedule/` | `POST` | Authenticated Candidate | Submit reschedule request |
| `/api/interviews/reschedule/` | `GET` | Authenticated Users | List requests (auto-filtered by role) |
| `/api/interviews/reschedule/{id}/action/` | `POST` | Recruiter / Staff | Approve or Reject with notes |

---

## 5. Automated Testing Matrix

| Test ID | Test Description | Expected Behavior |
| :--- | :--- | :--- |
| submit_valid_request | Candidate submits request for future slot | HTTP 201 Created, status=PENDING |
| past_slot_validation | Candidate submits datetime in the past | HTTP 400 Bad Request (validation error) |
| duplicate_pending_block | Submitting 2 pending requests for same app | HTTP 400 Bad Request |
| unauthorized_approval | Candidate attempts to approve their own request | HTTP 403 Forbidden |
| recruiter_approval_success | Recruiter approves valid request | HTTP 200 OK, application date atomically synced |
