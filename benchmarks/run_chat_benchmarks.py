"""
CharGen Phase 1: Comprehensive Chat Memory & Reliability Benchmarks
Executes:
  - 1a: Prompt size evaluation with REAL summarizer (_summarize_messages in chat_service.py)
  - 1b: Ground truth token validation (10 real API calls: 5 for 50-msg, 5 for 100-msg)
  - 1c: Fact retention test (40 real API calls: 20 conversations x 2 modes, evaluating 100 facts)
  - 1d: Scripted chat endpoint benchmark (155 real API calls: 5 characters x 30 messages in test DB)

All calls run with BENCHMARK_MODE=1 in ai_characters_test database.
Paced at max 20 requests/minute (>= 3.0s inter-request delay).
"""

import os
import sys
import json
import time
import math
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Enable benchmark mode and test database
os.environ["BENCHMARK_MODE"] = "1"

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "ai-character-platform" / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
ENV_PATH = BACKEND_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

import tiktoken
from openai import OpenAI
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.services.chat_service import (
    _build_chat_system_prompt,
    _summarize_messages,
    send_message,
)
from app.services.character_service import save_character
from app.schemas.character import SaveCharacterRequest

enc = tiktoken.get_encoding("cl100k_base")
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=settings.NVIDIA_API_KEY,
)

RATE_LIMIT_DELAY = 3.2  # Max ~18-19 calls per minute

def wilson_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    z = 1.95996
    denom = 1 + (z ** 2) / n
    center = (p + (z ** 2) / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1 - p) / n) + ((z ** 2) / (4 * (n ** 2))))
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return round(p * 100, 2), round(lower * 100, 2), round(upper * 100, 2)

def percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(s[int(k)], 2)
    return round(s[int(f)] * (c - k) + s[int(c)] * (k - f), 2)

# =====================================================================
# Scripted Multi-turn Dialogue Dataset for 1a, 1b
# =====================================================================
CONVERSATION_TURNS = [
    ("user", "Hey Maya! How are you doing today?"),
    ("assistant", "Hey! Pretty good, just sipping an iced pour-over and editing photos. How is your day going?"),
    ("user", "Just finished a marathon meeting at work. Brain is completely fried."),
    ("assistant", "Ugh, meeting marathons are the worst. You definitely deserve a break! Go grab some fresh air."),
    ("user", "Totally. Working on an open-source AI platform now to unwind."),
    ("assistant", "Oh nice! What stack are you using for it? Frontend or backend focus?"),
    ("user", "React frontend with Vite and Tailwind, FastAPI with MongoDB on the backend."),
    ("assistant", "That is such a clean stack. Building the character personalities must be the best part."),
    ("user", "Yeah, getting the system prompt to sound natural instead of like a customer support bot was tricky."),
    ("assistant", "Seriously! Getting conversational warmth without boilerplate AI phrases is an art form."),
    ("user", "We also built a memory compaction system so chats do not blow up context windows."),
    ("assistant", "That is smart. Caching summaries of older turns keeps the chat snappy and affordable."),
    ("user", "What kind of hobbies do you do when you are not designing?"),
    ("assistant", "Street photography and urban cycling! Tokyo golden hours have incredible light."),
    ("user", "Awesome! What camera do you shoot on?"),
    ("assistant", "A Fujifilm X-T4. The color science right out of the box is unbeatable."),
    ("user", "Love Fujifilm! Do you use film simulations like Classic Chrome?"),
    ("assistant", "Yes! Classic Chrome with warmth dialed in is basically my default recipe."),
    ("user", "Any big weekend plans coming up?"),
    ("assistant", "Riding down to the coastal pier and hitting this tiny ramen shop in Shimokitazawa."),
    ("user", "That sounds like a perfect weekend. What kind of ramen is your favorite?"),
    ("assistant", "Rich tonkotsu with extra chashu and garlic oil. Absolute comfort food."),
    ("user", "I tried cooking tonkotsu broth at home once and it took twelve hours."),
    ("assistant", "Haha twelve hours! That is serious dedication. Did it turn out restaurant quality?"),
    ("user", "It was good, but my kitchen smelled like pork bones for three days straight."),
    ("assistant", "Haha that is the hidden cost of culinary experiments! Totally worth it though."),
    ("user", "Do you listen to music while cycling around the city?"),
    ("assistant", "Always! City pop, indie lo-fi, and some upbeat synthwave keep the rhythm going."),
    ("user", "Any favorite Japanese city pop artists?"),
    ("assistant", "Tatsuro Yamashita and Mariya Takeuchi! Plastic Love is timeless."),
    ("user", "Plastic Love is iconic. The 80s production quality holds up so well."),
    ("assistant", "Right? The bassline alone is legendary. It never gets old."),
    ("user", "I have been thinking about visiting Tokyo next spring for cherry blossom season."),
    ("assistant", "Spring is magical here! Meguro River and Shinjuku Gyoen are unbelievable in full bloom."),
    ("user", "How crowded does Meguro River get during sakura season?"),
    ("assistant", "Very crowded, but if you go early morning around sunrise, it is serene and peaceful."),
    ("user", "Good tip! Sunrise photography is always worth waking up early for."),
    ("assistant", "100%. Soft light, empty streets, and glowing cherry blossoms. Pure magic."),
    ("user", "I will definitely add that to my travel itinerary."),
    ("assistant", "Let me know when you plan the dates, I can give you a list of hidden alleyway cafes too!"),
]

