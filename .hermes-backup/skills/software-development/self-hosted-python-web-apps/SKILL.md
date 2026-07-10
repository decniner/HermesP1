---
name: self-hosted-python-web-apps
description: "Build and deploy self-hosted Python web applications (Streamlit/Gradio) accessible over LAN via phone browser — project setup, headless deployment, dependency management, and live-data patterns."
version: 1.5.0
author: Hermes Agent
tags: [streamlit, gradio, python-web, deployment, lan, self-hosted]
---

# Self-Hosted Python Web Apps

Building a self-hosted Python web app accessible from a phone browser over Wi-Fi. Covers Streamlit (primarily) and Gradio — the full pipeline from scaffold to mobile-accessible deployment on a LAN host.

## When to Use

- User asks for a "self-hosted desktop app with mobile-accessible web UI"
- User wants a Python-based dashboard or analysis tool on LAN
- User specifies Streamlit or Gradio as the frontend framework
- User wants live-updating charts (financial, monitoring, sensor data)

## ⚠️ Mandatory: QA Protocol (User Expectation)

**QA your own work before reporting.** The user will tell you: *"Not working, qa it yourself to make sure it works before asking me."* Do not skip.

1. **Build** the code
2. **Smoke test locally** — syntax, imports, minimal `curl` against `localhost`
3. **Full workflow test** — hit the actual endpoints with real data
4. **Tunnel test** — if deploying via tunnel, verify the full pipeline through it
5. **Report** — only after all above pass

Diagnose and fix failures silently. Do not ask the user to "check if it works" — verify yourself first.

## Project Scaffold (Typical)

```
project-name/
├── app.py              # Streamlit/Gradio entry point
├── analysis.py         # Core logic / data processing
├── requirements.txt    # Dependencies
├── .env                # API keys (gitignored)
├── .env.example        # Template with placeholders
├── .gitignore
└── .venv/              # Virtual environment
```

## Step-by-Step Setup

### 1. Create & Virtualenv

```bash
mkdir -p ~/projects/YourProject && cd ~/projects/YourProject
python -m venv .venv
source .venv/Scripts/activate   # Windows (git-bash)
# source .venv/bin/activate      # Linux/macOS
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. .env Pattern

Use `python-dotenv` to load credentials at app startup:

```python
from dotenv import load_dotenv
load_dotenv()
```

`.env.example` goes in git (safe template), `.env` stays local (gitignored).

## Streamlit Deployment

### Required Env Vars (Headless Mode)

Streamlit prompts for an email on first run in non-interactive environments. This blocks startup. **Always set these:**

```bash
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
STREAMLIT_SERVER_HEADLESS=true
```

### LAN Binding

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

This binds to all interfaces. Accessible at `http://<LAN-IP>:8501` from any device on the same Wi-Fi.

### Full Start Command

```bash
cd ~/projects/YourProject && source .venv/Scripts/activate && \
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
STREAMLIT_SERVER_HEADLESS=true \
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Auto-Refresh / Live Data

Use `@st.cache_data(ttl=N)` with a time-based rerun check:

```python
REFRESH_SECONDS = 10
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

@st.cache_data(ttl=REFRESH_SECONDS)
def load_data(...):
    ...

# Trigger rerun
if time.time() - st.session_state.last_refresh > REFRESH_SECONDS:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()
```

## Gradio Deployment (Alternative)

```bash
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false STREAMLIT_SERVER_HEADLESS=true \
gradio app.py --server-port 7860 --server-address 0.0.0.0
```

Gradio doesn't have the email-onboarding prompt issue.

## Dependency Pitfalls on Windows

### pandas-ta vs ta

`pandas-ta` (aka `pandas_ta`) is NOT available for Python 3.11 on Windows via pip:
```
ERROR: Could not find a version that satisfies the requirement pandas-ta
```

**Fix:** Use the `ta` library instead — different API but equivalent indicators:

| pandas-ta | ta |
|-----------|-----|
| `ta.ema(close, length=9)` | `EMAIndicator(close, window=9).ema_indicator()` |
| `ta.rsi(close, length=14)` | `RSIIndicator(close, window=14).rsi()` |
| `ta.macd(close)` | `MACD(close, window_slow=26, window_fast=12, window_sign=9)` |
| `ta.bbands(close, length=20)` | `BollingerBands(close, window=20, window_dev=2)` |
| `ta.atr(high, low, close, length=14)` | `AverageTrueRange(high, low, close, window=14)` |

```python
from ta.trend import EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange, BollingerBands
```

### yfinance on Windows

Works normally. Watch for MultiIndex columns on `.iloc` access — flatten with:
```python
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
data.columns = [str(c).lower() for c in data.columns]
```

## Reference Files

- `references/sqlite-session-history.md` — Replacing Google Sheets with local SQLite for session history.
- `references/yfinance-crypto-stock-patterns.md` — Symbol normalization, 4H candles, MultiIndex flattening.
- `references/flask-ai-proxy-pattern.md` — 3-tier Flask proxy + AI API integration patterns.
- `references/google-genai-sdk-migration.md` — Migrating `google.generativeai` → `google.genai` SDK.
- `references/gemini-video-analysis.md` — YouTube URL input, file upload, JSON truncation, model probing.
- `references/dual-ai-pipeline.md` — Two-phase AI pipeline: Gemini extraction → DeepSeek reasoning.

## Kanban Task Per Project

Always create a kanban task (`hermes kanban create "..." --body "..."`) for every project build. Mark it complete before the final summary.

## Flask AI Proxy Backend (Dual-AI Pipeline)

### Architecture

```
[Static Frontend (GitHub Pages / local)]
    ↕ fetch() to same origin
