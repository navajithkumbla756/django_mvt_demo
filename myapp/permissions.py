# myapp/permissions.py
from rest_framework import permissions

class IsEmployerRole(permissions.BasePermission):
    """Grants access exclusively to validated corporate recruiters/employers."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'EMPLOYER'

class IsCandidateRole(permissions.BasePermission):
    """Grants access exclusively to job seekers/candidates."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'CANDIDATE'