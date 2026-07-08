# OpenRouter Anthropic-Format API — Discovery Notes

## Key Finding (July 2026)

OpenRouter's `POST /api/v1/messages` endpoint **natively accepts the Anthropic Messages
API format** for non-Claude models (Qwen, DeepSeek, Gemma, etc.). This means you can
send Anthropic-format requests to OpenRouter and get Anthropic-format responses back
without any format translation layer.

## Direct API Test

```bash
curl -X POST "https://openrouter.ai/api/v1/messages" \
  -H "Authorization: Bearer sk-or-v1-..." \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "qwen/qwen-2.5-coder-32b-instruct",
    "max_tokens": 100,
    "messages": [
      {"role": "user", "content": "Say hello"}
    ]
  }'
```

Response is valid Anthropic format:
```json
{
  "id": "gen-...",
  "type": "message",
  "role": "assistant",
  "content": [{"type": "text", "text": "Hello!"}],
  "model": "qwen/qwen-2.5-coder-32b-instruct",
  "usage": {...}
}
```

## Why This Doesn't Solve Claude Code Auth

Claude Code v2.1+ has **client-side model name validation** baked into its compiled
binary. Even though OpenRouter accepts Anthropic format, Claude Code refuses to send
the request because the model name (e.g. `qwen/qwen-2.5-coder-32b-instruct`) isn't
in its hardcoded list of valid Claude models.

The community `fuergaosi233/claude-code-proxy` solves this by translating to **OpenAI
format** instead, so Claude Code sees its own valid model names while the proxy handles
mapping to OpenRouter models in OpenAI format.

## Practical Use Cases for This Discovery

This is useful for:
1. **Custom tooling** — Building agents that speak Anthropic format but route through
   OpenRouter's free tier
2. **Testing** — Validating OpenRouter model behavior with Anthropic-format requests
   before building full integrations
3. **Migrating Anthropic-native code** — Pointing Anthropic SDK clients at OpenRouter
   with model name changes
4. **Fallback routing** — Agents that prefer Anthropic API but can fall back to
   OpenRouter without changing their message format layer

## Model Compatibility

Tested working with Anthropic format on OpenRouter (July 2026):
- `qwen/qwen-2.5-coder-32b-instruct` — Fully functional
- `google/gemma-4-9b-it` — Fully functional
- `deepseek/deepseek-chat` — Fully functional

All OpenRouter model IDs that accept Anthropic format follow the `provider/model` scheme
(e.g. `google/gemma-4-9b-it`), not Anthropic's `claude-model-name` scheme.
