"""
Views for the core project.
"""

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


def _check_sql_database():
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")


def _describe_required_tables():
    from django.conf import settings as django_settings

    from core.dynamodb.client import get_client

    client = get_client()
    required = getattr(django_settings, "DYNAMODB_REQUIRED_TABLE_KEYS", ())
    statuses = {}

    for key in required:
        table_name = django_settings.DYNAMODB_TABLES[key]
        description = client.describe_table(TableName=table_name)
        statuses[table_name] = description["Table"]["TableStatus"]

    return statuses


def _build_dependency_status():
    from django.conf import settings as django_settings

    response_data = {"status": "healthy", "service": "MobileID"}
    persistence_mode = getattr(django_settings, "PERSISTENCE_MODE", "hybrid")
    response_data["persistence_mode"] = persistence_mode

    if persistence_mode == "dynamodb":
        response_data["database"] = "disabled"
    else:
        try:
            _check_sql_database()
            response_data["database"] = "connected"
        except Exception:
            response_data["status"] = "unhealthy"
            response_data["database"] = "disconnected"
            response_data["error"] = "Database connection failed"
            return response_data, 503

    try:
        table_statuses = _describe_required_tables()
        response_data["dynamodb"] = "connected"
        response_data["dynamodb_tables"] = table_statuses
    except Exception:
        response_data["status"] = "unhealthy"
        response_data["dynamodb"] = "disconnected"
        response_data["error"] = "DynamoDB table validation failed"
        return response_data, 503

    try:
        cache.set("_health_check", "ok", timeout=5)
        value = cache.get("_health_check")
        if value == "ok":
            response_data["cache"] = "connected"
        else:
            response_data["status"] = "unhealthy"
            response_data["cache"] = "degraded"
            response_data["error"] = "Cache read-back mismatch"
            return response_data, 503
    except Exception:
        response_data["status"] = "unhealthy"
        response_data["cache"] = "unavailable"
        response_data["error"] = "Cache connection failed"
        return response_data, 503

    return response_data, 200


@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """
    Health check endpoint for monitoring and orchestration tools.

    Checks request-serving dependencies and returns 503 when any required
    dependency is unavailable.
    """
    response_data, status_code = _build_dependency_status()
    return JsonResponse(response_data, status=status_code)


@require_http_methods(["GET", "HEAD"])
def readiness_check(request):
    """Readiness probe: all request-serving dependencies must be available."""
    response_data, status_code = _build_dependency_status()
    response_data["probe"] = "readiness"
    return JsonResponse(response_data, status=status_code)


@require_http_methods(["GET", "HEAD"])
def liveness_check(request):
    """Liveness probe: process is up without dependency checks."""
    return JsonResponse(
        {"status": "alive", "service": "MobileID", "probe": "liveness"},
        status=200,
    )
