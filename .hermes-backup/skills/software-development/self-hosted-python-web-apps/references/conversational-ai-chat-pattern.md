# Adding Conversational AI Chat to a Flask App

Pattern for adding a chat/conversation endpoint to a Flask AI proxy backend.

## Backend: POST /chat Endpoint

```python
CHAT_SYSTEM_PROMPT = """You are a [persona] — [description].

You have access to the last analysis results. Use them as context.

Rules:
1. Be direct — reference actual data from the analysis
2. Give actionable advice
3. If asked about something not in the analysis, say so
4. Keep responses concise — 2-4 paragraphs
5. Track conversation continuity""""

def run_deepseek_chat(user_message, conversation, last_analysis, historical_rows):
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "system", "content": analysis_context + "\n\n" + history_context},
    ]
    # Append last 10 conversation exchanges
    for msg in (conversation or [])[-10:]:
        if msg.get("role") in ("user", "assistant"):
            messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
    )
    return resp.choices[0].message.content.strip()
```

## Request/Response Shape

```
POST /chat
{
  "message": "string",
  "conversation": [{"role": "user"|"assistant", "content": "..."}],
  "last_analysis": { ... }  // optional, from most recent /analyze response
}

→ { "reply": "string" }
```

## Frontend Integration

```javascript
// State
let chatConversation = [];
let lastAnalysisData = null;

// Store after each analysis
function storeLastAnalysis(data) {
  lastAnalysisData = {
    events: data.events,
    overall_score: data.overall_score,
    technique_ratings: data.technique_ratings,
    highlights: data.highlights,
    flaws: data.flaws,
    coaching_output: data.coaching_output,
  };
}

// Send and receive
async function sendChat() {
  const msg = chatInput.value.trim();
  if (!msg) return;

  appendChatMsg('user', msg);
  chatInput.value = '';

  const resp = await fetch(`/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: msg,
      conversation: chatConversation,
      last_analysis: lastAnalysisData,
    }),
  });
  const data = await resp.json();

  appendChatMsg('assistant', data.reply);
  chatConversation.push({ role: 'user', content: msg });
  chatConversation.push({ role: 'assistant', content: data.reply });
}
```

## Key Design Decisions

1. **Conversation array maintained client-side** — Server is stateless. Client sends the full history each time.
2. **Last 10 messages only** — Prevents token bloat. Older context is summarized via `last_analysis`.
3. **Analysis context injected as system message** — Not user message — so the model treats it as ground truth, not something to argue with.
4. **Persona prompt in system message** — Sets tone and behavior consistently.
5. **History fetched server-side** — SQLite session history is pulled by the backend, not sent by the client.
