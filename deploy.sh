#!/bin/bash
set -e

APP_DIR="/var/www/django_app"
VENV_PATH="$APP_DIR/venv"
BRANCH="feature/ats-models-setup"

echo "=== [1/5] Moving to project root ==="
cd "$APP_DIR"

echo "=== [2/5] Pulling latest changes from Git ($BRANCH) ==="
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "=== [3/5] Updating dependencies in virtual environment ==="
source "$VENV_PATH/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn djangorestframework-simplejwt

echo "=== [4/5] Running migrations and compiling static assets ==="
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "=== [5/5] Restarting Gunicorn daemon & Reloading Nginx ==="
sudo systemctl restart gunicorn
sudo systemctl reload nginx

echo "=== Automated Deployment Finished Successfully ==="
