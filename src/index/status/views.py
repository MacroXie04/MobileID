"""
Views for the core project.
"""

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """
    Health check endpoint for monitoring and orchestration tools.

    Returns:
        JsonResponse: A JSON response with status and database connectivity
                      info.
    """
    response_data = {"status": "healthy", "service": "MobileID"}

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        response_data["database"] = "connected"
    except Exception:
        response_data["status"] = "unhealthy"
        response_data["database"] = "disconnected"
        response_data["error"] = "Database connection failed"
        return JsonResponse(response_data, status=503)

    return JsonResponse(response_data, status=200)
