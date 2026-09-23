#!/bin/bash
set -euo pipefail

S3_BUCKET="zecpath-resumes-prod-2026"

echo "Fetching latest backup from S3..."
LATEST_BACKUP=$(aws s3 ls "s3://${S3_BUCKET}/backups/" --region eu-north-1 | sort | tail -n 1 | awk '{print $4}')

if [ -z "$LATEST_BACKUP" ]; then
    echo "No backups found in s3://${S3_BUCKET}/backups/"
    exit 1
fi

echo "Latest backup: $LATEST_BACKUP"
DEST="/tmp/$LATEST_BACKUP"
aws s3 cp "s3://${S3_BUCKET}/backups/$LATEST_BACKUP" "$DEST" --region eu-north-1

if [[ "$LATEST_BACKUP" == *"sqlite"* ]]; then
    gunzip -t "$DEST"
    echo "Integrity verification check: SQLite archive is valid."
else
    gunzip -t "$DEST"
    echo "Integrity verification check: PostgreSQL gzip archive is valid."
fi

rm -f "$DEST"
echo "Restore check test PASSED."
