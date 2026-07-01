from pydantic import BaseModel


class FavoriteToggleResponse(BaseModel):
    character_id: str
    is_favorite: bool


class FavoriteListResponse(BaseModel):
    character_ids: list[str]
