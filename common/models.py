import uuid

from django.db import models


class BaseModel(models.Model):
    """
    Base model for all models which includes minimum required date fields
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
