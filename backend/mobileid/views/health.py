from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.core.cache import cache
import json


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for Docker containers and monitoring.

    Returns:
        - 200 OK: Application is healthy
        - 503 Service Unavailable: Application is unhealthy

    Checks:
        - Database connectivity
        - Cache connectivity (if Redis is configured)
        - Basic application status
    """
    health_status = {
        "status": "healthy",
        "checks": {"database": "healthy", "cache": "healthy", "application": "healthy"},
    }

    overall_status = "healthy"
    status_code = 200

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        health_status["checks"]["database"] = "unhealthy"
        health_status["checks"]["database_error"] = str(e)
        overall_status = "unhealthy"
        status_code = 503

    # Check cache connectivity (Redis)
    try:
        cache.set("health_check", "ok", 10)
        cache_value = cache.get("health_check")
        if cache_value != "ok":
            raise Exception("Cache read/write test failed")
    except Exception as e:
        health_status["checks"]["cache"] = "unhealthy"
        health_status["checks"]["cache_error"] = str(e)
        # Cache failure doesn't make the entire app unhealthy, just log it
        # overall_status = "unhealthy"
        # status_code = 503

    # Update overall status
    health_status["status"] = overall_status

    return JsonResponse(health_status, status=status_code)
