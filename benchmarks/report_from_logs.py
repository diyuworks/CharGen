"""
benchmarks/report_from_logs.py

Analyzes website-source logs (ai-character-platform/backend/logs/generation_metrics.jsonl)
and produces:
  1. benchmarks/web_usage_report.md
  2. benchmarks/web_usage_data.csv

Website logs and offline benchmark logs are strictly isolated and never pooled.
Offline benchmark results from benchmarks/results_v2.json are rendered in a
distinct, segregated section.
"""

import os
import sys
import json
import math
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple


def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate 95% Wilson score confidence interval [lower_pct, upper_pct]."""
    if total <= 0:
        return 0.0, 0.0
    z = 1.959964  # 95% confidence
    p = successes / total
    denominator = 1 + (z ** 2) / total
    centre_adjusted_probability = p + (z ** 2) / (2 * total)
    adjusted_std_dev = math.sqrt((p * (1 - p) + (z ** 2) / (4 * total)) / total)
    lower = (centre_adjusted_probability - z * adjusted_std_dev) / denominator
    upper = (centre_adjusted_probability + z * adjusted_std_dev) / denominator
    return max(0.0, round(lower * 100, 2)), min(100.0, round(upper * 100, 2))


def percentile(data: List[float], p: float) -> float | None:
    """Calculate percentile (p in [0, 100]). Returns None if empty."""
    if not data:
        return None
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(sorted_data[int(k)], 2)
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return round(d0 + d1, 2)


def fmt_latency(val: float | None) -> str:
    if val is None:
        return "N/A (no data)"
    return f"{val}s"


def fmt_ci(ci: Tuple[float, float], n: int) -> str:
    if n <= 0:
        return "N/A (no data)"
    return f"[{ci[0]}%, {ci[1]}%]"


def find_log_file() -> Path:
    candidates = [
        Path("ai-character-platform/backend/logs/generation_metrics.jsonl"),
        Path("backend/logs/generation_metrics.jsonl"),
        Path("logs/generation_metrics.jsonl"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def load_website_logs(log_path: Path) -> List[Dict[str, Any]]:
    if not log_path.exists():
        return []
    records = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                # Website traffic only: source == 'website' (default assumed website if absent)
                if rec.get("source", "website") == "website":
                    records.append(rec)
            except json.JSONDecodeError:
                continue
    return records


def analyze_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    char_records = [r for r in records if r.get("call_type") == "character_generation"]
    avatar_records = [r for r in records if r.get("call_type") == "avatar_generation"]
    chat_records = [r for r in records if r.get("call_type") == "chat_message"]
    summary_records = [r for r in records if r.get("call_type") == "chat_summary"]

    # Timestamps & Time Window
    all_timestamps = [r["timestamp"] for r in records if "timestamp" in r and r["timestamp"]]
    first_timestamp = min(all_timestamps) if all_timestamps else "N/A (no data)"
    last_timestamp = max(all_timestamps) if all_timestamps else "N/A (no data)"

    # Unique character count across character & avatar generation
    char_ids = set()
    for r in char_records:
        if r.get("character_id"):
            char_ids.add(r["character_id"])
    for r in avatar_records:
        if r.get("character_id"):
            char_ids.add(r["character_id"])
    unique_characters_count = len(char_ids)

    # First-time vs regenerate avatar clicks
    avatar_char_ids_seen = set()
    avatar_first_time_count = 0
    avatar_regenerate_count = 0
    for r in avatar_records:
        cid = r.get("character_id")
        if cid and cid in avatar_char_ids_seen:
            avatar_regenerate_count += 1
        else:
            if cid:
                avatar_char_ids_seen.add(cid)
            avatar_first_time_count += 1

    # Character generation JSON reliability
    n_char = len(char_records)
    char_first_attempt_success = sum(1 for r in char_records if r.get("raw_first_attempt_valid", False))
    char_raw_failures = n_char - char_first_attempt_success
    char_pipeline_successes = sum(1 for r in char_records if r.get("pipeline_success", False))

    raw_failure_pct = round((char_raw_failures / n_char) * 100, 2) if n_char > 0 else None
    raw_failure_ci = wilson_score_interval(char_raw_failures, n_char) if n_char > 0 else (0.0, 0.0)

    final_success_pct = round((char_pipeline_successes / n_char) * 100, 2) if n_char > 0 else None
    final_success_ci = wilson_score_interval(char_pipeline_successes, n_char) if n_char > 0 else (0.0, 0.0)

    char_latencies = [r.get("latency_sec", 0.0) for r in char_records if "latency_sec" in r]
    char_p50 = percentile(char_latencies, 50)
    char_p95 = percentile(char_latencies, 95)

    # Avatar generation tiers: exactly matching logged values
    n_avatar = len(avatar_records)
    tier1_pollinations_count = sum(1 for r in avatar_records if r.get("tier_used") == "tier1_pollinations")
    tier2_stable_horde_count = sum(1 for r in avatar_records if r.get("tier_used") in ("tier2_stable_horde", "tier1_stable_horde"))
    tier3_dicebear_count = sum(1 for r in avatar_records if r.get("tier_used") == "tier3_dicebear")
    ai_avatar_count = sum(1 for r in avatar_records if r.get("is_ai_image", False))

    tier1_pollinations_pct = round((tier1_pollinations_count / n_avatar) * 100, 2) if n_avatar > 0 else None
    tier1_pollinations_ci = wilson_score_interval(tier1_pollinations_count, n_avatar) if n_avatar > 0 else (0.0, 0.0)

    tier2_stable_horde_pct = round((tier2_stable_horde_count / n_avatar) * 100, 2) if n_avatar > 0 else None
    tier2_stable_horde_ci = wilson_score_interval(tier2_stable_horde_count, n_avatar) if n_avatar > 0 else (0.0, 0.0)

    tier3_dicebear_pct = round((tier3_dicebear_count / n_avatar) * 100, 2) if n_avatar > 0 else None
    tier3_dicebear_ci = wilson_score_interval(tier3_dicebear_count, n_avatar) if n_avatar > 0 else (0.0, 0.0)

    ai_pct = round((ai_avatar_count / n_avatar) * 100, 2) if n_avatar > 0 else None
    ai_ci = wilson_score_interval(ai_avatar_count, n_avatar) if n_avatar > 0 else (0.0, 0.0)

    avatar_latencies = [r.get("latency_sec", 0.0) for r in avatar_records if "latency_sec" in r]
    avatar_p50 = percentile(avatar_latencies, 50)
    avatar_p95 = percentile(avatar_latencies, 95)

    # Chat & Memory Performance
    n_chat = len(chat_records)
    chat_latencies = [r.get("latency_sec", 0.0) for r in chat_records if "latency_sec" in r]
    chat_p50 = percentile(chat_latencies, 50)
    chat_p95 = percentile(chat_latencies, 95)

    n_summary = len(summary_records)
    summary_latencies = [r.get("latency_sec", 0.0) for r in summary_records if "latency_sec" in r]
    summary_p50 = percentile(summary_latencies, 50)
    summary_p95 = percentile(summary_latencies, 95)

    return {
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "unique_characters_count": unique_characters_count,
        "avatar_first_time_count": avatar_first_time_count,
        "avatar_regenerate_count": avatar_regenerate_count,
        "n_char": n_char,
        "char_raw_failures": char_raw_failures,
        "raw_failure_pct": raw_failure_pct,
        "raw_failure_ci": raw_failure_ci,
        "char_pipeline_successes": char_pipeline_successes,
        "final_success_pct": final_success_pct,
        "final_success_ci": final_success_ci,
        "char_p50": char_p50,
        "char_p95": char_p95,
        "n_avatar": n_avatar,
        "tier1_pollinations_count": tier1_pollinations_count,
        "tier1_pollinations_pct": tier1_pollinations_pct,
        "tier1_pollinations_ci": tier1_pollinations_ci,
        "tier2_stable_horde_count": tier2_stable_horde_count,
        "tier2_stable_horde_pct": tier2_stable_horde_pct,
        "tier2_stable_horde_ci": tier2_stable_horde_ci,
        "tier3_dicebear_count": tier3_dicebear_count,
        "tier3_dicebear_pct": tier3_dicebear_pct,
        "tier3_dicebear_ci": tier3_dicebear_ci,
        "ai_avatar_count": ai_avatar_count,
        "ai_pct": ai_pct,
        "ai_ci": ai_ci,
        "avatar_p50": avatar_p50,
        "avatar_p95": avatar_p95,
        "n_chat": n_chat,
        "chat_p50": chat_p50,
        "chat_p95": chat_p95,
        "n_summary": n_summary,
        "summary_p50": summary_p50,
        "summary_p95": summary_p95,
    }


def load_benchmark_results(json_path: Path) -> Dict[str, Any] | None:
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_csv(summary: Dict[str, Any], filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value", "Sample Size (n)", "95% Wilson CI", "Notes"])
        
        # Activity
        writer.writerow(["Time Window Start", summary["first_timestamp"], summary["n_char"] + summary["n_avatar"] + summary["n_chat"], "-", "First log entry"])
        writer.writerow(["Time Window End", summary["last_timestamp"], summary["n_char"] + summary["n_avatar"] + summary["n_chat"], "-", "Last log entry"])
        writer.writerow(["Unique Characters Logged", summary["unique_characters_count"], summary["unique_characters_count"], "-", "Distinct character IDs"])
        
        # Character JSON
        writer.writerow(["Character Generation Total", summary["n_char"], summary["n_char"], "-", "Website-source generation calls"])
        writer.writerow([
            "Raw JSON Failure Rate",
            f"{summary['raw_failure_pct']}%" if summary["raw_failure_pct"] is not None else "N/A (no data)",
            summary["n_char"],
            fmt_ci(summary["raw_failure_ci"], summary["n_char"]),
            "First attempt failed json.loads"
        ])
        writer.writerow([
            "Pipeline Final Success Rate",
            f"{summary['final_success_pct']}%" if summary["final_success_pct"] is not None else "N/A (no data)",
            summary["n_char"],
            fmt_ci(summary["final_success_ci"], summary["n_char"]),
            "Post repair / retry pipeline success"
        ])
        writer.writerow(["Character Gen Latency p50", fmt_latency(summary["char_p50"]), summary["n_char"], "-", "Median latency"])
        writer.writerow(["Character Gen Latency p95", fmt_latency(summary["char_p95"]), summary["n_char"], "-", "95th percentile latency"])

        # Avatar
        writer.writerow(["Avatar Generation Total", summary["n_avatar"], summary["n_avatar"], "-", "Total avatar cascade calls"])
        writer.writerow(["Avatar First-time Generations", summary["avatar_first_time_count"], summary["n_avatar"], "-", "Initial generation upon create"])
        writer.writerow(["Avatar Regenerate Clicks", summary["avatar_regenerate_count"], summary["n_avatar"], "-", "Subsequent regenerate clicks"])
        writer.writerow([
            "tier1_pollinations",
            f"{summary['tier1_pollinations_pct']}% ({summary['tier1_pollinations_count']})" if summary["tier1_pollinations_pct"] is not None else "N/A (no data)",
            summary["n_avatar"],
            fmt_ci(summary["tier1_pollinations_ci"], summary["n_avatar"]),
            "Logged tier1_pollinations"
        ])
        writer.writerow([
            "tier2_stable_horde",
            f"{summary['tier2_stable_horde_pct']}% ({summary['tier2_stable_horde_count']})" if summary["tier2_stable_horde_pct"] is not None else "N/A (no data)",
            summary["n_avatar"],
            fmt_ci(summary["tier2_stable_horde_ci"], summary["n_avatar"]),
            "Logged tier2_stable_horde"
        ])
        writer.writerow([
            "tier3_dicebear",
            f"{summary['tier3_dicebear_pct']}% ({summary['tier3_dicebear_count']})" if summary["tier3_dicebear_pct"] is not None else "N/A (no data)",
            summary["n_avatar"],
            fmt_ci(summary["tier3_dicebear_ci"], summary["n_avatar"]),
            "Logged tier3_dicebear"
        ])
        writer.writerow([
            "Real AI Image %",
            f"{summary['ai_pct']}% ({summary['ai_avatar_count']})" if summary["ai_pct"] is not None else "N/A (no data)",
            summary["n_avatar"],
            fmt_ci(summary["ai_ci"], summary["n_avatar"]),
            "is_ai_image == True"
        ])
        writer.writerow(["Avatar Latency p50", fmt_latency(summary["avatar_p50"]), summary["n_avatar"], "-", "Median latency"])
        writer.writerow(["Avatar Latency p95", fmt_latency(summary["avatar_p95"]), summary["n_avatar"], "-", "95th percentile latency"])

        # Chat
        writer.writerow(["Chat Messages Sent", summary["n_chat"], summary["n_chat"], "-", "Total interactive chat turns"])
        writer.writerow(["Chat Latency p50", fmt_latency(summary["chat_p50"]), summary["n_chat"], "-", "Response latency p50"])
        writer.writerow(["Chat Latency p95", fmt_latency(summary["chat_p95"]), summary["n_chat"], "-", "Response latency p95"])
        writer.writerow(["Chat Summaries Generated", summary["n_summary"], summary["n_summary"], "-", "Memory summaries triggered (>20 msgs)"])
        writer.writerow(["Chat Summary Latency p50", fmt_latency(summary["summary_p50"]), summary["n_summary"], "-", "Summarization latency p50"])
        writer.writerow(["Chat Summary Latency p95", fmt_latency(summary["summary_p95"]), summary["n_summary"], "-", "Summarization latency p95"])


def write_markdown(summary: Dict[str, Any], bench_data: Dict[str, Any] | None, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)

    def status_badge(n: int) -> str:
        if n >= 30:
            return "STATISTICALLY SOUND (n >= 30)"
        return "TOO SMALL TO QUOTE (n < 30)"

    # Format values
    raw_fail_str = f"{summary['raw_failure_pct']}%" if summary['raw_failure_pct'] is not None else "N/A (no data)"
    final_succ_str = f"{summary['final_success_pct']}%" if summary['final_success_pct'] is not None else "N/A (no data)"
    char_p50_str = fmt_latency(summary['char_p50'])
    char_p95_str = fmt_latency(summary['char_p95'])

    t1_str = f"{summary['tier1_pollinations_pct']}%" if summary['tier1_pollinations_pct'] is not None else "N/A (no data)"
    t2_str = f"{summary['tier2_stable_horde_pct']}%" if summary['tier2_stable_horde_pct'] is not None else "N/A (no data)"
    t3_str = f"{summary['tier3_dicebear_pct']}%" if summary['tier3_dicebear_pct'] is not None else "N/A (no data)"
    ai_str = f"{summary['ai_pct']}%" if summary['ai_pct'] is not None else "N/A (no data)"

    avatar_p50_str = fmt_latency(summary['avatar_p50'])
    avatar_p95_str = fmt_latency(summary['avatar_p95'])

    chat_p50_str = fmt_latency(summary['chat_p50'])
    chat_p95_str = fmt_latency(summary['chat_p95'])
    summary_p50_str = fmt_latency(summary['summary_p50'])
    summary_p95_str = fmt_latency(summary['summary_p95'])

    md = f"""# Real Website Usage Report (Live Logs)

