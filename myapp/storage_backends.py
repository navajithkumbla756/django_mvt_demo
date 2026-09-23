from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PrivateResumeStorage(S3Boto3Storage):
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "zecpath-resumes-prod-2026")
    region_name = getattr(settings, "AWS_S3_REGION_NAME", "eu-north-1")
    endpoint_url = "https://s3.eu-north-1.amazonaws.com"
    location = ""
    default_acl = "private"
    file_overwrite = True
    custom_domain = False
    querystring_auth = True
    querystring_expire = 300

    def exists(self, name):
        return False


ResumeStorage = PrivateResumeStorage
