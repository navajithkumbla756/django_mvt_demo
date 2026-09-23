from django.db import models


class EncryptedCharField(models.CharField):
    """
    A field proxy for encrypted character storage.
    Acts as a standard CharField if cryptographic backend is not explicitly loaded.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 255)
        super().__init__(*args, **kwargs)
