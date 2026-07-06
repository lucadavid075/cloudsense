from fastapi import APIRouter, Query
from app.services.aws_cost import (
    get_cost_by_service,
    get_total_cost_by_day,
    get_cost_forecast,
    detect_anomalies,
)

router = APIRouter()


@router.get("/daily")
async def daily_costs(days: int = Query(default=30, ge=1, le=365)):
    """Total cost per day for the last N days."""
    data = get_total_cost_by_day(days=days)
    total = sum(d["amount"] for d in data)
    return {
        "data": data,
        "total": round(total, 2),
        "days": days,
    }


@router.get("/by-service")
async def costs_by_service(days: int = Query(default=30, ge=1, le=365)):
    """Cost breakdown by AWS service."""
    data = get_cost_by_service(days=days)

    # Aggregate totals per service
    service_totals: dict[str, float] = {}
    for row in data:
        service_totals[row["service"]] = service_totals.get(row["service"], 0) + row["amount"]

    ranked = sorted(
        [{"service": k, "total": round(v, 2)} for k, v in service_totals.items()],
        key=lambda x: x["total"],
        reverse=True,
    )

    return {
        "raw": data,
        "by_service": ranked,
        "days": days,
    }


@router.get("/forecast")
async def cost_forecast(days_ahead: int = Query(default=30, ge=7, le=90)):
    """Forecast spend for the next N days."""
    return get_cost_forecast(days_ahead=days_ahead)


@router.get("/anomalies")
async def cost_anomalies(
    days: int = Query(default=30, ge=7, le=365),
    threshold: float = Query(default=1.5, ge=1.1, le=5.0),
):
    """Detect days with unusually high spend."""
    anomalies = detect_anomalies(days=days, threshold_multiplier=threshold)
    return {
        "anomalies": anomalies,
        "count": len(anomalies),
        "days_analyzed": days,
        "threshold_multiplier": threshold,
    }
