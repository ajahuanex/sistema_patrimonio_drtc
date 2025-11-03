from django.db import models
from django.contrib.auth.models import User


class BaseModel(models.Model):
    """Modelo base con campos de auditoría"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='%(class)s_created',
        null=True, 
        blank=True
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='%(class)s_updated',
        null=True, 
        blank=True
    )

    class Meta:
        abstract = True