#!/usr/bin/env python3
import os, sys, gzip, datetime, django
from pathlib import Path

# Setup Django environment
sys.path.append('/var/www/django_app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import boto3
from django.conf import settings

timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_dir = Path('/tmp/db_backups')
backup_dir.mkdir(parents=True, exist_ok=True)

db_conf = settings.DATABASES['default']
db_name = str(db_conf['NAME'])
bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'zecpath-resumes-prod-2026')
region = getattr(settings, 'AWS_S3_REGION_NAME', 'eu-north-1')

s3 = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=region
)

if 'sqlite' in db_conf['ENGINE']:
    compressed_file = backup_dir / f'sqlite_backup_{timestamp}.db.gz'
    print(f'[{datetime.datetime.now()}] Compressing SQLite database: {db_name}...')
    with open(db_name, 'rb') as f_in:
        with gzip.open(compressed_file, 'wb') as f_out:
            f_out.writelines(f_in)
    s3_key = f'backups/{compressed_file.name}'
else:
    compressed_file = backup_dir / f'{db_name}_{timestamp}.sql.gz'
    os.system(f'pg_dump {db_name} | gzip > {compressed_file}')
    s3_key = f'backups/{compressed_file.name}'

print(f'[{datetime.datetime.now()}] Uploading to s3://{bucket}/{s3_key}...')
s3.upload_file(str(compressed_file), bucket, s3_key)
compressed_file.unlink()
print(f'[{datetime.datetime.now()}] Backup successfully stored at {s3_key}')
