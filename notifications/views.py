from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Notification, NotificationTemplate
from .serializers import NotificationSerializer, NotificationTemplateSerializer
from core.permissions import IsSystemAdmin


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.status = Notification.Status.READ
        notification.read_at = timezone.now()
        notification.save(update_fields=['status', 'read_at'])
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(
            recipient=request.user,
            status=Notification.Status.SENT
        ).update(status=Notification.Status.READ, read_at=timezone.now())
        return Response({'status': 'all marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            status__in=[Notification.Status.SENT, Notification.Status.DELIVERED]
        ).count()
        return Response({'unread_count': count})


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsSystemAdmin]

    def get_queryset(self):
        return NotificationTemplate.objects.filter(organisation=self.request.user.organisation)

    def perform_create(self, serializer):
        serializer.save(organisation=self.request.user.organisation)
