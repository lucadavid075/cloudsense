from unittest.mock import patch, MagicMock
from app.observability.decorators import traced, add_span_attributes, record_error


def test_traced_decorator_runs_function():
    """@traced should not change return value of wrapped function."""
    @traced("test.span")
    def add(a, b):
        return a + b

    assert add(2, 3) == 5


def test_traced_decorator_propagates_exception():
    """@traced should re-raise exceptions after recording them."""
    @traced("test.error_span")
    def boom():
        raise ValueError("intentional error")

    try:
        boom()
        assert False, "should have raised"
    except ValueError as e:
        assert "intentional error" in str(e)


def test_traced_with_static_attributes():
    """@traced should accept static attributes without error."""
    @traced("test.attributed", attributes={"model": "gemini", "env": "test"})
    def noop():
        return "ok"

    assert noop() == "ok"


def test_add_span_attributes_does_not_raise():
    """add_span_attributes should be safe to call even with no active span."""
    # No active span in test context — should not raise
    add_span_attributes(service="ec2", region="us-east-1")


def test_record_error_does_not_raise():
    """record_error should be safe to call even with no active span."""
    record_error(ValueError("test error"), message="something went wrong")
