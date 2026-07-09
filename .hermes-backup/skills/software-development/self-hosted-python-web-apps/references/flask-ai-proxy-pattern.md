# Flask AI Proxy Pattern

3-tier architecture: Static Frontend → Local Flask Proxy → External AI APIs

## Architecture

```
[Static Frontend (GitHub Pages / Vercel / local)]
         ↕ fetch() to localhost:5000
[Flask Proxy — runs on your LAN machine]
    │  ├─ Gemini (video / vision analysis)
    │  ├─ DeepSeek / OpenAI (LLM reasoning)
    │  └─ Google Sheets (session history / logging)
    │
[External APIs — keys stay on your machine, never in the frontend]
```

## When to Use

- You need to keep API keys server-side (never embed in static HTML/JS)
- You want a local "orchestrator" that chains multiple AI calls
- You need persistent session storage (Google Sheets, SQLite) without a cloud DB
- The frontend is completely static (GitHub Pages) and cannot have a backend

## Project Scaffold

```
project/
├── backend/
│   ├── app.py              # Flask proxy
│   ├── requirements.txt
│   ├── .env                # API keys (gitignored)
│   ├── .env.example        # Template
│   └── credentials.json    # Google Service Account (gitignored)
└── frontend/
    └── index.html          # Static SPA
```

## Key Endpoints

```python
@app.route("/health", methods=["GET"])
def health():
    """Liveness probe — used by the frontend to check backend is running."""

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Full orchestration pipeline:
    1. Validate input
    2. (Optional) Fetch historical data from Google Sheets / DB
    3. Run Phase 1 AI (e.g., Gemini: video/vision analysis → structured JSON)
    4. Run Phase 2 AI (e.g., DeepSeek: events + history → coaching text)
    5. Parse structured fields from LLM output
    6. Log session to Google Sheets / DB
    7. Return combined JSON
    """
```

## CORS Configuration

```python
from flask_cors import CORS

# Development (allow all)
CORS(app)

# Production (pin to your GitHub Pages domain)
CORS(app, origins=[
    "https://decniner.github.io",
    "http://localhost:5500",  # local dev
])
```

For production, set `CORS_ORIGIN` in `.env` and load it:

```python
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "*")
CORS(app, origins=CORS_ORIGIN.split(",") if CORS_ORIGIN != "*" else "*")
```

## Launch Command

```bash
cd backend/
python app.py
# → ⚡ Server starting on 0.0.0.0:5000
```

**Port 5000 conflict on Windows:** Port 5000 is reserved by `Universal.Server` on many Windows 10/11 installs. If you get `An attempt was made to access a socket in a way forbidden by its access permissions`, switch to port 5001:

```bash
PORT=5001 python app.py
```

And update the frontend's `BACKEND_URL` to `http://localhost:5001`.

Frontend at `localhost:5500` (or GitHub Pages) communicates with backend at `localhost:5000` (or whatever port you choose).

## Google Sheets Integration

### Service Account Setup

1. Google Cloud Console → Enable Sheets API → Create Service Account → Download JSON key
2. Save as `credentials.json` in `backend/`
3. Share your Google Sheet with the service account email (Editor role)
4. Copy Sheet ID from URL: `https://docs.google.com/spreadsheets/d/<ID>/edit`

### Read (Last N Rows)

```python
def fetch_recent_sessions(n=5):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    all_rows = sheet.get_all_values()
    return all_rows[1:][-n:]  # skip header, take last N
```

### Write (Append Row)

```python
def _ensure_sheet_headers(worksheet):
    """Write headers if the sheet is empty (first run ever)."""
    HEADERS = ["Date", "Video URL", "Overall Score", "Technique Ratings (JSON)",
               "Key Timestamps & Notes", "Direct Advice / The Verdict"]
    if worksheet.row_count == 0:
        worksheet.append_row(HEADERS)

def append_session_log(video_url, score, ratings, notes, verdict):
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    _ensure_sheet_headers(sheet)  # ← critical: new sheets are empty
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        video_url,
        str(score),
        json.dumps(ratings, ensure_ascii=False),  # store as JSON string
        notes,
        verdict,
    ]
    sheet.append_row(row)
```

**Always call `_ensure_sheet_headers` before the first append.** Without it, writing to a brand-new sheet (zero rows) fails silently — gspread returns 200 but nothing is persisted.

## Lazy API Client Init

**Critical pattern for .env-driven proxies:** Never initialize API clients at module import time. The user installs the app before configuring `.env`, so eager init crashes the server on first boot.

