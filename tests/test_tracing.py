# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest import TestCase
from unittest.mock import patch

import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.datastructures import Address
from structlog import get_logger
from structlog.testing import CapturedCall, CapturingLoggerFactory

from os2mo_fastapi_utils.tracing import setup_instrumentation, setup_logging


def create_app():
    app = FastAPI()

    def other_function():
        logger = get_logger()
        logger.info("other_function called", r2="d2")

    @app.get("/")
    async def root():
        other_function()
        return {"message": "Hello World"}

    app = setup_instrumentation(app)

    return app


class TracingTests(TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_app(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload, {"message": "Hello World"})

    def test_response_headers(self):
        response = self.client.get("/")
        trace_id = response.headers["X-Trace-ID"]
        span_id = response.headers["X-Span-ID"]
        # Check that we got two hex values back
        self.assertIn("0x", trace_id)
        self.assertIn("0x", span_id)
        int(trace_id, 16)
        int(span_id, 16)

    def test_logs(self):
        cf = CapturingLoggerFactory()
        setup_logging(logger_factory=cf)

        response = self.client.get("/")
        self.assertEqual(len(cf.logger.calls), 3)

        logmsg = cf.logger.calls[0].kwargs
        self.assertEqual(logmsg["event"], "Request received")
        self.assertIn("0x", logmsg["trace_id"])
        self.assertIn("0x", logmsg["span_id"])
        trace_id = logmsg["trace_id"]
        span_id = logmsg["span_id"]
        self.assertEqual(logmsg["method"], "GET")
        self.assertEqual(logmsg["url"], "/")

        logmsg = cf.logger.calls[1].kwargs
        self.assertEqual(logmsg["event"], "other_function called")
        self.assertEqual(logmsg["trace_id"], trace_id)
        self.assertEqual(logmsg["span_id"], span_id)
        self.assertEqual(logmsg["r2"], "d2")

        logmsg = cf.logger.calls[2].kwargs
        self.assertEqual(logmsg["event"], "Request processed")
        self.assertEqual(logmsg["trace_id"], trace_id)
        self.assertEqual(logmsg["span_id"], span_id)

    def test_x_request_id(self):
        request_id = "Alfa Beta Mogens"

        # Request without x-request-id header
        cf = CapturingLoggerFactory()
        setup_logging(logger_factory=cf)

        response = self.client.get("/")
        self.assertGreaterEqual(len(cf.logger.calls), 1)

        logmsg = cf.logger.calls[0].kwargs
        self.assertNotIn("request_id", logmsg)

        # Request with x-request-id header
        cf = CapturingLoggerFactory()
        setup_logging(logger_factory=cf)

        response = self.client.get("/", headers={"X-Request-ID": request_id})
        self.assertGreaterEqual(len(cf.logger.calls), 1)

        logmsg = cf.logger.calls[0].kwargs
        self.assertIn("request_id", logmsg)
        self.assertEqual(logmsg["request_id"], request_id)

        # Request with x-request-id header
        cf = CapturingLoggerFactory()
        setup_logging(logger_factory=cf)

        response = self.client.get("/", headers={"x-rEqUeSt-Id": request_id})
        self.assertGreaterEqual(len(cf.logger.calls), 1)

        logmsg = cf.logger.calls[0].kwargs
        self.assertIn("request_id", logmsg)
        self.assertEqual(logmsg["request_id"], request_id)
