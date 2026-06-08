"""
MAGHAZ Assist — Notification Celery Tasks
Each channel dispatched as an async background task.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def dispatch_notification(recipient, event_type, context: dict, channels: list = None, related_obj=None):
    """
    Entry point for all modules to fire notifications.
    Respects user channel preferences.
    """
    from core.models import User
    from .models import Notification, NotificationTemplate

    if channels is None:
        # Default: use all channels the user has enabled
        channels = []
        if recipient.notify_email:
            channels.append('email')
        if recipient.notify_sms:
            channels.append('sms')
        if recipient.notify_push:
            channels.append('push')
        if recipient.notify_whatsapp:
            channels.append('whatsapp')
        channels.append('in_app')  # always send in-app

    for channel in channels:
        try:
            template = NotificationTemplate.objects.get(
                organisation=recipient.organisation,
                event_type=event_type,
                channel=channel,
                is_active=True,
            )
            body = _render(template.body, context)
            subject = _render(template.subject, context) if template.subject else ''
        except NotificationTemplate.DoesNotExist:
            body = context.get('message', event_type)
            subject = context.get('subject', '')

        notification = Notification.objects.create(
            organisation=recipient.organisation,
            recipient=recipient,
            channel=channel,
            event_type=event_type,
            subject=subject,
            body=body,
            related_object_type=related_obj.__class__.__name__ if related_obj else '',
            related_object_id=str(related_obj.pk) if related_obj else '',
        )
        _send_async(notification.id, channel)


def _render(template_str, context):
    """Simple {{ key }} template rendering."""
    for key, value in context.items():
        template_str = template_str.replace(f'{{{{{key}}}}}', str(value))
    return template_str


def _send_async(notification_id, channel):
    task_map = {
        'email':    send_email_notification,
        'sms':      send_sms_notification,
        'push':     send_push_notification,
        'whatsapp': send_whatsapp_notification,
        'in_app':   mark_inapp_sent,
    }
    task = task_map.get(channel)
    if task:
        task.delay(str(notification_id))


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, notification_id):
    from .models import Notification
    from django.core.mail import send_mail
    from django.conf import settings

    try:
        n = Notification.objects.get(id=notification_id)
        send_mail(
            subject=n.subject or 'MAGHAZ Assist Notification',
            message=n.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[n.recipient.email],
            fail_silently=False,
        )
        n.status = Notification.Status.SENT
        n.sent_at = timezone.now()
        n.save(update_fields=['status', 'sent_at'])
    except Exception as exc:
        logger.error(f"Email notification {notification_id} failed: {exc}")
        from .models import Notification
        Notification.objects.filter(id=notification_id).update(
            status=Notification.Status.FAILED,
            error_message=str(exc)
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_sms_notification(self, notification_id):
    """Sends via Hubtel (primary) with Twilio fallback."""
    from .models import Notification
    from django.conf import settings
    import requests

    try:
        n = Notification.objects.get(id=notification_id)
        phone = n.recipient.phone
        if not phone:
            n.status = Notification.Status.FAILED
            n.error_message = 'Recipient has no phone number'
            n.save(update_fields=['status', 'error_message'])
            return

        sent = False
        if settings.HUBTEL_CLIENT_ID:
            try:
                resp = requests.post(
                    'https://smsc.hubtel.com/v1/messages/send',
                    auth=(settings.HUBTEL_CLIENT_ID, settings.HUBTEL_CLIENT_SECRET),
                    json={
                        'From': settings.HUBTEL_SENDER_ID,
                        'To': phone,
                        'Content': n.body[:160],
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                sent = True
            except Exception as e:
                logger.warning(f"Hubtel SMS failed, trying Twilio: {e}")

        if not sent and settings.TWILIO_ACCOUNT_SID:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=n.body[:160],
                from_=settings.TWILIO_FROM_NUMBER,
                to=phone,
            )
            sent = True

        if sent:
            n.status = Notification.Status.SENT
            n.sent_at = timezone.now()
            n.save(update_fields=['status', 'sent_at'])
        else:
            raise Exception("No SMS provider configured")

    except Exception as exc:
        logger.error(f"SMS notification {notification_id} failed: {exc}")
        from .models import Notification
        Notification.objects.filter(id=notification_id).update(
            status=Notification.Status.FAILED, error_message=str(exc)
        )
        raise self.retry(exc=exc, countdown=120)


@shared_task(bind=True, max_retries=3)
def send_push_notification(self, notification_id):
    """Sends via Firebase Cloud Messaging."""
    from .models import Notification
    from django.conf import settings
    import requests

    try:
        n = Notification.objects.get(id=notification_id)
        tokens = list(
            n.recipient.device_tokens.filter(is_active=True).values_list('token', flat=True)
        )
        if not tokens or not settings.FCM_SERVER_KEY:
            return

        payload = {
            'registration_ids': tokens,
            'notification': {
                'title': n.subject or 'MAGHAZ Assist',
                'body': n.body,
            },
            'data': {
                'event_type': n.event_type,
                'related_object_type': n.related_object_type,
                'related_object_id': n.related_object_id,
            },
        }
        resp = requests.post(
            'https://fcm.googleapis.com/fcm/send',
            headers={
                'Authorization': f'key={settings.FCM_SERVER_KEY}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        n.status = Notification.Status.SENT
        n.sent_at = timezone.now()
        n.save(update_fields=['status', 'sent_at'])

    except Exception as exc:
        logger.error(f"Push notification {notification_id} failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_whatsapp_notification(self, notification_id):
    """Sends via WhatsApp Business API."""
    from .models import Notification
    from django.conf import settings
    import requests

    try:
        n = Notification.objects.get(id=notification_id)
        phone = n.recipient.phone
        if not phone or not settings.WHATSAPP_API_URL:
            return

        resp = requests.post(
            settings.WHATSAPP_API_URL,
            headers={
                'Authorization': f'Bearer {settings.WHATSAPP_API_TOKEN}',
                'Content-Type': 'application/json',
            },
            json={
                'messaging_product': 'whatsapp',
                'to': phone,
                'type': 'text',
                'text': {'body': n.body},
            },
            timeout=10,
        )
        resp.raise_for_status()
        n.status = Notification.Status.SENT
        n.sent_at = timezone.now()
        n.save(update_fields=['status', 'sent_at'])

    except Exception as exc:
        logger.error(f"WhatsApp notification {notification_id} failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def mark_inapp_sent(notification_id):
    from .models import Notification
    Notification.objects.filter(id=notification_id).update(
        status=Notification.Status.SENT,
        sent_at=timezone.now()
    )
