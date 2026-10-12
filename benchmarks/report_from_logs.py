"""
benchmarks/report_from_logs.py

Analyzes website-source logs (default: logs/generation_metrics.jsonl or
ai-character-platform/backend/logs/generation_metrics.jsonl) and produces:
  1. web_usage_report.md
  2. web_usage_data.csv

Metrics reported (website-source only):
  - Characters created
  - Chats (messages, active characters)
  - Avatar tier split (Tier 1 Pollinations, Tier 2 Stable Horde, Tier 3 DiceBear)
  - Real-AI vs DiceBear %
  - JSON raw first-attempt failure & final pipeline success with 95% Wilson CIs
  - Chat summaries triggered & latency p50/p95
  - Safe resume claims section (flags n < 30 as 'too small to quote')
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


def percentile(data: List[float], p: float) -> float:
    """Calculate percentile (p in [0, 100])."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(sorted_data[int(k)], 2)
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return round(d0 + d1, 2)


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

    # Character generation
    n_char = len(char_records)
    char_first_attempt_success = sum(1 for r in char_records if r.get("raw_first_attempt_valid", False))
    char_raw_failures = n_char - char_first_attempt_success
    char_pipeline_successes = sum(1 for r in char_records if r.get("pipeline_success", False))

    raw_failure_pct = round((char_raw_failures / n_char) * 100, 2) if n_char > 0 else 0.0
    raw_failure_ci = wilson_score_interval(char_raw_failures, n_char)

    final_success_pct = round((char_pipeline_successes / n_char) * 100, 2) if n_char > 0 else 0.0
    final_success_ci = wilson_score_interval(char_pipeline_successes, n_char)

    char_latencies = [r.get("latency_sec", 0.0) for r in char_records if "latency_sec" in r]
    char_p50 = percentile(char_latencies, 50)
    char_p95 = percentile(char_latencies, 95)

    # Avatar generation
    n_avatar = len(avatar_records)
    tier1_count = sum(1 for r in avatar_records if r.get("tier_used") == "tier1_pollinations")
    tier2_count = sum(1 for r in avatar_records if r.get("tier_used") == "tier2_stable_horde")
    tier3_count = sum(1 for r in avatar_records if r.get("tier_used") == "tier3_dicebear")
    ai_avatar_count = sum(1 for r in avatar_records if r.get("is_ai_image", False))

    tier1_pct = round((tier1_count / n_avatar) * 100, 2) if n_avatar > 0 else 0.0
    tier2_pct = round((tier2_count / n_avatar) * 100, 2) if n_avatar > 0 else 0.0
    tier3_pct = round((tier3_count / n_avatar) * 100, 2) if n_avatar > 0 else 0.0
    ai_pct = round((ai_avatar_count / n_avatar) * 100, 2) if n_avatar > 0 else 0.0

    avatar_latencies = [r.get("latency_sec", 0.0) for r in avatar_records if "latency_sec" in r]
    avatar_p50 = percentile(avatar_latencies, 50)
    avatar_p95 = percentile(avatar_latencies, 95)

    # Chat & Summary
    n_chat = len(chat_records)
    chat_latencies = [r.get("latency_sec", 0.0) for r in chat_records if "latency_sec" in r]
    chat_p50 = percentile(chat_latencies, 50)
    chat_p95 = percentile(chat_latencies, 95)

    n_summary = len(summary_records)
    summary_latencies = [r.get("latency_sec", 0.0) for r in summary_records if "latency_sec" in r]
    summary_p50 = percentile(summary_latencies, 50)
    summary_p95 = percentile(summary_latencies, 95)

    return {
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
        "tier1_count": tier1_count,
        "tier1_pct": tier1_pct,
        "tier2_count": tier2_count,
        "tier2_pct": tier2_pct,
        "tier3_count": tier3_count,
        "tier3_pct": tier3_pct,
        "ai_avatar_count": ai_avatar_count,
        "ai_pct": ai_pct,
        "avatar_p50": avatar_p50,
        "avatar_p95": avatar_p95,
        "n_chat": n_chat,
        "chat_p50": chat_p50,
        "chat_p95": chat_p95,
        "n_summary": n_summary,
        "summary_p50": summary_p50,
        "summary_p95": summary_p95,
    }


