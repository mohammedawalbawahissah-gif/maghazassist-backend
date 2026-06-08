from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.StringRelatedField(source='uploaded_by')

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'module', 'tags',
            'file', 'file_size', 'mime_type', 'version', 'parent',
            'status', 'expiry_date', 'uploaded_by', 'uploaded_by_name',
            'related_object_type', 'related_object_id', 'created_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'version', 'created_at']

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        validated_data['organisation'] = self.context['request'].user.organisation
        file = validated_data.get('file')
        if file:
            validated_data['file_size'] = file.size
            validated_data['mime_type'] = getattr(file, 'content_type', '')
        return super().create(validated_data)
