import httpx
import asyncio
import os
import time
import base64
import urllib.parse
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logging_metrics import log_metric

# Read keys from environment / settings  never hardcode
STABLE_HORDE_KEY = os.getenv("STABLE_HORDE_API_KEY") or os.getenv("STABLE_HORDE_KEY") or getattr(settings, "STABLE_HORDE_API_KEY", "0000000000")
STABLE_HORDE_URL = "https://stablehorde.net/api/v2"

POLLINATIONS_KEY = os.getenv("POLLINATIONS_API_KEY") or getattr(settings, "POLLINATIONS_API_KEY", "")

AVATAR_DIR = "static/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

# Realism suffix  gender placeholder replaced dynamically
REALISM_SUFFIX_FEMALE = (
    ", RAW photo, 8k uhd, dslr, high quality, film grain, Fujifilm XT3, "
    "professional headshot photo portrait, real human skin texture, "
    "natural facial pores, subsurface scattering, real human eyes, "
    "professional studio lighting, sharp focus, 85mm lens, f/1.8 aperture, "
    "female, woman, photorealistic, hyperrealistic, NOT anime, NOT cartoon, NOT illustration"
)

REALISM_SUFFIX_MALE = (
    ", RAW photo, 8k uhd, dslr, high quality, film grain, Fujifilm XT3, "
    "professional headshot photo portrait, real human skin texture, "
    "natural facial pores, subsurface scattering, real human eyes, "
    "professional studio lighting, sharp focus, 85mm lens, f/1.8 aperture, "
    "male, man, photorealistic, hyperrealistic, NOT anime, NOT cartoon, NOT illustration"
)

NEGATIVE_PROMPT_FEMALE = (
    "male, man, boy, cartoon, 3d, cgi, anime, illustration, painting, drawing, "
    "digital art, smooth skin, plastic skin, doll, wax figure, unrealistic, "
    "bad eyes, bad anatomy, deformed, ugly, extra fingers, blurry, watermark, signature"
)

NEGATIVE_PROMPT_MALE = (
    "female, woman, girl, cartoon, 3d, cgi, anime, illustration, painting, drawing, "
    "digital art, smooth skin, plastic skin, doll, wax figure, unrealistic, "
    "bad eyes, bad anatomy, deformed, ugly, extra fingers, blurry, watermark, signature"
)


def _get_gender(character: dict) -> str:
    """Get gender from character, default to female."""
    return character.get("gender", "female").lower()


def _build_prompt(character: dict) -> str:
    gender = _get_gender(character)
    base = character.get("avatar_prompt", "")

    realism_suffix = REALISM_SUFFIX_MALE if gender == "male" else REALISM_SUFFIX_FEMALE

    if base:
        weak_endings = [
            "realistic photography, 8k",
            "highly detailed, realistic photography, 8k",
            "female, woman, highly detailed, realistic photography, 8k",
            "male, man, highly detailed, realistic photography, 8k",
        ]
        for ending in weak_endings:
            base = base.replace(ending, "").strip().rstrip(",")
        return base + realism_suffix

    # Fallback if no avatar_prompt exists
    age = character.get("age", 25)
    nationality = character.get("nationality", "")
    occupation = character.get("occupation", "")

    if gender == "male":
        return (
            f"portrait of a handsome {age}-year-old {nationality} man, "
            f"{occupation}, masculine features, realistic face, "
            f"professional headshot, natural lighting, highly detailed"
            + realism_suffix
        )
    else:
        return (
            f"portrait of a beautiful {age}-year-old {nationality} woman, "
            f"{occupation}, feminine features, realistic face, "
            f"professional headshot, natural lighting, highly detailed"
            + realism_suffix
        )


