"""
MAGHAZ Assist — Hospitality Serializers
"""
from rest_framework import serializers
from django.utils import timezone
from .models import RoomType, Room, Guest, Reservation, ReservationPayment, HousekeepingTask, ServiceRequest


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ['id', 'name', 'description', 'base_price', 'max_occupancy', 'amenities', 'created_at']
        read_only_fields = ['id', 'created_at']


class RoomSerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Room
        fields = [
            'id', 'room_number', 'room_type', 'room_type_name',
            'floor', 'status', 'price', 'price_override',
            'notes', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class RoomAvailabilitySerializer(serializers.Serializer):
    """Used for availability search."""
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()
    room_type = serializers.UUIDField(required=False)
    num_adults = serializers.IntegerField(default=1)

    def validate(self, data):
        if data['check_in_date'] >= data['check_out_date']:
            raise serializers.ValidationError('Check-out must be after check-in.')
        if data['check_in_date'] < timezone.now().date():
            raise serializers.ValidationError('Check-in date cannot be in the past.')
        return data


class GuestSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    total_stays = serializers.SerializerMethodField()

    class Meta:
        model = Guest
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'nationality',
            'id_type', 'id_number', 'date_of_birth',
            'address', 'notes', 'total_stays', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_total_stays(self, obj):
        return obj.reservations.filter(status=Reservation.Status.CHECKED_OUT).count()


class ReservationPaymentSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.StringRelatedField(source='recorded_by')

    class Meta:
        model = ReservationPayment
        fields = ['id', 'amount', 'method', 'reference', 'notes', 'recorded_by', 'recorded_by_name', 'created_at']
        read_only_fields = ['id', 'recorded_by', 'created_at']


class ReservationSerializer(serializers.ModelSerializer):
    guest_name = serializers.CharField(source='guest.get_full_name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    room_type_name = serializers.CharField(source='room.room_type.name', read_only=True)
    nights = serializers.IntegerField(read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payments = ReservationPaymentSerializer(many=True, read_only=True)
    created_by_name = serializers.StringRelatedField(source='created_by')

    class Meta:
        model = Reservation
        fields = [
            'id', 'reservation_number',
            'guest', 'guest_name',
            'room', 'room_number', 'room_type_name',
            'check_in_date', 'check_out_date',
            'actual_check_in', 'actual_check_out',
            'num_adults', 'num_children',
            'status', 'payment_status', 'source',
            'rate_per_night', 'total_amount', 'amount_paid', 'balance_due',
            'nights', 'special_requests', 'internal_notes',
            'created_by', 'created_by_name',
            'payments', 'created_at',
        ]
        read_only_fields = [
            'id', 'reservation_number', 'total_amount',
            'created_by', 'created_at',
        ]

    def validate(self, data):
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        room = data.get('room')

        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError({'check_out_date': 'Check-out must be after check-in.'})

        # Check room availability for new reservations
        if room and check_in and check_out:
            instance = self.instance
            qs = Reservation.objects.filter(
                room=room,
                status__in=[Reservation.Status.CONFIRMED, Reservation.Status.CHECKED_IN, Reservation.Status.PENDING],
                check_in_date__lt=check_out,
                check_out_date__gt=check_in,
            )
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'room': 'Room is not available for the selected dates.'})

        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['organisation'] = self.context['request'].user.organisation
        return super().create(validated_data)


class HousekeepingTaskSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    assigned_to_name = serializers.StringRelatedField(source='assigned_to')

    class Meta:
        model = HousekeepingTask
        fields = [
            'id', 'room', 'room_number', 'task_type', 'priority',
            'status', 'assigned_to', 'assigned_to_name',
            'scheduled_date', 'completed_at', 'notes', 'reservation', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ServiceRequestSerializer(serializers.ModelSerializer):
    reservation_number = serializers.CharField(source='reservation.reservation_number', read_only=True)
    assigned_to_name = serializers.StringRelatedField(source='assigned_to')

    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'reservation', 'reservation_number',
            'category', 'description', 'status',
            'assigned_to', 'assigned_to_name',
            'fulfilled_at', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
