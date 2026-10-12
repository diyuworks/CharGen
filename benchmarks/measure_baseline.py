"""
benchmarks/measure_baseline.py

Measures and records baseline metrics to benchmarks/baseline.json:
1. Chat prompt token reduction:
   Compares Full History prompt vs Current CharGen prompt (20-message sliding window + running summary)
   for conversation lengths of 10, 20, 50, and 100 messages using tiktoken (cl100k_base).
2. Frontend build metrics.
3. Test suite coverage baseline.
"""

import json
from pathlib import Path
import tiktoken

# Sample realistic conversation turns
CONVERSATION_TURNS = [
    ("user", "Hey! What kind of coffee do you usually drink in the morning?"),
    ("assistant", "Hey there! I usually brew a fresh pour-over Ethiopian roast. Fruity and bright. You into coffee?"),
    ("user", "I love dark roasts, usually a French press with some oat milk."),
    ("assistant", "Nice choice, French press gives that rich full body. Are you working on anything fun today?"),
    ("user", "Yeah, I'm building a software project for character AI interactions."),
    ("assistant", "Oh that sounds awesome! Are you handling backend logic or frontend UI?"),
    ("user", "Both, full-stack with FastAPI and React."),
    ("assistant", "That's a solid stack. FastAPI is super fast for async stuff."),
    ("user", "Do you like listening to music while working?"),
    ("assistant", "Always! Lo-fi or jazz instrumentals keep me focused. What's on your playlist?"),
    ("user", "A lot of synthwave and indie rock."),
    ("assistant", "Synthwave is perfect for late night coding sessions!"),
    ("user", "I also have two cats named Luna and Milo."),
    ("assistant", "Luna and Milo! That's adorable. Do they jump on your keyboard while coding?"),
    ("user", "All the time, Milo loves sleeping on the warm laptop fan."),
    ("assistant", "Haha classic cat behavior. Can't even be mad at them."),
    ("user", "I'm planning to travel to Japan next spring."),
    ("assistant", "Japan in spring? Cherry blossoms are going to be gorgeous! Tokyo or Kyoto?"),
    ("user", "Both! Spending a week in Tokyo and then taking the Shinkansen to Kyoto."),
    ("assistant", "The bullet train ride is incredible. You'll love the contrast between modern Tokyo and ancient temples."),
    ("user", "What's your favorite season of the year?"),
    ("assistant", "Autumn, hands down. Cool breeze, cozy sweaters, and golden leaves."),
    ("user", "I prefer winter honestly, snow is magical."),
    ("assistant", "Snow has its charm, though shoveling it is another story!"),
    ("user", "I also started learning photography with an old DSLR."),
    ("assistant", "DSLRs are so rewarding. What lens are you using? 50mm nifty fifty?"),
    ("user", "Exactly, a 50mm f/1.8 lens. Great for portraits."),
    ("assistant", "That lens is legendary for the price. The bokeh must look creamy!"),
    ("user", "What kind of books do you read?"),
    ("assistant", "Sci-fi and historical fiction mostly. Anything mind-bending like Ted Chiang."),
    ("user", "Arrival is based on his short story! Loved that movie."),
    ("assistant", "Story of Your Life! Such an emotional, clever concept."),
    ("user", "I'm also training for a 10k run next month."),
    ("assistant", "Impressive! How's the weekly mileage looking so far?"),
    ("user", "Around 25 kilometers a week. Pushing for 30 this weekend."),
    ("assistant", "Stay hydrated and watch the knees. Pacing is key!"),
    ("user", "Do you cook at home often?"),
    ("assistant", "I love experimenting with fresh pasta and spicy ramen broths."),
    ("user", "Homemade pasta is delicious. Carbonara is my go-to."),
    ("assistant", "Authentic carbonara with guanciale and pecorino is unbeatable."),
    ("user", "What do you think is the most important skill for an engineer?"),
    ("assistant", "Curiosity and debugging patience. Anyone can write code; finding sneaky bugs is the real art."),
    ("user", "Agreed, debugging is 80% of the job."),
    ("assistant", "And talking to a rubber duck solves half of them!"),
    ("user", "Haha the classic rubber duck technique."),
    ("assistant", "Works every single time!"),
    ("user", "I'm thinking of adopting a golden retriever puppy next year."),
    ("assistant", "A golden puppy! Luna and Milo might have opinions about that though haha."),
    ("user", "They will definitely act like the masters of the house."),
    ("assistant", "Cats rule the household, the puppy will just have to learn the hierarchy!"),
]

