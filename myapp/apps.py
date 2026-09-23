# myapp/apps.py
from django.apps import AppConfig


class MyappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "myapp"

    def ready(self):
        import myapp.signals  # noqa: F401  # Explicit absolute local module connection pattern
