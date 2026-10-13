import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from app.core.config import settings

client: AsyncIOMotorClient = None


def get_db_name() -> str:
    if os.getenv("BENCHMARK_MODE") == "1":
        return "ai_characters_test"
    return settings.MONGODB_DB_NAME


async def connect_db():
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db_name = get_db_name()
    db = client[db_name]

    # Create indexes for scalable querying (10M+ characters)
    await db.characters.create_index([("name", ASCENDING)])
    await db.characters.create_index([("category", ASCENDING)])
    await db.characters.create_index([("occupation", ASCENDING)])
    await db.characters.create_index([("nationality", ASCENDING)])
    await db.characters.create_index([("created_at", ASCENDING)])
    # Compound index for filtered gallery queries
    await db.characters.create_index([
        ("category", ASCENDING),
        ("nationality", ASCENDING),
        ("created_at", ASCENDING)
    ])

    # Chat history — fetched per character, ordered chronologically
    await db.chat_messages.create_index([
        ("character_id", ASCENDING),
        ("created_at", ASCENDING)
    ])

    # One memory-summary doc per character chat (upserted, so unique on character_id)
    await db.chat_summaries.create_index("character_id", unique=True)

    # One favorite doc per character (existence = favorited)
    await db.favorites.create_index("character_id", unique=True)

    print(f"[OK] Connected to MongoDB: {db_name}")
    return db


async def disconnect_db():
    global client
    if client:
        client.close()
        print("[INFO] Disconnected from MongoDB")


def get_database():
    return client[get_db_name()]
