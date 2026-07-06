from fastapi import APIRouter, Query
from app.services.aws_resources import run_full_resource_scan

router = APIRouter()


@router.get("/idle")
async def idle_resources(region: str = Query(default=None)):
    """Scan for idle/wasted AWS resources."""
    return run_full_resource_scan(region=region)


@router.get("/idle/summary")
async def idle_summary(region: str = Query(default=None)):
    """Quick summary of idle resource waste."""
    result = run_full_resource_scan(region=region)
    return result["summary"]
