from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from app.utils.config import settings

SERVICE_NAME = "cloudsense"


def init_tracer(app=None, db_engine=None):
    """
    Initialise OpenTelemetry tracing.
    Instrumentation packages are imported lazily here to avoid
    pkg_resources issues at module import time.
    """
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": "1.0.0",
        "deployment.environment": settings.environment,
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Lazy imports — only loaded when tracing is actually initialised
    if app:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)

    if db_engine:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        SQLAlchemyInstrumentor().instrument(engine=db_engine)

    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    HTTPXClientInstrumentor().instrument()

    return trace.get_tracer(SERVICE_NAME)


def get_tracer() -> trace.Tracer:
    return trace.get_tracer(SERVICE_NAME)
