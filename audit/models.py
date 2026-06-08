import uuid
from django.db import models
from core.models import TimestampedModel


class AuditLog(models.Model):
    """Immutable system-wide audit trail. No updates or deletes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL,
        null=True, related_name='audit_logs'
    )
    organisation = models.ForeignKey(
        'core.Organisation', on_delete=models.SET_NULL,
        null=True, related_name='audit_logs'
    )
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.PositiveSmallIntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        # Prevent any modifications to audit records
        default_permissions = ('add', 'view')

    def __str__(self):
        return f"[{self.timestamp}] {self.method} {self.path} by {self.user}"
