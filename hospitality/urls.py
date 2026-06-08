from rest_framework.routers import DefaultRouter
from .views import (
    RoomTypeViewSet, RoomViewSet, GuestViewSet,
    ReservationViewSet, HousekeepingTaskViewSet, ServiceRequestViewSet,
)

router = DefaultRouter()
router.register('room-types', RoomTypeViewSet, basename='room-type')
router.register('rooms', RoomViewSet, basename='room')
router.register('guests', GuestViewSet, basename='guest')
router.register('reservations', ReservationViewSet, basename='reservation')
router.register('housekeeping', HousekeepingTaskViewSet, basename='housekeeping')
router.register('service-requests', ServiceRequestViewSet, basename='service-request')

urlpatterns = router.urls
