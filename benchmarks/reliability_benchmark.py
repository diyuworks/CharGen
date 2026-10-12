"""
CharGen Reliability & Resilience Benchmark Suite
Tests and measures:
  Test A: LLM Character JSON Parsing & Recovery (Raw json.loads vs Two-Pass Pipeline)
  Test B: 3-Tier Avatar Generation Cascade (Pollinations vs Stable Horde vs DiceBear)

Saves results to benchmarks/results.json and prints summary comparison tables.
"""

import os
import sys
import json
import time
import re
import asyncio
import random
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Locate backend and .env
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

BACKEND_DIR = REPO_ROOT / "ai-character-platform" / "backend"
if not BACKEND_DIR.exists():
    BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load .env explicitly from backend directory or repo root
from dotenv import load_dotenv

ENV_PATH = BACKEND_DIR / ".env"
if not ENV_PATH.exists():
    ENV_PATH = REPO_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Verify API key without printing its value
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
if not NVIDIA_API_KEY:
    print("[ERROR] NVIDIA_API_KEY not found in .env. Please configure your .env file.")
    sys.exit(1)

# Import app modules
try:
    from app.core.config import settings
    from app.prompts.character_prompt import build_character_prompt
    from app.services.gemini_service import (
        _call_nvidia,
        _try_parse,
        _validate_character_dict,
        _extract_json,
        _repair_json,
    )
    from app.services.avatar_service import (
        _generate_pollinations,
        _generate_stable_horde,
        _dicebear_url,
        _build_prompt as _build_avatar_prompt,
    )
except ImportError as e:
    print(f"[ERROR] Failed to import app modules: {e}")
    print(f"Ensure backend directory is at {BACKEND_DIR}")
    sys.exit(1)


CATEGORIES = [
    "College Student", "Researcher", "Fitness Trainer",
    "Artist", "Influencer", "Software Engineer", "Chef", "Doctor"
]

NATIONALITIES = [
    "Japanese", "Korean", "American", "French", "Indian",
    "Brazilian", "Italian", "Spanish", "German", "British"
]


# =====================================================================
# Test A: LLM Character JSON Parsing & Recovery Benchmark
# =====================================================================

async def run_single_json_test(
    idx: int,
    total: int,
    sem: asyncio.Semaphore,
    model_name: str
) -> Dict[str, Any]:
    category = random.choice(CATEGORIES)
    nationality = random.choice(NATIONALITIES)
    gender = random.choice(["male", "female"])
    prompt = build_character_prompt(category, nationality, gender=gender)

    call_log = {
        "call_id": idx + 1,
        "category": category,
        "nationality": nationality,
        "gender": gender,
        "model": model_name,
        "raw_success": False,
        "raw_error_type": None,
        "raw_has_code_fences": False,
        "raw_has_smart_quotes": False,
        "raw_has_trailing_comma": False,
        "pass1_extract_success": False,
        "pass2_repair_success": False,
        "pipeline_success": False,
        "pipeline_attempts": 0,
        "pipeline_error": None,
        "latency_sec": 0.0,
    }

    async with sem:
        start_time = time.time()
        max_retries = 5

        for attempt in range(1, max_retries + 1):
            call_log["pipeline_attempts"] = attempt
            try:
                # LLM completion
                raw_text = await asyncio.to_thread(_call_nvidia, prompt)

                # Analyze raw text characteristics on first attempt
                if attempt == 1:
                    call_log["raw_has_code_fences"] = "```" in raw_text
                    call_log["raw_has_smart_quotes"] = any(
                        q in raw_text for q in ["\u2018", "\u2019", "\u201c", "\u201d"]
                    )
                    call_log["raw_has_trailing_comma"] = bool(
                        re.search(r",\s*([}\]])", raw_text)
                    )

                    # Test raw json.loads() without any extraction or repair
                    try:
                        json.loads(raw_text)
                        call_log["raw_success"] = True
                    except json.JSONDecodeError as jde:
                        call_log["raw_success"] = False
                        call_log["raw_error_type"] = jde.msg

                    # Test Pass 1 alone (bracket extraction without regex repair)
                    try:
                        candidate_pass1 = _extract_json(raw_text)
                        json.loads(candidate_pass1)
                        call_log["pass1_extract_success"] = True
                    except Exception:
                        call_log["pass1_extract_success"] = False

                # Test Full Pipeline (Pass 1 -> Pass 2 Repair -> Schema Validation)
                data = _try_parse(raw_text)
                if isinstance(data, list):
                    data = data[0]
                data["gender"] = gender

                _validate_character_dict(data)

                # Successfully parsed & validated
                call_log["pipeline_success"] = True
                if attempt == 1 and not call_log["pass1_extract_success"]:
                    call_log["pass2_repair_success"] = True
                break

            except Exception as exc:
                call_log["pipeline_error"] = str(exc)
                if attempt < max_retries:
                    await asyncio.sleep(1.5 * attempt)

        call_log["latency_sec"] = round(time.time() - start_time, 2)

    status = "OK" if call_log["pipeline_success"] else "FAIL"
    raw_st = "RAW:OK" if call_log["raw_success"] else f"RAW:ERR({call_log['raw_error_type']})"
    print(f"  [JSON {idx+1:03d}/{total:03d}] {status} (attempts={call_log['pipeline_attempts']}, {call_log['latency_sec']}s) | {raw_st}")
    return call_log


