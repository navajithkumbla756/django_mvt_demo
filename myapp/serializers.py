# myapp/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser, Job, Application

# --- AUTHENTICATION SERIALIZERS ---

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'phone', 'role', 'password']

    def validate_email(self, value):
        """Secures email uniqueness constraint."""
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return value.lower().strip()

    def create(self, validated_data):
        """Passes arguments down to the custom manager to safely handle password hashing."""
        return CustomUser.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Enriches the standard login response payload to return user metadata alongside tokens."""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['name'] = user.name
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'name': self.user.name,
            'role': self.user.role
        }
        return data


# --- ATS FEATURE SERIALIZERS (CRITICAL: Missing pieces added back) ---

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