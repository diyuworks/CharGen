import asyncio
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.schemas.character import (
    GenerateCharacterRequest,
    CharacterResponse,
    CharacterListResponse,
    SaveCharacterRequest,
)
from app.services import gemini_service, character_service, chat_service, favorite_service
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse, ChatListResponse
from app.schemas.favorite import FavoriteToggleResponse, FavoriteListResponse
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
    background_tasks: BackgroundTasks,
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
        # Use BackgroundTasks — runs after response is sent, errors show in terminal
        for char in saved:
            if char.id != "preview":
                background_tasks.add_task(generate_avatar_for_character, db, char.id)
        return saved
    else:
        from datetime import datetime
        return [
            CharacterResponse(
                id="preview",
                **c.model_dump(),
                avatar_url="",
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
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    # Verify character exists first
    character = await character_service.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    background_tasks.add_task(generate_avatar_for_character, db, character_id)
    return {"message": "Avatar generation started", "character_id": character_id}


@router.post("/characters/generate-avatars-bulk")
async def bulk_generate_avatars(
    limit: int = Query(20, ge=1, le=100),
    force: bool = Query(False, description="Also regenerate broken/stale .webp URLs, not just missing ones"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await generate_avatars_bulk(db, limit=limit, force=force)
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


# --- Chat endpoints ---

@router.get("/chats", response_model=ChatListResponse)
async def get_chat_list(
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    chats = await chat_service.get_chat_list(db)
    return ChatListResponse(chats=chats)


@router.get("/chat/{character_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    character_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    character = await character_service.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return await chat_service.get_chat_history(db, character_id)


@router.post("/chat/{character_id}", response_model=ChatMessageResponse)
async def send_chat_message(
    character_id: str,
    request: ChatMessageRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        return await chat_service.send_message(db, character_id, request.message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Favorites endpoints ---

@router.post("/favorites/{character_id}/toggle", response_model=FavoriteToggleResponse)
async def toggle_favorite(
    character_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    character = await character_service.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    is_favorite = await favorite_service.toggle_favorite(db, character_id)
    return FavoriteToggleResponse(character_id=character_id, is_favorite=is_favorite)


@router.get("/favorites", response_model=FavoriteListResponse)
async def get_favorites(
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    character_ids = await favorite_service.get_favorite_ids(db)
    return FavoriteListResponse(character_ids=character_ids)