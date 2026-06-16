# AI Female Character Platform

Scalable AI character generation platform — generates realistic female characters using Google Gemini, stores them in MongoDB, and serves them via a FastAPI backend + React frontend.

Built for 10M+ characters with proper pagination, indexing, and batch generation.

---

## Architecture

```
Frontend (React + Vite)     ──►  Backend (FastAPI)  ──►  MongoDB
                                        │
                                  Google Gemini API
```

### What it does (Phase 1 — this repo)
- Generate realistic female characters (name, backstory, personality, system prompt, avatar prompt, etc.)
- Store characters in MongoDB with indexes for fast queries
- Browse/search/filter characters in a gallery
- View full character details including copy-ready system prompts

### What comes next (Phase 2 — other team)
- Avatar image generation using stored `avatar_prompt`
- Chat integration using stored `system_prompt`

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)
- Google Gemini API key → https://aistudio.google.com/

---

## Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and set:
#   GEMINI_API_KEY=your_key_here
#   MONGODB_URL=mongodb://localhost:27017

# Run the server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# VITE_API_URL is already set to http://localhost:8000/api/v1

# Run dev server
npm run dev
```

Frontend available at: http://localhost:5173

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/generate-character` | Generate 1–50 characters |
| POST | `/api/v1/save-character` | Save a character manually |
| GET | `/api/v1/characters` | Paginated gallery (search, filter) |
| GET | `/api/v1/characters/stats` | Dashboard stats |
| GET | `/api/v1/character/{id}` | Single character |
| DELETE | `/api/v1/character/{id}` | Delete character |

### Generate request example

```json
POST /api/v1/generate-character
{
  "category": "Doctor",
  "nationality": "Indian",
  "count": 5
}
```

### List query parameters
- `page` (default: 1)
- `page_size` (default: 20, max: 100)
- `category` — filter by category
- `nationality` — filter by nationality
- `search` — full-text search on name/occupation/description

---

## Scalability Notes

**For 10M+ characters:**

1. **Batch generation** — use `count: 20` per request (Gemini handles 10 per API call internally)
2. **MongoDB indexes** — already created on `name`, `category`, `occupation`, `nationality`, `created_at`
3. **Compound index** — `(category, nationality, created_at)` for filtered gallery queries
4. **Pagination** — all listing endpoints are paginated, never loads full collection
5. **Bulk insert** — uses `insert_many` for batch saves

**To run bulk generation (e.g. 10,000 characters):**
```bash
# Simple curl loop
for i in $(seq 1 500); do
  curl -X POST http://localhost:8000/api/v1/generate-character \
    -H "Content-Type: application/json" \
    -d '{"count": 20}'
  sleep 1
done
```

---

## Project Structure

```
ai-character-platform/
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # FastAPI route handlers
│   │   ├── core/
│   │   │   ├── config.py          # Settings from .env
│   │   │   └── database.py        # MongoDB connection + indexes
│   │   ├── models/character.py    # MongoDB document model
│   │   ├── schemas/character.py   # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── gemini_service.py  # Gemini API + retry logic
│   │   │   └── character_service.py # CRUD business logic
│   │   ├── prompts/
│   │   │   └── character_prompt.py # Gemini prompt templates
│   │   └── main.py                # App entry point
│   └── requirements.txt
│
└── frontend/
    └── src/
        ├── components/            # Reusable UI components
        ├── pages/                 # Dashboard, Generate, Gallery
        ├── services/api.ts        # API client
        └── types/character.ts     # TypeScript types
```

---

## Integration Notes for Chatbot Team

When your team is ready to integrate:

1. Each character already has a `system_prompt` field — pass this directly to your LLM as the system message
2. Each character has a `greeting` field — use this as the first message shown to users
3. Each character has an `avatar_prompt` field — pass this to your image generation service (Stable Diffusion, DALL-E, Midjourney API, etc.)
4. The `GET /api/v1/character/{id}` endpoint returns everything your chatbot needs

---

## License

Internal use — [Your Company Name]
