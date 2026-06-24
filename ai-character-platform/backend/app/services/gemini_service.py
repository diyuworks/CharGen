print("LOADED FROM: AI-character-platform - gender fix v3 + json repair v1")
from openai import OpenAI
import json
import re
import random
import asyncio
import unicodedata
from typing import Optional
from app.schemas.character import GeneratedCharacterData
from app.prompts.character_prompt import build_character_prompt

REQUIRED_FIELDS = {
    "name", "age", "nationality", "occupation", "category",
    "personality", "hobbies", "interests", "communication_style",
    "interaction_style", "emotional_traits", "description",
    "backstory", "greeting", "system_prompt", "avatar_prompt"
}

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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",
)


def _ascii_safe(text: str) -> str:
    """Convert accented characters to ASCII equivalents using unicode normalization."""
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _extract_json(text: str) -> str:
    text = _ascii_safe(text)
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text).strip()
    best = None
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        depth = 0
        for j, c in enumerate(text[i:], i):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            if depth == 0:
                candidate = text[i:j+1]
                try:
                    json.loads(candidate)
                    if best is None or len(candidate) > len(best):
                        best = candidate
                except json.JSONDecodeError:
                    pass
                break
    return best if best is not None else text.strip()


def _repair_json(text: str) -> str:
    """
    Fix common malformations small LLMs produce that break strict JSON parsing:
    - smart/curly quotes used instead of straight quotes
    - trailing commas before } or ]
    - stray control characters
    """
    # Normalize smart quotes to straight quotes first
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')

    # Strip control characters that sometimes sneak in (except \n \r \t which json.loads handles)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # Remove trailing commas before a closing } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    return text


def _try_parse(raw_text: str) -> dict:
    """Try parsing raw_text as JSON, attempting a repair pass if the first try fails."""
    candidate = _extract_json(raw_text)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Second attempt: run repair heuristics on the full raw text, then re-extract
    repaired = _repair_json(raw_text)
    candidate2 = _extract_json(repaired)
    return json.loads(candidate2)  # let this raise if it still fails


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
                "content": (
                    "You are a creative character designer. "
                    "Respond with a single valid JSON object only. "
                    "No markdown, no code fences, no explanations, no text before or after the JSON. "
                    "Inside string values, never use double quotes (\") for emphasis or dialogue — "
                    "use single quotes instead. Do not include unescaped line breaks inside string values. "
                    "Keep every string value on a single line."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
        top_p=0.95,
        max_tokens=2048,
    )
    return completion.choices[0].message.content


async def generate_single_character(
    category=None,
    nationality=None,
    gender: Optional[str] = None,
    max_retries: int = 5,
) -> GeneratedCharacterData:
    if gender not in ("male", "female"):
        gender = random.choice(["male", "female"])

    prompt = build_character_prompt(category, nationality, gender=gender)
    last_error = None

    for attempt in range(1, max_retries + 1):
        raw_text = None
        try:
            print(f"Generating {gender} character (attempt {attempt}/{max_retries})...")
            raw_text = await asyncio.to_thread(_call_nvidia, prompt)
            data = _try_parse(raw_text)
            if isinstance(data, list):
                data = data[0]

            data["gender"] = gender

            character = _validate_character_dict(data)
            print(f"Generated: {character.name} ({gender})")
            return character
        except json.JSONDecodeError as e:
            last_error = e
            snippet = raw_text[:200].replace("\n", " ") if raw_text else "N/A"
            print(f"Attempt {attempt} JSON error: {e} | raw: {snippet!r}")
        except (ValueError, KeyError) as e:
            last_error = e
            print(f"Attempt {attempt} validation error: {e}")
        if attempt < max_retries:
            await asyncio.sleep(1.5 * attempt)

    raise RuntimeError(f"Failed after {max_retries} attempts. Last error: {last_error}")


async def generate_batch_characters(
    count: int,
    category=None,
    nationality=None,
    max_retries: int = 5,
) -> list[GeneratedCharacterData]:
    half = count // 2
    genders = ["male"] * half + ["female"] * (count - half)
    random.shuffle(genders)

    results = []
    for i in range(count):
        print(f"Generating character {i + 1}/{count} ({genders[i]})...")
        character = await generate_single_character(
            category, nationality, gender=genders[i], max_retries=max_retries
        )
        results.append(character)
        if i < count - 1:
            await asyncio.sleep(0.5)
    return results