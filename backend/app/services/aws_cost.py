import boto3
from datetime import datetime, timedelta
from app.utils.config import settings
from app.observability.decorators import traced, add_span_attributes


def get_cost_client():
    return boto3.client(
        "ce",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name="us-east-1",
    )


@traced("aws.cost_explorer.daily_costs")
def get_cost_by_service(days: int = 30) -> list[dict]:
    """Get cost breakdown by AWS service for the last N days."""
    add_span_attributes(days=days)
    client = get_cost_client()
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)

    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    results = []
    for day in response["ResultsByTime"]:
        date = day["TimePeriod"]["Start"]
        for group in day["Groups"]:
            service = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amount > 0:
                results.append({
                    "date": date,
                    "service": service,
                    "amount": round(amount, 4),
                    "currency": group["Metrics"]["UnblendedCost"]["Unit"],
                })

    add_span_attributes(result_count=len(results))
    return results


@traced("aws.cost_explorer.total_by_day")
def get_total_cost_by_day(days: int = 30) -> list[dict]:
    """Get total daily spend for the last N days."""
    add_span_attributes(days=days)
    client = get_cost_client()
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)

    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )

    return [
        {
            "date": day["TimePeriod"]["Start"],
            "amount": round(float(day["Total"]["UnblendedCost"]["Amount"]), 4),
        }
        for day in response["ResultsByTime"]
    ]


@traced("aws.cost_explorer.forecast")
def get_cost_forecast(days_ahead: int = 30) -> dict:
    """Forecast spend for the next N days."""
    add_span_attributes(days_ahead=days_ahead)
    client = get_cost_client()
    start = datetime.utcnow().date()
    end = start + timedelta(days=days_ahead)

    try:
        response = client.get_cost_forecast(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Metric="UNBLENDED_COST",
            Granularity="MONTHLY",
        )
        return {
            "mean_value": round(float(response["Total"]["Amount"]), 2),
            "currency": response["Total"]["Unit"],
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "mean_value": 0}


@traced("aws.cost_explorer.summary_for_agent")
def get_cost_summary_for_agent(days: int = 14) -> str:
    """Return a plain-text cost summary for the AI agent to reason over."""
    daily = get_total_cost_by_day(days)
    by_service = get_cost_by_service(days)

    service_totals: dict[str, float] = {}
    for row in by_service:
        service_totals[row["service"]] = service_totals.get(row["service"], 0) + row["amount"]

    top_services = sorted(service_totals.items(), key=lambda x: x[1], reverse=True)[:10]

    if daily:
        avg = sum(d["amount"] for d in daily) / len(daily)
        anomalies = [d for d in daily if d["amount"] > avg * 1.5]
    else:
        avg = 0
        anomalies = []

    lines = [
        f"AWS Cost Summary — Last {days} days",
        f"Total spend: ${sum(d['amount'] for d in daily):.2f}",
        f"Daily average: ${avg:.2f}",
        "",
        "Top services by cost:",
    ]
    for svc, total in top_services:
        lines.append(f"  - {svc}: ${total:.2f}")

    if anomalies:
        lines.append("")
        lines.append("Anomaly days (>50% above average):")
        for a in anomalies:
            lines.append(f"  - {a['date']}: ${a['amount']:.2f}")

    add_span_attributes(anomaly_count=len(anomalies), service_count=len(top_services))
    return "\n".join(lines)


@traced("aws.cost_explorer.detect_anomalies")
def detect_anomalies(days: int = 30, threshold_multiplier: float = 1.5) -> list[dict]:
    """Detect days where spend was unusually high."""
    add_span_attributes(days=days, threshold=threshold_multiplier)
    daily = get_total_cost_by_day(days)
    if not daily:
        return []

    avg = sum(d["amount"] for d in daily) / len(daily)
    anomalies = [
        {**d, "average": round(avg, 4), "multiplier": round(d["amount"] / avg, 2)}
        for d in daily
        if d["amount"] > avg * threshold_multiplier
    ]
    add_span_attributes(anomaly_count=len(anomalies))
    return anomalies
