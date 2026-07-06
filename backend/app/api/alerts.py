from fastapi import APIRouter
from app.services.slack import send_daily_digest, send_alert

router = APIRouter()


@router.post("/digest/trigger")
async def trigger_digest():
    """Manually trigger the daily cost digest."""
    await send_daily_digest()
    return {"status": "digest sent"}


@router.post("/test")
async def test_alert():
    """Send a test alert to Slack."""
    await send_alert("🧪 CloudSense test alert — your Slack integration is working!")
    return {"status": "test alert sent"}