async def _generate_pollinations(prompt: str, gender: str = "female") -> bytes | None:
    negative = NEGATIVE_PROMPT_MALE if gender == "male" else NEGATIVE_PROMPT_FEMALE

    encoded_prompt = urllib.parse.quote(prompt)
    encoded_negative = urllib.parse.quote(negative)

    headers = {}
    if POLLINATIONS_KEY:
        headers["Authorization"] = f"Bearer {POLLINATIONS_KEY}"

    # Try models: prioritize 'sana' (active free model) then fallbacks
    models_to_try = ["flux", "sana", "turbo", ""] if POLLINATIONS_KEY else ["sana", "turbo", "", "flux"]

    async with httpx.AsyncClient(timeout=45) as client:
        for model in models_to_try:
            model_param = f"&model={model}" if model else ""
            url = (
                f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                f"?negative={encoded_negative}"
                f"&width=512&height=512"
                f"{model_param}"
                f"&nologo=true"
            )
            print(f" Pollinations URL ({model or 'default'}): {url[:90]}...")
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200 and len(response.content) > 1000:
                    return response.content
                elif response.status_code in (402, 500, 502, 503, 504):
                    print(f" Pollinations {model or 'default'} returned {response.status_code}, trying next model option...")
                    await asyncio.sleep(1)
                    continue
            except httpx.TimeoutException:
                print(f" Pollinations timeout on model {model or 'default'}")
                continue
            except Exception as e:
                print(f" Pollinations error: {e}")
                continue

    return None


