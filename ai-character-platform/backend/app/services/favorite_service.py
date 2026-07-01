from motor.motor_asyncio import AsyncIOMotorDatabase


async def toggle_favorite(db: AsyncIOMotorDatabase, character_id: str) -> bool:
    """Returns the new favorite state (True = now favorited, False = removed)."""
    existing = await db.favorites.find_one({"character_id": character_id})
    if existing:
        await db.favorites.delete_one({"character_id": character_id})
        return False
    await db.favorites.insert_one({"character_id": character_id})
    return True


async def get_favorite_ids(db: AsyncIOMotorDatabase) -> list[str]:
    cursor = db.favorites.find({}, {"character_id": 1})
    docs = await cursor.to_list(length=1000)
    return [doc["character_id"] for doc in docs]
