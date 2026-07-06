import httpx
from app.utils.config import settings
from app.agents.cost_agent import quick_insight


async def send_alert(message: str) -> bool:
    """Send a plain text message to Slack."""
    if not settings.slack_webhook_url:
        print("[Slack] No webhook URL configured, skipping alert.")
        return False

    payload = {"text": message}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(settings.slack_webhook_url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"[Slack] Failed to send alert: {e}")
            return False


async def send_daily_digest():
    """Generate and send the daily cost digest to Slack."""
    try:
        insight = quick_insight(
            "Give me a concise daily cloud cost digest. Include: "
            "1) Yesterday's total spend, "
            "2) Top 3 services by cost, "
            "3) Any anomalies or concerns, "
            "4) One actionable recommendation. "
            "Keep it under 200 words. Format for Slack."
        )

        message = f"☁️ *CloudSense Daily Digest*\n\n{insight}"
        await send_alert(message)
        print("[Digest] Daily digest sent successfully.")
    except Exception as e:
        print(f"[Digest] Failed to generate digest: {e}")
        await send_alert(f"⚠️ CloudSense: Failed to generate daily digest. Error: {str(e)}")
