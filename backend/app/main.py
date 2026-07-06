from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.api import costs, chat, resources, alerts
from app.models.database import create_tables, engine
from app.services.slack import send_daily_digest
from app.utils.config import settings
from app.observability import init_tracer

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()

    # Initialise OpenTelemetry — auto-instruments FastAPI + SQLAlchemy + httpx
    if settings.tracing_enabled:
        init_tracer(app=app, db_engine=engine)

    # Schedule daily digest at 8am UTC
    scheduler.add_job(
        send_daily_digest,
        "cron",
        hour=8,
        minute=0,
        id="daily_digest",
    )
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="CloudSense API",
    description="AI-powered AWS cost intelligence agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(costs.router, prefix="/api/costs", tags=["costs"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(resources.router, prefix="/api/resources", tags=["resources"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "cloudsense"}
