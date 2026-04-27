import uuid

from core.logging import request_id_context

REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
RESPONSE_REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128


def _clean_request_id(value):
    if not value:
        return uuid.uuid4().hex
    value = str(value).strip()
    if not value or len(value) > MAX_REQUEST_ID_LENGTH:
        return uuid.uuid4().hex
    return value


class RequestIdMiddleware:
    """Propagate or create a request id for logs and responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = _clean_request_id(request.META.get(REQUEST_ID_HEADER))
        token = request_id_context.set(request_id)
        request.request_id = request_id
        try:
            response = self.get_response(request)
        finally:
            request_id_context.reset(token)
        response[RESPONSE_REQUEST_ID_HEADER] = request_id
        return response
