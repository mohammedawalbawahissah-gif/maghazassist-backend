from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Organisation, BusinessUnit, Department, User
from .serializers import (
    OrganisationSerializer, BusinessUnitSerializer,
    DepartmentSerializer, UserSerializer, UserCreateSerializer
)
from .permissions import IsSystemAdmin, IsExecutive


class OrganisationViewSet(viewsets.ModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    permission_classes = [IsSystemAdmin]


class BusinessUnitViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessUnitSerializer
    permission_classes = [IsExecutive]

    def get_queryset(self):
        return BusinessUnit.objects.filter(organisation=self.request.user.organisation)


class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsExecutive]

    def get_queryset(self):
        return Department.objects.filter(organisation=self.request.user.organisation)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSystemAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        qs = User.objects.select_related('organisation', 'department')
        if not self.request.user.role == 'system_admin':
            qs = qs.filter(organisation=self.request.user.organisation)
        return qs

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
