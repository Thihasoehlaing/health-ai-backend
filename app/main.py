from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from sqlalchemy import text
from app.config import settings
from app.db.pg import engine
from app.db.mongo import connect_mongo, close_mongo, ensure_mongo_indexes, get_mongo

from app.routers import info, appointments, chat
from app.routers.admin import (
    auth as admin_auth,
    doctors as admin_doctors,
    departments as admin_departments,
    faqs as admin_faqs,
    reports as admin_reports,
)

app = FastAPI(title="AI Kiosk API")

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins() or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)
# Tighten in prod: put your kiosk/admin hostnames/IPs here
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*.your-hospital.local"])

# Routers
app.include_router(info.router, prefix=settings.API_PREFIX)
app.include_router(appointments.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)

app.include_router(admin_auth.router, prefix=settings.API_PREFIX)
app.include_router(admin_doctors.router, prefix=settings.API_PREFIX)
app.include_router(admin_departments.router, prefix=settings.API_PREFIX)
app.include_router(admin_faqs.router, prefix=settings.API_PREFIX)
app.include_router(admin_reports.router, prefix=settings.API_PREFIX)

@app.on_event("startup")
async def on_start():
    await connect_mongo()
    await ensure_mongo_indexes()

@app.on_event("shutdown")
async def on_stop():
    await close_mongo()

@app.get("/healthz")
def health():
    # Liveness: app is up
    return {"ok": True}

@app.get("/readyz")
async def ready():
    # Readiness: verify PG + Mongo connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db = get_mongo()
        await db.command("ping")
        return {"ready": True}
    except Exception as e:
        return {"ready": False, "error": str(e)}
