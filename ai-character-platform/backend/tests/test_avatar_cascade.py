import pytest
from app.services.avatar_service import _dicebear_url, _build_prompt, _get_gender


def test_gender_detection():
    assert _get_gender({"gender": "Male"}) == "male"
    assert _get_gender({"gender": "Female"}) == "female"
    assert _get_gender({}) == "female"


def test_dicebear_deterministic_fallback():
    char_female = {"name": "Aria", "nationality": "Japanese", "gender": "female"}
    char_male = {"name": "Leo", "nationality": "Italian", "gender": "male"}

    url_female = _dicebear_url(char_female)
    url_male = _dicebear_url(char_male)

    assert "api.dicebear.com/7.x/lorelei/svg" in url_female
    assert "api.dicebear.com/7.x/personas/svg" in url_male
    assert "AriaJapanese" in url_female
    assert "LeoItalian" in url_male


def test_build_prompt_realism_suffix():
    char = {
        "name": "Maya",
        "gender": "female",
        "age": 26,
        "nationality": "Indian",
        "occupation": "Botanist",
        "avatar_prompt": "woman examining tropical leaves in greenhouse",
    }
    prompt = _build_prompt(char)
    assert "woman examining tropical leaves in greenhouse" in prompt
    assert "photorealistic" in prompt
    assert "NOT anime" in prompt
