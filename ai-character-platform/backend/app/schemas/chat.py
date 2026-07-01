from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    character_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    character_id: str
    messages: list[ChatMessageResponse]


class ChatListItem(BaseModel):
    character_id: str
    character_name: str
    character_occupation: str
    character_avatar_url: str
    last_message: str
    last_message_role: Literal["user", "assistant"]
    last_message_at: datetime


class ChatListResponse(BaseModel):
    chats: list[ChatListItem]
