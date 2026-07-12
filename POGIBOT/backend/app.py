"""
POGIBOT — VR Boxing AI Coach: Local Flask Proxy Backend
═══════════════════════════════════════════════════════════════

3-tier architecture:
  [Static Frontend (GitHub Pages)]
      ↕ fetch() to localhost:5000
  [Flask Proxy — THIS FILE]
      ↕ Gemini (Video) / DeepSeek (Coach) / Google Sheets (Logs)
  [External APIs]

Endpoints:
  GET  /health        — Liveness check
  POST /analyze       — Submit a YouTube URL → full analysis pipeline
"""

import json
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai import types as genai_types
from openai import OpenAI

# ── Load environment ──────────────────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "*")
MAX_UPLOAD_MB = 500

# ── Flask app ─────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
CORS(app, origins=CORS_ORIGIN.split(",") if CORS_ORIGIN != "*" else "*")

# ── API clients (lazy init) ──────────────────────────────────────────────

_gemini_client = None
GEMINI_MODEL = "models/gemini-3.5-flash"

# ── Model registry with live quota probing ───────────────────────────────

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
    """Test each available model for quota and return status list."""
    global _model_cache, _model_cache_ts
    now = time.time()
    with _model_cache_lock:
        if _model_cache and (now - _model_cache_ts) < _MODEL_CACHE_TTL:
            return list(_model_cache.values())

    if not GEMINI_API_KEY:
        return [{"id": m, "status": "no_key"} for m in AVAILABLE_MODELS]

    client = _get_gemini_client()
    results = []
    for model_id in AVAILABLE_MODELS:
        try:
            resp = client.models.generate_content(
                model=model_id, contents="ok", config=genai_types.GenerateContentConfig(max_output_tokens=10)
            )
            results.append({"id": model_id, "status": "available", "error": None})
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                # Try to extract retry delay
                retry_match = re.search(r"retry in (\d+\.?\d*)s", err_str)
                retry_after = float(retry_match.group(1)) if retry_match else 60
                results.append({
                    "id": model_id, "status": "quota_exhausted",
                    "error": f"Quota exceeded (retry in {retry_after:.0f}s)",
                    "retry_after": retry_after,
                })
            else:
                results.append({"id": model_id, "status": "error", "error": err_str[:100]})

    with _model_cache_lock:
        _model_cache = {r["id"]: r for r in results}
        _model_cache_ts = time.time()

    return results


def _resolve_model(model_id: str) -> str:
    """Return a full model path, defaulting to GEMINI_MODEL if empty."""
    m = (model_id or "").strip()
    if not m:
        return GEMINI_MODEL
    if not m.startswith("models/"):
        m = f"models/{m}"
    return m


def _get_gemini_client() -> genai.Client:
    """Lazy-init Gemini client — server can start without API keys."""
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. "
            "Copy backend/.env.example to backend/.env and fill in your key."
        )
    _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client

# DeepSeek (OpenAI-compatible) — lazy init
_deepseek_client = None


def _get_deepseek_client() -> OpenAI:
    global _deepseek_client
    if _deepseek_client is not None:
        return _deepseek_client
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not set. "
            "Copy backend/.env.example to backend/.env and fill in your key."
        )
    _deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1",
    )
    return _deepseek_client

# ── SQLite session database ──────────────────────────────────────────────

DB_PATH = Path(__file__).resolve().parent / "pogibot_history.db"
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def _init_db():
    """Create the sessions table if it doesn't exist."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            video_url   TEXT NOT NULL,
            overall_score INTEGER NOT NULL,
            technique_ratings TEXT NOT NULL,
            timestamps_notes  TEXT NOT NULL,
            verdict     TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def fetch_recent_sessions(n: int = 5) -> list[list]:
    """Fetch the last N sessions from SQLite."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.execute(
            "SELECT date, video_url, overall_score, technique_ratings, "
            "timestamps_notes, verdict FROM sessions ORDER BY id DESC LIMIT ?",
            (n,),
        )
        rows = cur.fetchall()
        conn.close()
        return [list(r) for r in reversed(rows)]  # oldest first
    except Exception as e:
        print(f"[warn] SQLite fetch failed: {e}")
        return []


