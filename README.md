# CharGen: AI Character Generation and Interactive Chat Platform

A full-stack web application for generating AI characters and chatting with them in real time. It includes structured character generation, a 3-tier avatar generation fallback, and interactive chat with sliding-window memory and running summaries.

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.10+) with async route handlers, application lifespan database connection management (`ai-character-platform/backend/app/main.py`), and Motor (`AsyncIOMotorClient`) for non-blocking MongoDB access (`ai-character-platform/backend/app/core/database.py`).
- **Frontend**: React 18 with TypeScript, Vite, Tailwind CSS, Lucide Icons, and Framer Motion for gesture-driven character discovery (`ai-character-platform/frontend/src/pages/Swipe.tsx`).
- **LLM Engine**: NVIDIA NIM API running `meta/llama-3.2-11b-vision-instruct` (`ai-character-platform/backend/app/core/config.py`) for structured JSON character synthesis and interactive multi-turn messaging.
- **Database**: MongoDB with registered indexes for character querying, chronological chat message retrieval, cached conversation summaries, and user favorites (`ai-character-platform/backend/app/core/database.py`).

---

## Implementation Details and Pipelines

### 1. JSON Parsing and Repair
Vision-instruct LLMs can occasionally output invalid JSON (unescaped quotes, smart quotes, trailing commas, or markdown code fences) that fails standard deserialization.
- **Bracket-Depth Extraction** (`ai-character-platform/backend/app/services/gemini_service.py`): Scans raw model text while tracking bracket nesting depth:
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
- **Syntax Normalization Heuristics** (`ai-character-platform/backend/app/services/gemini_service.py`): Replaces smart quotes with straight quotes, strips stray control characters, and removes trailing commas before `}` or `]`:
  ```python
  text = text.replace("\u2018", "'").replace("\u2019", "'")
  text = text.replace("\u201c", '"').replace("\u201d", '"')
  text = re.sub(r",\s*([}\]])", r"\1", text)
  ```
- **Linear Backoff Retries** (`ai-character-platform/backend/app/services/gemini_service.py`): Retries up to 5 times with linear backoff (`1.5 * attempt` seconds) if validation or parsing fails.

### 2. 3-Tier Avatar Generation
Falls back to a deterministic DiceBear avatar when AI image services fail, ensuring characters still receive an avatar (`ai-character-platform/backend/app/services/avatar_service.py`):
- **Tier 1 (Pollinations AI / Flux)**: Primary realistic image provider with a 45s HTTP timeout and transient error retries.
- **Tier 2 (Stable Horde)**: Distributed worker network fallback with asynchronous job submission and polling. If an HTTP 403 kudos or demand error occurs, it catches the error and falls back immediately without crashing:
  ```python
  if response.status_code == 403:
      body = response.text[:200].replace("\n", " ")
      print(f" Stable Horde 403: {body}")
      return None, "horde_403_kudos"
  ```
- **Tier 3 (DiceBear SVG Fallback)**: Deterministic vector avatar generator using character name and gender seeds, keeping the avatar pipeline available even when external AI image services are down.

### 3. Interactive Chat with Sliding-Window Memory
- **Verbatim Window** (`ai-character-platform/backend/app/services/chat_service.py`): Keeps the 20 most recent messages verbatim in prompt context:
  ```python
  MAX_HISTORY_MESSAGES = 20
  ```
- **Inline Running Summarizer** (`ai-character-platform/backend/app/services/chat_service.py`): When conversation length exceeds 20 messages, older messages are summarized inline during the request turn using `_summarize_messages(character_name, messages)` (run in a separate thread via `asyncio.to_thread`):
  ```python
  summary_text = await asyncio.to_thread(_summarize_messages, character_name, older_messages)
  ```
  The summary is cached and upserted into the MongoDB `chat_summaries` collection to avoid re-summarizing on subsequent turns.
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

### 4. Frontend Structure and Pages
The frontend interface (`ai-character-platform/frontend/src/pages/`) consists of 6 dedicated pages:
- **`GenerateCharacter.tsx`**: Structured character creation wizard with async avatar polling.
- **`Swipe.tsx`**: Framer Motion touch and drag gesture discovery deck for liking and passing characters.
- **`ChatPage.tsx`**: Real-time messaging interface with active character persona and memory.
- **`ChatList.tsx`**: Recent conversations list and messaging hub.
- **`Gallery.tsx`**: Filterable character catalog with text search, category filtering, and bulk avatar generation.
- **`Dashboard.tsx`**: Grid of generated characters with search, category and gender filtering, follower counts, and deletion.
- **Favorites Management**: Managed through custom React hook `ai-character-platform/frontend/src/hooks/useFavorites.ts` with a dedicated viewing tab on `Dashboard.tsx`.

---

## Reliability Benchmarks

All metrics were measured using real API calls against `meta/llama-3.2-11b-vision-instruct` and recorded in `benchmarks/RESULTS.md`. Production website logs (`source: website`) and scripted benchmarks (`source: benchmark`) are kept separate.

### Character JSON Generation Benchmark (n = 100 calls)
- **Model**: `meta/llama-3.2-11b-vision-instruct`
- **Raw JSON First-Attempt Valid**: **86.0%** (86/100, 95% Wilson CI: `[77.86%, 91.48%]`)
- **Final Pipeline Success Rate**: **100.0%** (100/100, 95% Wilson CI: `[96.30%, 100.0%]`) with repair heuristics and retries.
- **Attempts Distribution**: 86 resolved on Attempt 1; 11 resolved on Attempt 2; 2 resolved on Attempt 3; 1 resolved on Attempt 4; 0 unresolved failures.

### Avatar Generation Cascade Benchmark (n = 30 calls per run mode)
- **Old (Burst / Unauthenticated)**: Real AI Image Rate = **6.67%** (2/30, 95% Wilson CI: `[1.85%, 21.32%]`)
- **New (Spaced / Authenticated)**: Real AI Image Rate = **96.67%** (29/30, 95% Wilson CI: `[83.33%, 99.41%]`)
- **Cascade Availability**: **100.0%** (30/30, 95% Wilson CI: `[88.65%, 100.0%]`) across both modes via Tier 3 fallback.

### Chat Memory and Fact Retention Benchmark (Scripted Conversations)
Evaluated across 20 scripted conversations with 100 planted facts, using the platform's summarizer (`_summarize_messages` in `ai-character-platform/backend/app/services/chat_service.py`):
- **Mode A (Full History, 40 messages verbatim)**: **100.0%** recall (100/100, 95% Wilson CI: `[96.30%, 100.0%]`)
- **Mode B (Window + Real Summary)**: **97.0%** recall (97/100, 95% Wilson CI: `[91.55%, 98.97%]`)
- **API-Verified Token Usage (n = 5 completions per length)**:
  - 50 messages: API prompt tokens mean = **1,258.0**
  - 100 messages: API prompt tokens mean = **1,327.0**
- **Live Endpoint Latency (n = 145 standard turns, 5 characters x 30 messages)**:
  - Standard Chat Latency: p50 = 2.21s, p95 = 21.53s
  - Inline Summary Turn: p50 = 2.61s, p95 = 8.09s (n = 5)

---

## Quickstart and Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
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

### 4. Running Benchmarks and Verifications
```bash
# Run chat memory & reliability benchmarks (requires MongoDB and NVIDIA NIM API key)
python benchmarks/run_chat_benchmarks.py

# Run audit cross-check
python benchmarks/cross_check.py
```
