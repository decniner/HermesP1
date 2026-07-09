---
name: html-preview-deployment
description: Patterns and pitfalls for deploying HTML artifacts through third-party preview services (htmlpreview.github.io, raw.githubusercontent.com, etc.) — ensuring interactivity, audio, and assets survive the serving pipeline.
trigger: Building a standalone HTML file or interactive web artifact that will be shared via a URL, especially through services that proxy raw GitHub content.
---

# HTML Preview Deployment

## The Core Problem

Third-party HTML preview services (`htmlpreview.github.io`, etc.) fetch raw HTML from GitHub and inject it into a sandboxed page. This breaks common patterns:

1. **Inline scripts truncated** at ~3,400 characters
2. **External script src** may not load (wrong MIME type from `raw.githubusercontent.com`)
3. **Relative asset paths** (`./image.jpg`, `audio.mp3`) resolve relative to the preview domain, not the repo
4. **Event listeners** may not persist if the service pre-renders DOM and strips JS

## Fixes

### Inline Script Truncation
Minify all inline JavaScript to **under ~3,400 characters**. Use a JS minifier or aggressively compress:
- Remove all comments, whitespace, and optional semicolons
- Shorten `document.getElementById` → use a short alias (e.g., `var d=document.getElementById`)
- Single-letter variable names inside closures
- Combine multiple var declarations

If your JS holds logic for a birthday card or similar interactive artifact, see the `birthday-card` skill for a minification strategy tuned to the 3,400-char limit (short variable names, reduced confetti colors, shorter console.log, combined declarations, etc.).

**Line-length truncation:** In addition to the total size limit, htmlpreview may also truncate individual lines longer than ~700-800 characters. After minification, split the JS across multiple lines (~300-400 chars per line) as insurance. Break at natural boundaries (between function definitions, after variable declarations).

**Diagnosis — how to confirm truncation happened:**

1. Open the htmlpreview URL in the browser
2. In console, run:
```javascript
let scripts = document.querySelectorAll('script'), last = '';
scripts.forEach(s => { if (s.textContent.includes('yourFunctionName')) last = s.textContent; });
'Script length: ' + last.length;
```
3. If length is ~3,400 (or suspiciously short) and your source is longer, truncation happened
4. Check the last ~80 chars of the script:
```javascript
last.substring(last.length - 80);
```
   - Should end with valid JS (`})();` for an IIFE, not mid-expression)
   - Historical example of corrupted ending: `'carousel-dot active':'carousel-dot'}})}})();` — extra `}})` brackets from truncation

### External Script Files (Avoid)
`<script src="script.js">` gets rewritten by htmlpreview to point at `raw.githubusercontent.com`, which serves with `Content-Type: text/plain`. Modern browsers block scripts served as text/plain. Inline minified is more reliable.

### Relative Asset Paths
Assets referenced with relative paths (`birthday-music.mp3`, `photo.jpeg`) resolve against the preview service's domain, not the GitHub repo. `htmlpreview.github.io` rewrites `<img src>` and `<audio src>` to raw GitHub URLs, but dynamically-created `new Audio('file.mp3')` in JS does NOT get rewritten — it will 404.

**Fix for dynamic audio/images:** Use paths that work relative to the HTML file's location in the repo (same directory). The service will only rewrite statically-declared src attributes.

## Testing Checklist
- [ ] Does the page render the front/initial state through the preview URL?
- [ ] Do click/tap interactions work?
- [ ] Do dynamically-loaded assets (audio, images from JS) load?
- [ ] Check console for 404s and JS errors
- [ ] Verify script content length isn't truncated

## Design Patterns

### Kindle-Style Books vs. Page-Flip Animation

When the user requests a "book" or "reading interface," start with a **Kindle-style single-page view** — NOT a 3D page-flip animation or two-page spread layout. The user has rejected both alternatives. 

**Navigation: Prev/Next buttons ONLY.** The user explicitly rejected all of these (in order):
1. ❌ 3D CSS page-flip — "it doesn't work"
2. ❌ Two-page spread — "it doesn't work"  
3. ❌ Tap zone overlays / left-right click — "rely on arrow at the bottom"
4. ❌ Touch swipe detection — "scrolling should not switch pages"
5. ✅ **Bottom arrow buttons (◀ Prev / Next ▶)** — this is the ONLY approved navigation

**Content: no scrolling.** All content must fit on one page using compact font defaults (14px body, 20px h1) and `overflow: hidden`. The user adjusts text size via the Aa button if needed.

Key characteristics:
- Single-page view with opacity fade transition (0.2s)
- Navigation exclusively via Prev/Next buttons at the bottom
- Tap on page content only toggles menu bars (NOT page navigation)
- No overlay tap zone divs — JS click handler with `touchmove` guard to distinguish taps from scrolls
- Content fits without scrolling (`overflow: hidden`, compact sizing)
- Slide-out TOC sidebar, font size controls (Aa), dark/light toggle
- Progress bar at bottom showing cumulative reading position
- All links clickable, all text selectable

