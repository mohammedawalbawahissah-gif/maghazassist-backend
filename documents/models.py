"""
MAGHAZ Assist — Document Management Models
"""
import uuid
from django.db import models
from core.models import TimestampedModel


class Document(TimestampedModel):
    class Module(models.TextChoices):
        HOSPITALITY   = 'hospitality',   'Hospitality'
        REAL_ESTATE   = 'real_estate',   'Real Estate'
        CONSTRUCTION  = 'construction',  'Construction'
        HR            = 'hr',            'HR'
        FINANCE       = 'finance',       'Finance'
        TRANSPORT     = 'transport',     'Transport'
        GENERAL       = 'general',       'General'

    class Status(models.TextChoices):
        DRAFT    = 'draft',    'Draft'
        ACTIVE   = 'active',   'Active'
        ARCHIVED = 'archived', 'Archived'
        EXPIRED  = 'expired',  'Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey('core.Organisation', on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=30, choices=Module.choices, default=Module.GENERAL)
    tags = models.CharField(max_length=500, blank=True)  # comma-separated
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_size = models.PositiveIntegerField(null=True, blank=True)  # bytes
    mime_type = models.CharField(max_length=100, blank=True)
    version = models.PositiveSmallIntegerField(default=1)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versions')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    expiry_date = models.DateField(null=True, blank=True)

    # Generic link to any model
    related_object_type = models.CharField(max_length=100, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (v{self.version})"