async def _generate_stable_horde(prompt: str, gender: str = "female") -> bytes | None:
    headers = {
        "apikey": STABLE_HORDE_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "ai-character-platform:1.0",
    }

    negative = NEGATIVE_PROMPT_MALE if gender == "male" else NEGATIVE_PROMPT_FEMALE

    payload = {
        "prompt": f"{prompt} ### {negative}",
        "params": {
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.0,
            "sampler_name": "k_euler",
            "n": 1,
        },
        "models": [
            "Realistic Vision",
            "AbsoluteReality",
            "ICBINP - I Can't Believe It's Not Photography",
            "Deliberate 3.0",
            "CyberRealistic Pony",
            "RealBiter",
        ],
        "r2": False,
        "shared": False,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            response = await client.post(
                f"{STABLE_HORDE_URL}/generate/async",
                headers=headers,
                json=payload
            )
        except Exception as e:
            print(f" Stable Horde connect error: {e}")
            return None

        if response.status_code == 403:
            body = response.text[:200].replace("\n", " ")
            print(f" Stable Horde 403: {body}")
            return None
        elif response.status_code != 202:
            print(f" Stable Horde submit error {response.status_code}: {response.text[:200]}")
            return None

        job_id = response.json().get("id")
        if not job_id:
            print(" No job ID returned from Stable Horde")
            return None

        print(f" Stable Horde job submitted: {job_id}")

        # Polling: check every 4s, up to 35 attempts (~140s max)
        max_poll_attempts = 35
        for attempt in range(max_poll_attempts):
            await asyncio.sleep(4)

            try:
                status_response = await client.get(
                    f"{STABLE_HORDE_URL}/generate/check/{job_id}",
                    headers=headers
                )
            except Exception:
                continue

            if status_response.status_code == 200:
                status = status_response.json()
                done = status.get("done", False)
                queue_position = status.get("queue_position", "?")
                wait_time = status.get("wait_time", "?")
                print(f" Horde attempt {attempt+1}/{max_poll_attempts}: done={done}, queue={queue_position}, wait={wait_time}s")

                if done:
                    result_response = await client.get(
                        f"{STABLE_HORDE_URL}/generate/status/{job_id}",
                        headers=headers
                    )

                    if result_response.status_code == 200:
                        result = result_response.json()
                        generations = result.get("generations", [])
                        if generations:
                            img_data = generations[0].get("img", "")
                            if img_data.startswith("data:image"):
                                img_data = img_data.split(",")[1]
                            return base64.b64decode(img_data)

        print(" Stable Horde timed out after polling wait")
        return None


def _save_image(image_bytes: bytes, character_id: str) -> str:
    filename = f"{character_id}.png"
    filepath = os.path.join(AVATAR_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    return f"/static/avatars/{filename}"


def _dicebear_url(character: dict) -> str:
    """DiceBear fallback  different style for male/female."""
    name = character.get("name", "default").replace(" ", "")
    nationality = character.get("nationality", "")
    gender = _get_gender(character)
    colors = ["b6e3f4", "c0aede", "d1d4f9", "ffd5dc", "ffdfbf"]
    color = colors[sum(ord(c) for c in name) % len(colors)]

    if gender == "male":
        return f"https://api.dicebear.com/7.x/personas/svg?seed={name}{nationality}&backgroundColor={color}"
    else:
        return f"https://api.dicebear.com/7.x/lorelei/svg?seed={name}{nationality}&backgroundColor={color}&flip=false"


async def generate_avatar_for_character(
    db: AsyncIOMotorDatabase,
    character_id: str,
) -> str | None:
    if not ObjectId.is_valid(character_id):
        return None

    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    if not character:
        return None

    gender = _get_gender(character)
    prompt = _build_prompt(character)

    print(f" Generating {gender} avatar for {character.get('name')}...")
    print(f" Prompt: {prompt[:100]}...")

    start_time = time.time()
    tier_used = None
    is_ai_image = False

    # 1. Try Stable Horde first (Tier 1 for photorealistic studio photography)
    print(" Attempting Tier 1: Stable Horde (photorealistic models)...")
    image_bytes = await _generate_stable_horde(prompt, gender)
    if image_bytes:
        tier_used = "tier1_stable_horde"
        is_ai_image = True
    else:
        # 2. Fallback to Pollinations if Horde is unavailable
        print(" Stable Horde unavailable/timed out, attempting Tier 2: Pollinations...")
        image_bytes = await _generate_pollinations(prompt, gender)
        if image_bytes:
            tier_used = "tier2_pollinations"
            is_ai_image = True
        else:
            tier_used = "tier3_dicebear"
            is_ai_image = False

    latency = round(time.time() - start_time, 2)

    # 3 Save result
    if image_bytes:
        avatar_url = _save_image(image_bytes, character_id)
        await db.characters.update_one(
            {"_id": ObjectId(character_id)},
            {"$set": {"avatar_url": avatar_url}}
        )
        print(f" Avatar saved: {avatar_url}")
    else:
        print(" All failed, using DiceBear fallback")
        avatar_url = _dicebear_url(character)
        await db.characters.update_one(
            {"_id": ObjectId(character_id)},
            {"$set": {"avatar_url": avatar_url}}
        )

    # Structured logging
    log_metric({
        "call_type": "avatar_generation",
        "character_id": character_id,
        "tier_used": tier_used,
        "is_ai_image": is_ai_image,
        "success": True,
        "latency_sec": latency,
    })

    return avatar_url


async def generate_avatars_bulk(
    db: AsyncIOMotorDatabase,
    limit: int = 20,
    force: bool = False,
) -> dict:
    if force:
        # Catch characters whose avatar_url is empty/missing OR points to a
        # .webp file  this codebase only ever writes .png (see _save_image),
        # so any .webp URL is leftover from an old/different backend run and
        # the file genuinely doesn't exist on disk. Regenerate those too.
        query = {"$or": [
            {"avatar_url": ""},
            {"avatar_url": None},
            {"avatar_url": {"$exists": False}},
            {"avatar_url": {"$regex": r"\.webp$"}},
        ]}
    else:
        query = {"$or": [
            {"avatar_url": ""},
            {"avatar_url": None},
            {"avatar_url": {"$exists": False}},
        ]}

    cursor = db.characters.find(query).limit(limit)

    characters = await cursor.to_list(length=limit)
    updated = 0

    for character in characters:
        char_id = str(character["_id"])
        result = await generate_avatar_for_character(db, char_id)
        if result:
            updated += 1
        await asyncio.sleep(0.3)

    return {"updated": updated, "total_processed": len(characters)}


def build_avatar_url(avatar_prompt: str, seed: int = 42) -> str:
    return ""


def name_to_seed(name: str) -> int:
    return abs(sum(ord(c) for c in name)) % 99999
