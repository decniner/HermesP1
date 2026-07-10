# Dual-AI Pipeline Pattern

Orchestrating a two-phase AI pipeline where Phase 1 feeds structured data into Phase 2 for contextual reasoning.

## Architecture

```
User Input → Phase 1 (Data Extraction) → structured JSON → Phase 2 (Reasoning) → Final Output
                                                                    ↑
                                                          Historical DB (SQLite/Sheets)
```

## Phase 1: Structured Data Extraction

Use Gemini with `system_instruction` + low temperature (0.1) for consistent JSON output:

```python
GEMINI_SYSTEM = """You are a cold, hyper-objective tracker. No personality.
Output a JSON array of events only. Each event has:
  - "timestamp": "MM:SS"
  - "technique": one of specific options
  - "type": "Highlight" | "Flaw"
  - "notes": one-sentence mechanical description"""

events = run_gemini_analysis(video_url)  # Returns list[dict]
```

## Phase 2: Contextual Coaching/Analysis

Feed Phase 1 output + historical data into a persona-driven LLM:

```python
DEEPSEEK_SYSTEM = """You are a [persona]. Brutally honest, evidence-based.
Output must follow this exact structure:

## OVERALL SCORE: [0-100]
## TECHNIQUE RATINGS
  - Technique: [0-100 or N/A]
## TIMESTAMPED BREAKDOWN
  - [MM:SS] Technique — mechanical truth
## KEY HIGHLIGHTS
## CRITICAL FLAWS
## PROGRESSION TRAJECTORY
  (reference historical data — cite specific numbers)
## THE RAW VERDICT
  (one paragraph, actionable, no sugarcoating)"""

user_prompt = f"Timeline:\n{json.dumps(events)}\n\nHistory:\n{historical_text}"
```

## Persona Crafting Rules

1. **Phase 1 persona**: Clinical, emotionless, mechanical. No identity, no coaching, no opinions.
2. **Phase 2 persona**: Strong voice, strict, evidence-based. Every claim must cite data.
3. **Output structure**: Must be parseable by regex/string matching after generation.
4. **No opinion in Phase 1** — only objective descriptions.

## Historical Data for Progression

Pass last 3-5 sessions to Phase 2 so it can assess improvement/regression:

```python
def fetch_recent_sessions(n=5):
    # From SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (n,))
    rows = cur.fetchall()
    conn.close()
    return [list(r) for r in reversed(rows)]  # oldest first
```

Format for prompt:
```
Session: 2026-07-09 13:04 | Score: 72 |
Ratings: {"Jab": 85, "Hook": 90} |
Verdict: ## OVERALL SCORE: 72...
```

## Structured Output Parsing

After Phase 2, extract structured fields from freeform text:

```python
def _extract_score(text):
    m = re.search(r"OVERALL\s*SCORE[:\s]*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 50

def _extract_technique_ratings(text):
    ratings = {}
    for t in ["Jab", "Hook", "Uppercut", "Guard", "Movement", "Speed"]:
        m = re.search(rf"{t}[:\s]*(\d+|N/A)", text, re.IGNORECASE)
        if m:
            ratings[t] = m.group(1) if m.group(1).upper() == "N/A" else int(m.group(1))
    return ratings

def _extract_bullet_section(text, section_start, section_end):
    """Extract bullet list between two ## headers."""
    pat = re.compile(rf"##\s*{re.escape(section_start)}\s*(.*?)(?:##|$)", re.DOTALL | re.IGNORECASE)
    m = pat.search(text)
    if not m: return []
    return [line.strip().strip("-").strip() for line in m.group(1).split("\n")
            if line.strip() and not line.strip().startswith("#")]
```

## Error Handling Pipeline

Wrap each phase independently so one failure doesn't cascade:

```python
try:
    events = run_gemini_analysis(url)
except Exception as e:
    return jsonify({"error": f"Phase 1 failed: {e}"}), 502

try:
    coaching = run_deepseek_coaching(events, history)
except Exception as e:
    return jsonify({"error": f"Phase 2 failed: {e}"}), 502

# Log regardless of partial results
append_session_log(...)
```
