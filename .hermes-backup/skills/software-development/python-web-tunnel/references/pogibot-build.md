# POGIBOT — VR Boxing AI Coach: Reference Build

Concrete example of the python-web-tunnel pattern in action.
Build: Flask proxy + Gemini 3.5 Flash (video analysis) + DeepSeek V3 (coaching) + SQLite + Cloudflare tunnel.

## Project Structure

```
backend/
├── app.py              # Flask app (frontend + API + AI pipeline)
├── .env                # API keys (GEMINI_API_KEY, DEEPSEEK_API_KEY)
├── requirements.txt    # flask, flask-cors, google-genai, openai, python-dotenv
├── pogibot_history.db  # SQLite (auto-created)
└── uploads/            # Temp uploads (auto-created)
frontend/
└── index.html          # Static dashboard served by Flask
```

## Key Decisions & Tradeoffs

### Why single-origin Flask over separate frontend/backend servers
- Problem: Phone browser at tunnel URL can't reach `localhost:5001`
- Solution: Flask serves `index.html` at `/` and API at `/analyze`, all on one port
- Result: fetch() calls are same-origin → no CORS, no cross-tunnel timeout

### Why cloudflared won over serveo/localtunnel
- serveo.net: dropped POST requests that took >30s (Gemini video analysis is 30-90s)
- localtunnel: returned "503 Tunnel Unavailable" under sustained load
- cloudflared: handles long-running requests, no account needed, free tier works

### Why SQLite over Google Sheets
- Required credentials.json + Google Cloud project setup → friction
- SQLite: zero config, always works, same data model
- Trade-off: no cloud backup, but keeps the app self-contained

## Error Recovery: Gemini JSON Truncation

Gemini with `max_output_tokens=8192` sometimes truncates JSON mid-value.

### Symptom
```
Gemini returned invalid JSON: Unterminated string starting at: line 12 column 14 (char 294)
```

### Root Cause
Gemini's text response gets cut at the token limit while constructing a JSON string value.
The `response_mime_type="application/json"` setting doesn't prevent truncation.

### Fix Applied
Character-by-character parser that tracks string/bracket state to find the last
complete JSON object/array boundary, then auto-closes unclosed brackets.
See SKILL.md §4 for the code.

## File Upload Flow

```
1. User picks video on phone
2. Frontend fetch POST /upload (multipart) → Backend saves to uploads/
3. Backend: client.files.upload(file=path) → Gemini File API
4. Backend polls Gemini file state until ACTIVE (not PROCESSING)
5. Backend returns {"file_uri": "https://..."} → Frontend
6. Frontend sends POST /analyze {source_type: "file_uri", file_uri: "..."}
7. Backend uses the file URI in generate_content() via Part.from_uri()
8. Temp file cleaned up after upload
```

### Pitfalls
- Flask `MAX_CONTENT_LENGTH` must be set BEFORE first upload attempt
- `MAX_UPLOAD_MB` must be defined **before** `app = Flask(__name__)` — Python raises NameError if referenced before assignment
- Gemini File API processing time scales with file size (~1-2 min for 200MB)
- The file URI from Gemini is only valid for 48 hours

## Refactoring Pitfalls Encountered During Build

### `import json` Removal on Restructure
When refactoring the import block to add `Flask.send_from_directory` and remove
`oauth2client`/`gspread`, the `import json` line was accidentally dropped.
This caused a silent crash: `NameError: name 'json' is not defined` on first `/analyze` call.

**Fix:** Always run `py_compile.compile()` after every import-block change.
Pin the json/datetime/re/os imports — they're easy to lose during bulk edits.

### Code-Path Variable Scope
When `run_gemini_analysis()` was refactored to accept both `url` and `file_uri`
source types, the try block IGNORED the `contents` variable set in the if/else
and rebuilt it using `normalized_url` — which only exists in the "url" code path.
Result: crash on every uploaded file analysis.

**Fix:** Use the already-assigned `contents` variable, never reconstruct.

## Session 2 Features Added (Jul 11, 2026)

### Chat / Conversational Coach (POST /chat)

A `POST /chat` endpoint was added so the user can have a continuing conversation with the AI coach after a video analysis.

**Backend design:**
```python
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message")
    conversation = data.get("conversation", [])      # [{role, content}, ...]
    last_analysis = data.get("last_analysis", None)   # from /analyze response

    # Inject analysis context as system message
    if last_analysis:
        context = f"Score: {last_analysis['overall_score']}\nRatings: {json.dumps(last_analysis['technique_ratings'])}"
        messages.append({"role": "system", "content": f"LAST ANALYSIS:\n{context}"})

    # Append conversation history (last 10)
    for msg in conversation[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})
    reply = client.chat.completions.create(messages=messages)
    return jsonify({"reply": reply})
```

**Frontend design:**
- `chatConversation[]` array persists the message history (client-side)
- `lastAnalysisData` object stores the most recent /analyze response fields
- Both are sent with each chat request for context continuity
- Loading indicator ("thinking...") while waiting for reply
- HTML escaping on chat output for XSS safety

**System prompt persona:**
Brutally honest VR boxing coach. Direct, specific, references real events from analysis. Gives actionable advice. If asked about something not in the data, says so.

### Progress Chart (GET /history + Canvas API)

A `/history` endpoint returns all logged sessions for charting.

**Backend:** `GET /history` returns `{"sessions": [{"session_order", "timestamp", "overall_score", "technique_ratings"}, ...]}` sorted oldest-first.

**Frontend:** Pure Canvas 2D API chart — no external libraries:
- Line connecting overall scores across sessions (#1, #2, #3...)
- Gradient fill under the line (red to transparent)
- Score dots color-coded: red <50, yellow 50-69, green 70+
- Latest dot in orange for emphasis
- Trend arrow at top: 📈 Improving / 📉 Declining / 📊 Stable (+/- pts diff)
- Grid lines with Y-axis labels
- Auto-updates after each analysis via `setTimeout(loadProgressChart, 500)`
- Shows "Run 2+ analyses to see progress" placeholder when <2 sessions exist

### Mobile Responsive CSS

Full `@media (max-width: 600px)` breakpoint:
- All inputs stack vertically (flex-direction: column)
- Buttons go full-width (width: 100%)
- Results grid collapses to single column (grid-template-columns: 1fr)
- Font sizes reduced: header 1.8rem, body 0.85rem, verbatim 0.7rem
- Padding reduced on cards, header, inputs
- Score badge number shrinks to 3rem
- Rating bars wrap and shrink
- History table cells tighten
- Chat box limited to 300px height, font 0.85rem
- Model selector min-width shrinks to 140px

### SQLite Reset (User Request)

When the user wants to start fresh:
```bash
rm -f ~/projects/POGIBOT/backend/pogibot_history.db
```
The database is auto-created on next startup by the `_init_db()` function.
