from datetime import timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from .models import Application, Job


class DocumentAccessService:
    """Service handling authorization and URL signing for candidate documents."""

    @staticmethod
    def get_resume_download_url(application_id: int, requesting_user):
        if not application_id or not isinstance(application_id, int):
            raise ValidationError("A valid integer application_id is required.")

        application = get_object_or_404(Application, pk=application_id)

        job_employer = getattr(application.job, "employer", None)
        user_owns_job = False

        if job_employer:
            if hasattr(job_employer, "user"):
                user_owns_job = job_employer.user == requesting_user
            else:
                user_owns_job = job_employer == requesting_user

        if not user_owns_job and not requesting_user.is_staff:
            raise PermissionDenied("You do not have permission to view resumes for this job post.")

        if not application.resume_snapshot:
            raise NotFound("No resume snapshot found for this application record.")

        try:
            download_url = application.resume_snapshot.storage.url(application.resume_snapshot.name)
        except Exception:
            download_url = f"https://s3.eu-north-1.amazonaws.com/{application.resume_snapshot.name}"

        candidate_email = getattr(application.candidate, "email", None) or getattr(
            getattr(application.candidate, "user", None), "email", ""
        )

        return {
            "application_id": application.id,
            "candidate_email": candidate_email,
            "download_url": download_url,
            "expires_in": 300,
        }


class AnalyticsService:
    """Service handling recruitment metrics and stage conversion calculations."""

    @staticmethod
    def get_base_recruiter_queryset(user):
        qs = Application.objects.all()
        if hasattr(user, "employer_profile"):
            return qs.filter(job__employer=user.employer_profile)
        if hasattr(Job, "employer"):
            if hasattr(user, "employer"):
                return qs.filter(job__employer__user=user)
            return qs.filter(job__employer=user)
        return qs

    @classmethod
    def get_funnel_metrics(cls, user, job_id=None):
        qs = cls.get_base_recruiter_queryset(user)
        job_title = "All Recruiter Postings"

        if job_id:
            try:
                job_id_int = int(job_id)
            except (ValueError, TypeError):
                raise ValidationError("Job ID parameter must be a valid integer.")

            job = Job.objects.filter(pk=job_id_int).first()
            if not job:
                raise NotFound("Job not found.")
            qs = qs.filter(job=job)
            job_title = job.title

        total_applied = qs.count()
        shortlisted = qs.filter(status__in=["SHORTLISTED", "INTERVIEW", "SELECTED"]).count()
        interview = qs.filter(status__in=["INTERVIEW", "SELECTED"]).count()
        selected = qs.filter(status="SELECTED").count()

        conversion_rate = round((selected / total_applied * 100), 2) if total_applied > 0 else 0.0

        return {
            "job_id": int(job_id) if job_id else None,
            "job_title": job_title,
            "funnel": {
                "applied": total_applied,
                "shortlisted": shortlisted,
                "interview": interview,
                "selected": selected,
                "conversion_rate_percent": conversion_rate,
            },
        }

    @classmethod
    def get_candidate_trends(cls, user, days: int = 30):
        try:
            days_int = int(days)
            if days_int <= 0:
                days_int = 30
        except (ValueError, TypeError):
            days_int = 30

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_int)

        qs = cls.get_base_recruiter_queryset(user).filter(applied_at__gte=start_date)

        trends_data = list(qs.values("job__title").annotate(applicant_count=Count("id")).order_by("-applicant_count"))

        return {
            "window_days": days_int,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trends": trends_data,
        }
