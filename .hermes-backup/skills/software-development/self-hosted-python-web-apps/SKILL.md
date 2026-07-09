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

- `references/yfinance-crypto-stock-patterns.md` — Symbol normalization, 4H candle fetching, MultiIndex flattening, and recommended Japanese-market + crypto defaults for market analysis apps.
- `references/flask-ai-proxy-pattern.md` — 3-tier architecture: static frontend → local Flask proxy → external AI APIs (Gemini, DeepSeek, etc.) with Google Sheets for session logging. Covers CORS, service account setup, dual-AI pipeline orchestration, and common pitfalls.
- `references/google-genai-sdk-migration.md` — Migrating from deprecated `google.generativeai` to current `google.genai` SDK: import changes, client init, YouTube video input, JSON mode, system instructions, and common pitfalls.

## Common Pitfalls

1. **Streamlit email prompt** — Always set `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false STREAMLIT_SERVER_HEADLESS=true`. Without these, the process hangs at an interactive email prompt.
2. **yfinance MultiIndex** — Recent versions return MultiIndex columns from `.download()`. Flatten before column access.
3. **Port 5000 conflict on Windows** — Port **5000** is reserved by the `Universal.Server` system process on many Windows 10/11 installs. `netstat -ano | grep ":5000"` shows PID 5108 (Universal.Server). Use port **5001+** for Flask backends, or switch to a different port.
4. **Auto-refresh kills scroll state** — `st.rerun()` resets the Streamlit component state. Users scrolling through charts will be reset to top. Accept this trade-off for live data.
5. **Phone accessibility** — Phone must be on the same Wi-Fi subnet. Use `http://<LAN-IP>:8501`, NOT localhost.
6. **No hot-reload in production** — Use `streamlit run`, not `streamlit hello` or dev mode.
7. **Kanban task per project** — The user expects a kanban task (`hermes kanban create "..." --body "..."`) for every project build. Create and mark it complete before giving the final summary — otherwise the user will tell you "you forgot to update kanban."
8. **Lazy API client init** — Never initialize API clients (`OpenAI`, `genai.Client`, `gspread.Client`) at module import time. The user's `.env` may not be configured yet, so eager init crashes the server before it can respond to `/health`. Use a lazy-init function:

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

When the user is NOT on the same Wi-Fi (e.g. on mobile data), they cannot reach the LAN IP. Use a tunnel to expose the service via a public URL.

### serveo.net (free, no-auth, works on Windows)

```
Forwarding HTTP traffic from https://<hash>-<ip>.serveousercontent.com
```

One tunnel per SSH connection — create separate background processes for multiple ports.

**Why serveo.net over ngrok:** No account, no install, works on Windows via bundled OpenSSH. `pyngrok` fails on Windows (zip corruption).

```bash
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
    -R 80:localhost:8501 serveo.net
```

**⚠️ LIMITATION:** serveo.net free tier drops long-running POST requests (>~30s). Not suitable for AI pipelines with Gemini video analysis (which takes 30-60s). Use Cloudflare Tunnel for those cases.

### Cloudflare Tunnel (recommended for long-running requests)

Handles long-running POST requests reliably. Install via npm:

```bash
npm install -g cloudflared
```

Then start a tunnel:

```bash
cloudflared tunnel --url http://localhost:5001
```

Output:
```
Your quick Tunnel has been created! Visit it at:
https://<random-words>.trycloudflare.com
```

**Why Cloudflare over serveo.net:**
- Handles 60s+ requests without dropping
- All connectivity checks (DNS, UDP, TCP, API) PASS automatically
- No account required for quick tunnels
- Stable connection for the lifetime of the process

### localtunnel (NOT RECOMMENDED)

`npx localtunnel --port 5001` produces a URL like `https://<random>.loca.lt` but the free tier is unreliable:
- Returns `503 - Tunnel Unavailable` intermittently
- Process exits without warning after ~4 minutes
- No keepalive options

Prefer Cloudflare Tunnel instead.

### Consolidated Deployment (One Port to Rule Them All)

When using tunnels, CORS and fetch issues multiply when frontend and backend are on different tunnel URLs. **Solution: serve the frontend static files FROM the Flask backend.**

```python
from pathlib import Path
from flask import Flask, send_from_directory

app = Flask(__name__)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@app.route("/")
def serve_index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(str(FRONTEND_DIR), path)
```

Now the frontend's `BACKEND_URL` can be `''` (relative path), meaning:
- One tunnel serves everything
- Same origin = no CORS issues
- Fetch calls use `/analyze` instead of `https://tunnel-url/analyze`
- Works seamlessly through any tunnel

### What to Tunnel (per-app approach)

| Scenario | Tunnel Target | Port |
|----------|---------------|------|
| Streamlit standalone | Streamlit process | `8501` |
| Flask-serving-everything | Flask process | `5001` |

### Caveats

- URL changes on reconnect — no custom subdomain without account
- Set `ServerAliveInterval=30` for SSH tunnels to prevent drop after inactivity
- Anyone with the URL can access — personal tools only, never production
- pyngrok fails on Windows with zip corruption error — use serveo or cloudflared instead