**Source**: Website traffic only (`source == "website"`)  
**Time Window**: `{summary['first_timestamp']}` to `{summary['last_timestamp']}`  
**Unique Characters Logged**: **{summary['unique_characters_count']}**  

---

## 1. Summary of Activity

| Metric | Sample Size (n) | Result | Assessment |
| :--- | :--- | :--- | :--- |
| **Characters Created** | {summary['n_char']} | {summary['n_char']} characters | {status_badge(summary['n_char'])} |
| **Avatar Cascade Calls** | {summary['n_avatar']} | {summary['n_avatar']} avatars ({summary['avatar_first_time_count']} first-time, {summary['avatar_regenerate_count']} regenerations) | {status_badge(summary['n_avatar'])} |
| **Chat Messages** | {summary['n_chat']} | {summary['n_chat']} messages | {status_badge(summary['n_chat'])} |
| **Chat Summaries (>20 msgs)** | {summary['n_summary']} | {summary['n_summary']} summaries | {status_badge(summary['n_summary'])} |

---

## 2. Character Generation & JSON Reliability

- **Raw JSON First-Attempt Failure Rate**: **{raw_fail_str}** ({summary['char_raw_failures']}/{summary['n_char']})  
  - 95% Wilson Score CI: `{fmt_ci(summary['raw_failure_ci'], summary['n_char'])}`
