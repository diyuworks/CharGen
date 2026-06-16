from openai import OpenAI
import json
import re
import asyncio
from typing import Optional
from app.core.config import settings
from app.schemas.character import GeneratedCharacterData
from app.prompts.character_prompt import build_character_prompt, build_batch_prompt

REQUIRED_FIELDS = {
    "name", "age", "nationality", "occupation", "category",
    "personality", "hobbies", "interests", "communication_style",
    "interaction_style", "emotional_traits", "description",
    "backstory", "greeting", "system_prompt", "avatar_prompt"
}

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=settings.NVIDIA_API_KEY,
)


def _extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
    if json_match:
        return json_match.group(1).strip()
    return text.strip()


def _validate_character_dict(data: dict) -> GeneratedCharacterData:
    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Missing fields: {missing}")
    return GeneratedCharacterData(**data)


def _call_nvidia(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[
            {
                "role": "system",
                "content": "You are a creative female character designer. Always respond with valid JSON only. No markdown, no extra text, no explanations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.9,
        top_p=0.95,
        max_tokens=2048,
    )
    return completion.choices[0].message.content


async def generate_single_character(
    category: Optional[str] = None,
    nationality: Optional[str] = None,
    max_retries: int = 3
) -> GeneratedCharacterData:
    prompt = build_character_prompt(category, nationality)
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Generating character (attempt {attempt})...")
            raw_text = await asyncio.to_thread(_call_nvidia, prompt)
            raw = _extract_json(raw_text)
            data = json.loads(raw)

            if isinstance(data, list):
                data = data[0]

            character = _validate_character_dict(data)
            print(f"✅ Generated character: {character.name}")
            return character

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            last_error = e
            print(f"⚠️  Attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(1.5 * attempt)

    raise RuntimeError(f"Failed after {max_retries} attempts. Last error: {last_error}")


async def generate_batch_characters(
    count: int,
    category: Optional[str] = None,
    nationality: Optional[str] = None,
    max_retries: int = 3
) -> list[GeneratedCharacterData]:
    results = []
    for i in range(count):
        print(f"📝 Generating character {i+1}/{count}...")
        character = await generate_single_character(category, nationality, max_retries)
        results.append(character)
        if i < count - 1:
            await asyncio.sleep(0.5)
    return results