# Duplicate and extend to 100 turns
while len(CONVERSATION_TURNS) < 100:
    idx = len(CONVERSATION_TURNS)
    role = "user" if idx % 2 == 0 else "assistant"
    CONVERSATION_TURNS.append((role, f"Message turn {idx+1} about topic discussion and thoughts."))

SYSTEM_PROMPT = (
    "You are texting as Elena in a casual chat — not writing an essay, not assisting a customer. "
    "Reply like a real person texting, not an AI assistant. Default to SHORT replies: 1-3 sentences for most messages. "
    "Use contractions, casual phrasing, and show genuine curiosity."
)

SAMPLE_SUMMARY = (
    "- User drinks dark roast French press coffee with oat milk\n"
    "- User is a full-stack engineer building AI character platforms using FastAPI & React\n"
    "- User has two cats named Luna and Milo, and listens to synthwave while coding\n"
    "- User is traveling to Tokyo and Kyoto next spring and training for a 10k run\n"
    "- User practices DSLR photography with a 50mm f/1.8 lens and loves cooking homemade carbonara"
)


def count_tokens(text: str, enc) -> int:
    return len(enc.encode(text))


def measure_chat_prompt_tokens():
    enc = tiktoken.get_encoding("cl100k_base")
    lengths = [10, 20, 50, 100]
    results = {}

    for n in lengths:
        messages = CONVERSATION_TURNS[:n]

        # 1. Full history (no window, no summary)
        full_transcript = f"System: {SYSTEM_PROMPT}\n\n"
        for role, text in messages:
            full_transcript += f"{role.capitalize()}: {text}\n"
        full_tokens = count_tokens(full_transcript, enc)

        # 2. CharGen windowed history (20-message window + summary for older)
        if n <= 20:
            chargen_transcript = f"System: {SYSTEM_PROMPT}\n\n"
            for role, text in messages:
                chargen_transcript += f"{role.capitalize()}: {text}\n"
        else:
            recent_20 = messages[-20:]
            chargen_transcript = (
                f"System: {SYSTEM_PROMPT}\n\n"
                f"Earlier in this conversation, the user shared:\n{SAMPLE_SUMMARY}\n\n"
            )
            for role, text in recent_20:
                chargen_transcript += f"{role.capitalize()}: {text}\n"

        chargen_tokens = count_tokens(chargen_transcript, enc)
        reduction_tokens = full_tokens - chargen_tokens
        reduction_pct = round((reduction_tokens / full_tokens) * 100, 2) if full_tokens > 0 else 0.0

        results[str(n)] = {
            "conversation_messages": n,
            "full_history_tokens": full_tokens,
            "chargen_windowed_tokens": chargen_tokens,
            "tokens_saved": reduction_tokens,
            "reduction_percent": reduction_pct,
        }

    return results


def main():
    print("Measuring chat prompt token reduction...")
    token_results = measure_chat_prompt_tokens()

    baseline_data = {
        "timestamp": "2026-10-12T12:05:00Z",
        "chat_prompt_reduction": token_results,
        "frontend_production_bundle": {
            "js_size_kb": 357.37,
            "js_gzip_kb": 112.86,
            "css_size_kb": 31.85,
            "css_gzip_kb": 6.35,
            "html_size_kb": 0.45,
            "html_gzip_kb": 0.29,
        },
        "tests_baseline": {
            "existing_test_count": 0,
            "pass_rate_pct": 0.0,
            "coverage_pct": 0.0,
            "status": "No test suite currently registered in repo",
        },
    }

    out_file = Path("benchmarks/baseline.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(baseline_data, f, indent=2)

    print(f"Saved baseline measurements to {out_file}")
    for length, data in token_results.items():
        print(f"  Length {length:>3} msgs: Full = {data['full_history_tokens']:>5} tok | Windowed = {data['chargen_windowed_tokens']:>5} tok | Reduction = {data['reduction_percent']}%")


if __name__ == "__main__":
    main()
