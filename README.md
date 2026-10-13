# CharGen: Full-Stack AI Character Generation & Interactive Chat Platform

An end-to-end AI character platform featuring structured character synthesis, a resilient 3-tier avatar generation cascade, and interactive messaging with running memory summarization.

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.10+) with async route handlers, application lifespan database connection management (`ai-character-platform/backend/app/main.py`), and Motor (`AsyncIOMotorClient`) for non-blocking MongoDB access (`ai-character-platform/backend/app/core/database.py`).
- **Frontend**: React 18 with TypeScript, Vite, Tailwind CSS, Lucide Icons, and Framer Motion for gesture-driven character discovery (`ai-character-platform/frontend/src/pages/Swipe.tsx`).
- **LLM Engine**: NVIDIA NIM API running `meta/llama-3.2-11b-vision-instruct` (`ai-character-platform/backend/app/core/config.py`) for structured JSON character synthesis and interactive multi-turn messaging.
- **Database**: MongoDB with registered indexes for character querying, chronological chat message retrieval, cached conversation summaries, and user favorites (`ai-character-platform/backend/app/core/database.py`).

---

## Engineering Implementation & Core Pipelines

### 1. Robust JSON Generation & Repair Engine
Vision-instruct LLMs can occasionally generate malformed JSON syntax (unescaped quotes, smart quotes, trailing commas, or markdown fences) that breaks standard deserialization.
- **Bracket-Depth Extraction** (`ai-character-platform/backend/app/services/gemini_service.py`): Traverses raw model output tracking bracket nesting depth:
  ```python
  for i, ch in enumerate(text):
      if ch != "{":
          continue
      depth = 0
      for j, c in enumerate(text[i:], i):
          if c == "{":
              depth += 1
          elif c == "}":
              depth -= 1
          if depth == 0:
              candidate = text[i:j+1]
  ```
- **Syntax Normalization Heuristics** (`ai-character-platform/backend/app/services/gemini_service.py`): Converts smart quotes to straight quotes, strips stray control characters, and removes trailing commas before `}` or `]`:
  ```python
  text = text.replace("\u2018", "'").replace("\u2019", "'")
  text = text.replace("\u201c", '"').replace("\u201d", '"')
  text = re.sub(r",\s*([}\]])", r"\1", text)
  ```
- **Linear Backoff Retries** (`ai-character-platform/backend/app/services/gemini_service.py`): Executes up to 5 attempts with linear backoff (`1.5 * attempt` seconds) if validation or parsing fails.

### 2. 3-Tier Avatar Generation Cascade
Falls back to a deterministic DiceBear avatar when AI tiers fail, so characters still get an avatar (`ai-character-platform/backend/app/services/avatar_service.py`):
- **Tier 1 (Pollinations AI / Flux)**: Primary realistic image synthesis provider with a 45s HTTP timeout and transient error retries.
- **Tier 2 (Stable Horde)**: Distributed worker network fallback with asynchronous job submission and polling. If an HTTP 403 kudos or demand error occurs, it handles the error gracefully by falling back immediately without unhandled crashes:
  ```python
  if response.status_code == 403:
      body = response.text[:200].replace("\n", " ")
      print(f" Stable Horde 403: {body}")
      return None, "horde_403_kudos"
  ```
- **Tier 3 (DiceBear SVG Fallback)**: Deterministic vector avatar generator using character name and gender seeds, ensuring complete cascade availability even when upstream AI services are unavailable.

### 3. Interactive Chat with Hybrid Sliding-Window Memory
- **Verbatim Window** (`ai-character-platform/backend/app/services/chat_service.py`): Keeps the 20 most recent messages verbatim in prompt context:
  ```python
  MAX_HISTORY_MESSAGES = 20
  ```
- **Inline Running Summarizer** (`ai-character-platform/backend/app/services/chat_service.py`): When conversation length exceeds 20 messages, older messages are summarized inline during the request turn using `_summarize_messages(character_name, messages)` (delegated via `asyncio.to_thread`):
  ```python
  summary_text = await asyncio.to_thread(_summarize_messages, character_name, older_messages)
  ```
  The summary is cached and upserted into the MongoDB `chat_summaries` collection to avoid redundant summarization on subsequent turns.
- **Persona Behavior Wrapper** (`ai-character-platform/backend/app/services/chat_service.py`): Enforces natural conversational texting:
  ```python
  rules = (
      f"You are texting as {character_name} in a casual chat — not writing an essay, "
      "not assisting a customer. Follow these rules strictly:\n\n"
      "- Reply like a real person texting, not an AI assistant...\n"
      "- Default to SHORT replies: 1-3 sentences for most messages...\n"
      "- Use contractions (I'm, don't, that's), casual phrasing, and occasional sentence fragments...\n"
  )
  ```

