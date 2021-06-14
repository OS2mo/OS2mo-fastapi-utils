# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

from contextlib import contextmanager
from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseSettings, HttpUrl
from pydantic.tools import parse_obj_as
from structlog import get_logger
from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    merge_contextvars,
    unbind_contextvars,
)

from os2mo_fastapi_utils.pydantic_types import Domain, Port


class TracingSettings(BaseSettings):
    jaeger_service: str = "OS2mo_fastapi_utils"
    jaeger_hostname: Optional[Domain] = None
    jaeger_port: Port = Port(6831)


def _get_settings(**overrides) -> TracingSettings:
    return TracingSettings(**overrides)


def setup_instrumentation(app):
    settings: TracingSettings = _get_settings()

    _TRACE_PROVIDER = TracerProvider(
        resource=Resource.create({"service.name": settings.jaeger_service})
    )
    trace.set_tracer_provider(_TRACE_PROVIDER)

    if settings.jaeger_hostname:  # pragma: no cover
        _JAEGER_EXPORTER = JaegerExporter(
            agent_host_name=settings.jaeger_hostname,
            agent_port=settings.jaeger_port,
        )

        _TRACE_PROVIDER.add_span_processor(BatchSpanProcessor(_JAEGER_EXPORTER))

    AioHttpClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()

    # Register logging middleware
    app.middleware("http")(_log_requests_middleware)
    app.middleware("http")(_bind_logger_tracecontext_middleware)

    FastAPIInstrumentor.instrument_app(app)
    return app


@contextmanager
def _bind_context(**kwargs):
    """Context manager to bind logging contextvars."""
    # Filter None values before binding vars
    filtered_kwargs = {
        key: value for (key, value) in kwargs.items() if value is not None
    }

    bind_contextvars(**filtered_kwargs)
    yield
    unbind_contextvars(*filtered_kwargs.keys())


async def _bind_logger_tracecontext_middleware(request: Request, call_next) -> Response:
    """Bind request and tracing variables to logging."""
    # X-Request-ID can be used to assign a user-defined value to all log messages
    # and to the tracing span context.
    request_id = request.headers.get("x-request-id")
    current_span = trace.get_current_span()
    if request_id is not None:
        current_span.set_attribute("request_id", request_id)

    # The Trace-ID and Span-ID from the spancontext will be bound to log messages
    spancontext = current_span.get_span_context()
    trace_id = hex(spancontext.trace_id)
    span_id = hex(spancontext.span_id)

    clear_contextvars()
    with _bind_context(trace_id=trace_id):
        with _bind_context(span_id=span_id):
            with _bind_context(request_id=request_id):
                response = await call_next(request)

    # Set response headers with tracing information
    if request_id is not None:
        response.headers["X-Request-ID"] = request_id
    response.headers["X-Trace-ID"] = trace_id
    response.headers["X-Span-ID"] = span_id

    return response


async def _log_requests_middleware(request: Request, call_next):
    """Log that a request has been received and processed."""
    logger = get_logger()
    logger.debug(
        "Request received",
        method=request.method,
        url=request.url.path,
    )

    response = await call_next(request)

    logger.debug("Request processed")
    return response


def setup_logging(**kwargs):
    """Wrapper around structlog.configure, to add merge_contextvar.

    NOTE: When using this you must yourself register a key-value processor.
    """
    processors = kwargs.get("processors", [])
    if merge_contextvars not in processors:
        # We prepend, as merge_contextvars must come before the key-value processor.
        processors.insert(0, merge_contextvars)
    kwargs["processors"] = processors

    structlog.configure(**kwargs)
