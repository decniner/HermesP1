# POGIBOT — VR Boxing AI Coach: Deployment Guide

## Directory Structure

```
POGIBOT/
├── backend/
│   ├── app.py                # Flask proxy (this repo)
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Template for secrets
│   ├── .env                  # YOUR real API keys (never commit)
│   └── credentials.json      # Google Service Account key (never commit)
└── frontend/
    ├── index.html            # Full static dashboard (GitHub Pages)
    └── pogibot-snippet.js    # Standalone JS snippet for integration
```

---

## 1. Backend Setup (Local Machine)

### Prerequisites
- Python 3.10+
- A Google Cloud Service Account with Sheets API enabled
- Gemini API Key (free tier: https://aistudio.google.com/apikey)
- DeepSeek API Key (https://platform.deepseek.com)

### Step-by-step

```bash
# Navigate to backend
cd ~/projects/POGIBOT/backend

# Create virtual environment
python -m venv .venv

# Activate it
source .venv/Scripts/activate        # Windows (git-bash)
# or: .venv\Scripts\activate          # Windows (cmd/PowerShell)
# or: source .venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — paste your GEMINI_API_KEY, DEEPSEEK_API_KEY, GOOGLE_SHEET_ID

# Add Google Service Account credentials
# Download your credentials.json from Google Cloud Console and place it here
```

### Google Sheets Setup

1. Go to https://console.cloud.google.com/ → Create a project (or use existing)
2. Enable **Google Sheets API**
3. Create a **Service Account** → Download its JSON key → save as `credentials.json`
4. Create a Google Sheet (or use existing)
5. Share the sheet with the service account email (Editor permissions)
6. Copy the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/<THIS_IS_THE_ID>/edit`

Sheets columns are auto-created on first session log.

### Run the Proxy

```bash
cd ~/projects/POGIBOT/backend
source .venv/Scripts/activate
python app.py
```

Expected output:
```
⚡ POGIBOT backend starting on 0.0.0.0:5000
```

Verify:
```bash
curl http://localhost:5000/health
# → {"status": "ok", "missing_keys": []}
```

---

## 2. Frontend Setup (GitHub Pages)

### Option A: Deploy to GitHub Pages

1. Create a repo: `https://github.com/decniner/pogibot`
2. Push `frontend/index.html` to the repo
3. Go to Settings → Pages → deploy from `main` branch `/docs` or root
4. Use `https://decniner.github.io/pogibot/`

### Option B: Run Locally (Live Server)

```bash
cd ~/projects/POGIBOT/frontend
# Using VS Code Live Server extension, or:
python -m http.server 5500
# Open http://localhost:5500
```

### Update CORS in .env (if needed)

If your frontend is at a specific domain:
```
CORS_ORIGIN=https://decniner.github.io
```
Or leave as `*` for development.

---

## 3. Using POGIBOT

1. Make sure the Flask backend is running (`python app.py`)
2. Open the frontend in your browser
3. Paste a YouTube URL of boxing/sparring footage
4. Click **🔥 ANALYZE**
5. Wait ~30-60 seconds for the two-phase AI pipeline

---

## 4. Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Pages (frontend/index.html)                         │
│  - YouTube URL input        │  fetch() to localhost:5000    │
│  - Ratings cards             │                              │
│  - Highlight / Flaw lists   │                              │
│  - Raw verdict display      │                              │
└──────────────────────┬──────────────────────────────────────┘
                       │ POST /analyze {video_url: "..."}
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Flask Proxy (app.py on localhost:5000)                     │
│                                                             │
│  1. Fetch last 3-5 session rows from Google Sheets         │
│  2. Send YouTube URL → Gemini API → structured JSON events │
│  3. Send events + history → DeepSeek → brutal coach text   │
│  4. Log results → Google Sheets (append row)               │
│  5. Return combined response to frontend                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Troubleshooting

| Problem | Fix |
|---------|-----|
| `credentials.json not found` | Download from GCP Console → place in backend/ |
| `Gemini API call failed` | Check GEMINI_API_KEY and model availability |
| `DeepSeek API call failed` | Check DEEPSEEK_API_KEY and credits |
| CORS error in browser | Set CORS_ORIGIN in .env to your frontend domain |
| Connection refused on :5000 | Is the Flask process running? |
| Sheet not updating | Share sheet with service account email (Editor) |