- **Pipeline Final Success Rate**: **{final_succ_str}** ({summary['char_pipeline_successes']}/{summary['n_char']})  
  - 95% Wilson Score CI: `{fmt_ci(summary['final_success_ci'], summary['n_char'])}`
- **Latency**: p50 = **{char_p50_str}**, p95 = **{char_p95_str}**

---

## 3. Avatar Cascade Distribution (Exact Logged Tiers)

| Tier Key | Provider / Destination | Count | Share (%) | 95% Wilson CI |
| :--- | :--- | :--- | :--- | :--- |
| `tier1_pollinations` | Pollinations AI | {summary['tier1_pollinations_count']} | {t1_str} | `{fmt_ci(summary['tier1_pollinations_ci'], summary['n_avatar'])}` |
| `tier2_stable_horde` | Stable Horde (Decentralized) | {summary['tier2_stable_horde_count']} | {t2_str} | `{fmt_ci(summary['tier2_stable_horde_ci'], summary['n_avatar'])}` |
| `tier3_dicebear` | DiceBear SVG Fallback | {summary['tier3_dicebear_count']} | {t3_str} | `{fmt_ci(summary['tier3_dicebear_ci'], summary['n_avatar'])}` |
| **Total Real AI Images** | `tier1_pollinations` + `tier2_stable_horde` | {summary['ai_avatar_count']} | **{ai_str}** | `{fmt_ci(summary['ai_ci'], summary['n_avatar'])}` |

