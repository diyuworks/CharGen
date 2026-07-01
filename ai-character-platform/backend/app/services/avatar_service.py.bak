import httpx
import asyncio
import os
import base64
import urllib.parse
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

STABLE_HORDE_KEY = "F-_9TvQSALgbHa5F2EdcXw"
STABLE_HORDE_URL = "https://stablehorde.net/api/v2"

AVATAR_DIR = "static/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

# Realism suffix — gender placeholder replaced dynamically
REALISM_SUFFIX_FEMALE = (
    ", photorealistic, hyperrealistic, real human skin texture, "
    "natural facial pores, subsurface scattering, real human eyes, "
    "professional studio lighting, sharp focus, DSLR photography, "
    "Canon EOS 5D, 85mm lens, f/1.8 aperture, 8k resolution, "
    "female, woman, NOT anime, NOT cartoon, NOT illustration"
)

REALISM_SUFFIX_MALE = (
    ", photorealistic, hyperrealistic, real human skin texture, "
    "natural facial pores, subsurface scattering, real human eyes, "
    "professional studio lighting, sharp focus, DSLR photography, "
    "Canon EOS 5D, 85mm lens, f/1.8 aperture, 8k resolution, "
    "male, man, NOT anime, NOT cartoon, NOT illustration"
)

NEGATIVE_PROMPT_FEMALE = (
    "male, man, boy, masculine, ugly, deformed, blurry, low quality, "
    "anime, cartoon, drawing, illustration, 3d render, CGI, animated, "
    "painting, digital art, unrealistic, plastic skin, doll, wax figure, "
    "extra fingers, bad anatomy, bad hands, missing limbs, "
    "watermark, signature, text, logo, border, frame"
)

NEGATIVE_PROMPT_MALE = (
    "female, woman, girl, feminine, ugly, deformed, blurry, low quality, "
    "anime, cartoon, drawing, illustration, 3d render, CGI, animated, "
    "painting, digital art, unrealistic, plastic skin, doll, wax figure, "
    "extra fingers, bad anatomy, bad hands, missing limbs, "
    "watermark, signature, text, logo, border, frame"
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

    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?negative={encoded_negative}"
        f"&width=512&height=512"
        f"&model=flux"
        f"&nologo=true"
    )

    print(f"🎨 Pollinations URL: {url[:100]}...")

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content
            else:
                print(f"❌ Pollinations error: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Pollinations failed: {e}")
            return None


async def _generate_stable_horde(prompt: str, gender: str = "female") -> bytes | None:
    headers = {
        "apikey": STABLE_HORDE_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "ai-character-platform:1.0",
    }

    negative = NEGATIVE_PROMPT_MALE if gender == "male" else NEGATIVE_PROMPT_FEMALE

    payload = {
        "prompt": prompt,
        "negative_prompt": negative,
        "params": {
            "width": 512,
            "height": 512,
            "steps": 30,
            "cfg_scale": 7.5,
            "sampler_name": "k_dpm_2_a",
            "n": 1,
        },
        "models": ["Realistic Vision"],
        "r2": False,
        "shared": False,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{STABLE_HORDE_URL}/generate/async",
            headers=headers,
            json=payload
        )

        if response.status_code != 202:
            print(f"❌ Stable Horde submit error {response.status_code}: {response.text[:200]}")
            return None

        job_id = response.json().get("id")
        if not job_id:
            print("❌ No job ID returned")
            return None

        print(f"⏳ Stable Horde job submitted: {job_id}")

        for attempt in range(30):
            await asyncio.sleep(10)

            status_response = await client.get(
                f"{STABLE_HORDE_URL}/generate/check/{job_id}",
                headers=headers
            )

            if status_response.status_code == 200:
                status = status_response.json()
                done = status.get("done", False)
                queue_position = status.get("queue_position", "?")
                wait_time = status.get("wait_time", "?")
                print(f"⏳ Attempt {attempt+1}: done={done}, queue={queue_position}, wait={wait_time}s")

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

        print("❌ Stable Horde timed out")
        return None


def _save_image(image_bytes: bytes, character_id: str) -> str:
    filename = f"{character_id}.png"
    filepath = os.path.join(AVATAR_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    return f"/static/avatars/{filename}"


def _dicebear_url(character: dict) -> str:
    """DiceBear fallback — different style for male/female."""
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

    print(f"🎨 Generating {gender} avatar for {character.get('name')}...")
    print(f"📝 Prompt: {prompt[:100]}...")

    # 1️⃣ Try Pollinations first
    image_bytes = await _generate_pollinations(prompt, gender)

    # 2️⃣ Fallback to Stable Horde
    if not image_bytes:
        print("⚠️ Pollinations failed, trying Stable Horde...")
        image_bytes = await _generate_stable_horde(prompt, gender)

    # 3️⃣ Last resort — DiceBear
    if image_bytes:
        avatar_url = _save_image(image_bytes, character_id)
        await db.characters.update_one(
            {"_id": ObjectId(character_id)},
            {"$set": {"avatar_url": avatar_url}}
        )
        print(f"✅ Avatar saved: {avatar_url}")
        return avatar_url
    else:
        print("⚠️ All failed, using DiceBear fallback")
        fallback_url = _dicebear_url(character)
        await db.characters.update_one(
            {"_id": ObjectId(character_id)},
            {"$set": {"avatar_url": fallback_url}}
        )
        return fallback_url


async def generate_avatars_bulk(
    db: AsyncIOMotorDatabase,
    limit: int = 20,
) -> dict:
    cursor = db.characters.find(
        {"$or": [
            {"avatar_url": ""},
            {"avatar_url": None},
            {"avatar_url": {"$exists": False}}
        ]}
    ).limit(limit)

    characters = await cursor.to_list(length=limit)
    updated = 0

    for character in characters:
        char_id = str(character["_id"])
        result = await generate_avatar_for_character(db, char_id)
        if result:
            updated += 1
        await asyncio.sleep(1)

    return {"updated": updated, "total_processed": len(characters)}


def build_avatar_url(avatar_prompt: str, seed: int = 42) -> str:
    return ""


def name_to_seed(name: str) -> int:
    return abs(sum(ord(c) for c in name)) % 99999