"""
MAGHAZ Assist — Audit Log Middleware
Captures write operations system-wide.
"""
import json
import logging

logger = logging.getLogger('audit')

WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
EXCLUDED_PATHS = ['/admin/', '/api/v1/auth/token/refresh/']


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.method in WRITE_METHODS
            and request.user.is_authenticated
            and not any(request.path.startswith(p) for p in EXCLUDED_PATHS)
            and response.status_code < 400
        ):
            self._log(request, response)

        return response

    def _log(self, request, response):
        try:
            from audit.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                organisation=request.user.organisation,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                ip_address=self._get_ip(request),
            )
        except Exception:
            pass  # Audit failure must never break the request

    def _get_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
