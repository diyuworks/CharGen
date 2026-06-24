import random

CATEGORIES = [
    "College Student", "Doctor", "Teacher", "Entrepreneur",
    "Software Engineer", "Fitness Trainer", "Artist", "Gamer",
    "Travel Blogger", "Fashion Designer", "Influencer", "Musician",
    "Photographer", "Writer", "Researcher", "Life Coach",
    "Chef", "Lawyer", "Nurse", "Architect"
]

NATIONALITIES = [
    "Indian", "American", "British", "Japanese", "Brazilian",
    "French", "Korean", "Australian", "Canadian", "German",
    "Italian", "Spanish", "Chinese", "Mexican", "Nigerian",
    "South African", "Swedish", "Dutch", "Argentine", "Thai"
]

CATEGORY_OUTFITS_FEMALE = {
    "Fitness Trainer": [
        "fitted black athletic tank top and leggings",
        "sporty zip-up jacket over a sports bra",
        "grey athletic crop top and joggers",
        "neon athletic wear with a sweatband",
        "compression top with running shorts",
        "yoga outfit in muted teal tones",
        "track jacket with matching joggers",
    ],
    "Doctor": [
        "white medical coat over scrubs",
        "light blue scrub top with a stethoscope",
        "professional white coat over a collared shirt",
        "teal surgical scrubs with an ID badge",
        "white coat over a turtleneck",
    ],
    "Software Engineer": [
        "casual hoodie with a laptop bag strap visible",
        "graphic tee under an open flannel shirt",
        "minimalist black turtleneck",
        "denim jacket over a plain tee",
        "oversized sweatshirt with glasses",
        "tech-company branded zip hoodie",
    ],
    "College Student": [
        "oversized hoodie and denim jacket",
        "casual graphic tee with a backpack strap",
        "cozy cardigan over a striped top",
        "varsity jacket over a plain tee",
        "denim jacket with a tote bag",
    ],
    "Teacher": [
        "smart casual blouse with a cardigan",
        "knee-length dress with a blazer",
        "collared shirt with a pencil skirt",
        "soft sweater with pearl earrings",
        "patterned blouse with a cardigan",
    ],
    "Entrepreneur": [
        "tailored navy blazer over a silk top",
        "sharp black pantsuit",
        "structured blazer with gold jewelry",
        "cream colored power suit",
        "fitted blazer dress with statement heels",
    ],
    "Artist": [
        "paint-splattered denim overalls",
        "flowy bohemian top with layered necklaces",
        "oversized linen shirt rolled at the sleeves",
        "colorful patchwork jacket",
        "loose smock top with paint stains",
    ],
    "Gamer": [
        "oversized graphic hoodie",
        "casual streetwear with a beanie",
        "graphic tee with fingerless gloves",
        "gaming headset around neck, casual hoodie",
        "esports team jersey",
    ],
    "Travel Blogger": [
        "linen shirt with a wide-brim hat",
        "casual sundress with a denim jacket",
        "earthy tones cargo jacket",
        "flowy kimono-style jacket",
        "backpacker style utility vest",
    ],
    "Fashion Designer": [
        "avant-garde tailored blazer",
        "statement designer dress",
        "structured coat with bold accessories",
        "asymmetric draped top",
        "high-fashion monochrome outfit",
    ],
    "Influencer": [
        "trendy crop top with high-waisted jeans",
        "stylish off-shoulder top",
        "designer streetwear with sunglasses",
        "matching loungewear set",
        "metallic statement top",
    ],
    "Musician": [
        "leather jacket over a band tee",
        "bohemian fringe top",
        "vintage denim with layered jewelry",
        "velvet blazer with rings",
        "punk-inspired studded jacket",
    ],
    "Photographer": [
        "utility vest over a plain tee",
        "casual flannel shirt with a camera strap",
        "olive cargo jacket",
        "denim jacket with multiple pockets",
        "minimalist black outfit with a camera bag",
    ],
    "Writer": [
        "cozy oversized sweater",
        "tweed blazer with reading glasses",
        "soft cardigan over a turtleneck",
        "vintage-style blouse with a brooch",
        "knitted shawl over a simple dress",
    ],
    "Researcher": [
        "lab coat over a collared shirt",
        "smart casual blouse with glasses",
        "structured blazer with a notebook in hand",
        "white lab coat with safety glasses",
        "professional cardigan with a lanyard",
    ],
    "Life Coach": [
        "soft blazer over a silk camisole",
        "elegant wrap dress",
        "calm pastel-toned cardigan",
        "flowy linen outfit in neutral tones",
        "structured but soft blazer dress",
    ],
    "Chef": [
        "white chef's coat with an apron",
        "double-breasted chef jacket",
        "apron over a casual kitchen uniform",
        "black chef coat with rolled sleeves",
    ],
    "Lawyer": [
        "sharp grey pantsuit",
        "tailored black blazer with a silk blouse",
        "structured dress with a blazer",
        "professional pencil skirt suit",
    ],
    "Nurse": [
        "navy blue scrubs with a stethoscope",
        "patterned scrub top with a badge",
        "light pink medical scrubs",
        "white nursing uniform with a cardigan",
    ],
    "Architect": [
        "structured black blazer with minimalist jewelry",
        "monochrome tailored outfit",
        "modern asymmetric blazer",
        "all-black outfit with statement glasses",
    ],
}

