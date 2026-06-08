from rest_framework import serializers
from .models import Notification, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'channel', 'event_type', 'subject', 'body',
            'status', 'sent_at', 'read_at',
            'related_object_type', 'related_object_id', 'created_at'
        ]
        read_only_fields = fields


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ['id', 'event_type', 'channel', 'subject', 'body', 'is_active']
        read_only_fields = ['id']
