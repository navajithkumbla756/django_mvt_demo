from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from myapp.encryption import EncryptedCharField
from myapp.storage_backends import PrivateResumeStorage

private_storage = PrivateResumeStorage()
ResumeStorage = PrivateResumeStorage


def resume_upload_path(instance, filename: str) -> str:
    return f"candidates/{instance.user_id}/{filename}"


class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be specified.")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")
        return self.create_user(email, name, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("EMPLOYER", "Employer"),
        ("CANDIDATE", "Candidate"),
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default="CANDIDATE", db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"


class Employer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employer_profile",
    )
    company_name = models.CharField(max_length=150, blank=True, db_index=True)
    domain = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=1)
    is_verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["is_deleted", "company_name"])]

    def __str__(self):
        return self.company_name if self.company_name else f"Workspace of {self.user.email}"


class CandidateProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
    )
    contact_number = EncryptedCharField(max_length=255, blank=True, null=True)
    skills = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    expected_salary = EncryptedCharField(max_length=255, blank=True, null=True)
    resume = models.FileField(
        storage=private_storage,
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx"])],
        null=True,
        blank=True,
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} Profile"


Candidate = CandidateProfile


class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full Time"
        PART_TIME = "PART_TIME", "Part Time"
        REMOTE = "REMOTE", "Remote"
        CONTRACT = "CONTRACT", "Contract"

    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name="posted_jobs", db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    skills_required = models.TextField(blank=True)
    experience_required = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=255, default="Remote")
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    posted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.employer.company_name})"


class Application(models.Model):
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="applications",
        null=True,
        blank=True,
        db_index=True,
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications", db_index=True)
    resume_snapshot = models.FileField(
        storage=private_storage,
        upload_to="resumes/snapshots/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx"])],
        max_length=255,
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=30, default="APPLIED", db_index=True)
    ats_score = models.FloatField(default=0.0, db_index=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True, db_index=True)
    applied_at = models.DateTimeField(default=timezone.now, null=True, blank=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Application #{self.id}"

    class Meta:
        indexes = [
            models.Index(fields=["status"], name="app_status_idx"),
        ]


class InterviewRescheduleRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='reschedule_requests')
    requested_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='interview_reschedules')
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

    def __str__(self):
        return f"Reschedule #{self.id} (App #{self.application_id}) - {self.status}"