def write_csv(summary: Dict[str, Any], filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value", "Sample Size (n)", "95% Wilson CI", "Notes"])
        
        # Character JSON
        writer.writerow([
            "Character Generation Total",
            summary["n_char"],
            summary["n_char"],
            "-",
            "Website-source generation calls"
        ])
        writer.writerow([
            "Raw JSON Failure Rate",
            f"{summary['raw_failure_pct']}%",
            summary["n_char"],
            f"[{summary['raw_failure_ci'][0]}%, {summary['raw_failure_ci'][1]}%]",
            "First attempt failed json.loads"
        ])
        writer.writerow([
            "Pipeline Final Success Rate",
            f"{summary['final_success_pct']}%",
            summary["n_char"],
            f"[{summary['final_success_ci'][0]}%, {summary['final_success_ci'][1]}%]",
            "Post repair / retry pipeline success"
        ])
        writer.writerow([
            "Character Gen Latency p50",
            f"{summary['char_p50']}s",
            summary["n_char"],
            "-",
            "Median latency"
        ])
        writer.writerow([
            "Character Gen Latency p95",
            f"{summary['char_p95']}s",
            summary["n_char"],
            "-",
            "95th percentile latency"
        ])

        # Avatar
        writer.writerow([
            "Avatar Generation Total",
            summary["n_avatar"],
            summary["n_avatar"],
            "-",
            "Total avatar cascade calls"
        ])
        writer.writerow([
            "Avatar Tier 1 (Pollinations)",
            f"{summary['tier1_pct']}% ({summary['tier1_count']})",
            summary["n_avatar"],
            "-",
            "Resolved via Tier 1"
        ])
        writer.writerow([
            "Avatar Tier 2 (Stable Horde)",
            f"{summary['tier2_pct']}% ({summary['tier2_count']})",
            summary["n_avatar"],
            "-",
            "Resolved via Tier 2"
        ])
        writer.writerow([
            "Avatar Tier 3 (DiceBear)",
            f"{summary['tier3_pct']}% ({summary['tier3_count']})",
            summary["n_avatar"],
            "-",
            "Resolved via Tier 3 fallback"
        ])
        writer.writerow([
            "Real AI Image %",
            f"{summary['ai_pct']}% ({summary['ai_avatar_count']})",
            summary["n_avatar"],
            "-",
            "Tier 1 + Tier 2 vs Tier 3"
        ])

        # Chat
        writer.writerow([
            "Chat Messages Sent",
            summary["n_chat"],
            summary["n_chat"],
            "-",
            "Total interactive chat turns"
        ])
        writer.writerow([
            "Chat Latency p50 / p95",
            f"{summary['chat_p50']}s / {summary['chat_p95']}s",
            summary["n_chat"],
            "-",
            "Response latency"
        ])
        writer.writerow([
            "Chat Summaries Generated",
            summary["n_summary"],
            summary["n_summary"],
            "-",
            "Memory summaries triggered (>20 msgs)"
        ])
        writer.writerow([
            "Chat Summary Latency p50 / p95",
            f"{summary['summary_p50']}s / {summary['summary_p95']}s",
            summary["n_summary"],
            "-",
            "Summarization latency"
        ])


def write_markdown(summary: Dict[str, Any], filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)

    def status_badge(n: int) -> str:
        if n >= 30:
            return "STATISTICALLY SOUND (n >= 30)"
        return "TOO SMALL TO QUOTE (n < 30)"

    md = f"""# Real Website Usage Report (Live Logs)

**Source**: Website traffic only (`source == "website"`)  
**Generated On**: Live Log Analysis  

---

## 1. Summary of Activity

| Metric | Sample Size (n) | Result | Assessment |
| :--- | :--- | :--- | :--- |
| **Characters Created** | {summary['n_char']} | {summary['n_char']} characters | {status_badge(summary['n_char'])} |
| **Avatar Cascade Calls** | {summary['n_avatar']} | {summary['n_avatar']} avatars | {status_badge(summary['n_avatar'])} |
| **Chat Messages** | {summary['n_chat']} | {summary['n_chat']} messages | {status_badge(summary['n_chat'])} |
| **Chat Summaries (>20 msgs)** | {summary['n_summary']} | {summary['n_summary']} summaries | {status_badge(summary['n_summary'])} |

---

## 2. Character Generation & JSON Reliability

- **Raw JSON First-Attempt Failure Rate**: **{summary['raw_failure_pct']}%** ({summary['char_raw_failures']}/{summary['n_char']})  
  - 95% Wilson Score CI: `[{summary['raw_failure_ci'][0]}%, {summary['raw_failure_ci'][1]}%]`
- **Pipeline Final Success Rate**: **{summary['final_success_pct']}%** ({summary['char_pipeline_successes']}/{summary['n_char']})  
  - 95% Wilson Score CI: `[{summary['final_success_ci'][0]}%, {summary['final_success_ci'][1]}%]`
- **Latency**: p50 = **{summary['char_p50']}s**, p95 = **{summary['char_p95']}s**

---

## 3. Avatar Cascade Distribution

| Tier | Provider | Count | Split (%) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Pollinations AI (Flux) | {summary['tier1_count']} | {summary['tier1_pct']}% | Primary realistic AI generator |
| **Tier 2** | Stable Horde | {summary['tier2_count']} | {summary['tier2_pct']}% | Distributed async AI fallback |
| **Tier 3** | DiceBear | {summary['tier3_count']} | {summary['tier3_pct']}% | Deterministic SVG fallback |
| **Total AI**| Tier 1 + Tier 2 | {summary['ai_avatar_count']} | **{summary['ai_pct']}%** | Real AI generated images |

- **Avatar Latency**: p50 = **{summary['avatar_p50']}s**, p95 = **{summary['avatar_p95']}s**

---

## 4. Chat & Memory Performance

- **User/Assistant Turns Logged**: {summary['n_chat']}
- **Chat Turn Latency**: p50 = **{summary['chat_p50']}s**, p95 = **{summary['chat_p95']}s**
- **Memory Summaries Triggered**: {summary['n_summary']} (for chats extending past 20 messages)
- **Summary Generation Latency**: p50 = **{summary['summary_p50']}s**, p95 = **{summary['summary_p95']}s**

---

## 5. Safe Resume Claims

> **Statistical Threshold Rule**: Any claim with sample size **n < 30** is strictly flagged as **"Too small to quote"** to prevent misleading or untruthful resume claims.

"""

    # Claim checks
    claims = [
        ("Character generation JSON repair recovery", summary['n_char'], f"Observed final success {summary['final_success_pct']}% (95% CI: [{summary['final_success_ci'][0]}%, {summary['final_success_ci'][1]}%])"),
        ("Avatar 3-tier cascade resilience", summary['n_avatar'], f"Observed AI avatar generation rate {summary['ai_pct']}% across 3 tiers"),
        ("Interactive chat conversation memory", summary['n_chat'], f"Observed {summary['n_chat']} chat turns, {summary['n_summary']} summaries past 20-message window"),
    ]

    for claim_name, n, detail in claims:
        if n >= 30:
            md += f"- [x] **SAFE TO QUOTE**: {claim_name} (n = {n} >= 30). {detail}\n"
        else:
            md += f"- [ ] **TOO SMALL TO QUOTE**: {claim_name} (n = {n} < 30). *Requires at least 30 observations on the live site before quoting numbers on resume.* Current: {detail}\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)


def main():
    log_path = find_log_file()
    print(f"Reading logs from: {log_path}")
    records = load_website_logs(log_path)
    print(f"Loaded {len(records)} website log records.")

    summary = analyze_records(records)

    report_md_path = Path("benchmarks/web_usage_report.md")
    data_csv_path = Path("benchmarks/web_usage_data.csv")

    write_csv(summary, data_csv_path)
    write_markdown(summary, report_md_path)

    print(f"Wrote report to {report_md_path}")
    print(f"Wrote CSV to {data_csv_path}")


if __name__ == "__main__":
    main()
