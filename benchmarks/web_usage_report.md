# Real Website Usage Report (Live Logs)

**Source**: Website traffic only (`source == "website"`)  
**Generated On**: Live Log Analysis  

---

## 1. Summary of Activity

| Metric | Sample Size (n) | Result | Assessment |
| :--- | :--- | :--- | :--- |
| **Characters Created** | 22 | 22 characters | TOO SMALL TO QUOTE (n < 30) |
| **Avatar Cascade Calls** | 26 | 26 avatars | TOO SMALL TO QUOTE (n < 30) |
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

## 3. Avatar Cascade Distribution

| Tier | Provider | Count | Split (%) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Primary AI (Stable Horde Photorealistic / Pollinations) | 8 | 30.77% | Primary realistic AI generator |
| **Tier 2** | Secondary AI (Pollinations / Horde Fallback) | 6 | 23.08% | Secondary AI generation tier |
| **Tier 3** | DiceBear | 12 | 46.15% | Deterministic SVG fallback |
| **Total AI**| Tier 1 + Tier 2 | 14 | **53.85%** | Real AI generated images |

- **Avatar Latency**: p50 = **3.85s**, p95 = **55.5s**

---

## 4. Chat & Memory Performance

- **User/Assistant Turns Logged**: 0
- **Chat Turn Latency**: p50 = **0.0s**, p95 = **0.0s**
- **Memory Summaries Triggered**: 0 (for chats extending past 20 messages)
- **Summary Generation Latency**: p50 = **0.0s**, p95 = **0.0s**

---

## 5. Safe Resume Claims

> **Statistical Threshold Rule**: Any claim with sample size **n < 30** is strictly flagged as **"Too small to quote"** to prevent misleading or untruthful resume claims.

- [ ] **TOO SMALL TO QUOTE**: Character generation JSON repair recovery (n = 22 < 30). *Requires at least 30 observations on the live site before quoting numbers on resume.* Current: Observed final success 100.0% (95% CI: [85.13%, 100.0%])
- [ ] **TOO SMALL TO QUOTE**: Avatar 3-tier cascade resilience (n = 26 < 30). *Requires at least 30 observations on the live site before quoting numbers on resume.* Current: Observed AI avatar generation rate 53.85% across 3 tiers
- [ ] **TOO SMALL TO QUOTE**: Interactive chat conversation memory (n = 0 < 30). *Requires at least 30 observations on the live site before quoting numbers on resume.* Current: Observed 0 chat turns, 0 summaries past 20-message window
