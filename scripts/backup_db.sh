#!/bin/bash
set -euo pipefail

BACKUP_DIR="/tmp/db_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
S3_BUCKET="zecpath-resumes-prod-2026"

mkdir -p "$BACKUP_DIR"

# Detect DB type from settings
DB_ENGINE=$(python3 -c "
import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings'); django.setup()
from django.conf import settings
print(settings.DATABASES['default']['ENGINE'])
")

if [[ "$DB_ENGINE" == *"sqlite"* ]]; then
    DB_FILE=$(python3 -c "
import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings'); django.setup()
from django.conf import settings
print(settings.DATABASES['default']['NAME'])
")
    BACKUP_FILE="${BACKUP_DIR}/sqlite_backup_${TIMESTAMP}.db.gz"
    gzip -c "$DB_FILE" > "$BACKUP_FILE"
    S3_KEY="backups/sqlite_backup_${TIMESTAMP}.db.gz"
else
    DB_NAME=$(python3 -c "
import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings'); django.setup()
from django.conf import settings
print(settings.DATABASES['default']['NAME'])
")
    BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"
    pg_dump "$DB_NAME" | gzip > "$BACKUP_FILE"
    S3_KEY="backups/${DB_NAME}_${TIMESTAMP}.sql.gz"
fi

echo "[$(date)] Uploading backup to s3://${S3_BUCKET}/${S3_KEY}..."
aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/${S3_KEY}" --region eu-north-1

rm -f "$BACKUP_FILE"
echo "[$(date)] Backup completed successfully."