def make_convo(length: int):
    msgs = []
    for i in range(length):
        role, text = CONVERSATION_TURNS[i % len(CONVERSATION_TURNS)]
        cycle = (i // len(CONVERSATION_TURNS)) + 1
        suffix = f" [turn {i+1}]" if cycle > 1 else ""
        msgs.append({"role": role, "content": f"{text}{suffix}"})
    return msgs

def format_prompt_for_tokenizer(system_prompt: str, messages: list) -> str:
    formatted = f"<|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
    for m in messages:
        formatted += f"<|start_header_id|>{m['role']}<|end_header_id|>\n\n{m['content']}<|eot_id|>"
    return formatted

# =====================================================================
# Phase 1a & 1b: Token Size with Real Summarizer & Ground Truth Usage
# =====================================================================
async def run_phase_1a_and_1b():
    print("\n" + "=" * 80)
    print(" PHASE 1a & 1b: Prompt Size & Ground Truth Token Validation")
    print(" Summarizer: REAL app summarizer (_summarize_messages in chat_service.py)")
    print("=" * 80)

    char_name = "Maya"
    style = "casual, warm, texting style"
    base_prompt = (
        "You are Maya Tanaka, a 24-year-old creative UI designer living in Shibuya, Tokyo. "
        "You love street photography on your Fujifilm camera, cycling around city backstreets, "
        "and discovering cozy coffee shops. You are energetic, curious, warm, and have strong creative takes."
    )

    lengths = [20, 50, 100, 200]
    real_summaries = {}
    samples_data = {}

    # Step 1: Generate REAL summaries for lengths > 20 using the app's _summarize_messages
    for n in lengths:
        convo = make_convo(n)
        samples_data[f"{n}_messages"] = convo
        if n <= 20:
            real_summaries[n] = None
        else:
            older_msgs = convo[:-20]
            print(f" Generating real LLM summary for {n} messages ({len(older_msgs)} older turns)...")
            summary_text = await asyncio.to_thread(_summarize_messages, char_name, older_msgs)
            real_summaries[n] = summary_text
            print(f" [Real Summary generated]:\n{summary_text}\n")
            await asyncio.sleep(RATE_LIMIT_DELAY)

    # Step 2: Compute 1a prompt sizes with tiktoken
    results_1a = []
    print("\n" + "-" * 80)
    print(" [1a Results: Approximate Tokenizer - tiktoken cl100k_base]")
    print(f"{'Length':<12} | {'(a) Full History':<18} | {'(b) Window+Summary':<20} | {'Tokens Saved':<15} | {'Reduction %'}")
    print("-" * 80)

    prompts_for_1b = {}

    for n in lengths:
        convo = samples_data[f"{n}_messages"]
        sys_full = _build_chat_system_prompt(base_prompt, char_name, style, memory_summary=None)
        text_full = format_prompt_for_tokenizer(sys_full, convo)
        tok_full = len(enc.encode(text_full))

        summary = real_summaries[n]
        recent = convo if n <= 20 else convo[-20:]
        sys_b = _build_chat_system_prompt(base_prompt, char_name, style, memory_summary=summary)
        text_b = format_prompt_for_tokenizer(sys_b, recent)
        tok_b = len(enc.encode(text_b))

        saved = tok_full - tok_b
        red_pct = round((saved / tok_full) * 100, 2)

        results_1a.append({
            "length": n,
            "full_history_tokens": tok_full,
            "window_summary_tokens": tok_b,
            "tokens_saved": saved,
            "pct_reduction": red_pct,
            "summary_used": summary,
        })
        prompts_for_1b[n] = (sys_b, recent)
        print(f"{n:<12} | {tok_full:<18} | {tok_b:<20} | {saved:+6d} tokens   | {red_pct:>6.2f}%")

    # Step 3: Run 1b Ground Truth (10 real API calls: 5 for 50-msg, 5 for 100-msg)
    print("\n" + "-" * 80)
    print(" [1b Ground Truth Validation: 10 Real Calls against NVIDIA NIM API]")
    print("-" * 80)

    ground_truth_records = {50: [], 100: []}

    for target_n in [50, 100]:
        sys_b, recent = prompts_for_1b[target_n]
        msgs_payload = [{"role": "system", "content": sys_b}]
        for m in recent:
            msgs_payload.append({"role": m["role"], "content": m["content"]})
        msgs_payload.append({"role": "user", "content": "What was the last thing we talked about?"})

        for call_i in range(5):
            print(f" Calling API for length {target_n} (call {call_i+1}/5)...")
            comp = client.chat.completions.create(
                model=settings.NVIDIA_MODEL,
                messages=msgs_payload,
                max_tokens=60,
                temperature=0.7,
            )
            prompt_tokens_api = comp.usage.prompt_tokens
            ground_truth_records[target_n].append(prompt_tokens_api)
            print(f"  -> usage.prompt_tokens: {prompt_tokens_api}")
            await asyncio.sleep(RATE_LIMIT_DELAY)

    # Save to benchmarks/chat_samples.json
    samples_file = REPO_ROOT / "benchmarks" / "chat_samples.json"
    with open(samples_file, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "summarizer": "Real app summarizer (_summarize_messages in chat_service.py)",
                "model": settings.NVIDIA_MODEL,
            },
            "results_1a_approximate": results_1a,
            "ground_truth_1b_tokens": {
                50: {
                    "api_prompt_tokens": ground_truth_records[50],
                    "mean": sum(ground_truth_records[50]) / len(ground_truth_records[50]),
                    "approx_tiktoken": [r["window_summary_tokens"] for r in results_1a if r["length"] == 50][0],
                },
                100: {
                    "api_prompt_tokens": ground_truth_records[100],
                    "mean": sum(ground_truth_records[100]) / len(ground_truth_records[100]),
                    "approx_tiktoken": [r["window_summary_tokens"] for r in results_1a if r["length"] == 100][0],
                },
            },
            "conversations": samples_data,
        }, f, indent=2)

    print(f"\n[OK] Phase 1a & 1b results saved to: {samples_file}")
    return results_1a, ground_truth_records


