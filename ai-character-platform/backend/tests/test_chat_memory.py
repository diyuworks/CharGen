import pytest
from app.services.chat_service import _build_chat_system_prompt, MAX_HISTORY_MESSAGES


def test_max_history_window_size():
    assert MAX_HISTORY_MESSAGES == 20


def test_build_chat_system_prompt_without_memory():
    base_prompt = "You are Marcus, a 30-year-old barista from Seattle."
    system_prompt = _build_chat_system_prompt(
        character_system_prompt=base_prompt,
        character_name="Marcus",
        communication_style="casual",
        memory_summary=None,
    )
    assert "You are Marcus" in system_prompt
    assert "Reply like a real person texting" in system_prompt
    assert "Default to SHORT replies: 1-3 sentences" in system_prompt
    assert "Earlier in this conversation" not in system_prompt


def test_build_chat_system_prompt_with_memory_summary():
    base_prompt = "You are Marcus, a 30-year-old barista from Seattle."
    memory = "- User drinks oat milk lattes\n- User has two cats"
    system_prompt = _build_chat_system_prompt(
        character_system_prompt=base_prompt,
        character_name="Marcus",
        communication_style="casual",
        memory_summary=memory,
    )
    assert "Earlier in this conversation, the user shared the following" in system_prompt
    assert "- User drinks oat milk lattes" in system_prompt
    assert "Never break character to mention you are an AI" in system_prompt
