#!/bin/bash
set -euo pipefail

cd /var/www/django_app
source venv/bin/activate

echo "=== PENDING MIGRATION CHECK ==="

echo "=== MIGRATION SAFETY GUIDELINES ==="
echo "1. Avoid adding NOT NULL columns without default on live high-traffic tables."
echo "2. For large tables: add nullable -> backfill data -> add constraint."
echo "3. Verify SQL impact with: python manage.py sqlmigrate <app> <migration_number>"
