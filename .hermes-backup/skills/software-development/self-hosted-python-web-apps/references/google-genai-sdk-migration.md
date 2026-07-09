# Google Gemini SDK: `google.generativeai` → `google.genai` Migration

## Why

The old `google.generativeai` SDK is **deprecated**:
```
FutureWarning: All support for the `google.generativeai` package has ended.
It will no longer be receiving updates or bug fixes.
Please switch to the `google.genai` package as soon as possible.
```

Use `google-genai>=1.0.0` (PyPI package name: `google-genai`, import: `google.genai`).

## Import Changes

| Old (`google.generativeai`) | New (`google.genai`) |
|------------------------------|----------------------|
| `import google.generativeai as genai` | `from google import genai`<br/>`from google.genai import types as genai_types` |

## Client Initialization

```python
# OLD
import google.generativeai as genai
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# NEW
from google import genai
client = genai.Client(api_key=API_KEY)
```

## Generate Content

```python
# OLD
response = model.generate_content(
    contents=[text_prompt, video_part],
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        temperature=0.1,
        max_output_tokens=2048,
    ),
    request_options={"timeout": 120},
)

# NEW
from google.genai import types as genai_types
response = client.models.generate_content(
    model="models/gemini-2.0-flash",
    contents=[text_prompt, video_part],
    config=genai_types.GenerateContentConfig(
        system_instruction="You are...",
        response_mime_type="application/json",
        temperature=0.1,
        max_output_tokens=2048,
    ),
)
```

## YouTube Video as Input

```python
# OLD
contents = [
    "Analyze this video",
    {"mime_type": "video/mp4", "uri": "https://www.youtube.com/watch?v=VIDEO_ID"},
]

# NEW — Use genai_types.Part.from_uri()
contents = [
    "Analyze this video",
    genai_types.Part.from_uri(
        file_uri="https://www.youtube.com/watch?v=VIDEO_ID",
        mime_type="video/mp4",
    ),
]
```

## System Instruction

```python
# OLD — Set on the model constructor
model = genai.GenerativeModel(
    "models/gemini-1.5-flash",
    system_instruction="You are a helpful assistant.",
)

# NEW — Set on the config, passed per-request
config=genai_types.GenerateContentConfig(
    system_instruction="You are a helpful assistant.",
)
```

## Common Pitfalls

1. **`genai_types` name collision** — Alias `from google.genai import types as genai_types` to avoid shadowing the `genai` module.
2. **Model name format** — Both `"gemini-2.0-flash"` and `"models/gemini-2.0-flash"` work in the new SDK.
3. **Model availability** — The `gemini-1.5` series (`gemini-1.5-flash`, `gemini-1.5-flash-001`, etc.) has been **removed from the API** (returns `404 NOT_FOUND`). Use `gemini-2.0-flash`, `gemini-2.5-flash`, or `gemini-flash-latest` instead. List available models with: `client.models.list()`.
4. **Timeout config** — Not available in `GenerateContentConfig`. Set at client init: `genai.Client(api_key=KEY, http_options={'timeout': 120})`.
5. **Streaming** — Use `client.models.generate_content_stream()` instead of `model.generate_content(..., stream=True)`.
6. **`response_mime_type="application/json"` unreliable** — On `gemini-2.5-flash` and newer, this mode returns truncated or non-JSON text. Remove it and implement manual JSON extraction with string-aware bracket balancing (see `flask-ai-proxy-pattern.md` for the implementation).
7. **Free-tier quota per model** — Each model has an independent daily quota (~20 requests/day). On 429, switch models: `gemini-2.0-flash` → `gemini-2.5-flash` → `gemini-3.5-flash` → `gemini-flash-latest` → `gemini-2.5-flash-lite`.
8. **Max tokens** — Increase from default 2048 to 8192 for video analysis to prevent truncation.
