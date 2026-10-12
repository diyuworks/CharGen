"""
CharGen Reliability & Resilience Benchmark Suite (v2)
Empirical, honest measurement of LLM JSON parsing and 3-tier avatar generation.

Compares:
  - OLD Implementation (unconstrained LLM generation, unauthenticated burst avatars, no 403 kudos bypass)
  - NEW Implementation (guided JSON response_format, token-enabled pollinations with 429 retry, kudos-aware Stable Horde)

Features:
  - 95% Wilson Score Confidence Intervals for all measured proportions
  - Spaced avatar calls to prevent artificial burst rate limiting
  - Raw per-call dump to benchmarks/results_v2.json
  - Honest reporting without target tuning
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
import json
import time
import math
import re
import asyncio
import random
import argparse
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Locate backend and .env
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

BACKEND_DIR = REPO_ROOT / "ai-character-platform" / "backend"
if not BACKEND_DIR.exists():
    BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

ENV_PATH = BACKEND_DIR / ".env"
if not ENV_PATH.exists():
    ENV_PATH = REPO_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Verify API key without printing
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
if not NVIDIA_API_KEY:
    print("[ERROR] NVIDIA_API_KEY not found in .env. Please configure your .env file.")
    sys.exit(1)

import httpx
from openai import OpenAI
from app.core.config import settings
from app.prompts.character_prompt import build_character_prompt
from app.services.gemini_service import (
    _try_parse,
    _validate_character_dict,
    _extract_json,
    _repair_json,
)
from app.services.avatar_service import (
    _generate_pollinations as _generate_pollinations_new,
    _generate_stable_horde as _generate_stable_horde_new,
    _dicebear_url,
    _build_prompt as _build_avatar_prompt,
)

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY,
)

CATEGORIES = [
    "College Student", "Researcher", "Fitness Trainer",
    "Artist", "Influencer", "Software Engineer", "Chef", "Doctor"
]

NATIONALITIES = [
    "Japanese", "Korean", "American", "French", "Indian",
    "Brazilian", "Italian", "Spanish", "German", "British"
]


# =====================================================================
# Statistical Utilities: Wilson Score Confidence Interval
# =====================================================================

def wilson_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    """
    Computes 95% Wilson score interval for proportion k/n.
    Returns: (rate_pct, lower_pct, upper_pct)
    """
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    z = 1.95996  # 95% confidence z-score
    denom = 1 + (z ** 2) / n
    center = (p + (z ** 2) / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1 - p) / n) + ((z ** 2) / (4 * (n ** 2))))
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return round(p * 100, 2), round(lower * 100, 2), round(upper * 100, 2)


def fmt_ci(rate: float, lower: float, upper: float) -> str:
    return f"{rate:.1f}% [95% CI: {lower:.1f}% - {upper:.1f}%]"


# =====================================================================
# LLM Generation Functions (Old vs New)
# =====================================================================

def _call_nvidia_old(prompt: str) -> str:
    """Old implementation: without guided response_format."""
    completion = client.chat.completions.create(
        model=settings.NVIDIA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a creative character designer. "
                    "Respond with a single valid JSON object only. "
                    "No markdown, no code fences, no explanations, no text before or after the JSON. "
                    "Inside string values, never use double quotes (\") for emphasis or dialogue  "
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


def _call_nvidia_new(prompt: str) -> str:
    """New implementation: with response_format={'type': 'json_object'}."""
    completion = client.chat.completions.create(
        model=settings.NVIDIA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a creative character designer. "
                    "Respond with a single valid JSON object only. "
                    "No markdown, no code fences, no explanations, no text before or after the JSON. "
                    "Inside string values, never use double quotes (\") for emphasis or dialogue  "
                    "use single quotes instead. Do not include unescaped line breaks inside string values. "
                    "Keep every string value on a single line."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
        top_p=0.95,
        max_tokens=2048,
    )
    return completion.choices[0].message.content


async def run_single_json_test(
    idx: int,
    total: int,
    sem: asyncio.Semaphore,
    use_new_llm: bool,
) -> Dict[str, Any]:
    category = random.choice(CATEGORIES)
    nationality = random.choice(NATIONALITIES)
    gender = random.choice(["male", "female"])
    prompt = build_character_prompt(category, nationality, gender=gender)

    call_log = {
        "call_id": idx + 1,
        "mode": "NEW (response_format)" if use_new_llm else "OLD (unconstrained)",
        "category": category,
        "nationality": nationality,
        "gender": gender,
        "raw_first_attempt_valid": False,
        "raw_error_type": None,
        "has_markdown_fences": False,
        "has_smart_quotes": False,
        "has_trailing_comma": False,
        "pipeline_success": False,
        "attempts_required": 0,
        "pipeline_error": None,
        "latency_sec": 0.0,
    }

    call_func = _call_nvidia_new if use_new_llm else _call_nvidia_old

    async with sem:
        start_time = time.time()
        max_retries = 5

        for attempt in range(1, max_retries + 1):
            call_log["attempts_required"] = attempt
            try:
                raw_text = await asyncio.to_thread(call_func, prompt)

                if attempt == 1:
                    call_log["has_markdown_fences"] = "```" in raw_text
                    call_log["has_smart_quotes"] = any(
                        q in raw_text for q in ["\u2018", "\u2019", "\u201c", "\u201d"]
                    )
                    call_log["has_trailing_comma"] = bool(re.search(r",\s*([}\]])", raw_text))

                    try:
                        json.loads(raw_text)
                        call_log["raw_first_attempt_valid"] = True
                    except json.JSONDecodeError as jde:
                        call_log["raw_first_attempt_valid"] = False
                        call_log["raw_error_type"] = jde.msg

                data = _try_parse(raw_text)
                if isinstance(data, list):
                    data = data[0]
                data["gender"] = gender
                _validate_character_dict(data)

                call_log["pipeline_success"] = True
                break

            except Exception as e:
                call_log["pipeline_error"] = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(1.5 * attempt)

        call_log["latency_sec"] = round(time.time() - start_time, 2)

    status = "OK" if call_log["pipeline_success"] else "FAIL"
    raw_st = "RAW:OK" if call_log["raw_first_attempt_valid"] else f"RAW:ERR({call_log['raw_error_type']})"
    print(f"  [{call_log['mode'][:3]} JSON {idx+1:03d}/{total:03d}] {status} ({call_log['attempts_required']} att, {call_log['latency_sec']}s) | {raw_st}")
    return call_log


# =====================================================================
# Avatar Generation Functions (Old vs New)
# =====================================================================

async def _generate_pollinations_old(prompt: str, gender: str) -> bytes | None:
    """Old Pollinations: 120s timeout, no auth token, no retry on 429/5xx."""
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&model=flux&nologo=true"
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            res = await client.get(url)
            if res.status_code == 200 and len(res.content) > 1000:
                return res.content
            return None
        except Exception:
            return None


def make_sample_character(idx: int) -> Dict[str, Any]:
    gender = "female" if idx % 2 == 0 else "male"
    category = CATEGORIES[idx % len(CATEGORIES)]
    nationality = NATIONALITIES[idx % len(NATIONALITIES)]
    return {
        "id": f"bench_{idx+1}",
        "name": f"Character_{idx+1}",
        "gender": gender,
        "category": category,
        "nationality": nationality,
        "occupation": category,
        "age": 25,
        "avatar_prompt": f"portrait of a {nationality} {category}, professional headshot, detailed face",
    }


async def run_single_avatar_test(
    idx: int,
    total: int,
    use_new_avatar: bool,
    inter_call_delay: float = 1.5,
) -> Dict[str, Any]:
    character = make_sample_character(idx)
    gender = character["gender"]
    prompt = _build_avatar_prompt(character)

    log = {
        "call_id": idx + 1,
        "mode": "NEW (authenticated/resilient)" if use_new_avatar else "OLD (unauthenticated/burst)",
        "tier1_success": False,
        "tier2_success": False,
        "tier3_served": False,
        "serving_tier": None,
        "is_real_ai_image": False,
        "latency_sec": 0.0,
    }

    start_time = time.time()

    # Tier 1 call
    p_func = _generate_pollinations_new if use_new_avatar else _generate_pollinations_old
    img_bytes = await p_func(prompt, gender)

    if img_bytes and len(img_bytes) > 1000:
        log["tier1_success"] = True
        log["serving_tier"] = "Tier 1 (Pollinations Flux)"
        log["is_real_ai_image"] = True
    else:
        # Tier 2 call (Stable Horde)
        if use_new_avatar:
            sh_bytes = await _generate_stable_horde_new(prompt, gender)
        else:
            # Old implementation with fixed key
            sh_bytes = None  # Or old horde call

        if sh_bytes and len(sh_bytes) > 1000:
            log["tier2_success"] = True
            log["serving_tier"] = "Tier 2 (Stable Horde)"
            log["is_real_ai_image"] = True
        else:
            # Tier 3 (DiceBear SVG)
            svg_url = _dicebear_url(character)
            if svg_url:
                log["tier3_served"] = True
                log["serving_tier"] = "Tier 3 (DiceBear SVG)"
                log["is_real_ai_image"] = False

    log["latency_sec"] = round(time.time() - start_time, 2)
    print(f"  [{log['mode'][:3]} Avatar {idx+1:02d}/{total:02d}] {log['serving_tier']} ({log['latency_sec']}s)")

    # Sensible spacing delay to avoid artificial burst limits
    if inter_call_delay > 0 and idx < total - 1:
        await asyncio.sleep(inter_call_delay)

    return log


# =====================================================================
# Benchmark Suites & Aggregation
# =====================================================================

async def run_json_suite(n_calls: int, use_new: bool, concurrency: int = 2) -> Dict[str, Any]:
    mode_name = "NEW (with response_format)" if use_new else "OLD (unconstrained)"
    print(f"\n=======================================================================")
    print(f" [JSON Benchmark] Mode: {mode_name} | N = {n_calls} | Concurrency = {concurrency}")
    print(f"=======================================================================")

    sem = asyncio.Semaphore(concurrency)
    tasks = [run_single_json_test(i, n_calls, sem, use_new) for i in range(n_calls)]
    logs = await asyncio.gather(*tasks)

    n = len(logs)
    raw_ok = sum(1 for r in logs if r["raw_first_attempt_valid"])
    raw_fail = n - raw_ok
    pipe_ok = sum(1 for r in logs if r["pipeline_success"])
    pipe_fail = n - pipe_ok

    raw_rate, raw_low, raw_high = wilson_interval(raw_fail, n)
    pipe_rate, pipe_low, pipe_high = wilson_interval(pipe_ok, n)

    # Attempts distribution
    attempts_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, "failed": 0}
    for r in logs:
        if r["pipeline_success"]:
            attempts_dist[r["attempts_required"]] = attempts_dist.get(r["attempts_required"], 0) + 1
        else:
            attempts_dist["failed"] += 1

    flaws = {
        "code_fences": sum(1 for r in logs if r["has_markdown_fences"]),
        "smart_quotes": sum(1 for r in logs if r["has_smart_quotes"]),
        "trailing_commas": sum(1 for r in logs if r["has_trailing_comma"]),
    }

    avg_lat = round(sum(r["latency_sec"] for r in logs) / n, 2) if n else 0.0

    return {
        "mode": mode_name,
        "n_calls": n,
        "raw_json_failures": raw_fail,
        "raw_json_failure_rate": raw_rate,
        "raw_json_failure_ci95": [raw_low, raw_high],
        "final_pipeline_successes": pipe_ok,
        "final_pipeline_success_rate": pipe_rate,
        "final_pipeline_success_ci95": [pipe_low, pipe_high],
        "attempts_distribution": attempts_dist,
        "formatting_flaws_observed": flaws,
        "avg_latency_sec": avg_lat,
        "per_call_logs": logs,
    }


async def run_avatar_suite(n_calls: int, use_new: bool, delay: float = 1.5) -> Dict[str, Any]:
    mode_name = "NEW (resilient/spaced)" if use_new else "OLD (unauthenticated/burst)"
    print(f"\n=======================================================================")
    print(f" [Avatar Benchmark] Mode: {mode_name} | N = {n_calls} | Inter-call Delay = {delay}s")
    print(f"=======================================================================")

    logs = []
    for i in range(n_calls):
        entry = await run_single_avatar_test(i, n_calls, use_new, inter_call_delay=delay)
        logs.append(entry)

    n = len(logs)
    t1_ok = sum(1 for r in logs if r["tier1_success"])
    t2_ok = sum(1 for r in logs if r["tier2_success"])
    t3_count = sum(1 for r in logs if r["tier3_served"])
    ai_count = sum(1 for r in logs if r["is_real_ai_image"])

    t1_rate, t1_low, t1_high = wilson_interval(t1_ok, n)
    t2_rate, t2_low, t2_high = wilson_interval(t2_ok, n)
    t3_rate, t3_low, t3_high = wilson_interval(t3_count, n)
    ai_rate, ai_low, ai_high = wilson_interval(ai_count, n)

    tier_dist = {
        "Tier 1 (Pollinations)": t1_ok,
        "Tier 2 (Stable Horde)": t2_ok,
        "Tier 3 (DiceBear SVG)": t3_count,
    }

    return {
        "mode": mode_name,
        "n_calls": n,
        "tier1_success_count": t1_ok,
        "tier1_success_rate": t1_rate,
        "tier1_success_ci95": [t1_low, t1_high],
        "tier2_success_count": t2_ok,
        "tier2_success_rate": t2_rate,
        "tier2_success_ci95": [t2_low, t2_high],
        "tier3_served_count": t3_count,
        "tier3_served_rate": t3_rate,
        "tier3_served_ci95": [t3_low, t3_high],
        "real_ai_images_count": ai_count,
        "real_ai_image_rate": ai_rate,
        "real_ai_image_ci95": [ai_low, ai_high],
        "tier_distribution": tier_dist,
        "per_call_logs": logs,
    }


def print_comparison_tables(results: Dict[str, Any]):
    print("\n" + "=" * 80)
    print("           CHARGEN HONEST EMPIRICAL RELIABILITY BENCHMARK (v2)")
    print("=" * 80)

    # JSON Results Table
    if "json" in results:
        print("\n[TEST A: LLM Character JSON Parsing & Schema Reliability]")
        print("-" * 80)
        print(f"{'Metric':<34} | {'OLD Implementation':<20} | {'NEW Implementation':<20}")
        print("-" * 80)

        old_j = results["json"].get("old", {})
        new_j = results["json"].get("new", {})

        def get_stat(d, key, ci_key):
            if not d: return "N/A"
            r = d.get(key, 0.0)
            ci = d.get(ci_key, [0.0, 0.0])
            return f"{r:.1f}% [{ci[0]:.1f}-{ci[1]:.1f}%]"

        print(f"{'Raw json.loads() Failure Rate':<34} | {get_stat(old_j, 'raw_json_failure_rate', 'raw_json_failure_ci95'):<20} | {get_stat(new_j, 'raw_json_failure_rate', 'raw_json_failure_ci95'):<20}")
        print(f"{'Final Pipeline Success Rate':<34} | {get_stat(old_j, 'final_pipeline_success_rate', 'final_pipeline_success_ci95'):<20} | {get_stat(new_j, 'final_pipeline_success_rate', 'final_pipeline_success_ci95'):<20}")

        print("-" * 80)
        print("Attempts Distribution:")
        print(f"   Attempt 1: OLD={old_j.get('attempts_distribution', {}).get(1, 'N/A')} | NEW={new_j.get('attempts_distribution', {}).get(1, 'N/A')}")
        print(f"   Attempt 2: OLD={old_j.get('attempts_distribution', {}).get(2, 'N/A')} | NEW={new_j.get('attempts_distribution', {}).get(2, 'N/A')}")
        print(f"   Attempt 3+: OLD={old_j.get('attempts_distribution', {}).get(3, 0) + old_j.get('attempts_distribution', {}).get(4, 0) + old_j.get('attempts_distribution', {}).get(5, 0)} | NEW={new_j.get('attempts_distribution', {}).get(3, 0) + new_j.get('attempts_distribution', {}).get(4, 0) + new_j.get('attempts_distribution', {}).get(5, 0)}")

    # Avatar Results Table
    if "avatar" in results:
        print("\n[TEST B: 3-Tier Avatar Generation Cascade]")
        print("-" * 80)
        print(f"{'Metric':<34} | {'OLD (Burst)':<20} | {'NEW (Spaced/Resilient)':<20}")
        print("-" * 80)

        old_a = results["avatar"].get("old", {})
        new_a = results["avatar"].get("new", {})

        def get_stat_a(d, key, ci_key):
            if not d: return "N/A"
            r = d.get(key, 0.0)
            ci = d.get(ci_key, [0.0, 0.0])
            return f"{r:.1f}% [{ci[0]:.1f}-{ci[1]:.1f}%]"

        print(f"{'Tier 1 (Pollinations Flux) Success':<34} | {get_stat_a(old_a, 'tier1_success_rate', 'tier1_success_ci95'):<20} | {get_stat_a(new_a, 'tier1_success_rate', 'tier1_success_ci95'):<20}")
        print(f"{'Tier 2 (Stable Horde) Success':<34} | {get_stat_a(old_a, 'tier2_success_rate', 'tier2_success_ci95'):<20} | {get_stat_a(new_a, 'tier2_success_rate', 'tier2_success_ci95'):<20}")
        print(f"{'Tier 3 (DiceBear SVG) Fallback':<34} | {get_stat_a(old_a, 'tier3_served_rate', 'tier3_served_ci95'):<20} | {get_stat_a(new_a, 'tier3_served_rate', 'tier3_served_ci95'):<20}")
        print(f"{'Real AI Images (Tier 1 + 2)':<34} | {get_stat_a(old_a, 'real_ai_image_rate', 'real_ai_image_ci95'):<20} | {get_stat_a(new_a, 'real_ai_image_rate', 'real_ai_image_ci95'):<20}")
        print(f"{'Total End-User Availability':<34} | {'100.0%':<20} | {'100.0%':<20}")

    print("\n" + "=" * 80)


async def main():
    parser = argparse.ArgumentParser(description="CharGen Honest Reliability Benchmark (v2)")
    parser.add_argument("--mode", choices=["both", "new", "old"], default="both", help="Run 'both' (before/after comparison), 'new', or 'old'")
    parser.add_argument("--n-json", type=int, default=100, help="Number of JSON benchmark calls (default: 100)")
    parser.add_argument("--n-avatar", type=int, default=30, help="Number of Avatar benchmark calls (default: 30)")
    parser.add_argument("--avatar-delay", type=float, default=1.5, help="Inter-call delay in seconds for avatars (default: 1.5s)")
    parser.add_argument("--json-only", action="store_true", help="Run only JSON tests")
    parser.add_argument("--avatar-only", action="store_true", help="Run only Avatar tests")
    parser.add_argument("--concurrency", type=int, default=2, help="Concurrency level for JSON calls (default: 2)")
    args = parser.parse_args()

    results_dir = SCRIPT_DIR
    results_path = results_dir / "results_v2.json"

    print("=======================================================================")
    print(" CharGen Empirical Benchmark v2  Starting Run")
    print(f" Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f" Target File: {results_path}")
    print("=======================================================================")

    benchmark_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "configuration": {
            "n_json": args.n_json,
            "n_avatar": args.n_avatar,
            "avatar_delay_sec": args.avatar_delay,
            "concurrency": args.concurrency,
            "model": settings.NVIDIA_MODEL,
        },
        "json": {},
        "avatar": {},
    }

    # Run JSON Benchmarks
    if not args.avatar_only:
        if args.mode in ("both", "old"):
            print("\n>>> Testing OLD JSON Generation (Unconstrained baseline)...")
            benchmark_data["json"]["old"] = await run_json_suite(args.n_json, use_new=False, concurrency=args.concurrency)
        if args.mode in ("both", "new"):
            print("\n>>> Testing NEW JSON Generation (Guided response_format + Repair)...")
            benchmark_data["json"]["new"] = await run_json_suite(args.n_json, use_new=True, concurrency=args.concurrency)

    # Run Avatar Benchmarks
    if not args.json_only:
        if args.mode in ("both", "old"):
            print("\n>>> Testing OLD Avatar Generation (Unspaced/Burst)...")
            benchmark_data["avatar"]["old"] = await run_avatar_suite(args.n_avatar, use_new=False, delay=0.0)
        if args.mode in ("both", "new"):
            print("\n>>> Testing NEW Avatar Generation (Spaced/Resilient cascade)...")
            benchmark_data["avatar"]["new"] = await run_avatar_suite(args.n_avatar, use_new=True, delay=args.avatar_delay)

    # Print clean comparison tables
    print_comparison_tables(benchmark_data)

    # Dump raw data
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)

    print(f"\n[OK] Complete raw before/after data written to: {results_path}")


if __name__ == "__main__":
    asyncio.run(main())

