import google.generativeai as genai
from app.utils.config import settings
from app.services.aws_cost import get_cost_summary_for_agent, get_cost_forecast
from app.services.aws_resources import get_resource_summary_for_agent
from app.observability.decorators import traced, add_span_attributes

genai.configure(api_key=settings.gemini_api_key)

SYSTEM_PROMPT = """You are CloudSense, an expert FinOps (cloud financial operations) AI assistant.
You help engineers and platform teams understand, analyze, and optimize their AWS cloud spending.

You have access to real-time AWS cost data and resource scan results that will be provided to you in each message.

Your capabilities:
- Explain cost spikes and anomalies in plain English
- Identify wasteful or idle resources
- Provide actionable optimization recommendations
- Forecast spending trends
- Help prioritize cost-saving opportunities

Tone: Be direct, technical, and specific. Give concrete dollar amounts and percentages.
Don't hedge excessively — engineers want clear recommendations.
When you see anomalies, always suggest what to investigate next.

Format your responses with clear sections when helpful. Use bullet points for lists of resources or recommendations.
Always include estimated savings when recommending actions."""


@traced("agent.build_context")
def build_context() -> str:
    """Pull live AWS data to inject into agent context."""
    try:
        cost_summary = get_cost_summary_for_agent(days=14)
    except Exception as e:
        cost_summary = f"Cost data unavailable: {str(e)}"

    try:
        resource_summary = get_resource_summary_for_agent()
    except Exception as e:
        resource_summary = f"Resource scan unavailable: {str(e)}"

    try:
        forecast = get_cost_forecast(days_ahead=30)
        forecast_text = f"Forecast for next 30 days: ${forecast.get('mean_value', 'N/A')} {forecast.get('currency', 'USD')}"
    except Exception as e:
        forecast_text = f"Forecast unavailable: {str(e)}"

    return f"""
=== LIVE AWS DATA (as of now) ===

{cost_summary}

{resource_summary}

{forecast_text}

=== END AWS DATA ===
"""


@traced("agent.gemini.chat", attributes={"model": "gemini-1.5-flash"})
def chat(messages: list[dict], use_live_data: bool = True) -> str:
    """
    Send a conversation to Gemini with live AWS context injected.
    messages: list of {"role": "user"|"assistant", "content": "..."}
    """
    add_span_attributes(
        message_count=len(messages),
        use_live_data=use_live_data,
    )

    system = SYSTEM_PROMPT
    if use_live_data:
        system += f"\n\n{build_context()}"

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system,
    )

    history = []
    for msg in messages[:-1]:
        history.append({
            "role": "model" if msg["role"] == "assistant" else "user",
            "parts": [msg["content"]],
        })

    gemini_chat = model.start_chat(history=history)
    last_user_msg = messages[-1]["content"]
    response = gemini_chat.send_message(last_user_msg)

    add_span_attributes(response_length=len(response.text))
    return response.text


@traced("agent.gemini.quick_insight", attributes={"model": "gemini-1.5-flash"})
def quick_insight(prompt: str) -> str:
    """Single-shot query with live context — for alerts and digests."""
    return chat([{"role": "user", "content": prompt}])
