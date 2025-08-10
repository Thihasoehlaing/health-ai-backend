# app/db/mongo.py
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from app.config import settings

_client: Optional[AsyncIOMotorClient] = None

def get_mongo() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("Mongo client not initialized. Call connect_mongo() on startup.")
    return _client[settings.MONGO_DATABASE]

async def connect_mongo() -> None:
    """Create client and verify connectivity with a ping."""
    global _client
    _client = AsyncIOMotorClient(
        settings.mongo_url,
        serverSelectionTimeoutMS=3000,  # fail fast if unreachable
    )
    # Verify connection
    await _client.admin.command("ping")

async def close_mongo() -> None:
    global _client
    if _client:
        _client.close()
        _client = None

async def ensure_mongo_indexes() -> None:
    """Idempotent index creation for chat collections."""
    db = get_mongo()
    # Sessions: by device & recency, and status
    await db.chat_sessions.create_index([("deviceId", ASCENDING), ("startedAt", DESCENDING)])
    await db.chat_sessions.create_index([("status", ASCENDING)])
    # Messages: by session & time
    await db.messages.create_index([("sessionId", ASCENDING), ("timestamp", DESCENDING)])
    # Optional TTL on messages (e.g., 30 days). Uncomment if desired.
    # await db.messages.create_index([("timestamp", ASCENDING)], expireAfterSeconds=30*24*60*60)
