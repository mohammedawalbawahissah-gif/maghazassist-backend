from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationTemplateViewSet

router = DefaultRouter()
router.register('', NotificationViewSet, basename='notification')
router.register('templates', NotificationTemplateViewSet, basename='notification-template')
urlpatterns = router.urls
