import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = "mongodb://localhost:27017"
MONGODB_DB_NAME = "ai_characters"


async def main():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    cursor = db.characters.find({"avatar_url": {"$regex": r"\.webp$"}})
    broken = await cursor.to_list(length=1000)

    print(f"Found {len(broken)} characters with broken .webp avatar_url:")
    for char in broken:
        print(f"  - {char.get('name', 'Unknown')} ({char['_id']})")

    if not broken:
        print("Nothing to fix.")
        client.close()
        return

    confirm = input(f"\nReset these {len(broken)} avatar_url fields to empty string? [y/N]: ")
    if confirm.lower() != "y":
        print("Aborted - no changes made.")
        client.close()
        return

    result = await db.characters.update_many(
        {"avatar_url": {"$regex": r"\.webp$"}},
        {"$set": {"avatar_url": ""}},
    )
    print(f"\nReset {result.modified_count} character(s).")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