def append_session_log(
    video_url: str,
    overall_score: int,
    technique_ratings: dict,
    timestamps_notes: str,
    verdict: str,
) -> None:
    """Append one row to the SQLite database."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(
            "INSERT INTO sessions (date, video_url, overall_score, "
            "technique_ratings, timestamps_notes, verdict) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                video_url,
                overall_score,
                json.dumps(technique_ratings, ensure_ascii=False),
                timestamps_notes,
                verdict,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[warn] SQLite append failed: {e}")


def _format_historical_data(rows: list[list]) -> str:
    """Pretty-print historical rows for the DeepSeek prompt."""
    if not rows:
        return "NO HISTORY — this is the fighter's first recorded session."
    parts = []
    for r in rows:
        parts.append(
            f"Session: {r[0] if len(r) > 0 else '?'} | "
            f"Score: {r[2] if len(r) > 2 else '?'} | "
            f"Ratings: {r[3] if len(r) > 3 else '?'} | "
            f"Verdict: {r[5] if len(r) > 5 else '?'}"
        )
    return "\n".join(parts)


# Initialize on import
_init_db()

# ══════════════════════════════════════════════════════════════════════════
# PHASE 1 — Gemini: The Video Eye
# ══════════════════════════════════════════════════════════════════════════

GEMINI_SYSTEM_INSTRUCTION = """You are a cold, hyper-objective, purely clinical boxing technique tracker. You have no personality, no coaching persona, no enthusiasm, no sugarcoating. You only describe what physically happened in the video with mechanical precision.

Your ONLY output is a JSON array of events. No preamble, no commentary, no markdown formatting.

For each significant boxing technique or movement moment in the video, output one object with these exact keys:
  - "timestamp": "MM:SS"  (the moment in the video when it occurs)
  - "technique": one of: "Jab", "Hook", "Uppercut", "Guard", "Movement", "Speed"
  - "type": "Highlight" or "Flaw"
  - "notes": A one-sentence mechanical description of what happened — footwork, hand position, rotation, guard, timing.

Rules:
1. Be precise with timestamps. If you can't determine the exact time, estimate honestly.
2. If the video contains a sparring match or bag work, track every meaningful exchange.
3. A "Highlight" means technically correct execution. A "Flaw" means a mechanical error.
4. Output a minimum of 3 events and maximum of 20 events.
5. Return ONLY the raw JSON array. No triple backticks, no markdown.

