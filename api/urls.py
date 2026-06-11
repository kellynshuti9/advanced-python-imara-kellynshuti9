from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# JWT imports
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Imara Financial Services API",
        default_version='v1',
        description="Merchant financing MVP API with compliance retrofit",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Core API
    path('api/', include('api.urls')),

    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # Redirect default login to Swagger
    path('accounts/login/', RedirectView.as_view(url='/swagger/', permanent=False)),
]