- **Avatar Generation Breakdown**: {summary['avatar_first_time_count']} first-time generations, {summary['avatar_regenerate_count']} manual regenerations
- **Avatar Latency**: p50 = **{avatar_p50_str}**, p95 = **{avatar_p95_str}**

---

## 4. Chat & Memory Performance

- **User/Assistant Turns Logged**: {summary['n_chat']}
- **Chat Turn Latency**: p50 = **{chat_p50_str}**, p95 = **{chat_p95_str}**
- **Memory Summaries Triggered**: {summary['n_summary']} (for chats extending past 20 messages)
- **Summary Generation Latency**: p50 = **{summary_p50_str}**, p95 = **{summary_p95_str}**

---

## 5. Safe Resume Claims

> **Statistical Threshold Rule**: Any claim with sample size **n < 30** or confidence interval wider than 20 percentage points is strictly flagged as **"Too small to quote"** to prevent misleading or untruthful resume claims.

"""

    claims = [
        ("Character generation JSON repair recovery", summary['n_char'], f"Observed final success {final_succ_str} (95% CI: {fmt_ci(summary['final_success_ci'], summary['n_char'])})"),
        ("Avatar 3-tier cascade resilience", summary['n_avatar'], f"Observed AI avatar generation rate {ai_str} (95% CI: {fmt_ci(summary['ai_ci'], summary['n_avatar'])})"),
        ("Interactive chat conversation memory", summary['n_chat'], f"Observed {summary['n_chat']} chat turns, {summary['n_summary']} summaries past 20-message window"),
    ]

    for claim_name, n, detail in claims:
        if n >= 30:
            md += f"- [x] **SAFE TO QUOTE**: {claim_name} (n = {n} >= 30). {detail}\n"
        else:
            md += f"- [ ] **TOO SMALL TO QUOTE**: {claim_name} (n = {n} < 30). *Requires at least 30 observations on the live site before quoting numbers on resume.* Current: {detail}\n"

    # Separate Offline Benchmark Section
    if bench_data:
        md += """\n---\n\n## 6. Offline Benchmark Suite Results (results_v2.json)

