"""
MAGHAZ Assist — Hospitality Models
Rooms, reservations, guests, housekeeping, room service.
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import TimestampedModel


class RoomType(TimestampedModel):
    """Configurable room categories e.g. Standard, Deluxe, Suite."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey('core.Organisation', on_delete=models.CASCADE, related_name='room_types')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_occupancy = models.PositiveSmallIntegerField(default=2)
    amenities = models.TextField(blank=True, help_text='Comma-separated list of amenities')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Room(TimestampedModel):
    class Status(models.TextChoices):
        AVAILABLE   = 'available',   'Available'
        OCCUPIED    = 'occupied',    'Occupied'
        RESERVED    = 'reserved',    'Reserved'
        MAINTENANCE = 'maintenance', 'Under Maintenance'
        OUT_OF_SERVICE = 'out_of_service', 'Out of Service'

    class Floor(models.IntegerChoices):
        GROUND = 0, 'Ground Floor'
        FIRST  = 1, 'First Floor'
        SECOND = 2, 'Second Floor'
        THIRD  = 3, 'Third Floor'
        FOURTH = 4, 'Fourth Floor'
        FIFTH  = 5, 'Fifth Floor'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey('core.Organisation', on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name='rooms')
    floor = models.IntegerField(choices=Floor.choices, default=Floor.GROUND)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Overrides room type base price if set'
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    @property
    def price(self):
        return self.price_override or self.room_type.base_price

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name})"

    class Meta:
        ordering = ['room_number']
        unique_together = ['organisation', 'room_number']


class Guest(TimestampedModel):
    class IDType(models.TextChoices):
        PASSPORT      = 'passport',       'Passport'
        NATIONAL_ID   = 'national_id',    'National ID'
        DRIVERS_LICENSE = 'drivers_license', "Driver's Licence"
        OTHER         = 'other',          'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey('core.Organisation', on_delete=models.CASCADE, related_name='guests')
    # Optional link to a portal user account
    user_account = models.OneToOneField(
        'core.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='guest_profile'
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    id_type = models.CharField(max_length=20, choices=IDType.choices, blank=True)
    id_number = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.get_full_name()

    class Meta:
        ordering = ['last_name', 'first_name']


class Reservation(TimestampedModel):
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        CONFIRMED  = 'confirmed',  'Confirmed'
        CHECKED_IN = 'checked_in', 'Checked In'
        CHECKED_OUT = 'checked_out', 'Checked Out'
        CANCELLED  = 'cancelled',  'Cancelled'
        NO_SHOW    = 'no_show',    'No Show'

    class PaymentStatus(models.TextChoices):
        UNPAID     = 'unpaid',     'Unpaid'
        PARTIAL    = 'partial',    'Partially Paid'
        PAID       = 'paid',       'Fully Paid'
        REFUNDED   = 'refunded',   'Refunded'

    class Source(models.TextChoices):
        WALK_IN    = 'walk_in',    'Walk-in'
        PHONE      = 'phone',      'Phone'
        EMAIL      = 'email',      'Email'
        ONLINE     = 'online',     'Online Portal'
        AGENT      = 'agent',      'Travel Agent'
        OTHER      = 'other',      'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey('core.Organisation', on_delete=models.CASCADE, related_name='reservations')
    reservation_number = models.CharField(max_length=20, unique=True, editable=False)
    guest = models.ForeignKey(Guest, on_delete=models.PROTECT, related_name='reservations')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='reservations')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    actual_check_in = models.DateTimeField(null=True, blank=True)
    actual_check_out = models.DateTimeField(null=True, blank=True)
    num_adults = models.PositiveSmallIntegerField(default=1)
    num_children = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.WALK_IN)
    rate_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_requests = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL,
        null=True, related_name='created_reservations'
    )

    @property
    def nights(self):
        return (self.check_out_date - self.check_in_date).days

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    def save(self, *args, **kwargs):
        if not self.reservation_number:
            import random, string
            self.reservation_number = 'RES-' + ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=8)
            )
        if not self.total_amount:
            self.total_amount = self.rate_per_night * self.nights
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reservation_number} — {self.guest} in Room {self.room.room_number}"

    class Meta:
        ordering = ['-created_at']


class ReservationPayment(TimestampedModel):
    class Method(models.TextChoices):
        CASH         = 'cash',         'Cash'
        CARD         = 'card',         'Card'
        MOBILE_MONEY = 'mobile_money', 'Mobile Money'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        OTHER        = 'other',        'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, related_name='recorded_payments'
    )

    def __str__(self):
        return f"{self.reservation.reservation_number} — GHS {self.amount} via {self.method}"

    class Meta:
        ordering = ['-created_at']


class HousekeepingTask(TimestampedModel):
    class TaskType(models.TextChoices):
        CLEANING     = 'cleaning',     'Room Cleaning'
        TURNDOWN     = 'turndown',     'Turndown Service'
        DEEP_CLEAN   = 'deep_clean',   'Deep Clean'
        INSPECTION   = 'inspection',   'Room Inspection'
        RESTOCK      = 'restock',      'Restock Supplies'
        MAINTENANCE_REQ = 'maintenance_req', 'Maintenance Request'

    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH   = 'high',   'High'
        URGENT = 'urgent', 'Urgent'

    class Status(models.TextChoices):
        PENDING     = 'pending',     'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED   = 'completed',   'Completed'
        SKIPPED     = 'skipped',     'Skipped'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey('core.Organisation', on_delete=models.CASCADE, related_name='housekeeping_tasks')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='housekeeping_tasks')
    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    assigned_to = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='housekeeping_tasks'
    )
    scheduled_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    reservation = models.ForeignKey(
        Reservation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='housekeeping_tasks'
    )

    def __str__(self):
        return f"{self.get_task_type_display()} — Room {self.room.room_number} ({self.status})"

    class Meta:
        ordering = ['scheduled_date', 'priority']


class ServiceRequest(TimestampedModel):
    """In-room service requests from guests during a stay."""
    class Category(models.TextChoices):
        FOOD_BEVERAGE = 'food_beverage', 'Food & Beverage'
        AMENITIES     = 'amenities',     'Amenities'
        LAUNDRY       = 'laundry',       'Laundry'
        TRANSPORT     = 'transport',     'Transport'
        WAKE_UP_CALL  = 'wake_up_call',  'Wake-up Call'
        MAINTENANCE   = 'maintenance',   'Maintenance'
        OTHER         = 'other',         'Other'

    class Status(models.TextChoices):
        OPEN        = 'open',        'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        FULFILLED   = 'fulfilled',   'Fulfilled'
        CANCELLED   = 'cancelled',   'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey('core.Organisation', on_delete=models.CASCADE, related_name='service_requests')
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='service_requests')
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='service_requests'
    )
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_category_display()} — {self.reservation.reservation_number} [{self.status}]"

    class Meta:
        ordering = ['-created_at']