```python
# ── WRONG — crashes at import if .env is missing
genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"))

# ── RIGHT — lazy init via getter function
_gemini_client = None
def _get_gemini_client():
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY not set in .env")
    _gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _gemini_client
```

This applies to: `genai.Client`, `OpenAI`, `gspread.authorize()`, and any HTTP client that reads credentials from environment variables.

**Health endpoint pattern** — The `/health` route should always succeed (never call lazy getters), reporting missing keys as a `degraded` status so the frontend can show a clear "configure your .env" message.

## Dual-AI Pipeline Pattern

```python
# Phase 1: Structured extraction (Gemini)
events = gemini_client.models.generate_content(
    model="models/gemini-2.0-flash",
    contents=[prompt, genai_types.Part.from_uri(file_uri=url, mime_type="video/mp4")],
    config=genai_types.GenerateContentConfig(
        system_instruction="Return ONLY JSON array...",
        response_mime_type="application/json",
    ),
)
events_json = json.loads(events.text)

# Phase 2: Reasoning / coaching (DeepSeek)
analysis = deepseek.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": BRUTAL_COACH_PROMPT},
        {"role": "user", "content": f"Events: {json.dumps(events_json)}\nHistory: {history}"},
    ],
)
```

### Consolidated Deployment: Flask Serves Everything

When using tunnels (serveo, cloudflared), avoid CORS and multi-tunnel issues by serving both frontend AND backend from one Flask process:

```python
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@app.route("/")
def serve_index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(str(FRONTEND_DIR), path)
```

Benefits: one tunnel URL, same origin (no CORS needed), frontend uses relative paths (`BACKEND_URL = ''`).

### Gemini JSON Response Truncation Fix

The `response_mime_type="application/json"` mode does NOT work reliably with gemini-2.5-flash and newer models. Remove it and implement a robust manual JSON extractor:

```python
response = client.models.generate_content(
    model=GEMINI_MODEL,
    contents=[user_text, genai_types.Part.from_uri(...)],
    config=genai_types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.1,
        max_output_tokens=8192,
        # NO response_mime_type
    ),
)

text = response.text.strip()
text = re.sub(r"^```(?:json)?\s*", "", text)
text = re.sub(r"\s*```$", "", text)
text = text.strip()

array_match = re.search(r"\[\s*\{.*", text, re.DOTALL)
if array_match:
    text = array_match.group(0)

# String-aware bracket balancing for truncated output
open_objs = 0
open_arrays = 0
in_string = False
escape = False
cut_pos = len(text)
for i, ch in enumerate(text):
    if escape: escape = False; continue
    if ch == "\\" and in_string: escape = True; continue
    if ch == '"' and not escape: in_string = not in_string; continue
    if in_string: continue
    if ch == "{": open_objs += 1
    elif ch == "}": open_objs -= 1
    elif ch == "[": open_arrays += 1
    elif ch == "]":
        open_arrays -= 1
        if open_objs == 0 and open_arrays == 0:
            cut_pos = i + 1
            break

text = text[:cut_pos].strip().rstrip(",")
open_b = text.count("[") - text.count("]")
open_c = text.count("{") - text.count("}")
if open_b > 0: text += "]" * open_b
if open_c > 0: text += "}" * open_c

parsed = json.loads(text)
```

### Gemini Live Quota Probing (Model Selector)

For apps where the user may exhaust a model's daily quota mid-session, add a `GET /models` endpoint that probes each configured model and returns live status:

```python
AVAILABLE_MODELS = [
    "models/gemini-2.5-flash-lite",
    "models/gemini-3.5-flash",
    "models/gemini-3.1-flash-lite",
]

_model_cache: dict[str, dict] = {}
_model_cache_ts: float = 0
_model_cache_lock = Lock()
_MODEL_CACHE_TTL = 30  # seconds

def probe_models() -> list[dict]:
    global _model_cache, _model_cache_ts
    now = time.time()
    with _model_cache_lock:
        if _model_cache and (now - _model_cache_ts) < _MODEL_CACHE_TTL:
            return list(_model_cache.values())
    if not os.getenv("GEMINI_API_KEY"):
        return [{"id": m, "status": "no_key"} for m in AVAILABLE_MODELS]
    client = _get_gemini_client()
    results = []
    for model_id in AVAILABLE_MODELS:
        try:
            client.models.generate_content(
                model=model_id, contents="ok",
                config=genai_types.GenerateContentConfig(max_output_tokens=10))
            results.append({"id": model_id, "status": "available", "error": None})
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                results.append({"id": model_id, "status": "quota_exhausted", "error": err_str[:100]})
            else:
                results.append({"id": model_id, "status": "error", "error": err_str[:100]})
    with _model_cache_lock:
        _model_cache = {r["id"]: r for r in results}
        _model_cache_ts = time.time()
    return results

