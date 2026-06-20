# myapp/permissions.py
from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """Allows access exclusively to global system administrators or superusers."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role == 'ADMIN' or request.user.is_superuser
        )


class IsEmployerRole(permissions.BasePermission):
    """Allows access exclusively to registered and verified corporate recruiters/employers."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'EMPLOYER'


class IsCandidateRole(permissions.BasePermission):
    """Allows access exclusively to job seekers/candidates."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'CANDIDATE'


class IsJobOwner(permissions.BasePermission):
    """Object-level permission ensuring an Employer can only modify their own job posts."""
    def has_object_permission(self, request, view, obj):
        # Read-only safe methods (GET, HEAD, OPTIONS) are allowed for any authorized request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write operations are restricted strictly to the employer who posted the job
        return obj.employer.user == request.user