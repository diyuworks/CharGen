from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import OpenAI
import asyncio

from app.schemas.chat import ChatMessageResponse, ChatHistoryResponse
from app.services.character_service import get_character_by_id

# Reuse the same NVIDIA client setup pattern as gemini_service.py
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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",
)

# Keep the model context window manageable — only send the most recent N
# messages verbatim. Anything older gets folded into a running summary
# instead of being dropped entirely (see _get_or_update_memory_summary),
# so the character can still recall things from earlier in a long chat.
MAX_HISTORY_MESSAGES = 20


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


async def get_chat_history(
    db: AsyncIOMotorDatabase, character_id: str
) -> ChatHistoryResponse:
    cursor = db.chat_messages.find(
        {"character_id": character_id}
    ).sort("created_at", 1)
    docs = await cursor.to_list(length=1000)

    # First time opening this chat (no messages yet) — seed the character's
    # own greeting as the actual first assistant message, so it's a real,
    # persisted part of the conversation instead of a UI-only placeholder
    # that disappears once the user sends something.
    if not docs:
        character = await get_character_by_id(db, character_id)
        if character and character.greeting:
            seeded = await _save_message(db, character_id, "assistant", character.greeting)
            return ChatHistoryResponse(character_id=character_id, messages=[seeded])

    return ChatHistoryResponse(
        character_id=character_id,
        messages=[ChatMessageResponse(**_serialize(doc)) for doc in docs],
    )


async def get_chat_list(db: AsyncIOMotorDatabase) -> list[dict]:
    """
    Returns one entry per character the user has actually messaged (at least
    one role="user" message exists — the auto-seeded greeting alone doesn't
    count), each with the character's info and their most recent message,
    sorted by most recent activity first.
    """
    # Find character_ids that have at least one real user message
    user_character_ids = await db.chat_messages.distinct(
        "character_id", {"role": "user"}
    )
    if not user_character_ids:
        return []

    # For each, get the single most recent message (could be user or assistant)
    pipeline = [
        {"$match": {"character_id": {"$in": user_character_ids}}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": "$character_id",
            "last_message": {"$first": "$content"},
            "last_message_role": {"$first": "$role"},
            "last_message_at": {"$first": "$created_at"},
        }},
        {"$sort": {"last_message_at": -1}},
    ]
    last_messages = await db.chat_messages.aggregate(pipeline).to_list(length=200)

    # Join with character info
    results = []
    for entry in last_messages:
        char_id = entry["_id"]
        character = await get_character_by_id(db, char_id)
        if not character:
            continue  # character was deleted but chat history remains — skip
        results.append({
            "character_id": char_id,
            "character_name": character.name,
            "character_occupation": character.occupation,
            "character_avatar_url": character.avatar_url or "",
            "last_message": entry["last_message"],
            "last_message_role": entry["last_message_role"],
            "last_message_at": entry["last_message_at"],
        })

    return results


async def _save_message(
    db: AsyncIOMotorDatabase, character_id: str, role: str, content: str
) -> ChatMessageResponse:
    doc = {
        "character_id": character_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow(),
    }
    result = await db.chat_messages.insert_one(doc)
    doc["_id"] = result.inserted_id
    return ChatMessageResponse(**_serialize(doc))


def _summarize_messages(character_name: str, messages: list[dict]) -> str:
    """
    Condense older messages into a short factual summary the model can use
    as memory, instead of either dropping them entirely or sending the full
    raw transcript (which would blow past the context window in long chats).
    """
    transcript = "\n".join(
        f"{'User' if m['role'] == 'user' else character_name}: {m['content']}"
        for m in messages
    )
    completion = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[
            {
                "role": "system",
                "content": (
                    "Summarize the key facts, preferences, and topics from this "
                    "conversation in 3-5 short bullet points. Focus on things the "
                    "USER said about themselves (their life, interests, opinions, "
                    "plans) since that's what the assistant character needs to "
                    "remember. Be concise and factual, no commentary."
                ),
            },
            {"role": "user", "content": transcript},
        ],
        temperature=0.3,
        max_tokens=200,
    )
    return completion.choices[0].message.content.strip()


async def _get_or_update_memory_summary(
    db: AsyncIOMotorDatabase, character_id: str, character_name: str, all_messages: list[dict]
) -> tuple:
    """
    Returns (summary_text_or_None, recent_messages_to_send_verbatim).

    If the chat is short, there's nothing to summarize yet — just return the
    raw recent messages. Once a chat grows past MAX_HISTORY_MESSAGES, the
    older portion gets summarized (and cached in chat_summaries) so we don't
    re-summarize the same old messages on every single new message sent.
    """
    if len(all_messages) <= MAX_HISTORY_MESSAGES:
        return None, all_messages

    older_messages = all_messages[:-MAX_HISTORY_MESSAGES]
    recent_messages = all_messages[-MAX_HISTORY_MESSAGES:]

    existing = await db.chat_summaries.find_one({"character_id": character_id})
    covered_count = existing["covered_message_count"] if existing else 0

    if existing and covered_count >= len(older_messages):
        # Summary already covers everything older than the current recent window
        return existing["summary"], recent_messages

    # Need to (re)build the summary to cover the new older portion
    summary_text = await asyncio.to_thread(_summarize_messages, character_name, older_messages)
    await db.chat_summaries.update_one(
        {"character_id": character_id},
        {"$set": {
            "summary": summary_text,
            "covered_message_count": len(older_messages),
            "updated_at": datetime.utcnow(),
        }},
        upsert=True,
    )
    return summary_text, recent_messages


