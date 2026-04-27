import logging

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from core.logging import RequestIdFilter
from core.middleware.request_id import RequestIdMiddleware


class RequestIdMiddlewareTests(SimpleTestCase):
    def test_generates_request_id_header_when_missing(self):
        request = RequestFactory().get("/health/")
        middleware = RequestIdMiddleware(lambda req: HttpResponse("ok"))

        response = middleware(request)

        self.assertTrue(request.request_id)
        self.assertEqual(response["X-Request-ID"], request.request_id)

    def test_propagates_valid_request_id_header(self):
        request = RequestFactory().get("/health/", HTTP_X_REQUEST_ID="req-123")
        middleware = RequestIdMiddleware(lambda req: HttpResponse("ok"))

        response = middleware(request)

        self.assertEqual(request.request_id, "req-123")
        self.assertEqual(response["X-Request-ID"], "req-123")


class RequestIdFilterTests(SimpleTestCase):
    def test_filter_adds_request_id_attribute(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )

        self.assertTrue(RequestIdFilter().filter(record))
        self.assertTrue(hasattr(record, "request_id"))
