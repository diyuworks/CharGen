from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from app.core.config import settings

client: AsyncIOMotorClient = None


async def connect_db():
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]

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

    print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    return db


async def disconnect_db():
    global client
    if client:
        client.close()
        print("🔌 Disconnected from MongoDB")


def get_database():
    return client[settings.MONGODB_DB_NAME]
