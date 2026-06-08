"""
MAGHAZ Assist — Core Permission Classes
Role-based permission helpers used across all modules.
"""
from rest_framework.permissions import BasePermission
from .models import User


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.SYSTEM_ADMIN


class IsExecutive(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SYSTEM_ADMIN, User.Role.EXECUTIVE
        ]


class IsHotelManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SYSTEM_ADMIN, User.Role.EXECUTIVE, User.Role.HOTEL_MANAGER
        ]


class IsPropertyManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SYSTEM_ADMIN, User.Role.EXECUTIVE, User.Role.PROPERTY_MANAGER
        ]


class IsConstructionPM(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SYSTEM_ADMIN, User.Role.EXECUTIVE,
            User.Role.CONSTRUCTION_PM, User.Role.SITE_SUPERVISOR
        ]


class IsHRManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SYSTEM_ADMIN, User.Role.EXECUTIVE, User.Role.HR_MANAGER
        ]


class IsFinanceOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SYSTEM_ADMIN, User.Role.EXECUTIVE, User.Role.FINANCE_OFFICER
        ]


class IsTransportDispatcher(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SYSTEM_ADMIN, User.Role.EXECUTIVE, User.Role.TRANSPORT_DISPATCHER
        ]


class IsDriver(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.INTERNAL_DRIVER, User.Role.THIRD_PARTY_DRIVER
        ]


class IsStaffUser(BasePermission):
    """Any internal staff member (not portal users)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff_user


class IsPortalUser(BasePermission):
    """Tenant, Guest, or Third-Party Driver portal access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_portal_user


class IsSameOrganisation(BasePermission):
    """Object-level: user must belong to the same organisation as the object."""
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        obj_org = getattr(obj, 'organisation', None) or getattr(obj, 'org', None)
        return obj_org == request.user.organisation
