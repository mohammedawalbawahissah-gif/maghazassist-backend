"""
MAGHAZ Assist — Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

API_V1 = 'api/v1/'

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path(API_V1 + 'auth/', include('authentication.urls')),

    # Core
    path(API_V1 + 'core/', include('core.urls')),

    # Operational modules
    path(API_V1 + 'hospitality/', include('hospitality.urls')),
    path(API_V1 + 'real-estate/', include('real_estate.urls')),
    path(API_V1 + 'construction/', include('construction.urls')),
    path(API_V1 + 'hr/', include('hr.urls')),
    path(API_V1 + 'finance/', include('finance.urls')),
    path(API_V1 + 'maintenance/', include('maintenance.urls')),
    path(API_V1 + 'transport/', include('transport.urls')),

    # Platform services
    path(API_V1 + 'notifications/', include('notifications.urls')),
    path(API_V1 + 'documents/', include('documents.urls')),
    path(API_V1 + 'audit/', include('audit.urls')),
    path(API_V1 + 'reporting/', include('reporting.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