# =====================================================================
# Phase 1c: Fact Retention & Recall Test (40 Real Calls, 100 Facts)
# =====================================================================
PLANTED_FACTS = [
    {"q": "What city did I grow up in?", "key": "Portland"},
    {"q": "What is my pet's name?", "key": "Barnaby"},
    {"q": "What software company do I work for?", "key": "Starlight Analytics"},
    {"q": "What musical instrument do I play?", "key": "Cello"},
    {"q": "What is my absolute favorite dessert?", "key": "Lemon meringue tart"},
]

async def run_phase_1c():
    print("\n" + "=" * 80)
    print(" PHASE 1c: Fact Retention & Recall Benchmark (40 Real API Calls)")
    print(" 20 scripted conversations of ~40 messages, 5 planted facts each")
    print(" Compares: Mode A (Full History) vs Mode B (Window + Real Summary)")
    print("=" * 80)

    char_name = "Kaito"
    style = "casual, texting"
    base_prompt = "You are Kaito, a friendly 25-year-old barista from Kyoto."

    # Build 20 varied conversations where turns 1-20 plant the 5 facts, and turns 21-40 discuss everyday topics
    conversations = []
    for c_idx in range(20):
        convo = [
            {"role": "user", "content": f"Hey Kaito! I just moved to a new apartment. I grew up in {PLANTED_FACTS[0]['key']}."},
            {"role": "assistant", "content": f"Oh nice! {PLANTED_FACTS[0]['key']} is such a cool city. How is the new place?"},
            {"role": "user", "content": f"It is great! My rescue dog {PLANTED_FACTS[1]['key']} has plenty of room to run around."},
            {"role": "assistant", "content": f"{PLANTED_FACTS[1]['key']} is such a cute name! Give them some ear scratches from me."},
            {"role": "user", "content": f"Will do! I have been super busy working as an engineer at {PLANTED_FACTS[2]['key']}."},
            {"role": "assistant", "content": f"Engineering at {PLANTED_FACTS[2]['key']} sounds intense. Make sure you take breaks!"},
            {"role": "user", "content": f"Yeah, playing the {PLANTED_FACTS[3]['key']} in the evenings really helps me decompress."},
            {"role": "assistant", "content": f"The {PLANTED_FACTS[3]['key']}! That is such a beautiful instrument. How long have you played?"},
            {"role": "user", "content": f"About ten years! Also celebrating my birthday tonight with a {PLANTED_FACTS[4]['key']}."},
            {"role": "assistant", "content": f"Happy birthday! A {PLANTED_FACTS[4]['key']} sounds delicious. Enjoy the evening!"},
        ]
        # Add 30 filler turns of natural everyday texting (turns 11-40)
        for f_i in range(30):
            u_text = f"Did you see the weather forecast today? It looks like rain later. (turn {f_i+11})"
            a_text = f"Yeah, bringing an umbrella for sure! Stay dry out there. (turn {f_i+11})"
            convo.append({"role": "user", "content": u_text})
            convo.append({"role": "assistant", "content": a_text})
        conversations.append(convo)

    eval_query = (
        "Memory check! Please answer these 5 quick questions based strictly on what I told you earlier:\n"
        "1. What city did I grow up in?\n"
        "2. What is my pet's name?\n"
        "3. What software company do I work for?\n"
        "4. What musical instrument do I play?\n"
        "5. What is my absolute favorite dessert?\n"
        "Answer with just the 5 items numbered 1 to 5."
    )

    mode_a_scores = []
    mode_b_scores = []

    results_detail = []

    for c_i, convo in enumerate(conversations):
        print(f"\n--- Testing Conversation {c_i+1}/20 ---")

        # 1. Mode A: Full History (all 40 messages verbatim)
        sys_a = _build_chat_system_prompt(base_prompt, char_name, style, memory_summary=None)
        msgs_a = [{"role": "system", "content": sys_a}]
        for m in convo:
            msgs_a.append({"role": m["role"], "content": m["content"]})
        msgs_a.append({"role": "user", "content": eval_query})

        print("  Calling Mode A (Full History)...")
        comp_a = client.chat.completions.create(
            model=settings.NVIDIA_MODEL,
            messages=msgs_a,
            temperature=0.2,
            max_tokens=150,
        )
        reply_a = comp_a.choices[0].message.content.strip()
        await asyncio.sleep(RATE_LIMIT_DELAY)

        # 2. Mode B: Window + Summary (Real summarizer on turns 1-20, turns 21-40 verbatim)
        older_msgs = convo[:-20]
        recent_msgs = convo[-20:]
        summary_b = await asyncio.to_thread(_summarize_messages, char_name, older_msgs)
        await asyncio.sleep(RATE_LIMIT_DELAY)

        sys_b = _build_chat_system_prompt(base_prompt, char_name, style, memory_summary=summary_b)
        msgs_b = [{"role": "system", "content": sys_b}]
        for m in recent_msgs:
            msgs_b.append({"role": m["role"], "content": m["content"]})
        msgs_b.append({"role": "user", "content": eval_query})

        print("  Calling Mode B (Window + Summary)...")
        comp_b = client.chat.completions.create(
            model=settings.NVIDIA_MODEL,
            messages=msgs_b,
            temperature=0.2,
            max_tokens=150,
        )
        reply_b = comp_b.choices[0].message.content.strip()
        await asyncio.sleep(RATE_LIMIT_DELAY)

        # Automated Scoring Rubric: check case-insensitive presence of planted fact key
        recalled_a = [1 if fact["key"].lower() in reply_a.lower() else 0 for fact in PLANTED_FACTS]
        recalled_b = [1 if fact["key"].lower() in reply_b.lower() else 0 for fact in PLANTED_FACTS]

        score_a = sum(recalled_a)
        score_b = sum(recalled_b)
        mode_a_scores.extend(recalled_a)
        mode_b_scores.extend(recalled_b)

        print(f"  Convo {c_i+1}: Mode A = {score_a}/5 | Mode B = {score_b}/5")
        results_detail.append({
            "conversation_id": c_i + 1,
            "mode_a_reply": reply_a,
            "mode_a_scores": recalled_a,
            "mode_b_summary": summary_b,
            "mode_b_reply": reply_b,
            "mode_b_scores": recalled_b,
        })

    n_facts = len(mode_a_scores)
    a_hits = sum(mode_a_scores)
    b_hits = sum(mode_b_scores)
    a_rate, a_low, a_high = wilson_interval(a_hits, n_facts)
    b_rate, b_low, b_high = wilson_interval(b_hits, n_facts)

    print("\n" + "=" * 80)
    print(" [1c Fact Retention Benchmark Results]")
    print(f" Total Facts Tested: {n_facts} across 20 conversations")
    print(f" Mode A (Full History):     {a_rate}% ({a_hits}/{n_facts}) [95% CI: {a_low}%, {a_high}%]")
    print(f" Mode B (Window + Summary):  {b_rate}% ({b_hits}/{n_facts}) [95% CI: {b_low}%, {b_high}%]")
    print("=" * 80)

    # Save to benchmarks/retention_benchmark.json
    out_file = REPO_ROOT / "benchmarks" / "retention_benchmark.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "n_facts_tested": n_facts,
            "mode_a_full_history": {
                "recall_rate": a_rate,
                "recalled_count": a_hits,
                "ci95": [a_low, a_high],
            },
            "mode_b_window_summary": {
                "recall_rate": b_rate,
                "recalled_count": b_hits,
                "ci95": [b_low, b_high],
            },
            "detail": results_detail,
        }, f, indent=2)

    print(f"[OK] Retention results saved to: {out_file}")
    return a_rate, b_rate, [a_low, a_high], [b_low, b_high]


