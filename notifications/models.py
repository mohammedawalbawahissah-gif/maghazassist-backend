"""
MAGHAZ Assist — Notifications Models
Multi-channel notification engine: in-app, email, SMS, push, WhatsApp.
"""
import uuid
from django.db import models
from core.models import TimestampedModel


class NotificationTemplate(TimestampedModel):
    """Reusable message templates per event type and channel."""
    class Channel(models.TextChoices):
        IN_APP    = 'in_app',    'In-App'
        EMAIL     = 'email',     'Email'
        SMS       = 'sms',       'SMS'
        PUSH      = 'push',      'Push'
        WHATSAPP  = 'whatsapp',  'WhatsApp'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey('core.Organisation', on_delete=models.CASCADE, related_name='notification_templates')
    event_type = models.CharField(max_length=100)  # e.g. 'rent_due', 'booking_confirmed'
    channel = models.CharField(max_length=20, choices=Channel.choices)
    subject = models.CharField(max_length=255, blank=True)  # email subject
    body = models.TextField()  # supports {{ variable }} placeholders
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['organisation', 'event_type', 'channel']

    def __str__(self):
        return f"{self.event_type} via {self.channel}"


class Notification(TimestampedModel):
    """A single notification instance sent to a user."""
    class Channel(models.TextChoices):
        IN_APP    = 'in_app',    'In-App'
        EMAIL     = 'email',     'Email'
        SMS       = 'sms',       'SMS'
        PUSH      = 'push',      'Push'
        WHATSAPP  = 'whatsapp',  'WhatsApp'

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        SENT      = 'sent',      'Sent'
        DELIVERED = 'delivered', 'Delivered'
        FAILED    = 'failed',    'Failed'
        READ      = 'read',      'Read'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey('core.Organisation', on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(max_length=20, choices=Channel.choices)
    event_type = models.CharField(max_length=100)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Generic link back to the triggering object
    related_object_type = models.CharField(max_length=100, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} → {self.recipient} via {self.channel} [{self.status}]"
