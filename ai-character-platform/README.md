# CharGen: AI Character Generation and Interactive Chat Platform

A full-stack application for generating AI characters and chatting with them. It provides structured character creation, a 3-tier avatar generation fallback, and chat messaging with running memory summaries.

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.10+) with async route handlers, application lifespan database management (`backend/app/main.py:19-31`), and Motor (`AsyncIOMotorClient`) for non-blocking MongoDB interactions (`backend/app/core/database.py:1-40`).
- **Frontend**: React 18 with TypeScript, Vite, Tailwind CSS, Lucide Icons, and Framer Motion for touch and drag character discovery (`frontend/src/pages/Swipe.tsx:1-186`).
- **LLM Engine**: NVIDIA NIM API running `meta/llama-3.2-11b-vision-instruct` (`backend/app/core/config.py:13`) for structured JSON character synthesis and interactive messaging.
- **Database**: MongoDB with registered indexes for character querying, chronological chat message retrieval, cached conversation summaries, and user favorites (`backend/app/core/database.py:13-37`).

---

## Implementation Details

### 1. JSON Generation and Repair
Vision-instruct LLMs can generate malformed JSON syntax (unescaped quotes, smart quotes, trailing commas, or markdown code fences) that causes strict parsers to fail.
- **Bracket-Depth Extraction** (`backend/app/services/gemini_service.py:34-57`): Traverses raw text tracking bracket nesting depth to extract balanced JSON candidates without relying on markdown code fences.
- **Syntax Normalization Heuristics** (`backend/app/services/gemini_service.py:60-77`): Normalizes unicode curly and smart quotes (`\u2018`, `\u2019`, `\u201c`, `\u201d`) to straight quotes, strips stray control characters, and removes trailing commas before `}` or `]`.
- **Linear Backoff Retries** (`backend/app/services/gemini_service.py:130-187`): Up to 5 attempts with linear backoff (`1.5 * attempt` seconds) if validation or JSON decoding fails.

### 2. 3-Tier Avatar Generation Fallback
Ensures every character receives an avatar image by falling back across tiers (`backend/app/services/avatar_service.py:281-296`):
- **Tier 1 (Pollinations AI / Flux)** (`backend/app/services/avatar_service.py:98-146`): Primary realistic image generation with a 45s HTTP timeout and a 2-attempt transient error retry loop.
- **Tier 2 (Stable Horde)** (`backend/app/services/avatar_service.py:148-235`): Distributed async fallback submitting jobs and polling up to 12 times at 5s intervals (60s maximum wait). Immediately falls back if HTTP 403 (kudos or demand limit) is returned.
- **Tier 3 (DiceBear SVG Fallback)** (`backend/app/services/avatar_service.py:246-258`): Falls back to a deterministic DiceBear vector avatar (using character name and gender seeds) when AI tiers fail or time out.

### 3. Interactive Chat with Sliding-Window Memory
- **Verbatim Window** (`backend/app/services/chat_service.py:21, 157-162`): Retains the 20 most recent messages (`MAX_HISTORY_MESSAGES = 20`) verbatim in the prompt context.
- **Inline Running Summaries** (`backend/app/services/chat_service.py:163-181`): When chat history exceeds 20 messages, older messages are summarized inline during the request (thread-delegated via `asyncio.to_thread(_summarize_messages)`) into 3-5 factual memory bullet points, cached and upserted in the MongoDB `chat_summaries` collection.
- **Persona Behavior Wrapper** (`backend/app/services/chat_service.py:206-240`): Enforces concise texting habits (1-3 sentences default, contractions, natural tone, reactions to nonsensical input, and no AI assistant disclaimers).

### 4. Discovery and State Management
- **Swipe Discovery Deck** (`frontend/src/pages/Swipe.tsx:1-186`): Framer Motion gesture swipe deck supporting touch drag, card rotations, and like or pass actions.
- **Favorites Persistence** (`frontend/src/hooks/useFavorites.ts:1-33`): Client-side optimistic toggle reconciled against backend MongoDB `/api/v1/favorites` endpoints.

---

## Reliability Benchmarks

All metrics were measured using direct model calls against `meta/llama-3.2-11b-vision-instruct` and recorded in `benchmarks/results_v2.json`:

### Character JSON Generation Benchmark (n = 100 calls)
- **Model**: `meta/llama-3.2-11b-vision-instruct`
- **Raw JSON First-Attempt Failure Rate**: **14.0%** (14/100, 95% Wilson CI: `[8.53%, 22.14%]`)
- **Final Pipeline Success Rate**: **100.0%** (100/100, 95% Wilson CI: `[96.30%, 100.0%]`)
- **Attempts Distribution**: 86 resolved on Attempt 1; 11 resolved on Attempt 2; 2 resolved on Attempt 3; 1 resolved on Attempt 4; 0 failures.
- **Average Latency**: 14.85 seconds.

### Avatar Generation Cascade Benchmark
Evaluated across separate runs in `benchmarks/results_v2.json`:

| Run Mode | Sample Size (n) | Tier 1 (Pollinations) | Tier 2 (Stable Horde) | Tier 3 (DiceBear Fallback) | Real AI Image % (95% Wilson CI) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Old (Burst / Unauthenticated)** | n = 30 | 1 / 30 (3.33%) | 0 / 30 (0.00%) | 29 / 30 (96.67%) | 3.33% `[0.59%, 16.67%]` |
| **New (Resilient / Spaced)** | n = 30 | 3 / 30 (10.00%) | 0 / 30 (0.00%) | 27 / 30 (90.00%) | 10.00% `[3.46%, 25.62%]` |
| **Pooled Total** | n = 60 pooled | 4 / 60 (6.67%) | 0 / 60 (0.00%) | 56 / 60 (93.33%) | 6.67% `[2.62%, 15.89%]` |

*Note: Stable Horde (Tier 2) returned HTTP 403 kudos limits during test runs; the cascade fell back to Tier 3 DiceBear SVG avatars, avoiding unhandled request errors.*

---

## Quickstart and Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- MongoDB instance running on `localhost:27017`
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
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_MODEL=meta/llama-3.2-11b-vision-instruct
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=ai_characters
POLLINATIONS_API_KEY=
STABLE_HORDE_API_KEY=
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

### 4. Running Benchmarks
```bash
python benchmarks/reliability_benchmark_v2.py
python benchmarks/report_from_logs.py
```
