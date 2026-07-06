import pytest
from unittest.mock import patch, MagicMock
from app.services.aws_cost import detect_anomalies, get_cost_summary_for_agent


# ── Cost anomaly detection ──────────────────────────────────────────────────

def make_daily_data(amounts: list[float]) -> list[dict]:
    from datetime import date, timedelta
    base = date(2024, 1, 1)
    return [{"date": (base + timedelta(days=i)).isoformat(), "amount": a} for i, a in enumerate(amounts)]


@patch("app.services.aws_cost.get_total_cost_by_day")
def test_no_anomalies_when_spend_is_flat(mock_daily):
    mock_daily.return_value = make_daily_data([10.0] * 14)
    anomalies = detect_anomalies(days=14)
    assert anomalies == []


@patch("app.services.aws_cost.get_total_cost_by_day")
def test_detects_spike(mock_daily):
    amounts = [10.0] * 13 + [50.0]  # last day is 5x the average
    mock_daily.return_value = make_daily_data(amounts)
    anomalies = detect_anomalies(days=14, threshold_multiplier=1.5)
    assert len(anomalies) == 1
    assert anomalies[0]["amount"] == 50.0


@patch("app.services.aws_cost.get_total_cost_by_day")
def test_empty_data_returns_no_anomalies(mock_daily):
    mock_daily.return_value = []
    anomalies = detect_anomalies(days=14)
    assert anomalies == []


# ── Cost summary for agent ──────────────────────────────────────────────────

@patch("app.services.aws_cost.get_total_cost_by_day")
@patch("app.services.aws_cost.get_cost_by_service")
def test_cost_summary_contains_key_fields(mock_by_service, mock_daily):
    mock_daily.return_value = make_daily_data([5.0, 10.0, 7.5])
    mock_by_service.return_value = [
        {"date": "2024-01-01", "service": "Amazon EC2", "amount": 10.0, "currency": "USD"},
        {"date": "2024-01-02", "service": "Amazon S3", "amount": 2.5, "currency": "USD"},
    ]
    summary = get_cost_summary_for_agent(days=3)
    assert "Amazon EC2" in summary
    assert "Total spend" in summary
    assert "Daily average" in summary