### 4. Frontend Architecture & Real Pages
The frontend interface (`ai-character-platform/frontend/src/pages/`) consists of 6 dedicated pages:
- **`GenerateCharacter.tsx`**: Structured character synthesis wizard with async avatar polling.
- **`Swipe.tsx`**: Framer Motion touch/drag gesture discovery deck for liking and passing characters.
- **`ChatPage.tsx`**: Real-time messaging interface with active character persona and memory.
- **`ChatList.tsx`**: Recent conversations list and messaging hub.
- **`Gallery.tsx`**: Filterable character catalog with text search, category filtering, and bulk avatar generation.
- **`Dashboard.tsx`**: Grid of generated characters with search, category/gender filtering, follower counts, and deletion.
- **Favorites Management**: Managed via custom React hook `ai-character-platform/frontend/src/hooks/useFavorites.ts` with dedicated viewing tab on `Dashboard.tsx`.

---

## Empirical Reliability Benchmarks

All metrics were measured empirically using real API calls against `meta/llama-3.2-11b-vision-instruct` and recorded in `benchmarks/RESULTS.md`. Production website logs (`source: website`) and scripted benchmarks (`source: benchmark`) are strictly separated.

### Character JSON Generation Benchmark ($n = 100$ calls)
- **Model**: `meta/llama-3.2-11b-vision-instruct`
- **Raw JSON First-Attempt Valid**: **86.0%** (86/100, 95% Wilson CI: `[77.86%, 91.48%]`)
- **Final Pipeline Success Rate**: **100.0%** (100/100, 95% Wilson CI: `[96.30%, 100.0%]`) with repair heuristics and retries.
- **Attempts Distribution**: 86 resolved on Attempt 1; 11 resolved on Attempt 2; 2 resolved on Attempt 3; 1 resolved on Attempt 4; 0 unresolved failures.

### Avatar Generation Cascade Benchmark ($n = 30$ calls per run mode)
- **Old (Burst / Unauthenticated)**: Real AI Image Rate = **6.67%** (2/30, 95% Wilson CI: `[1.85%, 21.32%]`)
- **New (Spaced / Authenticated)**: Real AI Image Rate = **96.67%** (29/30, 95% Wilson CI: `[83.33%, 99.41%]`)
- **Cascade Availability**: **100.0%** (30/30, 95% Wilson CI: `[88.65%, 100.0%]`) across both modes via graceful Tier 3 fallback.

### Chat Memory & Fact Retention Benchmark (Scripted Conversations)
Evaluated across 20 scripted conversations with 100 planted facts, using the platform's real summarizer (`_summarize_messages` in `ai-character-platform/backend/app/services/chat_service.py`):
- **Mode A (Full History, 40 messages verbatim)**: **100.0%** recall (100/100, 95% Wilson CI: `[96.30%, 100.0%]`)
- **Mode B (Window + Real Summary)**: **97.0%** recall (97/100, 95% Wilson CI: `[91.55%, 98.97%]`)
- **API-Verified Token Usage ($n = 5$ completions per length)**:
  - 50 messages: API prompt tokens mean = **1,258.0**
  - 100 messages: API prompt tokens mean = **1,327.0**
- **Live Endpoint Latency ($n = 145$ standard turns, 5 characters $\times$ 30 messages)**:
  - Standard Chat Latency: $p_{50} = 2.21$s, $p_{95} = 21.53$s
  - Inline Summary Turn: $p_{50} = 2.61$s, $p_{95} = 8.09$s ($n = 5$)

---

## Quickstart & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- MongoDB running on `localhost:27017`
- NVIDIA NIM API Key

### 1. Environment Configuration
Copy `.env.example` templates to `.env`:
```bash
# Backend configuration
cp ai-character-platform/backend/.env.example ai-character-platform/backend/.env

# Frontend configuration
cp ai-character-platform/frontend/.env.example ai-character-platform/frontend/.env
```

Populate `ai-character-platform/backend/.env`:
```env
# NVIDIA NIM API (Required)
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_MODEL=meta/llama-3.2-11b-vision-instruct

# MongoDB Database (Required)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=ai_characters

# Avatar Generation Providers (Optional for increased rate limits & AI image reliability)
POLLINATIONS_API_KEY=
STABLE_HORDE_API_KEY=

# Application Settings
DEBUG=True
```

### 2. Backend Setup
```bash
cd ai-character-platform/backend
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd ai-character-platform/frontend
npm install
npm run dev
```

### 4. Running Benchmarks & Verifications
```bash
# Run chat memory & reliability benchmarks (requires MongoDB and NVIDIA NIM API key)
python benchmarks/run_chat_benchmarks.py

# Run audit cross-check
python benchmarks/cross_check.py
```