See `references/kindle-style-reader.md` for the full implementation.

### Content Completeness

When the user asks for a list of use cases or features in a book/guide, **every entry must include concrete, copy-pasteable commands.** Descriptions alone are not sufficient — each use case needs:
- The actual cron job `cronjob action='create' ...` command
- The skill `skill_manage action='create' ...` block
- The prompt the user sends
- Configuration YAML snippets

The user has explicitly rejected "just descriptions" multiple times. If a use case doesn't have a working command the reader can run, it's incomplete.

### Sharing via htmlpreview.github.io

When the user wants a clickable URL to share with friends, use `htmlpreview.github.io` — not raw.githubusercontent.com (shows source, not rendered) and not GitHub Pages (requires repo settings changes):

```
https://htmlpreview.github.io/?https://github.com/decniner/HermesP1/blob/main/hermes-book/HermesAgentBook.html
```

This renders the HTML in a browser sandbox, keeping all interactivity (links, JS, CSS) intact. No GitHub Pages setup or repo configuration needed.

## Related Skills

- `web-app-demo-video` — After deploying an HTML app via htmlpreview, use this skill to create a professional demo/promo video from browser screenshots, with ffmpeg slideshow transitions and TTS narration.

## Live App Tunneling (Flask / Streamlit / HTTP Servers)

When you need to expose a locally-running Python web app (Flask, Streamlit, etc.) to a remote browser without Wi-Fi or port forwarding, use a tunnel service.

### Tunnel Service Comparison

| Service | Install | Long POST handling | Free tier reliability |
|---------|---------|-------------------|----------------------|
| **serveo.net** | `ssh -R 80:localhost:PORT serveo.net` | ❌ Drops requests >30s | ⚠️ Intermittent |
| **localtunnel** | `npx localtunnel --port PORT` | ❌ 503 after first use | ❌ Unreliable |
| **cloudflared** | `npm install -g cloudflared` | ✅ Handles long requests | ✅ Most reliable |

**Winner:** `cloudflared` — handles long-running POST requests (Gemini/DeepSeek pipelines taking 60+ seconds), stays up reliably, and is free:

```bash
npm install -g cloudflared
cloudflared tunnel --url http://localhost:5001
# → https://xxxxx.trycloudflare.com
```

### Same-Origin Architecture (Eliminates CORS)

When tunneling a multi-service app (frontend + backend), **serve both from Flask**:

```
❌ TWO TUNNELS: Frontend URL → fetch() → Backend URL (CORS + timeouts)
✅ ONE TUNNEL: Flask serves HTML + API on one port (relative fetch, no CORS)
```

```python
# Flask serves frontend static files
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@app.route("/")
def serve_index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")
```

Frontend JS uses relative path: `const BACKEND_URL = '';`

### Lazy API Client Init

Allow server to start even without API keys configured:

```python
_gemini_client = None
def _get_gemini_client():
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client
```

### Gemini API (google-genai SDK) — Current State

Old `google.generativeai` SDK is **deprecated**. Use `google.genai`:

```python
from google import genai
from google.genai import types as genai_types
client = genai.Client(api_key=GEMINI_API_KEY)

# YouTube video analysis
response = client.models.generate_content(
    model="models/gemini-2.5-flash",
    contents=[
        "Analyze this video...",
        genai_types.Part.from_uri(file_uri=youtube_url, mime_type="video/mp4"),
    ],
    config=genai_types.GenerateContentConfig(
        system_instruction="...",
        temperature=0.1,
        max_output_tokens=8192,
    ),
)
```

**Model notes:** `gemini-1.5-flash` removed from API (404). `gemini-2.0-flash` 429 exhausted. `gemini-2.5-flash` current best. List with `client.models.list()`.

### Tunnel Pitfalls

1. **Test with the real request** — Curling `GET /health` is not enough. Test `POST /analyze` with the actual payload through the tunnel URL before telling the user
2. **Tunnel warning pages** — serveo/localtunnel show interstitial pages. Check with `curl -D -` for redirects
3. **pyngrok on Windows** — auto-downloader may fail with zip errors. Use native binary or cloudflared instead
4. **Same-origin fetch** — When `BACKEND_URL=''`, Flask must serve the HTML at root path

## Reference Files

- `references/kindle-style-reader.md` — Full Kindle-style reading interface implementation: architecture, CSS variables, page transitions, navigation logic, progress calculation, touch swipe detection, mobile responsiveness, tap zones via JS click detection, links/text selection handling, GitHub sharing pattern, and 11 documented pitfalls.