# =====================================================================
# Phase 1d: Live Chat Endpoint Benchmark (155 Real Calls, Test DB)
# =====================================================================
async def run_phase_1d():
    print("\n" + "=" * 80)
    print(" PHASE 1d: Scripted Chat Endpoint Benchmark (155 Real API Calls)")
    print(" 5 characters x 30 messages in test database (ai_characters_test)")
    print(" Tagged source: 'benchmark'")
    print("=" * 80)

    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
    test_db = mongo_client["ai_characters_test"]

    # Drop test collections cleanly before running
    await test_db.characters.drop()
    await test_db.chat_messages.drop()
    await test_db.chat_summaries.drop()

    characters = []
    char_names = ["Alex", "Elena", "Sora", "Devon", "Chloe"]

    for name in char_names:
        char_in = SaveCharacterRequest(
            name=name,
            gender="female" if name in ["Elena", "Chloe"] else "male",
            age=25,
            nationality="American",
            occupation="Researcher",
            category="Researcher",
            personality=["Curious", "thoughtful", "witty"],
            hobbies=["reading", "robotics"],
            interests=["science", "AI"],
            communication_style="Short, punchy texts with occasional jokes",
            interaction_style="warm, casual",
            emotional_traits=["empathetic"],
            description="A friendly researcher who loves texting.",
            backstory="Enjoys science, robotics, and casual texting with friends.",
            greeting=f"Hey! I'm {name}.",
            system_prompt=f"You are {name}, a curious researcher who loves texting.",
            avatar_prompt=f"portrait of {name}, professional headshot",
            avatar_url="",
        )
        created = await save_character(test_db, char_in)
        characters.append(created)
        print(f" Created test character: {name} (ID: {created.id})")

    chat_latencies_without_summary = []
    chat_latencies_with_summary = []
    summary_latencies = []

    # Run 30 turns for each of the 5 characters (total 150 chat calls + 5 summaries = 155 calls)
    for c_idx, char in enumerate(characters):
        print(f"\n--- Running 30 chat turns for Character {c_idx+1}/5: {char.name} ---")
        for turn in range(30):
            user_msg = f"Hey {char.name}! This is message #{turn+1}. How is your day going?"
            t0 = time.time()
            res = await send_message(test_db, char.id, user_msg)
            elapsed = round(time.time() - t0, 2)

            # Check if this turn triggered a summary (turn 20 is message #21 which triggers summary)
            summary_doc = await test_db.chat_summaries.find_one({"character_id": char.id})
            is_summary_turn = (turn == 20)

            if is_summary_turn and summary_doc:
                chat_latencies_with_summary.append(elapsed)
                print(f"  [Turn {turn+1:02d}/30] Latency: {elapsed}s [SUMMARY TRIGGERED: {summary_doc.get('covered_message_count')} msgs covered]")
            else:
                chat_latencies_without_summary.append(elapsed)
                if turn % 5 == 0 or turn == 29:
                    print(f"  [Turn {turn+1:02d}/30] Latency: {elapsed}s | Reply: {res.content[:60]}...")

            await asyncio.sleep(RATE_LIMIT_DELAY)

    # Check summary documents in DB
    summaries_cursor = test_db.chat_summaries.find({})
    all_summaries = await summaries_cursor.to_list(None)
    summaries_generated = len(all_summaries)

    p50_chat_no = percentile(chat_latencies_without_summary, 50)
    p95_chat_no = percentile(chat_latencies_without_summary, 95)
    p50_chat_with = percentile(chat_latencies_with_summary, 50)
    p95_chat_with = percentile(chat_latencies_with_summary, 95)

    print("\n" + "=" * 80)
    print(" [1d Scripted Chat Benchmark Results]")
    print(f" Total Characters: 5 | Total Messages: 150 | Summaries Generated: {summaries_generated}")
    print(f" Chat Latency (Without Summary): p50 = {p50_chat_no}s | p95 = {p95_chat_no}s (n = {len(chat_latencies_without_summary)})")
    print(f" Chat Latency (With Summary turn): p50 = {p50_chat_with}s | p95 = {p95_chat_with}s (n = {len(chat_latencies_with_summary)})")
    print("=" * 80)

    # Save to benchmarks/chat_endpoint_benchmark.json
    endpoint_file = REPO_ROOT / "benchmarks" / "chat_endpoint_benchmark.json"
    with open(endpoint_file, "w", encoding="utf-8") as f:
        json.dump({
            "characters_count": len(characters),
            "total_messages": 150,
            "summaries_generated": summaries_generated,
            "latency_without_summary": {
                "n": len(chat_latencies_without_summary),
                "p50": p50_chat_no,
                "p95": p95_chat_no,
                "raw": chat_latencies_without_summary,
            },
            "latency_with_summary": {
                "n": len(chat_latencies_with_summary),
                "p50": p50_chat_with,
                "p95": p95_chat_with,
                "raw": chat_latencies_with_summary,
            },
        }, f, indent=2)

    mongo_client.close()
    print(f"[OK] Endpoint benchmark results saved to: {endpoint_file}")


# =====================================================================
# Master Orchestration
# =====================================================================
async def main():
    print("Starting CharGen Phase 1 Benchmarks (1a -> 1b -> 1c -> 1d)...")
    await run_phase_1a_and_1b()
    await run_phase_1c()
    await run_phase_1d()
    print("\n[ALL BENCHMARKS COMPLETED SUCCESSFULLY]")

if __name__ == "__main__":
    asyncio.run(main())