@app.route("/models", methods=["GET"])
def list_models():
    try:
        return jsonify({"models": probe_models()})
    except Exception as e:
        return jsonify({"models": [{"id": m, "status": "error", "error": str(e)[:100]} for m in AVAILABLE_MODELS]})
```

Frontend model selector with live quota status indicators:

```javascript
async function refreshModels() {
  const resp = await fetch(`/models`);
  const data = await resp.json();
  const models = data.models || [];
  modelSelect.innerHTML = '';
  models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    const name = m.id.replace('models/gemini-', '');
    if (m.status === 'available') {
      opt.textContent = `✅ ${name}`;
      opt.style.color = '#00c853';
    } else if (m.status === 'quota_exhausted') {
      opt.textContent = `❌ ${name} (${m.error || 'quota full'})`;
      opt.style.color = '#ff1744';
      opt.disabled = true;
    } else {
      opt.textContent = `⚠️ ${name}`;
      opt.style.color = '#ffd600';
      opt.disabled = true;
    }
    modelSelect.appendChild(opt);
  });
  const firstAvail = models.find(m => m.status === 'available');
  if (firstAvail) modelSelect.value = firstAvail.id;
  modelStatus.textContent = `(${models.filter(m => m.status === 'available').length}/${models.length} available)`;
}
```

Pass selected model with analyze request:
```javascript
const body = { video_url: url };
if (modelSelect.value) body.model = modelSelect.value;
```

Backend extracts:
```python
data = request.get_json(silent=True) or {}
selected_model = (data.get("model") or "").strip()
events = run_gemini_analysis(normalized, selected_model)
```

### Gemini Model Fallback Chain

Free-tier Gemini quotas are per-model per-day (typically 20 requests/day). When one model is exhausted (HTTP 429):

Available models for fallback (confirmed working 2026-07):
- `gemini-2.0-flash` — baseline, often quota-exhausted
- `gemini-2.5-flash` — separate quota pool
- `gemini-3.5-flash` — newest, separate quota pool
- `gemini-flash-latest` — alias, separate quota pool
- `gemini-2.5-flash-lite` — lighter, separate quota pool
- `gemini-3.1-flash-lite` — lightweight, separate quota pool
- **gemini-1.5-flash is REMOVED from API (404 NOT_FOUND)**

Make model a top-level config constant. When 429 is returned with `quotaId` matching `GenerateContentRequestsPerDayPerProjectPerModel-FreeTier`, switch to the next model.

## Pitfalls

1. **YouTube URL normalization** — Users paste URLs in many formats (`youtu.be/`, `youtube.com/watch?v=`, `/shorts/`, with `m.` subdomain). Normalise to `https://www.youtube.com/watch?v={id}` before passing to APIs.
2. **Gemini video processing timeout** — Gemini can take 30-60s to process a YouTube video. Set generous timeouts (120s).
3. **Google Sheets rate limits** — 60 requests per minute per project for read/write operations. Fine for low-volume personal use.
4. **Google Sheets credentials location** — Must be at the exact path specified. Use `os.path.join(os.path.dirname(__file__), "credentials.json")` to resolve relative to the script.
5. **Service account sharing** — The sheet MUST be explicitly shared with the service account email (found in the JSON key's `client_email` field). Without this, `gspread` returns a 404.
6. **LLM output parsing** — LLMs (especially DeepSeek) may not follow the exact output format. Use regex fallbacks to extract scores and structured data from free-form text.
7. **Gemini free-tier quota exhaustion** — Free-tier Gemini quotas are per-model. If `gemini-2.0-flash` hits `429 RESOURCE_EXHAUSTED`, switch to `gemini-2.5-flash` or `gemini-flash-latest` which have independent quota pools. **Do NOT use `gemini-1.5-flash`** — it has been **removed from the API** (returns `404 NOT_FOUND`). Make the model name a top-level constant so the user can swap without touching logic. The error body includes `retryDelay` (~47s) and `quotaId` fields — log these so the user knows which model is saturated.
8. **Model fallback guard** — When Gemini free tier is exhausted, check the 429 error's `details[].quotaId` to identify the specific metric (e.g., `GenerateContentInputTokensPerModelPerMinute-FreeTier`) and log it. This tells the user whether they need to wait, switch models, or upgrade to a paid tier.
