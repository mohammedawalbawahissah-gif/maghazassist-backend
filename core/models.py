"""
MAGHAZ Assist — Core Models
Shared entities used across all modules.
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class TimestampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organisation(TimestampedModel):
    """
    Top-level tenant. Supports multi-organisation SaaS in the future.
    All data is scoped to an Organisation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='org/logos/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class BusinessUnit(TimestampedModel):
    """
    A business unit within an Organisation.
    E.g. Hotel, Real Estate Portfolio, Construction Division.
    """
    class UnitType(models.TextChoices):
        HOSPITALITY = 'hospitality', 'Hospitality'
        REAL_ESTATE = 'real_estate', 'Real Estate'
        CONSTRUCTION = 'construction', 'Construction'
        TRANSPORT = 'transport', 'Transport'
        ADMINISTRATION = 'administration', 'Administration'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='business_units')
    name = models.CharField(max_length=255)
    unit_type = models.CharField(max_length=30, choices=UnitType.choices)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.organisation.name} — {self.name}"

    class Meta:
        ordering = ['name']


class Department(TimestampedModel):
    """Department within a BusinessUnit."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='departments')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='departments')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.organisation.name} — {self.name}"

    class Meta:
        ordering = ['name']


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.SYSTEM_ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    """
    Custom User model for MAGHAZ Assist.
    Role is stored on the user; fine-grained permissions handled via RBAC.
    """
    class Role(models.TextChoices):
        SYSTEM_ADMIN         = 'system_admin',         'System Administrator'
        EXECUTIVE            = 'executive',             'Executive Management'
        HOTEL_MANAGER        = 'hotel_manager',         'Hotel Manager'
        FRONT_DESK           = 'front_desk',            'Front Desk / Guest Services'
        PROPERTY_MANAGER     = 'property_manager',      'Property Manager'
        CONSTRUCTION_PM      = 'construction_pm',       'Construction Project Manager'
        SITE_SUPERVISOR      = 'site_supervisor',       'Site Supervisor / Contractor'
        HR_MANAGER           = 'hr_manager',            'HR Manager'
        FINANCE_OFFICER      = 'finance_officer',       'Finance Officer / Accountant'
        MAINTENANCE_TEAM     = 'maintenance_team',      'Maintenance Team'
        TRANSPORT_DISPATCHER = 'transport_dispatcher',  'Transport Dispatcher'
        INTERNAL_DRIVER      = 'internal_driver',       'Internal Driver'
        THIRD_PARTY_DRIVER   = 'third_party_driver',    'Third-Party Driver'
        TENANT               = 'tenant',                'Tenant'
        GUEST                = 'guest',                 'Guest'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=30, choices=Role.choices)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='users'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='users'
    )
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Notification preferences
    notify_email = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=True)
    notify_push = models.BooleanField(default=True)
    notify_whatsapp = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_portal_user(self):
        """Tenant, Guest, and Third-Party Driver have limited portal access."""
        return self.role in [self.Role.TENANT, self.Role.GUEST, self.Role.THIRD_PARTY_DRIVER]

    @property
    def is_staff_user(self):
        return not self.is_portal_user

    class Meta:
        ordering = ['first_name', 'last_name']


class DeviceToken(TimestampedModel):
    """FCM push notification device tokens per user."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.TextField()
    device_type = models.CharField(
        max_length=10,
        choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')]
    )
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'token']