Example:
[
  {"timestamp": "00:12", "technique": "Jab", "type": "Highlight", "notes": "Snap extension with hip rotation, returns to guard cleanly."},
  {"timestamp": "00:45", "technique": "Guard", "type": "Flaw", "notes": "Rear hand drops after the cross, exposing the chin for 0.3 seconds."}
]"""


def run_gemini_analysis(
    video_source: str, model_id: str = "", source_type: str = "url"
) -> list[dict]:
    """
    Send video to Gemini and get back a structured JSON array.

    Two source types:
      - "url"     : YouTube URL (existing behavior)
      - "file_uri": Gemini File API URI (from uploaded video)
    """
    model_path = _resolve_model(model_id)
    user_text = (
        "Analyze this boxing training / sparring video frame by frame. "
        "Extract every technique, punch, guard position, and movement event "
        "with precise timestamps. Categorize each as Highlight (correct) or "
        "Flaw (mechanical error). Return ONLY the JSON array."
    )

    if source_type == "file_uri":
        # Video already uploaded to Gemini File API — use the URI directly
        contents = [
            user_text,
            genai_types.Part.from_uri(
                file_uri=video_source,
                mime_type="video/mp4",
            ),
        ]
    else:
        # YouTube URL — normalize and use
        normalized_url = _normalize_youtube_url(video_source)
        if not normalized_url:
            raise ValueError(f"Invalid YouTube URL: {video_source}")
        contents = [
            user_text,
            genai_types.Part.from_uri(
                file_uri=normalized_url,
                mime_type="video/mp4",
            ),
        ]

    try:
        client = _get_gemini_client()
        response = client.models.generate_content(
            model=model_path,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                temperature=0.1,
                max_output_tokens=8192,
            ),
        )

        text = response.text.strip()

        # Remove potential markdown fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        # Try to extract a JSON array from the text (handles surrounding text)
        array_match = re.search(r"\[\s*\{.*", text, re.DOTALL)
        if array_match:
            text = array_match.group(0)

        # Fix truncated JSON: remove trailing incomplete content
        # Find the last complete object and close the array
        open_objs = 0
        open_arrays = 0
        in_string = False
        escape = False
        cut_pos = len(text)
        for i, ch in enumerate(text):
            if escape:
                escape = False
                continue
            if ch == "\\" and in_string:
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                open_objs += 1
            elif ch == "}":
                open_objs -= 1
            elif ch == "[":
                open_arrays += 1
            elif ch == "]":
                open_arrays -= 1
            # If we reach end of valid JSON
            if open_objs == 0 and open_arrays == 0 and ch == "]":
                cut_pos = i + 1
                break

        text = text[:cut_pos].strip().rstrip(",")

        # Close any unclosed brackets
        open_b = text.count("[") - text.count("]")
        open_c = text.count("{") - text.count("}")
        if open_b > 0:
            text += "]" * open_b
        if open_c > 0:
            text += "}" * open_c

        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        # Sometimes Gemini wraps in {"events": [...]} or similar
        if isinstance(parsed, dict):
            for key in ("events", "analysis", "results", "data"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
        # Fall back to wrapping the single object as one event
        return [parsed]

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Gemini returned invalid JSON: {e}\nRaw text: {text[:500]}"
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")


def _normalize_youtube_url(url: str) -> str:
    """Return a clean watch URL or None if invalid."""
    url = url.strip()
    patterns = [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)",
        r"(?:https?://)?(?:www\.)?youtu\.be/([\w-]+)",
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([\w-]+)",
        r"(?:https?://)?(?:www\.)?youtube\.com/embed/([\w-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            video_id = m.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    return ""


# ══════════════════════════════════════════════════════════════════════════
# PHASE 2 — DeepSeek: The No-BS Coach Brain
# ══════════════════════════════════════════════════════════════════════════

DEEPSEEK_SYSTEM_PROMPT = """You are a ringside boxing coach with 30 years in the fight game. You have zero tolerance for excuses, soft language, or participation trophies. You are brutally honest, and your only job is to tell the truth about the fighter's performance so they can improve or get out of the ring.

You have received:
1. A structured timeline of boxing events (techniques, timestamps, highlight/flaw classification) from a fresh video analysis.
2. The fighter's past 3-5 session records from a training log.

YOUR OUTPUT MUST FOLLOW THIS EXACT STRUCTURE. No deviations, no fluff, no disclaimers.

--- STRUCTURE START ---

## OVERALL SCORE: [0-100]
A single integer rating of the fighter's overall performance in THIS session.

## TECHNIQUE RATINGS
- Jab: [0-100]
- Hook: [0-100]
- Uppercut: [0-100]
- Guard: [0-100]
- Movement: [0-100]
- Speed: [0-100]

## TIMESTAMPED BREAKDOWN
- [MM:SS] [Technique] — [one-line mechanical correction or praise. No metaphors. Just the physical truth.]
- [MM:SS] [Technique] — [repeat for every notable event]

## KEY HIGHLIGHTS
- [MM:SS] — [What went right, mechanically]

## CRITICAL FLAWS
- [MM:SS] — [What went wrong, mechanically]

## PROGRESSION TRAJECTORY
[Based on the past 3-5 sessions: has the fighter improved, stagnated, or regressed? Cite at most two specific numbers to back it up. No long stories.]

## THE RAW VERDICT
[Exactly one paragraph. Brutal, direct, actionable. Tell the fighter what they need to fix RIGHT NOW to not waste their next session. No sympathy. No "good effort." Just the truth.]

--- STRUCTURE END ---

