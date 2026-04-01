"""
Views for the core project.
"""

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


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

    from django.conf import settings as django_settings

    persistence_mode = getattr(django_settings, "PERSISTENCE_MODE", "hybrid")
    response_data["persistence_mode"] = persistence_mode

    if persistence_mode == "dynamodb":
        response_data["database"] = "disabled"
        try:
            table_statuses = _describe_required_tables()
            response_data["dynamodb"] = "connected"
            response_data["dynamodb_tables"] = table_statuses
        except Exception:
            response_data["status"] = "unhealthy"
            response_data["dynamodb"] = "disconnected"
            response_data["error"] = "DynamoDB table validation failed"
            return JsonResponse(response_data, status=503)
    else:
        from django.db import connection

        # Check database connectivity (critical)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            response_data["database"] = "connected"
        except Exception:
            response_data["status"] = "unhealthy"
            response_data["database"] = "disconnected"
            response_data["error"] = "Database connection failed"
            return JsonResponse(response_data, status=503)

        # Check DynamoDB connectivity (non-critical)
        try:
            table_statuses = _describe_required_tables()
            response_data["dynamodb"] = "connected"
            response_data["dynamodb_tables"] = table_statuses
        except Exception:
            response_data["dynamodb"] = "disconnected"
            warnings.append("DynamoDB connection failed")

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