[Flask Backend — serves API + static files on one port]
    ↕ Gemini (Video → structured JSON)
    ↕ DeepSeek (Contextual coaching → verdict)
    ↕ SQLite (Session history, progression tracking)
```

### Key Patterns

1. **Single-origin serving** — Flask serves both frontend static files AND API routes on one port. Frontend uses `BACKEND_URL = ''` (relative paths). No CORS issues, one tunnel for everything.
2. **Lazy API client init** — Never init API clients at module import time. Use lazy getters so the server boots without .env configured.
3. **Dual-AI pipeline** — Gemini Phase 1 (structured JSON extraction) → DeepSeek Phase 2 (persona-driven analysis). Each phase independently error-handled.
4. **SQLite session history** — Replace Google Sheets with local SQLite. Zero-config, same data shape, no cloud setup. `_init_db()` on import.
5. **Model selector with quota probing** — `GET /models` endpoint probes available Gemini models. Frontend shows green/red indicators. Auto-selects first available model.
6. **File upload** — `POST /upload` accepts video files, uploads to Gemini File API, returns URI. `POST /analyze` accepts both `video_url` and `file_uri`+`source_type`.
7. **Gemini JSON truncation fix** — Walk bytes tracking bracket depth and string state to find valid JSON cut point. Close unclosed brackets.
8. **Dual-mode input** — Frontend tab toggle: 🔗 YouTube URL / 📤 Upload Video. Both hit `/analyze` with different `source_type`.

## Common Pitfalls

1. **Streamlit email prompt** — Always set `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false STREAMLIT_SERVER_HEADLESS=true`. Without these, the process hangs at an interactive email prompt.
2. **yfinance MultiIndex** — Recent versions return MultiIndex columns from `.download()`. Flatten before column access.
3. **Port 5000 conflict on Windows** — Port **5000** is reserved by the `Universal.Server` system process on many Windows 10/11 installs. `netstat -ano | grep ":5000"` shows PID 5108 (Universal.Server). Use port **5001+** for Flask backends, or switch to a different port.
4. **Auto-refresh kills scroll state** — `st.rerun()` resets the Streamlit component state. Users scrolling through charts will be reset to top. Accept this trade-off for live data.
5. **Phone accessibility** — Phone must be on the same Wi-Fi subnet. Use `http://<LAN-IP>:8501`, NOT localhost.
6. **No hot-reload in production** — Use `streamlit run`, not `streamlit hello` or dev mode.
7. **Lazy API client init** — Never initialize API clients (`OpenAI`, `genai.Client`, `gspread.Client`) at module import time. The user's `.env` may not be configured yet, so eager init crashes the server before it can respond to `/health`. Use a lazy-init function:

   ```python
   # GOOD — server starts even without .env configured
   _client = None
   def get_client():
       global _client
       if _client is not None:
           return _client
       if not os.getenv("API_KEY"):
           raise RuntimeError("API_KEY not set — configure .env")
       _client = SomeClient(api_key=os.getenv("API_KEY"))
       return _client

   # BAD — crashes on import if .env is missing
   client = SomeClient(api_key=os.getenv("API_KEY"))
   ```

   This lets the server boot, serve `/health` (showing missing keys), and only fail with a clear error when a key-dependent endpoint is actually called.

## Remote Access (Tunneling)