CATEGORY_OUTFITS_MALE = {
    "Fitness Trainer": [
        "fitted black athletic t-shirt and shorts",
        "zip-up track jacket over a tank top",
        "grey athletic tee and joggers",
        "compression shirt with running shorts",
        "sleeveless gym tank with joggers",
    ],
    "Doctor": [
        "white medical coat over a collared shirt",
        "light blue scrub top with a stethoscope",
        "professional white coat over a tie",
        "teal surgical scrubs with an ID badge",
    ],
    "Software Engineer": [
        "casual hoodie with a laptop bag strap visible",
        "graphic tee under an open flannel shirt",
        "minimalist black crewneck sweater",
        "denim jacket over a plain tee",
        "oversized sweatshirt with glasses",
        "tech-company branded zip hoodie",
    ],
    "College Student": [
        "oversized hoodie and denim jacket",
        "casual graphic tee with a backpack strap",
        "varsity jacket over a plain tee",
        "denim jacket with a beanie",
    ],
    "Teacher": [
        "collared shirt with a sweater vest",
        "button-down shirt with a blazer",
        "smart casual shirt with a tie",
        "cardigan over a collared shirt",
    ],
    "Entrepreneur": [
        "tailored navy blazer over a dress shirt",
        "sharp black suit",
        "structured blazer with a pocket square",
        "fitted suit, confident posture",
    ],
    "Artist": [
        "paint-splattered denim overalls",
        "oversized linen shirt rolled at the sleeves",
        "colorful patchwork jacket",
        "loose smock shirt with paint stains",
    ],
    "Gamer": [
        "oversized graphic hoodie",
        "casual streetwear with a beanie",
        "graphic tee with fingerless gloves",
        "gaming headset around neck, casual hoodie",
        "esports team jersey",
    ],
    "Travel Blogger": [
        "linen shirt with a wide-brim hat",
        "casual henley with a denim jacket",
        "earthy tones cargo jacket",
        "backpacker style utility vest",
    ],
    "Fashion Designer": [
        "avant-garde tailored blazer",
        "statement designer jacket",
        "structured coat with bold accessories",
        "high-fashion monochrome outfit",
    ],
    "Influencer": [
        "trendy graphic tee with fitted jeans",
        "stylish open shirt over a tank",
        "designer streetwear with sunglasses",
        "matching loungewear set",
    ],
    "Musician": [
        "leather jacket over a band tee",
        "vintage denim with layered necklaces",
        "velvet blazer with rings",
        "punk-inspired studded jacket",
    ],
    "Photographer": [
        "utility vest over a plain tee",
        "casual flannel shirt with a camera strap",
        "olive cargo jacket",
        "denim jacket with multiple pockets",
    ],
    "Writer": [
        "cozy oversized sweater",
        "tweed blazer with reading glasses",
        "soft cardigan over a collared shirt",
        "vintage-style shirt with suspenders",
    ],
    "Researcher": [
        "lab coat over a collared shirt",
        "structured blazer with a notebook in hand",
        "white lab coat with safety glasses",
        "professional cardigan with a lanyard",
    ],
    "Life Coach": [
        "soft blazer over a casual shirt",
        "calm pastel-toned cardigan",
        "flowy linen outfit in neutral tones",
        "structured but relaxed blazer",
    ],
    "Chef": [
        "white chef's coat with an apron",
        "double-breasted chef jacket",
        "apron over a casual kitchen uniform",
        "black chef coat with rolled sleeves",
    ],
    "Lawyer": [
        "sharp grey suit",
        "tailored black blazer with a tie",
        "structured suit with a pocket square",
        "professional pinstripe suit",
    ],
    "Nurse": [
        "navy blue scrubs with a stethoscope",
        "patterned scrub top with a badge",
        "light blue medical scrubs",
        "white nursing uniform with a cardigan",
    ],
    "Architect": [
        "structured black blazer with minimalist accessories",
        "monochrome tailored outfit",
        "modern asymmetric jacket",
        "all-black outfit with statement glasses",
    ],
}

DEFAULT_OUTFITS_FEMALE = [
    "fitted black blazer over a silk camisole",
    "olive green utility jacket with gold jewelry",
    "burgundy turtleneck sweater",
    "denim jacket over a graphic tee",
    "tailored navy pantsuit",
    "emerald green wrap dress",
]