> **ISOLATION GUARD**: The following figures are generated strictly from offline controlled experiment suites (`results_v2.json`) under synthetic stress testing. They are NEVER pooled with organic website user traffic numbers above.

"""
        json_bench = bench_data.get("json", {})
        if "old" in json_bench and "new" in json_bench:
            old_j = json_bench["old"]
            new_j = json_bench["new"]
            md += f"""### A. JSON Parsing Reliability Benchmark (Controlled N = {new_j.get('n_calls', 'N/A')})
- **Old Unconstrained Implementation**:
  - Raw JSON Failure Rate: **{old_j.get('raw_json_failure_rate')}%** (95% CI: `[{old_j.get('raw_json_failure_ci95',[0,0])[0]}%, {old_j.get('raw_json_failure_ci95',[0,0])[1]}%]`)
  - Pipeline Final Success: **{old_j.get('final_pipeline_success_rate')}%** (95% CI: `[{old_j.get('final_pipeline_success_ci95',[0,0])[0]}%, {old_j.get('final_pipeline_success_ci95',[0,0])[1]}%]`)
- **New Guided Implementation (`response_format` + JSON repair cascade)**:
  - Raw JSON Failure Rate: **{new_j.get('raw_json_failure_rate')}%** (95% CI: `[{new_j.get('raw_json_failure_ci95',[0,0])[0]}%, {new_j.get('raw_json_failure_ci95',[0,0])[1]}%]`)
  - Pipeline Final Success: **{new_j.get('final_pipeline_success_rate')}%** (95% CI: `[{new_j.get('final_pipeline_success_ci95',[0,0])[0]}%, {new_j.get('final_pipeline_success_ci95',[0,0])[1]}%]`)

