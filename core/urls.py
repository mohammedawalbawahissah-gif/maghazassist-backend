from rest_framework.routers import DefaultRouter
from .views import OrganisationViewSet, BusinessUnitViewSet, DepartmentViewSet, UserViewSet

router = DefaultRouter()
router.register('organisations', OrganisationViewSet, basename='organisation')
router.register('business-units', BusinessUnitViewSet, basename='business-unit')
router.register('departments', DepartmentViewSet, basename='department')
router.register('users', UserViewSet, basename='user')

urlpatterns = router.urls