async def run_json_benchmark(n_calls: int = 100, concurrency: int = 2) -> Dict[str, Any]:
    print(f"\n=======================================================================")
    print(f" TEST A: LLM Character JSON Parsing & Recovery Benchmark")
    print(f" Model: {settings.NVIDIA_MODEL} | Total Calls: {n_calls} | Concurrency: {concurrency}")
    print(f"=======================================================================")

    sem = asyncio.Semaphore(concurrency)
    tasks = [
        run_single_json_test(i, n_calls, sem, settings.NVIDIA_MODEL)
        for i in range(n_calls)
    ]
    results = await asyncio.gather(*tasks)

    # Aggregate metrics
    raw_ok_count = sum(1 for r in results if r["raw_success"])
    pipeline_ok_count = sum(1 for r in results if r["pipeline_success"])
    pass1_ok_count = sum(1 for r in results if r["pass1_extract_success"])
    pass2_ok_count = sum(1 for r in results if r["pass2_repair_success"])

    fences_count = sum(1 for r in results if r["raw_has_code_fences"])
    smart_quotes_count = sum(1 for r in results if r["raw_has_smart_quotes"])
    trailing_comma_count = sum(1 for r in results if r["raw_has_trailing_comma"])

    latencies = [r["latency_sec"] for r in results]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    raw_failure_rate = ((n_calls - raw_ok_count) / n_calls) * 100
    pipeline_failure_rate = ((n_calls - pipeline_ok_count) / n_calls) * 100

    summary = {
        "total_calls": n_calls,
        "model": settings.NVIDIA_MODEL,
        "raw_json_success_count": raw_ok_count,
        "raw_json_failure_count": n_calls - raw_ok_count,
        "raw_json_error_rate_pct": round(raw_failure_rate, 2),
        "pass1_bracket_depth_success_count": pass1_ok_count,
        "pass2_regex_repair_recovered_count": pass2_ok_count,
        "pipeline_success_count": pipeline_ok_count,
        "pipeline_failure_count": n_calls - pipeline_ok_count,
        "pipeline_error_rate_pct": round(pipeline_failure_rate, 2),
        "avg_latency_sec": avg_latency,
        "raw_flaws_observed": {
            "markdown_code_fences": fences_count,
            "smart_curly_quotes": smart_quotes_count,
            "trailing_commas": trailing_comma_count,
        },
        "per_call_logs": results,
    }
    return summary


# =====================================================================
# Test B: 3-Tier Avatar Fallback Benchmark
# =====================================================================

def make_sample_character(idx: int) -> Dict[str, Any]:
    gender = "female" if idx % 2 == 0 else "male"
    category = CATEGORIES[idx % len(CATEGORIES)]
    nationality = NATIONALITIES[idx % len(NATIONALITIES)]
    name = f"Character_{idx+1}"
    return {
        "id": f"bench_{idx+1}",
        "name": name,
        "gender": gender,
        "category": category,
        "nationality": nationality,
        "occupation": category,
        "age": 24,
        "avatar_prompt": f"portrait of a {nationality} {category}, professional headshot, detailed face",
    }


