# 🔐 CharGen - Environment Setup

After cloning the repo, you need to create 2 `.env` files:

---

## 1. Backend `.env`
**Path:** `ai-character-platform/backend/.env`

```env
NVIDIA_API_KEY=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
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=ai_characters
DEBUG=True
```

---

## 2. Frontend `.env`
**Path:** `ai-character-platform/frontend/.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Setup Steps
1. `git clone https://github.com/diyuworks/CharGen.git`
2. Create both `.env` files above
3. **Backend:** `cd ai-character-platform/backend` → `pip install -r requirements.txt` → `python -m uvicorn app.main:app --reload`
4. **Frontend:** `cd ai-character-platform/frontend` → `npm install` → `npm run dev`
