# CharGen Consolidated Master Numbers Table

This single consolidated table contains every measured metric across the CharGen platform.
Strict separation is maintained between organic production website logs (`source: website`) and synthetic/scripted benchmarks (`source: benchmark`).

| Metric | Value | $n$ | 95% CI | Source | Raw File | What Changed Between Before/After |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **JSON Raw First-Attempt Valid** | 86.0% (86/100) | 100 | [77.86%, 91.48%] | benchmark | `benchmarks/results_v2.json` | First raw LLM output passed strict JSON deserialization before any repair |
| **JSON Pipeline Success Rate** | 100.0% (100/100) | 100 | [96.30%, 100.0%] | benchmark | `benchmarks/results_v2.json` | Final success after bracket extraction, smart-quote/syntax repair heuristics, and up to 5 retries |
| **Avatar Real-AI Image Rate (Old)** | 6.67% (2/30) | 30 | [1.85%, 21.32%] | benchmark | `benchmarks/results_v3.json` | Burst requests (0s delay), unauthenticated Pollinations, anonymous Horde `0000000000` |
| **Avatar Real-AI Image Rate (New)** | 96.67% (29/30) | 30 | [83.33%, 99.41%] | benchmark | `benchmarks/results_v3.json` | Auth tokens, 402/5xx fallback models, kudos 403 handling AND 10s request spacing all changed together |
| **Avatar Cascade Availability (Old)** | 100.0% (30/30) | 30 | [88.65%, 100.0%] | benchmark | `benchmarks/results_v3.json` | Fell back to DiceBear SVG on AI failure (zero unhandled HTTP/timeout crashes) |
| **Avatar Cascade Availability (New)** | 100.0% (30/30) | 30 | [88.65%, 100.0%] | benchmark | `benchmarks/results_v3.json` | Falls back to DiceBear SVG on AI failure (zero unhandled HTTP/timeout crashes) |
| **Fact Retention: Mode A (Full History)** | 100.0% (100/100) | 100 | [96.30%, 100.0%] | benchmark | `benchmarks/retention_benchmark.json` | All 40 messages provided verbatim in context across 20 scripted benchmark conversations |
| **Fact Retention: Mode B (Window + Real Summary)** | 97.0% (97/100) | 100 | [91.55%, 98.97%] | benchmark | `benchmarks/retention_benchmark.json` | Recent 20 turns verbatim + real LLM summary (`_summarize_messages`) of older turns |
| **Chat Endpoint Latency (Without Summary)** | p50: 2.21s, p95: 21.53s | 145 | - | benchmark | `benchmarks/chat_endpoint_benchmark.json` | Live API turns where context fits in verbatim window ($n=145$ calls across 5 characters) |
| **Chat Endpoint Latency (With Summary Turn)** | p50: 2.61s, p95: 8.09s | 5 | - | benchmark | `benchmarks/chat_endpoint_benchmark.json` | Inline summarization turn (`asyncio.to_thread(_summarize_messages)`) updating DB summary |
| **Chat Ground Truth Prompt Tokens (50 msgs)** | 1,258.0 mean | 5 | - | benchmark | `benchmarks/chat_samples.json` | Verified `usage.prompt_tokens` from NVIDIA NIM API completions ($n=5$ real API calls) |
| **Chat Ground Truth Prompt Tokens (100 msgs)** | 1,327.0 mean | 5 | - | benchmark | `benchmarks/chat_samples.json` | Verified `usage.prompt_tokens` from NVIDIA NIM API completions ($n=5$ real API calls) |
| **Chat Prompt Reduction (20 msgs)** | 0.00% (0 tok saved) | 1 | - | benchmark | `benchmarks/chat_samples.json` | All 20 turns fit within verbatim window; no compaction triggered |
| **Chat Prompt Reduction (50 msgs)** | 37.09% (889 tok saved) | 1 | - | benchmark | `benchmarks/chat_samples.json` | 30 older messages compacted into real LLM summary (2,397 vs 1,508 tiktoken) |
| **Chat Prompt Reduction (100 msgs)** | 64.28% (2840 tok saved) | 1 | - | benchmark | `benchmarks/chat_samples.json` | 80 older messages compacted into real LLM summary (4,418 vs 1,578 tiktoken) |
| **Chat Prompt Reduction (200 msgs)** | 82.10% (6961 tok saved) | 1 | - | benchmark | `benchmarks/chat_samples.json` | 180 older messages compacted into real LLM summary (8,479 vs 1,518 tiktoken) |
| **Test Coverage (pytest-cov)** | 43% (285/658 stmts) | 658 | - | benchmark | `pytest --cov=app` | Measured unit test coverage across backend service modules |
| **Unit Test Pass Rate** | 100.0% (13/13) | 13 | [77.19%, 100.0%] | benchmark | `ai-character-platform/backend/tests/` | Cascade, json repair, chat memory unit tests |
| **Website (Current Code): Real AI Rate** | 50.00% (12/24) | 24 | [31.43%, 68.57%] | website | `generation_metrics.jsonl` | Standard cascade rows (`tier1_pollinations`, `tier2_stable_horde`, `tier3_dicebear`) |
| **Website (Current Code): tier1_pollinations** | 25.00% (6/24) | 24 | [12.00%, 44.90%] | website | `generation_metrics.jsonl` | Standard cascade Tier 1 |
| **Website (Current Code): tier2_stable_horde** | 25.00% (6/24) | 24 | [12.00%, 44.90%] | website | `generation_metrics.jsonl` | Standard cascade Tier 2 |
| **Website (Current Code): tier3_dicebear** | 50.00% (12/24) | 24 | [31.43%, 68.57%] | website | `generation_metrics.jsonl` | Standard cascade Tier 3 fallback |
| **Website (All Rows): Real AI Rate** | 53.85% (14/26) | 26 | [35.46%, 71.24%] | website | `generation_metrics.jsonl` | All raw avatar rows (includes 2 legacy inverted cascade rows) |
| **Website (All Rows): tier1_pollinations** | 23.08% (6/26) | 26 | [11.03%, 42.05%] | website | `generation_metrics.jsonl` | All raw avatar rows |
| **Website (All Rows): tier2_stable_horde** | 30.77% (8/26) | 26 | [16.50%, 49.99%] | website | `generation_metrics.jsonl` | Includes 2 legacy `tier1_stable_horde` rows under Stable Horde |
| **Website (All Rows): tier3_dicebear** | 46.15% (12/26) | 26 | [28.76%, 64.54%] | website | `generation_metrics.jsonl` | Initial batch before API keys added |
| **Website (All Rows): Raw JSON Failure Rate** | 9.09% (2/22) | 22 | [2.53%, 27.81%] | website | `generation_metrics.jsonl` | First-attempt json.loads failures |
| **Website (All Rows): Pipeline Success Rate** | 100.0% (22/22) | 22 | [85.13%, 100.0%] | website | `generation_metrics.jsonl` | Pipeline recovery via repair |
| **Website (All Rows): Chat Messages Logged** | 0 | 0 | - | website | `generation_metrics.jsonl` | No organic user chat turns logged on website yet |
| **Website (All Rows): Chat Summaries Logged** | 0 | 0 | - | website | `generation_metrics.jsonl` | No chat summaries triggered on website yet |
