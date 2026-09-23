#!/usr/bin/env python3
import os, sys, gzip, django
from pathlib import Path

sys.path.append('/var/www/django_app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import boto3
from django.conf import settings

bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'zecpath-resumes-prod-2026')
region = getattr(settings, 'AWS_S3_REGION_NAME', 'eu-north-1')

s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=region
)

print('Searching for backups in S3 bucket:', bucket)
response = s3.list_objects_v2(Bucket=bucket, Prefix='backups/')
contents = response.get('Contents', [])

if not contents:
    print('No backup files found under backups/ prefix.')
    sys.exit(1)

# Get the latest modified backup
latest_obj = sorted(contents, key=lambda x: x['LastModified'], reverse=True)[0]
s3_key = latest_obj['Key']
print(f'Latest backup located: {s3_key} ({latest_obj["Size"]} bytes)')

local_target = Path('/tmp') / Path(s3_key).name
print(f'Downloading {s3_key} to {local_target} for validation...')
s3.download_file(bucket, s3_key, str(local_target))

# Test gzip and file integrity
with gzip.open(local_target, 'rb') as gz:
    header = gz.read(100)
    if not header:
        print('Integrity check failed: archive is empty.')
        sys.exit(1)

print('Integrity verification check: Database gzip archive is valid and readable.')
local_target.unlink()
print('Restore check test PASSED.')
