# TruthScan Implementation Checklist

## 🔑 API Keys & Secrets
You need to obtain these keys and add them to your `backend/.env` file.

- [ ] **Google Gemini API Key**
    - **Purpose**: Core reasoning agent and text analysis.
    - **Get it here**: [Google AI Studio](https://makersuite.google.com/app/apikey)
    - **Env Var**: `GOOGLE_API_KEY`

- [ ] **HuggingFace API Token**
    - **Purpose**: Accessing specialized detection models (Text, Image, Video) via Inference API.
    - **Get it here**: [HuggingFace Settings](https://huggingface.co/settings/tokens)
    - **Env Var**: `HUGGINGFACE_API_TOKEN`

- [ ] **Tavily API Key**
    - **Purpose**: Web search for fact-checking agent.
    - **Get it here**: [Tavily](https://tavily.com/)
    - **Env Var**: `TAVILY_API_KEY`

- [ ] **Database URL (PostgreSQL)**
    - **Purpose**: Primary database for user data and logs.
    - **Get it here**: [Supabase](https://supabase.com/) or [Neon](https://neon.tech/)
    - **Env Var**: `DATABASE_URL`
    - **Format**: `postgresql://user:password@host:port/dbname`

## 🛠️ Setup Steps

### Backend
1.  Navigate to `backend/`.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate it: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4.  Install dependencies: `pip install -r requirements.txt`
5.  Run the server: `uvicorn app.main:app --reload`

### Frontend (Future)
1.  Navigate to `frontend/`.
2.  Install dependencies: `npm install`
3.  Run dev server: `npm run dev`