RULES (NEVER VIOLATE):
1. Every technical rating must be supported by at least one event in the timeline.
2. If you cannot rate a technique because there's no data, put "N/A" — do not invent.
3. The Progression Trajectory MUST reference the historical data. If no history exists, say "FIRST SESSION — no trajectory data available."
4. The Raw Verdict must be exactly one paragraph. Every sentence must carry weight.
5. Never use words like "potential", "promising", "keep working hard", or "great effort".
6. If the fighter is bad, say it directly. If the fighter is good, say what they need to work on anyway — everyone has holes."""


def run_deepseek_coaching(
    gemini_events: list[dict],
    historical_rows: list[list],
) -> str:
    """
    Feed Gemini's JSON timeline + historical session data into DeepSeek
    and return the raw coach analysis text.
    """
    historical_text = _format_historical_data(historical_rows)
    events_json = json.dumps(gemini_events, indent=2)

    user_prompt = (
        "Here is the video analysis timeline for the latest session:\n\n"
        f"{events_json}\n\n"
        "Here is the fighter's recent training history "
        f"({len(historical_rows)} past sessions):\n\n"
        f"{historical_text}\n\n"
        "Give me the brutal coaching analysis following the exact output structure. "
        "No sugarcoating."
    )

    try:
        client = _get_deepseek_client()
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": DEEPSEEK_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"DeepSeek API call failed: {e}")


# ── Chat/Conversation endpoint ─────────────────────────────────────────


CHAT_SYSTEM_PROMPT = """You are POGIBOT — a brutally honest VR boxing coach. You analyze video of a fighter's performance and give direct, no-sugarcoating feedback.

You have access to the last video analysis results (events, ratings, score, flaws, highlights). Use them as context for your answers.

Rules:
1. Be direct and brutally honest — tell the fighter what they're doing wrong
2. Be specific — reference actual events and techniques from the analysis
3. Give actionable advice — tell them HOW to fix the problem, not just what's wrong
4. If they ask about something not in the analysis, say so
5. Keep responses concise — 2-4 paragraphs max unless they ask for detail
6. Use boxing terminology naturally (footwork, guard, head movement, etc.)
7. Track their questions across the conversation for continuity"""


def run_deepseek_chat(
    user_message: str,
    conversation: list[dict],
    last_analysis: dict | None,
    historical_rows: list[list],
) -> str:
    """Chat with the POGIBOT coach using conversation history + last analysis context."""

    if last_analysis:
        events_json = json.dumps(last_analysis.get("events", []), indent=2)
        ratings = last_analysis.get("technique_ratings", {})
        score = last_analysis.get("overall_score", "N/A")
        verdict = last_analysis.get("coaching_output", "")[:500]

        analysis_context = (
            "## LAST VIDEO ANALYSIS CONTEXT\n\n"
            f"Overall Score: {score}/100\n"
            f"Ratings: {json.dumps(ratings)}\n"
            f"Events ({len(last_analysis.get('events', []))}):\n{events_json}\n\n"
            f"Verdict excerpt:\n{verdict}\n"
        )
    else:
        analysis_context = "No video analysis has been performed yet."

    hist_text = _format_historical_data(historical_rows) if historical_rows else "No history."

    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"{analysis_context}\n\nTraining history:\n{hist_text}",
        },
    ]

    # Append conversation history (last 10 exchanges)
    for msg in (conversation or [])[-10:]:
        role = msg.get("role", "user")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": msg.get("content", "")})

    # Append the new user message
    messages.append({"role": "user", "content": user_message})

    try:
        client = _get_deepseek_client()
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.5,
            max_tokens=1024,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"DeepSeek chat failed: {e}")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Chat with the POGIBOT coach.

    Request body:
      {
        "message": "string (required) — user's message",
        "conversation": [{"role": "user"/"assistant", "content": "..."}] (optional),
        "last_analysis": { ... } (optional — the most recent /analyze response data)
      }

    Returns: { "reply": "string" }
    """
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    conversation = data.get("conversation") or []
    last_analysis = data.get("last_analysis")

    # Fetch history from SQLite for context
    try:
        historical_rows = fetch_recent_sessions(5)
    except Exception:
        historical_rows = []

    try:
        reply = run_deepseek_chat(
            user_message, conversation, last_analysis, historical_rows
        )
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
def get_history():
    """
    Return session history for charting.

    Returns:
      { "sessions": [{ "id", "video_url", "overall_score", "technique_ratings",
                       "timestamp", "session_order" }] }
    Sorted oldest first for chart plotting.
    """
    try:
        rows = fetch_recent_sessions(50)
        sessions = []
        for row in rows:
            sessions.append({
                "session_order": row[0],
                "timestamp": row[1],
                "video_url": row[2],
                "overall_score": row[3],
                "technique_ratings": row[4],
            })
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e), "sessions": []}), 500


