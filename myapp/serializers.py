# myapp/serializers.py
from rest_framework import serializers
from .models import CustomUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'phone', 'role', 'password']

    def create(self, validated_data):
        # Extracts user details and hashes passwords using CustomUserManager
        return CustomUser.objects.create_user(**validated_data)
    
    # myapp/serializers.py (Append to bottom)
from .models import Job, Application

class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='employer.company_name', read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'company_name', 'title', 'description', 'posted_at']


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    candidate_name = serializers.CharField(source='candidate.user.name', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job', 'job_title', 'candidate_name', 'cover_letter', 'applied_at']