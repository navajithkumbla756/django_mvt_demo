# myapp/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Employer, Candidate

@receiver(post_save, sender=CustomUser)
def create_role_based_profile(sender, instance, created, **kwargs):
    """Wired event listener that catches new account entries and generates the correct profile profile row."""
    if created:
        if instance.role == 'EMPLOYER':
            Employer.objects.create(
                user=instance,
                company_name=f"{instance.name}'s Organization Workspace"
            )
        elif instance.role == 'CANDIDATE':
            Candidate.objects.create(
                user=instance,
                skills="Initial Registration State"
            )

@receiver(post_save, sender=CustomUser)
def save_role_based_profile(sender, instance, **kwargs):
    """Ensures downstream profile relations sync parameters whenever user mutations evaluate."""
    if instance.role == 'EMPLOYER' and hasattr(instance, 'employer_profile'):
        instance.employer_profile.save()
    elif instance.role == 'CANDIDATE' and hasattr(instance, 'candidate_profile'):
        instance.candidate_profile.save()