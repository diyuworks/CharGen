from fastapi import APIRouter, HTTPException, Query, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.schemas.character import (
    GenerateCharacterRequest,
    CharacterResponse,
    CharacterListResponse,
    SaveCharacterRequest,
)
from app.services import gemini_service, character_service
from app.services.avatar_service import (
    generate_avatar_for_character,
    generate_avatars_bulk,
    build_avatar_url,
    name_to_seed,
)

router = APIRouter()


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


@router.post("/generate-character", response_model=list[CharacterResponse])
async def generate_character(
    request: GenerateCharacterRequest,
    save: bool = Query(True),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    count = max(1, min(request.count, 50))

    if count == 1:
        characters_data = [await gemini_service.generate_single_character(
            category=request.category,
            nationality=request.nationality,
        )]
    else:
        characters_data = await gemini_service.generate_batch_characters(
            count=count,
            category=request.category,
            nationality=request.nationality,
        )

    if save:
        saved = await character_service.save_many_characters(db, characters_data)
        # Auto-generate avatar URLs
        for char in saved:
            if char.id != "preview":
                await generate_avatar_for_character(db, char.id)
        # Re-fetch with avatar URLs
        updated = []
        for char in saved:
            refreshed = await character_service.get_character_by_id(db, char.id)
            updated.append(refreshed if refreshed else char)
        return updated
    else:
        from datetime import datetime
        return [
            CharacterResponse(
                id="preview",
                **c.model_dump(),
                avatar_url=build_avatar_url(c.avatar_prompt, name_to_seed(c.name)),
                created_at=datetime.utcnow()
            )
            for c in characters_data
        ]


@router.post("/save-character", response_model=CharacterResponse)
async def save_character(
    request: SaveCharacterRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await character_service.save_character(db, request)


@router.get("/characters", response_model=CharacterListResponse)
async def list_characters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str = Query(None),
    nationality: str = Query(None),
    search: str = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await character_service.get_characters(
        db, page=page, page_size=page_size,
        category=category, search=search, nationality=nationality
    )


@router.get("/characters/stats")
async def get_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await character_service.get_stats(db)


@router.get("/character/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    character = await character_service.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.post("/character/{character_id}/generate-avatar")
async def generate_avatar(
    character_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    avatar_url = await generate_avatar_for_character(db, character_id)
    if not avatar_url:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"avatar_url": avatar_url, "character_id": character_id}


@router.post("/characters/generate-avatars-bulk")
async def bulk_generate_avatars(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await generate_avatars_bulk(db, limit=limit)
    return result


@router.delete("/character/{character_id}")
async def delete_character(
    character_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    deleted = await character_service.delete_character(db, character_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Character deleted successfully"}
