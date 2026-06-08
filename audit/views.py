from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuditLog
from core.permissions import IsSystemAdmin, IsExecutive
from rest_framework import serializers


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.StringRelatedField(source='user')

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_name', 'organisation', 'method', 'path', 'status_code', 'ip_address', 'timestamp']


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsSystemAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['method', 'status_code', 'user', 'organisation']
    search_fields = ['path', 'ip_address']
    ordering_fields = ['timestamp']

    def get_queryset(self):
        return AuditLog.objects.select_related('user', 'organisation').filter(
            organisation=self.request.user.organisation
        )
