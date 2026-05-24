from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Imara Financial Services API",
      default_version='v1',
      description="Merchant financing MVP API",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # Add this to redirect accounts/login back to swagger
    path('accounts/login/', RedirectView.as_view(url='/swagger/', permanent=False)),
]