from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['module', 'status', 'related_object_type']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'expiry_date', 'title']

    def get_queryset(self):
        return Document.objects.filter(
            organisation=self.request.user.organisation
        ).select_related('uploaded_by')

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        doc = self.get_object()
        versions = Document.objects.filter(parent=doc).order_by('version')
        serializer = self.get_serializer(versions, many=True)
        return Response(serializer.data)
