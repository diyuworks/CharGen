CATEGORIES = [
    "College Student", "Doctor", "Teacher", "Entrepreneur",
    "Software Engineer", "Fitness Trainer", "Artist", "Gamer",
    "Travel Blogger", "Fashion Designer", "Influencer", "Musician",
    "Photographer", "Writer", "Researcher", "Life Coach"
]

NATIONALITIES = [
    "Indian", "American", "British", "Japanese", "Brazilian",
    "French", "Korean", "Australian", "Canadian", "German",
    "Italian", "Spanish", "Chinese", "Mexican", "Nigerian",
    "South African", "Swedish", "Dutch", "Argentine", "Thai",
    "Vietnamese", "Indonesian", "Filipino", "Turkish", "Egyptian",
    "Pakistani", "Bangladeshi", "Sri Lankan", "Nepalese", "Maldivian"
]


def build_character_prompt(category: str = None, nationality: str = None) -> str:
    category_instruction = (
        f'The character must be in the "{category}" category.'
        if category else
        f"Pick a random category from: {', '.join(CATEGORIES)}."
    )
    nationality_instruction = (
        f'The character must be {nationality}.'
        if nationality else
        f"Pick a random nationality from: {', '.join(NATIONALITIES)}."
    )

    return f"""
You are generating a realistic, unique FEMALE AI character profile for a conversational AI platform.

INSTRUCTIONS:
- {category_instruction}
- {nationality_instruction}
- The character MUST be female (woman). Never generate male characters.
- The character must feel like a real, believable person - not a generic template.
- Make the backstory emotionally rich and specific (include childhood, education, a defining life moment).
- The system_prompt should be written in 2nd person ("You are [Name]...") as instructions for an AI to roleplay this character.
- The avatar_prompt MUST start with "portrait of a beautiful [age]-year-old [nationality] woman," and include: feminine features, hair description, eye color, skin tone, clothing, expression, lighting. Always end with "female, woman, highly detailed, realistic photography, 8k".
- Vary personality significantly - not every character should be warm and friendly.
- Age must be between 18 and 45.
- All list fields must have 3-6 items.

Return ONLY a single valid JSON object with EXACTLY these fields, no extra text, no markdown:

{{
  "name": "string",
  "age": integer,
  "nationality": "string",
  "occupation": "string",
  "category": "string",
  "personality": ["trait1", "trait2", "trait3"],
  "hobbies": ["hobby1", "hobby2", "hobby3"],
  "interests": ["interest1", "interest2", "interest3"],
  "communication_style": "string (1 sentence)",
  "interaction_style": "string (1 sentence)",
  "emotional_traits": ["trait1", "trait2", "trait3"],
  "description": "string (2-3 sentences describing the character)",
  "backstory": "string (4-6 sentences with specific life details)",
  "greeting": "string (opening message this character would send to a new user)",
  "system_prompt": "string (detailed roleplay instruction starting with You are [Name]...)",
  "avatar_prompt": "string (MUST start with portrait of a beautiful [age]-year-old [nationality] woman, and end with female, woman, highly detailed, realistic photography, 8k)"
}}
"""


def build_batch_prompt(count: int, category: str = None, nationality: str = None) -> str:
    category_instruction = (
        f'All characters must be in the "{category}" category.'
        if category else
        f"Pick varied categories from: {', '.join(CATEGORIES)}. Each character should have a DIFFERENT category."
    )
    nationality_instruction = (
        f'All characters must be {nationality}.'
        if nationality else
        f"Pick varied nationalities from: {', '.join(NATIONALITIES)}. Each character should have a DIFFERENT nationality."
    )

    return f"""
You are generating {count} realistic, unique FEMALE AI character profiles for a conversational AI platform.

INSTRUCTIONS:
- {category_instruction}
- {nationality_instruction}
- ALL characters MUST be female (women). Never generate male characters.
- Each character must feel like a real, distinct person - no two characters should be similar.
- Vary personalities, backstories, ages, and communication styles significantly.
- Each backstory must be emotionally specific and unique.
- system_prompt for each character must be written in 2nd person: "You are [Name]..."
- avatar_prompt MUST start with "portrait of a beautiful [age]-year-old [nationality] woman," and end with "female, woman, highly detailed, realistic photography, 8k"
- Age must be between 18 and 45 for each character.
- All list fields must have 3-6 items.

Return ONLY a valid JSON array of {count} objects. No markdown, no extra text. Each object must have EXACTLY these fields:

[
  {{
    "name": "string",
    "age": integer,
    "nationality": "string",
    "occupation": "string",
    "category": "string",
    "personality": ["trait1", "trait2"],
    "hobbies": ["hobby1", "hobby2"],
    "interests": ["interest1", "interest2"],
    "communication_style": "string",
    "interaction_style": "string",
    "emotional_traits": ["trait1", "trait2"],
    "description": "string",
    "backstory": "string",
    "greeting": "string",
    "system_prompt": "string",
    "avatar_prompt": "string"
  }}
]
"""