DEFAULT_OUTFITS_MALE = [
    "fitted black blazer over a button-down shirt",
    "olive green utility jacket",
    "burgundy crewneck sweater",
    "denim jacket over a graphic tee",
    "tailored navy suit",
    "charcoal wool overcoat",
]

HAIRSTYLES_FEMALE = [
    "long wavy dark hair", "short pixie cut", "sleek straight bob",
    "curly shoulder-length hair", "braided hair pulled back",
    "long hair in a high ponytail", "tousled beach waves",
    "hair in a low bun", "thick natural curls", "asymmetric bob with bangs",
    "long hair with side-swept bangs", "half-up half-down hairstyle",
]

HAIRSTYLES_MALE = [
    "short textured crop", "classic side part", "buzz cut",
    "slicked back undercut", "messy tousled hair", "short curly hair",
    "fade with textured top", "short beard with cropped hair",
    "clean shaven with short hair", "medium length swept-back hair",
]

FEMALE_NAME_EXAMPLES = {
    "Indian": "Priya Sharma, Ananya Reddy, Kavya Iyer, Meera Nair",
    "American": "Emily Carter, Madison Brooks, Olivia Bennett",
    "British": "Charlotte Whitfield, Isla Thompson, Poppy Hargreaves",
    "Japanese": "Yuki Tanaka, Sakura Watanabe, Hina Kobayashi",
    "Brazilian": "Camila Santos, Beatriz Oliveira, Larissa Costa",
    "French": "Camille Dubois, Manon Lefevre, Chloe Moreau",
    "Korean": "Ji-yeon Park, Soo-min Kim, Eun-ji Lee",
    "Australian": "Chloe Mitchell, Ruby Anderson, Matilda Cooper",
    "Canadian": "Hannah MacDonald, Olivia Tremblay",
    "German": "Lena Schmidt, Anna Mueller, Sophie Wagner",
    "Italian": "Giulia Rossi, Francesca Bianchi, Valentina Russo",
    "Spanish": "Lucia Garcia, Carmen Lopez, Paula Martinez",
    "Chinese": "Mei Lin, Xin Yi Chen, Li Wei",
    "Mexican": "Sofia Reyes, Valeria Hernandez, Camila Torres",
    "Nigerian": "Amara Okafor, Chiamaka Eze, Ngozi Adeyemi",
    "South African": "Lerato Mokoena, Thandiwe Dlamini",
    "Swedish": "Astrid Lindqvist, Elin Bergstrom, Saga Nilsson",
    "Dutch": "Emma de Vries, Sanne Bakker, Fleur Jansen",
    "Argentine": "Valentina Fernandez, Martina Lopez",
    "Thai": "Pim Suwanmongkol, Nat Charoensuk",
}

MALE_NAME_EXAMPLES = {
    "Indian": "Arjun Sharma, Rohan Mehta, Vikram Reddy, Aditya Nair",
    "American": "Ethan Carter, Jackson Brooks, Mason Bennett",
    "British": "Oliver Whitfield, James Thompson, Henry Hargreaves",
    "Japanese": "Haruto Tanaka, Sora Watanabe, Ren Kobayashi",
    "Brazilian": "Lucas Santos, Gabriel Oliveira, Matheus Costa",
    "French": "Lucas Dubois, Hugo Lefevre, Louis Moreau",
    "Korean": "Min-jun Park, Joon-ho Kim, Seung-hyun Lee",
    "Australian": "Jack Mitchell, Lucas Anderson, Oliver Cooper",
    "Canadian": "Liam MacDonald, Noah Tremblay",
    "German": "Lukas Schmidt, Max Mueller, Felix Wagner",
    "Italian": "Marco Rossi, Luca Bianchi, Matteo Russo",
    "Spanish": "Pablo Garcia, Javier Lopez, Diego Martinez",
    "Chinese": "Wei Lin, Hao Chen, Jun Wei",
    "Mexican": "Diego Reyes, Carlos Hernandez, Mateo Torres",
    "Nigerian": "Chidi Okafor, Emeka Eze, Tunde Adeyemi",
    "South African": "Sipho Mokoena, Bongani Dlamini",
    "Swedish": "Erik Lindqvist, Oskar Bergstrom, Liam Nilsson",
    "Dutch": "Daan de Vries, Sem Bakker, Lars Jansen",
    "Argentine": "Mateo Fernandez, Joaquin Lopez",
    "Thai": "Somchai Suwanmongkol, Nat Charoensuk",
}


