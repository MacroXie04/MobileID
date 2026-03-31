"""
Views for the core project.
"""

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """
    Health check endpoint for monitoring and orchestration tools.

    Checks database connectivity and cache round-trip.
    Returns 503 only for database failure (critical).
    Non-critical failures (cache) are reported as warnings
    with a 200 status.
    """
    response_data = {"status": "healthy", "service": "MobileID"}
    warnings = []

    # Check database connectivity (critical)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        response_data["database"] = "connected"
    except Exception as e:
        response_data["status"] = "unhealthy"
        response_data["database"] = "disconnected"
        response_data["error"] = str(e)
        return JsonResponse(response_data, status=503)

    # Check cache round-trip (non-critical)
    try:
        cache.set("_health_check", "ok", timeout=5)
        value = cache.get("_health_check")
        if value == "ok":
            response_data["cache"] = "connected"
        else:
            response_data["cache"] = "degraded"
            warnings.append("Cache read-back mismatch")
    except Exception:
        response_data["cache"] = "unavailable"
        warnings.append("Cache connection failed")

    if warnings:
        response_data["status"] = "degraded"
        response_data["warnings"] = warnings

    return JsonResponse(response_data, status=200)
