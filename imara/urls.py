from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Import health check views
from api.health_views import health_check, readiness_check, liveness_check

schema_view = get_schema_view(
    openapi.Info(
        title="Imara Financial Services API",
        default_version='v1',
        description="Imara Financial Services API with JWT Auth, RBAC, and Audit Logs",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API
    path('api/', include('api.urls')),
    
    # Swagger Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', RedirectView.as_view(url='/swagger/', permanent=False)),
    
    # Health Checks (Summative)
    path('health/', health_check, name='health'),
    path('ready/', readiness_check, name='readiness'),
    path('live/', liveness_check, name='liveness'),
]