def _build_chat_system_prompt(
    character_system_prompt: str,
    character_name: str,
    communication_style: str,
    memory_summary,
) -> str:
    """
    The character's stored system_prompt (from generation time) describes WHO
    the character is — it doesn't say HOW to text like a real person. Without
    this wrapper, the model defaults to assistant-speak: long, eager, helpful-
    customer-service tone ("What's on your mind? Want to discuss..."). This
    layer adds texting behavior, curiosity, and memory on top, while keeping
    their personality.
    """
    memory_block = ""
    if memory_summary:
        memory_block = (
            "\n\nEarlier in this conversation, the user shared the following — "
            "remember and naturally refer back to it when relevant, the way a "
            f"friend who's been paying attention would:\n{memory_summary}\n"
        )

    rules = (
        f"You are texting as {character_name} in a casual chat — not writing an essay, "
        "not assisting a customer. Follow these rules strictly:\n\n"
        "- Reply like a real person texting, not an AI assistant. Never say things like "
        "\"How can I help you\" or \"What's on your mind\" or \"Let's explore\" — that's "
        "assistant language, not human language.\n"
        "- Default to SHORT replies: 1-3 sentences for most messages. Only write longer "
        "if the user asks something that genuinely needs more detail, or shares something "
        "emotionally significant that deserves a real response.\n"
        "- Use contractions (I'm, don't, that's), casual phrasing, and occasional sentence "
        "fragments — the way people actually text, not formal written English.\n"
        "- Don't end every message with a question forcing the conversation forward. Real "
        "people sometimes just react, agree, joke, or let a message sit.\n"
        "- Show genuine curiosity about the user sometimes — ask about their day, their "
        "opinions, what they're up to — the way a friend getting to know someone would. "
        "Don't do this every message, just naturally, the way real conversations flow.\n"
        "- Have real opinions and reactions based on your personality and traits — agree, "
        "disagree, joke, push back — instead of being endlessly agreeable or neutral. A "
        "real friend has takes. BUT this should still feel warm, not cold or guarded — "
        "having personality doesn't mean being distant, skeptical of the user's intentions, "
        "or hesitant to be friendly. Default to warmth; add personality on top of that, "
        "not instead of it.\n"
        "- Stay fully in character based on the personality and traits above — but express "
        "it through tone, word choice, and reactions, not by narrating your own traits.\n"
        "- If the user sends something nonsensical, confusing, or like a typo/random keys, "
        "react the way a real person would — confused, amused, or just asking \"what?\" — "
        "don't give a polished customer-service-style response addressing it as a "
        "\"communication issue.\"\n"
        "- When the user is being friendly, warm, or trying to connect, meet that energy "
        "— don't hedge, deflect, or add disclaimers like 'I don't know you yet.' Real "
        "people warm up to friendliness, they don't gatekeep it.\n"
        "- Never break character to mention you are an AI, a language model, or a chatbot."
    )

    return f"{character_system_prompt}\n\n{rules}{memory_block}"


def _call_nvidia_chat(
    character_system_prompt: str,
    character_name: str,
    communication_style: str,
    memory_summary,
    recent_history: list[dict],
    user_message: str,
) -> str:
    system_prompt = _build_chat_system_prompt(
        character_system_prompt, character_name, communication_style, memory_summary
    )
    messages = [{"role": "system", "content": system_prompt}]
    for msg in recent_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=messages,
        temperature=0.9,
        top_p=0.95,
        max_tokens=220,  # nudges the model toward shorter, texting-length replies
    )
    return completion.choices[0].message.content.strip()


async def send_message(
    db: AsyncIOMotorDatabase, character_id: str, user_message: str
) -> ChatMessageResponse:
    character = await get_character_by_id(db, character_id)
    if not character:
        raise ValueError("Character not found")

    # Pull full history, then split into (optional summary of older stuff) +
    # (recent messages sent verbatim) — this is what gives the character
    # memory of things said earlier without blowing past the context window.
    history_doc = await get_chat_history(db, character_id)
    all_messages = [
        {"role": m.role, "content": m.content} for m in history_doc.messages
    ]
    memory_summary, recent_history = await _get_or_update_memory_summary(
        db, character_id, character.name, all_messages
    )

    # Save the user's message first
    await _save_message(db, character_id, "user", user_message)

    # character.system_prompt already encodes name, personality, communication
    # style, backstory etc — generated at character creation time. We layer a
    # chat-specific behavioral wrapper on top (see _build_chat_system_prompt)
    # so replies sound like real texting instead of an AI assistant, and
    # include a memory summary of older messages so the character can recall
    # things from earlier in a long conversation.
    reply_text = await asyncio.to_thread(
        _call_nvidia_chat,
        character.system_prompt,
        character.name,
        character.communication_style,
        memory_summary,
        recent_history,
        user_message,
    )

    assistant_msg = await _save_message(db, character_id, "assistant", reply_text)
    return assistant_msg
