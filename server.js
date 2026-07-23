// ── Clippy ↔ Hermes Agent WebSocket Bridge ─────────────────────────────
const { spawn } = require('child_process');
const { WebSocketServer } = require('ws');
const fs = require('fs');
const path = require('path');
const https = require('https');

const PORT = 8081;
const HERMES_BIN = process.env.HERMES_BIN || 'C:/Users/decni/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes';
const GEMINI_KEY = process.env.GEMINI_API_KEY || 'YOUR_GEMINI_API_KEY_HERE';
const TMP = path.join(__dirname, 'tmp');

if (!fs.existsSync(TMP)) fs.mkdirSync(TMP, { recursive: true });

const wss = new WebSocketServer({ port: PORT });
console.log(`[clippy-bridge] Listening on ws://0.0.0.0:${PORT}`);
console.log(`[clippy-bridge] Gemini vision: ${GEMINI_KEY ? '✅ configured' : '❌ missing'}`);

wss.on('connection', (ws, req) => {
  const ip = req.socket.remoteAddress;
  console.log(`[clippy-bridge] Client: ${ip}`);

  ws.on('message', async (raw) => {
    let p;
    try { p = JSON.parse(raw.toString()); } catch { return; }

    if (p.type === 'camera_image') {
      console.log(`[clippy-bridge] Camera: ${(p.image || '').length} bytes`);
      try { await vision(ws, p.image); } catch (e) { ws.send(JSON.stringify({ type: 'clippy_message', text: '📷 Oops, my eyes blurred! ' + e.message })); }
    } else if (p.type === 'user_message') {
      const t = (p.text || '').trim();
      if (!t) return;
      // Let chat() handle all message types including news
      console.log(`[clippy-bridge] Chat: ${t.substring(0, 80)}`);
      try { await chat(ws, t); } catch (e) { ws.send(JSON.stringify({ type: 'clippy_message', text: '⚠️ ' + e.message })); }
    }
  });

  ws.on('close', () => console.log(`[clippy-bridge] Disconnected: ${ip}`));
  ws.on('error', (e) => console.log(`[clippy-bridge] Error: ${e.message}`));
});

// ── Web Search (Wikipedia API — free, no key) ──
function webSearch(text, callback) {
  const query = encodeURIComponent(text.replace(/news|latest|what|happening|search|find|look up/gi, '').trim() || 'technology');
  const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${query}`;
  const req = https.get(url, (res) => {
    let data = '';
    res.on('data', c => data += c);
    res.on('end', () => {
      try {
        const j = JSON.parse(data);
        if (j.title && j.extract) {
          const summary = j.extract.replace(/<[^>]+>/g, '').substring(0, 300);
          callback(`📖 ${j.title}: ${summary}`);
        } else {
          callback(`🔍 I found "${query}" but couldn't get details. Try a different search!`);
        }
      } catch {
        callback(`🔍 Hmm, I couldn't look up "${query}" right now. Try asking differently!`);
      }
    });
  });
  req.on('error', () => callback('🔍 Web search is unavailable right now.'));
  req.setTimeout(8000, () => { req.destroy(); callback('🔍 Search timed out.'); });
}

// ── News Fetch (BBC RSS) ──
function fetchNews(callback) {
  const req = https.get('https://feeds.bbci.co.uk/news/technology/rss.xml', (res) => {
    let data = '';
    res.on('data', c => data += c);
    res.on('end', () => {
      try {
        const titles = [];
        const regex = /<title>(?:<!\[CDATA\[)?([^<]+?)(?:\]\]>)?<\/title>/g;
        let m;
        while ((m = regex.exec(data)) !== null && titles.length < 5) {
          const t = m[1].replace(/<!\[CDATA\[|\]\]>/g, '').trim();
          if (t && !t.includes('BBC News')) titles.push(t);
        }
        if (titles.length > 0) {
          callback(`📰 Latest headlines:\n• ${titles.join('\n• ')}`);
        } else {
          callback('📰 News feeds are quiet right now. Try asking me something else!');
        }
      } catch {
        callback('📰 Could not fetch news right now.');
      }
    });
  });
  req.on('error', () => callback('📰 News unavailable right now.'));
  req.setTimeout(8000, () => { req.destroy(); callback('📰 Search timed out.'); });
}

// ── Chat (Hermes CLI + Web fallback) ──
async function chat(ws, text) {
  const lower = text.toLowerCase();
  
  // News query — fetch live headlines
  if (lower.includes('news') || lower.includes('headline') || lower.includes('what\'s happening') || lower.includes('latest')) {
    fetchNews((result) => {
      ws.send(JSON.stringify({ type: 'clippy_message', text: result }));
    });
    return;
  }
  
  // Web search query — look up Wikipedia
  if (lower.includes('search') || lower.includes('look up') || lower.includes('find') || lower.includes('who is') || lower.includes('what is')) {
    webSearch(text, (result) => {
      ws.send(JSON.stringify({ type: 'clippy_message', text: result }));
    });
    return;
  }
  
  // Default: use Hermes CLI
  return new Promise((resolve) => {
    const child = spawn(HERMES_BIN, ['-z', `You are BB-8, created by Denver Sanchez. You are a feisty brave astromech droid in a spherical body. Answer in 1-2 short sentences. Speak naturally — never describe your sounds with brackets or asterisks. Be sassy, loyal, and heroic. If asked about Denver Sanchez, only say he created you and keep it vague. ${text}`], {
      shell: false,
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let o = '', e = '';
    child.stdout.on('data', d => o += d);
    child.stderr.on('data', d => e += d);
    child.on('close', () => {
      const r = o.trim() || e.trim() || 'Beep boop! 🤖';
      ws.send(JSON.stringify({ type: 'clippy_message', text: r }));
      resolve();
    });
    child.on('error', (er) => {
      ws.send(JSON.stringify({ type: 'clippy_message', text: 'Bzzzt! Error: ' + er.message }));
      resolve();
    });
    setTimeout(() => { if (!child.killed) child.kill(); resolve(); }, 30000);
  });
}

// ── Vision (Gemini API) ──
async function vision(ws, base64Image) {
  return new Promise((resolve) => {
    // Build Gemini API request
    const body = JSON.stringify({
      contents: [{
        parts: [
          { text: 'Describe what you see in this image in 1-2 short natural sentences. Never use brackets or asterisks. Be playful and brief.' },
          { inline_data: { mime_type: 'image/jpeg', data: base64Image } }
        ]
      }]
    });

    const opts = {
      hostname: 'generativelanguage.googleapis.com',
      path: `/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_KEY}`,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': body.length },
    };

    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const j = JSON.parse(data);
          const text = j.candidates?.[0]?.content?.parts?.[0]?.text || 'I see something interesting! 👀';
          ws.send(JSON.stringify({ type: 'clippy_message', text: '📷 ' + text }));
        } catch {
          // Fallback when Gemini is unavailable
          ws.send(JSON.stringify({ type: 'clippy_message', text: '📷 I see you! Camera works — Gemini vision API is rate limited right now. Try again later or get a new API key! 🔄' }));
        }
        resolve();
      });
    });
    req.on('error', (e) => {
      ws.send(JSON.stringify({ type: 'clippy_message', text: '📷 My eyes are a bit blurry right now. Try again! 😅' }));
      resolve();
    });
    req.write(body);
    req.end();
  });
}

console.log(`[clippy-bridge] Ready on port ${PORT}`);
