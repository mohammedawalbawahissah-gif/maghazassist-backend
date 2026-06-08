"""
MAGHAZ Assist — Hospitality Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Sum, Q

from core.permissions import IsHotelManager, IsStaffUser
from notifications.tasks import dispatch_notification
from .models import RoomType, Room, Guest, Reservation, ReservationPayment, HousekeepingTask, ServiceRequest
from .serializers import (
    RoomTypeSerializer, RoomSerializer, RoomAvailabilitySerializer,
    GuestSerializer, ReservationSerializer, ReservationPaymentSerializer,
    HousekeepingTaskSerializer, ServiceRequestSerializer,
)
from .filters import RoomFilter, ReservationFilter, HousekeepingTaskFilter, ServiceRequestFilter


class RoomTypeViewSet(viewsets.ModelViewSet):
    serializer_class = RoomTypeSerializer
    permission_classes = [IsHotelManager]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'base_price']

    def get_queryset(self):
        return RoomType.objects.filter(organisation=self.request.user.organisation)

    def perform_create(self, serializer):
        serializer.save(organisation=self.request.user.organisation)


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RoomFilter
    search_fields = ['room_number', 'notes']
    ordering_fields = ['room_number', 'floor', 'status']

    def get_queryset(self):
        return Room.objects.filter(
            organisation=self.request.user.organisation
        ).select_related('room_type')

    def perform_create(self, serializer):
        serializer.save(organisation=self.request.user.organisation)

    @action(detail=False, methods=['post'])
    def check_availability(self, request):
        """Return available rooms for given dates and criteria."""
        serializer = RoomAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Rooms with conflicting reservations
        booked_room_ids = Reservation.objects.filter(
            organisation=request.user.organisation,
            status__in=[
                Reservation.Status.CONFIRMED,
                Reservation.Status.CHECKED_IN,
                Reservation.Status.PENDING,
            ],
            check_in_date__lt=data['check_out_date'],
            check_out_date__gt=data['check_in_date'],
        ).values_list('room_id', flat=True)

        rooms = Room.objects.filter(
            organisation=request.user.organisation,
            status=Room.Status.AVAILABLE,
            is_active=True,
        ).exclude(id__in=booked_room_ids).select_related('room_type')

        if 'room_type' in data:
            rooms = rooms.filter(room_type__id=data['room_type'])

        if data.get('num_adults'):
            rooms = rooms.filter(room_type__max_occupancy__gte=data['num_adults'])

        return Response(RoomSerializer(rooms, many=True).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsHotelManager])
    def update_status(self, request, pk=None):
        room = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Room.Status.choices):
            return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
        room.status = new_status
        room.save(update_fields=['status', 'updated_at'])
        return Response(RoomSerializer(room).data)


class GuestViewSet(viewsets.ModelViewSet):
    serializer_class = GuestSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'id_number']
    ordering_fields = ['last_name', 'created_at']

    def get_queryset(self):
        return Guest.objects.filter(organisation=self.request.user.organisation)

    def perform_create(self, serializer):
        serializer.save(organisation=self.request.user.organisation)

    @action(detail=True, methods=['get'])
    def stay_history(self, request, pk=None):
        guest = self.get_object()
        reservations = guest.reservations.select_related('room', 'room__room_type').order_by('-check_in_date')
        return Response(ReservationSerializer(reservations, many=True, context={'request': request}).data)


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ReservationFilter
    search_fields = ['reservation_number', 'guest__first_name', 'guest__last_name', 'room__room_number']
    ordering_fields = ['check_in_date', 'created_at', 'status']

    def get_queryset(self):
        return Reservation.objects.filter(
            organisation=self.request.user.organisation
        ).select_related('guest', 'room', 'room__room_type', 'created_by').prefetch_related('payments')

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        reservation = self.get_object()
        if reservation.status != Reservation.Status.CONFIRMED:
            return Response(
                {'error': f'Cannot check in a reservation with status "{reservation.status}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        reservation.status = Reservation.Status.CHECKED_IN
        reservation.actual_check_in = timezone.now()
        reservation.save(update_fields=['status', 'actual_check_in', 'updated_at'])

        reservation.room.status = Room.Status.OCCUPIED
        reservation.room.save(update_fields=['status', 'updated_at'])

        # Fire notification to guest if they have an account
        if reservation.guest.user_account:
            dispatch_notification(
                recipient=reservation.guest.user_account,
                event_type='guest_checked_in',
                context={
                    'guest_name': reservation.guest.get_full_name(),
                    'room_number': reservation.room.room_number,
                    'check_out_date': str(reservation.check_out_date),
                },
                related_obj=reservation,
            )
        return Response(ReservationSerializer(reservation, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        reservation = self.get_object()
        if reservation.status != Reservation.Status.CHECKED_IN:
            return Response(
                {'error': 'Only checked-in reservations can be checked out.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        reservation.status = Reservation.Status.CHECKED_OUT
        reservation.actual_check_out = timezone.now()
        reservation.save(update_fields=['status', 'actual_check_out', 'updated_at'])

        reservation.room.status = Room.Status.AVAILABLE
        reservation.room.save(update_fields=['status', 'updated_at'])

        # Auto-create housekeeping task after checkout
        HousekeepingTask.objects.create(
            organisation=reservation.organisation,
            room=reservation.room,
            task_type=HousekeepingTask.TaskType.CLEANING,
            priority=HousekeepingTask.Priority.HIGH,
            scheduled_date=timezone.now().date(),
            reservation=reservation,
            notes=f'Post-checkout cleaning for {reservation.reservation_number}',
        )
        return Response(ReservationSerializer(reservation, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        if reservation.status in [Reservation.Status.CHECKED_IN, Reservation.Status.CHECKED_OUT]:
            return Response(
                {'error': 'Cannot cancel a checked-in or checked-out reservation.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=['status', 'updated_at'])

        if reservation.room.status == Room.Status.RESERVED:
            reservation.room.status = Room.Status.AVAILABLE
            reservation.room.save(update_fields=['status', 'updated_at'])

        return Response(ReservationSerializer(reservation, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        reservation = self.get_object()
        serializer = ReservationPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(reservation=reservation, recorded_by=request.user)

        # Update amount paid and payment status
        total_paid = reservation.payments.aggregate(total=Sum('amount'))['total'] or 0
        reservation.amount_paid = total_paid
        if total_paid >= reservation.total_amount:
            reservation.payment_status = Reservation.PaymentStatus.PAID
        elif total_paid > 0:
            reservation.payment_status = Reservation.PaymentStatus.PARTIAL
        reservation.save(update_fields=['amount_paid', 'payment_status', 'updated_at'])

        return Response(ReservationPaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Hospitality KPIs for the dashboard."""
        org = request.user.organisation
        today = timezone.now().date()

        total_rooms = Room.objects.filter(organisation=org, is_active=True).count()
        occupied = Room.objects.filter(organisation=org, status=Room.Status.OCCUPIED).count()
        available = Room.objects.filter(organisation=org, status=Room.Status.AVAILABLE).count()
        maintenance = Room.objects.filter(organisation=org, status=Room.Status.MAINTENANCE).count()

        arrivals_today = Reservation.objects.filter(
            organisation=org, check_in_date=today,
            status=Reservation.Status.CONFIRMED
        ).count()
        departures_today = Reservation.objects.filter(
            organisation=org, check_out_date=today,
            status=Reservation.Status.CHECKED_IN
        ).count()
        in_house = Reservation.objects.filter(
            organisation=org, status=Reservation.Status.CHECKED_IN
        ).count()

        pending_housekeeping = HousekeepingTask.objects.filter(
            organisation=org,
            status__in=[HousekeepingTask.Status.PENDING, HousekeepingTask.Status.IN_PROGRESS],
            scheduled_date=today,
        ).count()

        open_service_requests = ServiceRequest.objects.filter(
            organisation=org,
            status__in=[ServiceRequest.Status.OPEN, ServiceRequest.Status.IN_PROGRESS],
        ).count()

        occupancy_rate = round((occupied / total_rooms * 100), 1) if total_rooms else 0

        return Response({
            'rooms': {
                'total': total_rooms,
                'occupied': occupied,
                'available': available,
                'maintenance': maintenance,
                'occupancy_rate': occupancy_rate,
            },
            'today': {
                'arrivals': arrivals_today,
                'departures': departures_today,
                'in_house': in_house,
            },
            'operations': {
                'pending_housekeeping': pending_housekeeping,
                'open_service_requests': open_service_requests,
            },
        })


