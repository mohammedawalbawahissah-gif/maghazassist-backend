from django.contrib import admin
from .models import RoomType, Room, Guest, Reservation, ReservationPayment, HousekeepingTask, ServiceRequest


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price', 'max_occupancy', 'organisation']
    search_fields = ['name']
    list_filter = ['organisation']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'floor', 'status', 'price', 'organisation']
    list_filter = ['status', 'floor', 'room_type', 'organisation']
    search_fields = ['room_number']


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'email', 'phone', 'nationality', 'organisation']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    list_filter = ['nationality', 'organisation']


class ReservationPaymentInline(admin.TabularInline):
    model = ReservationPayment
    extra = 0


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['reservation_number', 'guest', 'room', 'check_in_date', 'check_out_date', 'status', 'payment_status']
    list_filter = ['status', 'payment_status', 'source', 'organisation']
    search_fields = ['reservation_number', 'guest__first_name', 'guest__last_name']
    inlines = [ReservationPaymentInline]
    readonly_fields = ['reservation_number', 'total_amount']


@admin.register(HousekeepingTask)
class HousekeepingTaskAdmin(admin.ModelAdmin):
    list_display = ['room', 'task_type', 'priority', 'status', 'scheduled_date', 'assigned_to']
    list_filter = ['status', 'priority', 'task_type']
    search_fields = ['room__room_number']


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'category', 'status', 'assigned_to', 'created_at']
    list_filter = ['status', 'category']