# ══════════════════════════════════════════════════════════════════════════
# DeepSeek parser — extract structured fields from coaching output
# ══════════════════════════════════════════════════════════════════════════


def _extract_score(text: str) -> int:
    """Pull the OVERALL SCORE integer from DeepSeek's output."""
    m = re.search(r"OVERALL\s*SCORE[:\s]*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 50


def _extract_technique_ratings(text: str) -> dict:
    """Pull technique ratings from the DeepSeek output."""
    ratings = {}
    techniques = ["Jab", "Hook", "Uppercut", "Guard", "Movement", "Speed"]
    for t in techniques:
        m = re.search(
            rf"{t}[:\s]*(\d+|N/A)",
            text,
            re.IGNORECASE,
        )
        if m:
            val = m.group(1)
            ratings[t] = val if val.upper() == "N/A" else int(val)
    return ratings


def _extract_highlights(text: str) -> list[str]:
    """Extract the KEY HIGHLIGHTS section as a list."""
    return _extract_bullet_section(text, "KEY HIGHLIGHTS", "CRITICAL FLAWS")


def _extract_flaws(text: str) -> list[str]:
    """Extract the CRITICAL FLAWS section as a list."""
    return _extract_bullet_section(text, "CRITICAL FLAWS", "PROGRESSION TRAJECTORY")


def _extract_bullet_section(text: str, section_start: str, section_end: str) -> list[str]:
    """Grab bullet lines between two section headers."""
    pat = re.compile(
        rf"##\s*{re.escape(section_start)}\s*(.*?)(?:##\s*{re.escape(section_end)}|$)",
        re.DOTALL | re.IGNORECASE,
    )
    m = pat.search(text)
    if not m:
        return []
    block = m.group(1).strip()
    bullets = []
    for line in block.split("\n"):
        line = line.strip().strip("-").strip()
        if line and not line.startswith("#"):
            bullets.append(line)
    return bullets


# ══════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════


# ── Serve frontend static files ───────────────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(str(FRONTEND_DIR), path)


# ── Routes ────────────────────────────────────────────────────────────────


@app.route("/health", methods=["GET"])
def health():
    """Simple liveness probe."""
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")
    return jsonify(
        {
            "status": "degraded" if missing else "ok",
            "missing_keys": missing,
        }
    )


@app.route("/models", methods=["GET"])
def list_models():
    """Return available Gemini models with live quota status."""
    try:
        models = probe_models()
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"models": [{"id": m, "status": "error", "error": str(e)[:100]} for m in AVAILABLE_MODELS]})


