import django_filters
from .models import Room, Reservation, HousekeepingTask, ServiceRequest


class RoomFilter(django_filters.FilterSet):
    floor = django_filters.NumberFilter()
    status = django_filters.CharFilter()
    room_type = django_filters.UUIDFilter(field_name='room_type__id')
    min_price = django_filters.NumberFilter(field_name='room_type__base_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='room_type__base_price', lookup_expr='lte')

    class Meta:
        model = Room
        fields = ['floor', 'status', 'room_type', 'is_active']


class ReservationFilter(django_filters.FilterSet):
    check_in_from = django_filters.DateFilter(field_name='check_in_date', lookup_expr='gte')
    check_in_to = django_filters.DateFilter(field_name='check_in_date', lookup_expr='lte')
    status = django_filters.CharFilter()
    payment_status = django_filters.CharFilter()
    source = django_filters.CharFilter()
    guest = django_filters.UUIDFilter(field_name='guest__id')
    room = django_filters.UUIDFilter(field_name='room__id')

    class Meta:
        model = Reservation
        fields = ['status', 'payment_status', 'source', 'guest', 'room']


class HousekeepingTaskFilter(django_filters.FilterSet):
    scheduled_from = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='gte')
    scheduled_to = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='lte')

    class Meta:
        model = HousekeepingTask
        fields = ['status', 'priority', 'task_type', 'assigned_to', 'room']


class ServiceRequestFilter(django_filters.FilterSet):
    class Meta:
        model = ServiceRequest
        fields = ['status', 'category', 'assigned_to', 'reservation']
