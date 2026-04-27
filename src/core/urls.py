"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.schemas import get_schema_view

from core.health.views import health_check, liveness_check, readiness_check

schema_view = get_schema_view(
    title="MobileID API",
    description="Mobile identification, barcode, profile, and authentication API.",
    version="1.0.0",
    public=True,
    renderer_classes=[JSONOpenAPIRenderer],
    permission_classes=[AllowAny],
)

urlpatterns = [
    path(f"{settings.ADMIN_URL_PATH}/", admin.site.urls),
    # Health check endpoint
    path("health/", health_check, name="health_check"),
    path("readyz/", readiness_check, name="readiness_check"),
    path("livez/", liveness_check, name="liveness_check"),
    path("openapi.json", schema_view, name="openapi_schema"),
    # path for index app
    path("", include("index.urls")),
    # path for auth app
    path("authn/", include("authn.urls")),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
