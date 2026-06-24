from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GenerateCharacterRequest(BaseModel):
    category: Optional[str] = None          # e.g. "Doctor" — if None, picked randomly
    nationality: Optional[str] = None        # e.g. "Indian" — if None, picked randomly
    gender: Optional[str] = None             # "male" / "female" — if None, service does 50/50 random pick
    count: int = 1                           # Generate 1-50 characters at once


class CharacterResponse(BaseModel):
    id: str
    name: str
    age: int
    gender: Optional[str] = "female"  # default covers old records saved before this field existed
    nationality: str
    occupation: str
    category: str
    personality: list[str]
    hobbies: list[str]
    interests: list[str]
    communication_style: str
    interaction_style: str
    emotional_traits: list[str]
    description: str
    backstory: str
    greeting: str
    system_prompt: str
    avatar_prompt: str = ""
    avatar_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class CharacterListResponse(BaseModel):
    characters: list[CharacterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SaveCharacterRequest(BaseModel):
    name: str
    age: int
    gender: Optional[str] = "female"
    nationality: str
    occupation: str
    category: str
    personality: list[str]
    hobbies: list[str]
    interests: list[str]
    communication_style: str
    interaction_style: str
    emotional_traits: list[str]
    description: str
    backstory: str
    greeting: str
    system_prompt: str
    avatar_prompt: str = ""
    avatar_url: str = ""


class GeneratedCharacterData(BaseModel):
    """Schema that the LLM must return — used for validation"""
    name: str
    age: int
    gender: str  # required — gemini_service.py always sets this explicitly before validation
    nationality: str
    occupation: str
    category: str
    personality: list[str]
    hobbies: list[str]
    interests: list[str]
    communication_style: str
    interaction_style: str
    emotional_traits: list[str]
    description: str
    backstory: str
    greeting: str
    system_prompt: str
    avatar_prompt: str = ""