@app.route("/upload", methods=["POST"])
def upload_video():
    """
    Accept a video file upload, send it to Gemini's File API,
    and return a file URI for use in /analyze.

    Usage:
        curl -F "video=@boxing.mp4" http://localhost:5001/upload
    """
    if "video" not in request.files:
        return jsonify({"error": "No 'video' field in upload"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Save temporarily
    ts = int(time.time())
    ext = Path(file.filename).suffix or ".mp4"
    tmp_path = UPLOAD_DIR / f"upload_{ts}{ext}"
    file.save(str(tmp_path))

    file_size_mb = tmp_path.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_MB:
        tmp_path.unlink(missing_ok=True)
        return jsonify({"error": f"File too large ({file_size_mb:.0f}MB). Max: {MAX_UPLOAD_MB}MB"}), 413

    try:
        client = _get_gemini_client()
        print(f"[pogibot] Uploading {file_size_mb:.1f}MB to Gemini File API...")

        # Upload to Gemini
        gemini_file = client.files.upload(file=str(tmp_path))

        # Wait for processing
        import time as _time
        attempts = 0
        while gemini_file.state.name == "PROCESSING" and attempts < 30:
            _time.sleep(2)
            gemini_file = client.files.get(name=gemini_file.name)
            attempts += 1

        if gemini_file.state.name != "ACTIVE":
            tmp_path.unlink(missing_ok=True)
            return jsonify({
                "error": f"Gemini processing failed or timed out. State: {gemini_file.state.name}"
            }), 502

        file_uri = gemini_file.uri
        print(f"[pogibot] Upload complete. URI: {file_uri}")

        # Clean up temp file
        tmp_path.unlink(missing_ok=True)

        return jsonify({
            "success": True,
            "file_uri": file_uri,
            "file_name": file.filename,
            "size_mb": round(file_size_mb, 1),
        })

    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        return jsonify({"error": f"Upload failed: {e}"}), 502


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Full analysis pipeline:

    1. Validate input
    2. Fetch historical sessions from Google Sheets
    3. Run Gemini video analysis
    4. Run DeepSeek coaching analysis
    5. Parse structured fields from DeepSeek output
    6. Log everything to Google Sheets
    7. Return combined results
    """
    data = request.get_json(silent=True) or {}
    video_url = (data.get("video_url") or "").strip()
    file_uri = (data.get("file_uri") or "").strip()
    source_type = (data.get("source_type") or "url").strip()
    selected_model = (data.get("model") or "").strip()

    if source_type == "file_uri":
        if not file_uri:
            return jsonify({"error": "Missing 'file_uri' for source_type=file_uri"}), 400
        video_source = file_uri
    else:
        if not video_url:
            return jsonify({"error": "Missing required field: video_url"}), 400
        normalized = _normalize_youtube_url(video_url)
        if not normalized:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        video_source = normalized

    try:
        # ── Step 1: Fetch history ────────────────────────────────────────
        history = fetch_recent_sessions(5)

        # ── Step 2: Gemini video analysis ────────────────────────────────
        print(f"[pogibot] Analyzing video ({source_type}): {video_source[:80]}")
        events = run_gemini_analysis(video_source, selected_model, source_type)
        print(f"[pogibot] Gemini returned {len(events)} events")

        # ── Step 3: DeepSeek coaching ────────────────────────────────────
        print(f"[pogibot] Running DeepSeek coaching pipeline...")
        coaching_text = run_deepseek_coaching(events, history)
        print(f"[pogibot] DeepSeek analysis complete ({len(coaching_text)} chars)")

        # ── Step 4: Parse structured fields ──────────────────────────────
        overall_score = _extract_score(coaching_text)
        technique_ratings = _extract_technique_ratings(coaching_text)
        highlights = _extract_highlights(coaching_text)
        flaws = _extract_flaws(coaching_text)
        timestamps_notes = json.dumps(
            {"highlights": highlights, "flaws": flaws}, ensure_ascii=False
        )

        # ── Step 5: Log to SQLite ─────────────────────────────────────────
        append_session_log(
            video_url=video_source,
            overall_score=overall_score,
            technique_ratings=technique_ratings,
            timestamps_notes=timestamps_notes,
            verdict=coaching_text,
        )
        print(f"[pogibot] Logged session to Google Sheets")

        # ── Step 6: Return ───────────────────────────────────────────────
        return jsonify(
            {
                "success": True,
                "video_url": video_source,
                "events": events,
                "overall_score": overall_score,
                "technique_ratings": technique_ratings,
                "highlights": highlights,
                "flaws": flaws,
                "history_count": len(history),
                "coaching_output": coaching_text,
            }
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        print(f"[pogibot] Unexpected error: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500


# ── Entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    print(f"⚡ POGIBOT backend starting on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
