from functools import wraps
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from app.observability.tracer import get_tracer


def traced(span_name: str = None, attributes: dict = None):
    """
    Decorator that wraps a function in an OpenTelemetry span.

    Usage:
        @traced("aws.cost_explorer.fetch")
        def get_cost_by_service(days: int = 30): ...

        @traced("ai.gemini.chat", attributes={"model": "gemini-1.5-flash"})
        def chat(messages): ...
    """
    def decorator(fn):
        name = span_name or f"{fn.__module__}.{fn.__qualname__}"

        @wraps(fn)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(name) as span:
                # Set provided static attributes
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, str(v))

                try:
                    result = fn(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper
    return decorator


def add_span_attributes(**kwargs):
    """Add attributes to the current active span."""
    span = trace.get_current_span()
    for k, v in kwargs.items():
        span.set_attribute(k, str(v))


def record_error(error: Exception, message: str = None):
    """Record an exception on the current span."""
    span = trace.get_current_span()
    span.record_exception(error)
    span.set_status(Status(StatusCode.ERROR, message or str(error)))