class HousekeepingTaskViewSet(viewsets.ModelViewSet):
    serializer_class = HousekeepingTaskSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = HousekeepingTaskFilter
    search_fields = ['room__room_number', 'notes']
    ordering_fields = ['scheduled_date', 'priority', 'status']

    def get_queryset(self):
        return HousekeepingTask.objects.filter(
            organisation=self.request.user.organisation
        ).select_related('room', 'assigned_to', 'reservation')

    def perform_create(self, serializer):
        serializer.save(organisation=self.request.user.organisation)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = HousekeepingTask.Status.COMPLETED
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at', 'updated_at'])
        return Response(HousekeepingTaskSerializer(task).data)


class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ServiceRequestFilter
    search_fields = ['description', 'notes']
    ordering_fields = ['created_at', 'status']

    def get_queryset(self):
        return ServiceRequest.objects.filter(
            organisation=self.request.user.organisation
        ).select_related('reservation', 'assigned_to')

    def perform_create(self, serializer):
        serializer.save(organisation=self.request.user.organisation)

    @action(detail=True, methods=['post'])
    def fulfill(self, request, pk=None):
        req = self.get_object()
        req.status = ServiceRequest.Status.FULFILLED
        req.fulfilled_at = timezone.now()
        req.save(update_fields=['status', 'fulfilled_at', 'updated_at'])
        return Response(ServiceRequestSerializer(req).data)