async def run_single_avatar_test(
    idx: int,
    total: int,
    sem: asyncio.Semaphore,
) -> Dict[str, Any]:
    character = make_sample_character(idx)
    gender = character["gender"]
    prompt = _build_avatar_prompt(character)

    log = {
        "call_id": idx + 1,
        "gender": gender,
        "tier1_pollinations_success": False,
        "tier1_error": None,
        "full_pipeline_success": False,
        "serving_tier": None,
        "latency_sec": 0.0,
    }

    async with sem:
        start_time = time.time()

        # Step 1: Test Tier 1 alone (Pollinations Flux)
        try:
            p_bytes = await _generate_pollinations(prompt, gender)
            if p_bytes and len(p_bytes) > 1000:
                log["tier1_pollinations_success"] = True
            else:
                log["tier1_pollinations_success"] = False
                log["tier1_error"] = "Empty or invalid image payload"
        except Exception as e:
            log["tier1_pollinations_success"] = False
            log["tier1_error"] = str(e)

        # Step 2: Full Cascade Pipeline simulation (Pollinations -> Stable Horde -> DiceBear)
        if log["tier1_pollinations_success"]:
            log["serving_tier"] = "Tier 1 (Pollinations Flux)"
            log["full_pipeline_success"] = True
        else:
            # Fallback to Tier 2 (Stable Horde)
            print(f"    [Avatar {idx+1:02d}] Tier 1 failed ({log['tier1_error']}) -> Attempting Tier 2 (Stable Horde)...")
            try:
                sh_bytes = await _generate_stable_horde(prompt, gender)
                if sh_bytes and len(sh_bytes) > 1000:
                    log["serving_tier"] = "Tier 2 (Stable Horde)"
                    log["full_pipeline_success"] = True
            except Exception as e:
                pass

            # Fallback to Tier 3 if Tier 2 failed
            if not log["full_pipeline_success"]:
                print(f"    [Avatar {idx+1:02d}] Tier 2 failed -> Falling back to Tier 3 (DiceBear SVG)...")
                svg_url = _dicebear_url(character)
                if svg_url and svg_url.startswith("http"):
                    log["serving_tier"] = "Tier 3 (DiceBear SVG)"
                    log["full_pipeline_success"] = True
                else:
                    log["serving_tier"] = "None (Total Failure)"
                    log["full_pipeline_success"] = False

        log["latency_sec"] = round(time.time() - start_time, 2)

    t1_st = "T1:OK" if log["tier1_pollinations_success"] else f"T1:FAIL"
    print(f"  [Avatar {idx+1:02d}/{total:02d}] {log['serving_tier']} ({log['latency_sec']}s) | {t1_st}")
    return log


async def run_avatar_benchmark(n_calls: int = 30, concurrency: int = 2) -> Dict[str, Any]:
    print(f"\n=======================================================================")
    print(f" TEST B: 3-Tier Avatar Fallback Benchmark")
    print(f" Total Calls: {n_calls} | Concurrency: {concurrency}")
    print(f" Flow: Pollinations Flux -> Stable Horde -> DiceBear SVG")
    print(f"=======================================================================")

    sem = asyncio.Semaphore(concurrency)
    tasks = [run_single_avatar_test(i, n_calls, sem) for i in range(n_calls)]
    results = await asyncio.gather(*tasks)

    tier1_ok = sum(1 for r in results if r["tier1_pollinations_success"])
    full_pipeline_ok = sum(1 for r in results if r["full_pipeline_success"])

    tier_counts = {
        "Tier 1 (Pollinations Flux)": 0,
        "Tier 2 (Stable Horde)": 0,
        "Tier 3 (DiceBear SVG)": 0,
        "Failed": 0,
    }
    for r in results:
        tier = r["serving_tier"]
        if tier in tier_counts:
            tier_counts[tier] += 1
        elif r["full_pipeline_success"]:
            tier_counts[tier] = 1
        else:
            tier_counts["Failed"] += 1

    tier1_failure_rate = ((n_calls - tier1_ok) / n_calls) * 100
    pipeline_failure_rate = ((n_calls - full_pipeline_ok) / n_calls) * 100

    summary = {
        "total_calls": n_calls,
        "tier1_only_success_count": tier1_ok,
        "tier1_only_failure_count": n_calls - tier1_ok,
        "tier1_only_failure_rate_pct": round(tier1_failure_rate, 2),
        "full_pipeline_success_count": full_pipeline_ok,
        "full_pipeline_failure_count": n_calls - full_pipeline_ok,
        "full_pipeline_failure_rate_pct": round(pipeline_failure_rate, 2),
        "tier_distribution": tier_counts,
        "per_call_logs": results,
    }
    return summary


# =====================================================================
# Main Runner & Reporter
# =====================================================================

