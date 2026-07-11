---
name: python-web-tunnel
description: Build Python Flask web apps with AI API backends, tunnel them for mobile/remote access, and handle API quirks.
category: software-development
triggers:
  - "build a web app / dashboard with a local Python backend"
  - "expose a local server to the internet via tunnel"
  - "mobile-accessible web UI from desktop machine"
  - "Gemini / DeepSeek / OpenAI API integration in Flask"
  - "file upload to AI API with video analysis"
---

# Python Web App + Tunnel — Patterns & Pitfalls

Class-level guide for building a local Flask proxy with AI API backends
and exposing it via tunnels for mobile access.

---

## ⚠️ Mandatory: QA Protocol (User Expectation)

**QA your own work before reporting.** The user will say: *"Not working, qa it yourself to make sure it works before asking me."* Do not skip.

1. **Build** the code
2. **Smoke test locally** — syntax, imports, `curl localhost/health`
3. **Full workflow test** — hit every endpoint with real data through the tunnel
4. **Verify error handling** — test with invalid input, missing keys, API timeouts
5. **Report** — only after all above pass

Diagnose and fix failures silently. Do not ask the user to check if something works.

## 1. Architecture: Single-Origin Flask

Serve frontend static files FROM the Flask backend — not from a separate HTTP server.
This eliminates all CORS issues and long-request tunnel timeouts.

```python
from pathlib import Path
from flask import Flask, send_from_directory

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@app.route("/")
def index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(str(FRONTEND_DIR), path)
```

**Why:** The JS frontend makes fetch() calls to `/analyze` (same origin).
No CORS headers needed. No cross-tunnel fetch issues.

## 2. Tunnel Selection

| Tunnel    | Long requests (>30s) | Setup                  | Reliability |
|-----------|---------------------|------------------------|-------------|
| serveo.net| ❌ Drops            | `ssh -R 80:localhost:PORT serveo.net` | Poor — drops long POSTs |
| localtunnel | ❌ Drops          | `npx localtunnel --port PORT` | Poor — 503s under load |
| **cloudflared** | ✅ Handles    | `cloudflared tunnel --url http://localhost:PORT` | **Best** — no account needed |

**Always use cloudflared** for apps with AI API calls that take 30-120s.

```bash
npm install -g cloudflared
cloudflared tunnel --url http://localhost:5001
```

> **Windows port 5000:** Port 5000 is reserved by `Universal.Server` on Windows 10/11. Use port **5001+** or kill the process with `taskkill /PID $(netstat -ano | grep ':5000' | awk '{print $5}' | head -1)`.

## 3. Gemini API — Quota Handling

Free tier Gemini has per-model daily limits (~20 requests/day for 2.5-flash).
**Always probe models and let the user switch.**

### Model Registry Pattern (REQUIRED for free-tier Gemini):

```python
AVAILABLE_MODELS = [
    "models/gemini-2.5-flash-lite",
    "models/gemini-3.5-flash",
    "models/gemini-3.1-flash-lite",
]

def probe_models(client) -> list[dict]:
    """Test each model for quota. Cache results for 30s."""
    results = []
    for model_id in AVAILABLE_MODELS:
        try:
            client.models.generate_content(model=model_id, contents="ok", ...)
            results.append({"id": model_id, "status": "available"})
        except Exception as e:
            if "429" in str(e):
                results.append({"id": model_id, "status": "quota_exhausted"})
            else:
                results.append({"id": model_id, "status": "error"})
    return results
```

### Frontend: show colored dropdown:
- ✅ Green = available (auto-select first)
- ❌ Red = quota exhausted (disabled)
- ⚠️ Yellow = unknown error

### Model fallback chain (good default):
```
gemini-3.5-flash → gemini-2.5-flash-lite → gemini-3.1-flash-lite
```

## 4. Gemini JSON Parsing — Truncation Recovery

Gemini responses with `max_output_tokens` can truncate JSON mid-string.
**Always apply truncation recovery** — never trust raw `.text` from Gemini.

```python
# 1. Strip markdown fences
text = re.sub(r"^```(?:json)?\s*", "", text)
text = re.sub(r"\s*```$", "", text)

