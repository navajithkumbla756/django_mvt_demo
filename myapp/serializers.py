# myapp/serializers.py
from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        # Remove any non-existent fields like 'company_name' from the writable inputs
        fields = ['id', 'employer', 'title', 'description', 'posted_at']