def print_benchmark_tables(json_res: Dict[str, Any] | None, avatar_res: Dict[str, Any] | None):
    print("\n" + "=" * 76)
    print("                      CHARGEN RELIABILITY BENCHMARK REPORT")
    print("=" * 76)

    if json_res:
        n = json_res["total_calls"]
        print(f"\n--- TEST A: LLM Character JSON Parsing & Recovery (N={n}) ---")
        print(f"Model: {json_res['model']}")
        print("-" * 76)
        print(f"{'Metric':<46} | {'Count':<10} | {'Rate (%)':<12}")
        print("-" * 76)
        print(f"{'Raw json.loads() Success (Baseline)':<46} | {json_res['raw_json_success_count']:<10} | {100 - json_res['raw_json_error_rate_pct']:>6.2f}%")
        print(f"{'Raw json.loads() Failures (Syntax / Fences)':<46} | {json_res['raw_json_failure_count']:<10} | {json_res['raw_json_error_rate_pct']:>6.2f}%")
        print(f"{'Pass 1 Bracket Extraction Solved':<46} | {json_res['pass1_bracket_depth_success_count']:<10} | {round(json_res['pass1_bracket_depth_success_count']/n*100, 2):>6.2f}%")
        print(f"{'Pass 2 Regex Repair Rescued (from Pass 1 err)':<46} | {json_res['pass2_regex_repair_recovered_count']:<10} | {round(json_res['pass2_regex_repair_recovered_count']/n*100, 2):>6.2f}%")
        print(f"{'Full App Pipeline Success (Extraction+Repair+Retry)':<46} | {json_res['pipeline_success_count']:<10} | {100 - json_res['pipeline_error_rate_pct']:>6.2f}%")
        print(f"{'Final Unrecoverable Pipeline Error Rate':<46} | {json_res['pipeline_failure_count']:<10} | {json_res['pipeline_error_rate_pct']:>6.2f}%")
        print("-" * 76)
        print(f"Formatting flaws detected in raw outputs:")
        for flaw, count in json_res["raw_flaws_observed"].items():
            print(f"  • {flaw:<30}: {count} occurrences ({round(count/n*100, 1)}%)")
        print(f"Average Request Latency: {json_res['avg_latency_sec']}s")

    if avatar_res:
        n = avatar_res["total_calls"]
        print(f"\n--- TEST B: 3-Tier Avatar Generation Cascade (N={n}) ---")
        print("-" * 76)
        print(f"{'Tier / Pipeline Strategy':<46} | {'Count':<10} | {'Availability':<12}")
        print("-" * 76)
        print(f"{'Tier 1 Only (Pollinations Flux alone)':<46} | {avatar_res['tier1_only_success_count']:<10} | {100 - avatar_res['tier1_only_failure_rate_pct']:>6.2f}%")
        print(f"{'Tier 1 Failure Rate (Dropped / Timed out)':<46} | {avatar_res['tier1_only_failure_count']:<10} | {avatar_res['tier1_only_failure_rate_pct']:>6.2f}%")
        print(f"{'Full 3-Tier Cascade Availability':<46} | {avatar_res['full_pipeline_success_count']:<10} | {100 - avatar_res['full_pipeline_failure_rate_pct']:>6.2f}%")
        print(f"{'Final User-Facing Avatar Failure Rate':<46} | {avatar_res['full_pipeline_failure_count']:<10} | {avatar_res['full_pipeline_failure_rate_pct']:>6.2f}%")
        print("-" * 76)
        print("Final Tier Serving Distribution:")
        for tier, count in avatar_res["tier_distribution"].items():
            print(f"  • {tier:<32}: {count:>3} ({round(count/n*100, 1)}%)")

    print("\n" + "=" * 76)


async def main():
    parser = argparse.ArgumentParser(description="CharGen Reliability & Resilience Benchmark")
    parser.add_argument("--n-json", type=int, default=100, help="Number of JSON benchmark calls (default: 100)")
    parser.add_argument("--n-avatar", type=int, default=30, help="Number of Avatar benchmark calls (default: 30)")
    parser.add_argument("--json-only", action="store_true", help="Run only Test A (JSON benchmark)")
    parser.add_argument("--avatar-only", action="store_true", help="Run only Test B (Avatar benchmark)")
    parser.add_argument("--concurrency", type=int, default=2, help="Concurrency level (default: 2)")
    args = parser.parse_args()

    # Create benchmarks dir
    os.makedirs(SCRIPT_DIR, exist_ok=True)
    results_path = SCRIPT_DIR / "results.json"

    print("=======================================================================")
    print(" Starting CharGen Reliability Benchmark Suite")
    print(f" Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f" Results will be saved to: {results_path}")
    print("=======================================================================")

    json_results = None
    avatar_results = None

    if not args.avatar_only:
        json_results = await run_json_benchmark(n_calls=args.n_json, concurrency=args.concurrency)

    if not args.json_only:
        avatar_results = await run_avatar_benchmark(n_calls=args.n_avatar, concurrency=args.concurrency)

    # Print summary tables
    print_benchmark_tables(json_results, avatar_results)

    # Save to results.json
    output_payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "test_a_json_parsing": json_results,
        "test_b_avatar_cascade": avatar_results,
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"[OK] Full raw benchmark logs and metrics written to: {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
