# Gemini Video Analysis Patterns

Working with the `google.genai` SDK for video analysis in a Flask backend.

## YouTube URL Input

Gemini 2.5+ models can process YouTube URLs natively using `Part.from_uri()`:

```python
from google import genai
from google.genai import types as genai_types

client = genai.Client(api_key=API_KEY)
response = client.models.generate_content(
    model="models/gemini-3.5-flash",
    contents=[
        "Analyze this boxing video...",
        genai_types.Part.from_uri(
            file_uri="https://www.youtube.com/watch?v=VIDEO_ID",
            mime_type="video/mp4",
        ),
    ],
    config=genai_types.GenerateContentConfig(
        system_instruction="You are a clinical boxing analyst...",
        temperature=0.1,
        max_output_tokens=8192,
    ),
)
```

## Local File Upload via Gemini File API

For uploaded video files (not YouTube URLs):

```python
# Step 1: Upload to Gemini
gemini_file = client.files.upload(file="/path/to/video.mp4")

# Step 2: Wait for processing (can take 10-60s depending on file size)
import time as _time
while gemini_file.state.name == "PROCESSING":
    _time.sleep(2)
    gemini_file = client.files.get(name=gemini_file.name)

# Step 3: Use the returned URI in generate_content
if gemini_file.state.name == "ACTIVE":
    contents = [
        "Analyze this video...",
        genai_types.Part.from_uri(
            file_uri=gemini_file.uri,
            mime_type="video/mp4",
        ),
    ]
```

Gemini File API accepts: `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv`, `.flv`, `.wmv`, `.mpeg`.
Max file size: 2GB (Gemini free tier may have lower limits).

## JSON Truncation Handling

Gemini sometimes truncates JSON output mid-response (especially for long videos). Always handle this:

```python
text = response.text.strip()
# Find first JSON array
array_match = re.search(r"\[\s*\{.*", text, re.DOTALL)
if array_match:
    text = array_match.group(0)

# Walk through tracking brackets/strings to find valid end
open_objs = open_arrays = 0
in_string = escape = False
cut_pos = len(text)
for i, ch in enumerate(text):
    if escape: escape = False; continue
    if ch == "\\" and in_string: escape = True; continue
    if ch == '"' and not escape: in_string = not in_string; continue
    if in_string: continue
    if ch == "{": open_objs += 1
    elif ch == "}": open_objs -= 1
    elif ch == "[": open_arrays += 1
    elif ch == "]": open_arrays -= 1
    if open_objs == 0 and open_arrays == 0 and ch == "]":
        cut_pos = i + 1; break

text = text[:cut_pos].strip().rstrip(",")
text += "]" * (text.count("[") - text.count("]"))
text += "}" * (text.count("{") - text.count("}"))
parsed = json.loads(text)
```

## Available Models Quota Probing

Free tier Gemini has daily per-model quotas (~20 req/day). Probe at startup:

```python
AVAILABLE_MODELS = [
    "models/gemini-2.5-flash-lite",
    "models/gemini-3.5-flash",
    "models/gemini-3.1-flash-lite",
]

def probe_models() -> list[dict]:
    results = []
    for model_id in AVAILABLE_MODELS:
        try:
            client.models.generate_content(model=model_id, contents="ok")
            results.append({"id": model_id, "status": "available"})
        except Exception as e:
            if "429" in str(e):
                results.append({"id": model_id, "status": "quota_exhausted"})
            else:
                results.append({"id": model_id, "status": "error"})
    return results
```

Cache ~30s. Expose as `GET /models` endpoint. Frontend shows color-coded dropdown.

## Known Models

| Model | Video | Notes |
|-------|-------|-------|
| `gemini-2.5-flash` | ✅ | 20 req/day free |
| `gemini-2.5-flash-lite` | ✅ | Cheaper tier |
| `gemini-3.5-flash` | ✅ | Newest, separate quota |
| `gemini-1.5-flash` | ❌ | Removed — 404 |
