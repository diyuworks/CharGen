# Real Website Usage Report (Live Logs)

**Source**: Website traffic only (`source == "website"`)  
**Time Window**: `2026-10-12T08:57:01.881234Z` to `2026-10-12T10:05:31.451698Z`  
**Unique Characters Logged**: **24**  

---

## 1. Summary of Activity

| Metric | Sample Size (n) | Result | Assessment |
| :--- | :--- | :--- | :--- |
| **Characters Created** | 22 | 22 characters | TOO SMALL TO QUOTE (n < 30) |
| **Avatar Cascade Calls** | 26 | 26 avatars (24 first-time, 2 regenerations) | TOO SMALL TO QUOTE (n < 30) |
| **Chat Messages** | 0 | 0 messages | TOO SMALL TO QUOTE (n < 30) |
| **Chat Summaries (>20 msgs)** | 0 | 0 summaries | TOO SMALL TO QUOTE (n < 30) |

---

## 2. Character Generation & JSON Reliability

- **Raw JSON First-Attempt Failure Rate**: **9.09%** (2/22)  
  - 95% Wilson Score CI: `[2.53%, 27.81%]`
- **Pipeline Final Success Rate**: **100.0%** (22/22)  
  - 95% Wilson Score CI: `[85.13%, 100.0%]`
- **Latency**: p50 = **9.11s**, p95 = **23.13s**

---

## 3. Avatar Cascade Distribution (Exact Logged Tiers)

| Tier Key | Provider / Destination | Count | Share (%) | 95% Wilson CI |
| :--- | :--- | :--- | :--- | :--- |
| `tier1_pollinations` | Pollinations AI | 6 | 23.08% | `[11.03%, 42.05%]` |
| `tier2_stable_horde` | Stable Horde (Decentralized) | 8 | 30.77% | `[16.5%, 49.99%]` |
| `tier3_dicebear` | DiceBear SVG Fallback | 12 | 46.15% | `[28.76%, 64.54%]` |
| **Total Real AI Images** | `tier1_pollinations` + `tier2_stable_horde` | 14 | **53.85%** | `[35.46%, 71.24%]` |

- **Avatar Generation Breakdown**: 24 first-time generations, 2 manual regenerations
- **Avatar Latency**: p50 = **3.85s**, p95 = **55.5s**

---

## 4. Chat & Memory Performance

- **User/Assistant Turns Logged**: 0
- **Chat Turn Latency**: p50 = **N/A (no data)**, p95 = **N/A (no data)**
- **Memory Summaries Triggered**: 0 (for chats extending past 20 messages)
- **Summary Generation Latency**: p50 = **N/A (no data)**, p95 = **N/A (no data)**

---

## 5. Safe Resume Claims

> **Statistical Threshold Rule**: Any claim with sample size **n < 30** or confidence interval wider than 20 percentage points is marked as **"Too small to quote"** to prevent misleading claims.

- **TOO SMALL TO QUOTE**: Character generation JSON repair recovery (n = 22 < 30). Requires at least 30 observations on the live site before quoting numbers on resume. Current: Observed final success 100.0% (95% CI: [85.13%, 100.0%])
- **TOO SMALL TO QUOTE**: Avatar 3-tier cascade resilience (n = 26 < 30). Requires at least 30 observations on the live site before quoting numbers on resume. Current: Observed AI avatar generation rate 53.85% (95% CI: [35.46%, 71.24%])
- **TOO SMALL TO QUOTE**: Interactive chat conversation memory (n = 0 < 30). Requires at least 30 observations on the live site before quoting numbers on resume. Current: Observed 0 chat turns, 0 summaries past 20-message window

---

## 6. Offline Benchmark Suite Results (results_v2.json)

> **Note on offline benchmark isolation**: The figures below come directly from offline test suites (`results_v2.json`) under synthetic tests. They are kept separate from live website usage numbers above.

### A. JSON Parsing Reliability Benchmark (Controlled N = 100)
- **Old Unconstrained Implementation**:
  - Raw JSON Failure Rate: **None%** (95% CI: `[0%, 0%]`)
  - Pipeline Final Success: **None%**
- **New Guided Implementation (`response_format` + JSON repair cascade)**:
  - Raw JSON Failure Rate: **None%** (95% CI: `[0%, 0%]`)
  - Pipeline Final Success: **None%** (95% CI: `[0%, 0%]`)

### B. Avatar Cascade Resilience Benchmark (Controlled N = 30)
- **Old Unauthenticated Burst Mode**:
  - Real AI Image Rate: **3.33%** (1/30)
  - Tier 3 Fallback Rate: **96.67%**
- **New Token-Enabled Resilient Mode**:
  - Real AI Image Rate: **10.0%** (95% CI: `[3.46%, 25.62%]`)
  - Tier Breakdown: Tier 1 = 3, Tier 2 = 0, Tier 3 = 27
