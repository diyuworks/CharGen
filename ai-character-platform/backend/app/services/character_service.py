from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas.character import (
    GeneratedCharacterData,
    CharacterResponse,
    CharacterListResponse,
    SaveCharacterRequest,
)


def _serialize(doc: dict) -> dict:
    """Convert MongoDB _id to string id."""
    doc["id"] = str(doc.pop("_id"))
    return doc


async def save_character(
    db: AsyncIOMotorDatabase,
    data: GeneratedCharacterData | SaveCharacterRequest
) -> CharacterResponse:
    """Insert a character document into MongoDB."""
    doc = data.model_dump()
    doc["avatar_url"] = ""
    doc["created_at"] = datetime.utcnow()

    result = await db.characters.insert_one(doc)
    saved = await db.characters.find_one({"_id": result.inserted_id})
    return CharacterResponse(**_serialize(saved))


async def save_many_characters(
    db: AsyncIOMotorDatabase,
    characters: list[GeneratedCharacterData]
) -> list[CharacterResponse]:
    """Bulk insert characters — efficient for large batch generation."""
    docs = []
    for c in characters:
        doc = c.model_dump()
        doc["avatar_url"] = ""
        doc["created_at"] = datetime.utcnow()
        docs.append(doc)

    result = await db.characters.insert_many(docs)
    saved = await db.characters.find(
        {"_id": {"$in": result.inserted_ids}}
    ).to_list(length=len(docs))

    return [CharacterResponse(**_serialize(doc)) for doc in saved]


async def get_characters(
    db: AsyncIOMotorDatabase,
    page: int = 1,
    page_size: int = 20,
    category: str = None,
    search: str = None,
    nationality: str = None,
) -> CharacterListResponse:
    """Paginated, filterable character listing — scales to 10M+ records."""
    query = {}
    if category:
        query["category"] = category
    if nationality:
        query["nationality"] = nationality
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"occupation": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    total = await db.characters.count_documents(query)
    skip = (page - 1) * page_size

    cursor = db.characters.find(query).sort("created_at", -1).skip(skip).limit(page_size)
    docs = await cursor.to_list(length=page_size)

    return CharacterListResponse(
        characters=[CharacterResponse(**_serialize(doc)) for doc in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


async def get_character_by_id(
    db: AsyncIOMotorDatabase,
    character_id: str
) -> CharacterResponse | None:
    if not ObjectId.is_valid(character_id):
        return None
    doc = await db.characters.find_one({"_id": ObjectId(character_id)})
    if not doc:
        return None
    return CharacterResponse(**_serialize(doc))


async def delete_character(
    db: AsyncIOMotorDatabase,
    character_id: str
) -> bool:
    if not ObjectId.is_valid(character_id):
        return False
    result = await db.characters.delete_one({"_id": ObjectId(character_id)})
    return result.deleted_count > 0


async def get_stats(db: AsyncIOMotorDatabase) -> dict:
    """Dashboard stats."""
    total = await db.characters.count_documents({})
    pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}]
    category_counts = await db.characters.aggregate(pipeline).to_list(length=100)
    return {
        "total_characters": total,
        "by_category": {item["_id"]: item["count"] for item in category_counts},
    }