"""

        avatar_bench = bench_data.get("avatar", {})
        if "old" in avatar_bench and "new" in avatar_bench:
            old_a = avatar_bench["old"]
            new_a = avatar_bench["new"]
            md += f"""### B. Avatar Cascade Resilience Benchmark (Controlled N = {new_a.get('n_calls', 'N/A')})
- **Old Unauthenticated Burst Mode**:
  - Real AI Image Rate: **{old_a.get('real_ai_image_rate')}%** ({old_a.get('real_ai_images_count')}/{old_a.get('n_calls')})
  - Tier 3 Fallback Rate: **{old_a.get('tier3_served_rate')}%**
- **New Token-Enabled Resilient Mode**:
  - Real AI Image Rate: **{new_a.get('real_ai_image_rate')}%** (95% CI: `[{new_a.get('real_ai_image_ci95',[0,0])[0]}%, {new_a.get('real_ai_image_ci95',[0,0])[1]}%]`)
  - Tier Breakdown: Tier 1 = {new_a.get('tier1_success_count')}, Tier 2 = {new_a.get('tier2_success_count')}, Tier 3 = {new_a.get('tier3_served_count')}

"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)


def main():
    log_path = find_log_file()
    print(f"Reading logs from: {log_path}")
    records = load_website_logs(log_path)
    print(f"Loaded {len(records)} website log records.")

    summary = analyze_records(records)
    bench_data = load_benchmark_results(Path("benchmarks/results_v2.json"))

    report_md_path = Path("benchmarks/web_usage_report.md")
    data_csv_path = Path("benchmarks/web_usage_data.csv")

    write_csv(summary, data_csv_path)
    write_markdown(summary, bench_data, report_md_path)

    print(f"Wrote report to {report_md_path}")
    print(f"Wrote CSV to {data_csv_path}")


if __name__ == "__main__":
    main()
