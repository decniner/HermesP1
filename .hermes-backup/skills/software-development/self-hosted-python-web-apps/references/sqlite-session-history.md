# SQLite Session History — Google Sheets Replacement

When a user doesn't want to set up Google Cloud service accounts, or just wants simpler local persistence, replace Google Sheets with SQLite for session logging.

## Why

- **No Google Cloud Console setup** — no service account, no credentials.json, no API enablement
- **No sharing permissions** — no need to share sheets with service account emails
- **Zero config** — the database auto-creates on first run
- **No network dependency** — works offline, no API rate limits
- **Same data shape** — same columns as the Google Sheets layout

## Implementation

### 1. Import + Schema

```python
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "myapp_history.db"

def _init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            video_url   TEXT NOT NULL,
            overall_score INTEGER NOT NULL,
            technique_ratings TEXT NOT NULL,  -- stored as JSON string
            timestamps_notes  TEXT NOT NULL,
            verdict     TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Call once at module level
_init_db()
```

### 2. Read (Last N Sessions)

```python
def fetch_recent_sessions(n: int = 5) -> list[list]:
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute(
        "SELECT date, video_url, overall_score, technique_ratings, "
        "timestamps_notes, verdict FROM sessions ORDER BY id DESC LIMIT ?",
        (n,),
    )
    rows = cur.fetchall()
    conn.close()
    return [list(r) for r in reversed(rows)]  # oldest first for display
```

### 3. Write (Append Session)

```python
def append_session_log(video_url, overall_score, technique_ratings, notes, verdict):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO sessions (date, video_url, overall_score, "
        "technique_ratings, timestamps_notes, verdict) VALUES (?, ?, ?, ?, ?, ?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            video_url,
            overall_score,
            json.dumps(technique_ratings, ensure_ascii=False),
            notes,
            verdict,
        ),
    )
    conn.commit()
    conn.close()
```

### 4. Format for LLM Prompt

Same format as Google Sheets — the existing `_format_historical_data()` function works unchanged since the row structure is identical.

### 5. Cleanup After Migration

Remove these from your project:
- `google-sheet-id` from `.env`
- `credentials.json` file
- `import gspread` and `from oauth2client.service_account import ServiceAccountCredentials`
- Google Sheets API enablement step from docs

The health endpoint should also drop the `GOOGLE_SHEET_ID` check:

```python
# Before
missing.append("GOOGLE_SHEET_ID")

# After — remove this line
```

## Pitfalls

1. **Database location** — Use `Path(__file__).resolve().parent` so the .db file lives next to app.py, not in the working directory. This survives `cd` changes.
2. **Thread safety** — SQLite has limited concurrent write support. For single-user Flask dev server (one request at a time), simple `connect/execute/close` per call is fine. For production, use `check_same_thread=False` + a connection pool or `flask.g`.
3. **Data portability** — SQLite is a single binary file. Back it up by just copying the .db file. To migrate to a new machine, copy the file along with the code.
4. **Ordering** — `ORDER BY id DESC` with `reversed()` gives oldest-first order for the LLM (chronological history). Without the `reversed()`, the DeepSeek prompt would see most-recent-first, confusing the progression trajectory analysis.
5. **JSON columns** — Store technique ratings as `json.dumps()` string. Read them back with `json.loads()`. This matches the Google Sheets schema where JSON was stored as a text cell.