# 2. Extract JSON array (ignore surrounding text)
array_match = re.search(r"\[\s*\{.*", text, re.DOTALL)
if array_match:
    text = array_match.group(0)

# 3. Walk character-by-character tracking string/bracket state
#    to find the last complete JSON object, then close any unclosed brackets
open_objs = open_arrays = 0
in_string = False
cut_pos = len(text)
for i, ch in enumerate(text):
    if ch == '"' and not escape: in_string = not in_string
    if in_string: continue
    if ch == "{": open_objs += 1
    elif ch == "}": open_objs -= 1
    elif ch == "[": open_arrays += 1
    elif ch == "]":
        open_arrays -= 1
        if open_objs == 0 and open_arrays == 0:
            cut_pos = i + 1
            break

text = text[:cut_pos]
text += "]" * (text.count("[") - text.count("]"))
text += "}" * (text.count("{") - text.count("}"))
```

## 5. Gemini File API — Video Upload

For local/uploaded videos, use Gemini's File API:

```python
# Upload
gemini_file = client.files.upload(file=str(local_path))

# Wait for processing (can take 1-2 minutes for large files)
while gemini_file.state.name == "PROCESSING":
    time.sleep(2)
    gemini_file = client.files.get(name=gemini_file.name)

# Use the returned URI in generate_content
part = genai_types.Part.from_uri(
    file_uri=gemini_file.uri,
    mime_type="video/mp4",
)
```

**Important:** Set Flask's `MAX_CONTENT_LENGTH` for large uploads.

## 6. SQLite for Local Persistence

Replace Google Sheets (requires credentials.json + API setup) with SQLite for
zero-config persistence:

```python
import sqlite3

conn = sqlite3.connect("app_history.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        video_url TEXT NOT NULL,
        overall_score INTEGER NOT NULL,
        technique_ratings TEXT NOT NULL,
        timestamps_notes TEXT NOT NULL,
        verdict TEXT NOT NULL
    )
""")
```

## 7. Common Refactoring Pitfalls

### 7a. Variable Scope Bug: Code-Path Splitting

When you refactor a function to support TWO code paths (e.g. URL vs file_uri),
ANY code OUTSIDE the if/else that references a variable set INSIDE one branch
will crash: `cannot access local variable 'X' where it is not associated with a value`.

**Wrong — variable used after if/else but only set in one branch:**
```python
if source_type == "file_uri":
    contents = [user_text, file_part]
else:
    normalized_url = normalize(url)
    contents = [user_text, url_part]

# BUG: try block reconstructs 'contents' using 'normalized_url'
# which only exists in the 'else' branch
try:
    response = client.generate_content(
        contents=[user_text, Part.from_uri(file_uri=normalized_url)],  # CRASH
    )
```

**Fix — use the already-assigned result variable:**
```python
if source_type == "file_uri":
    contents = [user_text, file_part]
else:
    contents = [user_text, url_part]

try:
    response = client.generate_content(contents=contents, ...)
```

**Rule:** Assign the SAME result variable in BOTH branches, then use it
downstream. Never reconstruct or reference per-branch intermediates.

### 7b. Flask Config Ordering

`MAX_CONTENT_LENGTH` must reference a constant defined BEFORE `app = Flask(__name__)`.

```python
# GOOD
MAX_UPLOAD_MB = 500                          # defined first
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

# BAD — NameError: referenced before assignment
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024  # 💥
MAX_UPLOAD_MB = 500                          # too late
```

## 8. Error Handling Pattern

Always return JSON even on errors. Wrap AI API calls with specific error messages.

```python
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # Gemini
        events = run_gemini_analysis(...)
        # DeepSeek
        coaching = run_deepseek_coaching(...)
        return jsonify({"success": True, ...})
    except ValueError as e:      # 400 — bad input
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:     # 502 — API failure
        return jsonify({"error": str(e)}), 502
    except Exception as e:        # 500 — unexpected
        return jsonify({"error": f"Internal: {e}"}), 500
```

## Reference Build

See `references/pogibot-build.md` for a complete session-level walkthrough of building a Flask + Gemini + DeepSeek + SQLite app (POGIBOT VR Boxing Coach) using every pattern in this skill. Includes error transcripts, troubleshooting flow, and the exact sequence of fixes applied during development.