def _get_outfit(category=None, gender="female"):
    outfit_map = CATEGORY_OUTFITS_MALE if gender == "male" else CATEGORY_OUTFITS_FEMALE
    defaults = DEFAULT_OUTFITS_MALE if gender == "male" else DEFAULT_OUTFITS_FEMALE
    if category and category in outfit_map:
        return random.choice(outfit_map[category])
    return random.choice(defaults)


def _get_hair(gender="female"):
    return random.choice(HAIRSTYLES_MALE if gender == "male" else HAIRSTYLES_FEMALE)


def _name_instruction(nationality=None, gender="female"):
    name_pool = MALE_NAME_EXAMPLES if gender == "male" else FEMALE_NAME_EXAMPLES
    pronoun = "his" if gender == "male" else "her"
    if nationality and nationality in name_pool:
        return f"Use an authentic {nationality} first and last name, in the STYLE of: {name_pool[nationality]} (invent a new name, do not reuse these exact ones)."
    return f"Use a first and last name that is authentic and specific to {pronoun} nationality."


def build_character_prompt(category=None, nationality=None, gender=None):
    # FIX: gender now actually controls the prompt instead of being hardcoded to female.
    # If caller doesn't specify, pick randomly here as a safety net — but gemini_service.py
    # should always pass an explicit gender so it can force-set it on the returned data too.
    if gender not in ("male", "female"):
        gender = random.choice(["male", "female"])

    gender_word = "man" if gender == "male" else "woman"
    pronoun = "his" if gender == "male" else "her"

    cat = f'"{category}"' if category else f"one of: {', '.join(CATEGORIES)}"
    nat = f'"{nationality}"' if nationality else f"one of: {', '.join(NATIONALITIES)}"
    name_rule = _name_instruction(nationality, gender)
    outfit = _get_outfit(category, gender)
    hair = _get_hair(gender)

    return f"""Create a {gender_word} AI character. Category: {cat}. Nationality: {nat}.

NAME RULE: {name_rule}

Return ONLY this JSON, no extra text:
{{"name":"string","age":25,"gender":"{gender}","nationality":"string","occupation":"string","category":"string","personality":["trait1","trait2","trait3"],"hobbies":["h1","h2","h3"],"interests":["i1","i2","i3"],"communication_style":"one sentence","interaction_style":"one sentence","emotional_traits":["e1","e2","e3"],"description":"two sentences about {pronoun}","backstory":"two sentences about {pronoun} past","greeting":"{pronoun} opening message","system_prompt":"You are [name], [2 sentence description of how to roleplay this character]","avatar_prompt":"photorealistic portrait of a [age]-year-old [nationality] {gender_word}, {hair}, wearing {outfit}, professional lighting, setting appropriate to {pronoun} occupation as {category or 'their profession'}"}}"""


def build_batch_prompt(count, category=None, nationality=None, gender=None):
    # NOTE: not currently called anywhere in gemini_service.py (batch generation loops
    # build_character_prompt one at a time instead) — fixed here anyway for consistency
    # in case it gets wired up later.
    if gender == "male":
        gender_word, plural_word = "man", "men"
    elif gender == "female":
        gender_word, plural_word = "woman", "women"
    else:
        gender_word, plural_word = "person", "people (mix of men and women)"

    cat = f'"{category}"' if category else f"varied from: {', '.join(CATEGORIES)}"
    nat = f'"{nationality}"' if nationality else f"varied from: {', '.join(NATIONALITIES)}"
    name_rule = _name_instruction(nationality, gender or "female")

    return f"""Create {count} {plural_word} AI characters. Categories: {cat}. Nationalities: {nat}.

NAME RULE: {name_rule} Each character must have a DIFFERENT name, no repeats.

OUTFIT RULE: Each character's outfit must MATCH their occupation/category realistically - a Fitness Trainer wears athletic wear, a Doctor wears a lab coat or scrubs, a Software Engineer wears casual hoodies/tees, an Entrepreneur wears tailored blazers/suits, an Artist wears paint-splattered or bohemian clothes, a Chef wears a chef's coat, a Lawyer wears a sharp suit, a Nurse wears scrubs. Do NOT default to generic outfits regardless of category. Each character must also wear a DIFFERENT specific color/style even within the same category. Vary hairstyles too.

Return ONLY a JSON array, no extra text:
[{{"name":"string","age":25,"gender":"male or female","nationality":"string","occupation":"string","category":"string","personality":["t1","t2","t3"],"hobbies":["h1","h2","h3"],"interests":["i1","i2","i3"],"communication_style":"one sentence","interaction_style":"one sentence","emotional_traits":["e1","e2","e3"],"description":"two sentences","backstory":"two sentences","greeting":"opening message","system_prompt":"You are [name], [2 sentences]","avatar_prompt":"photorealistic portrait of [age]-year-old [nationality] {gender_word}, [specific hairstyle], wearing [outfit that matches their exact occupation], [setting appropriate to their job], professional lighting"}}]"""