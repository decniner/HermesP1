/**
 * POGIBOT — VR Boxing AI Coach
 * ───────────────────────────────────────────────────────
 * Frontend JavaScript Snippet
 * 
 * Standalone fetch + DOM manipulation module.
 * Integrate this into any static HTML page by:
 *   1. Copying the <script> block into your page
 *   2. Adding the matching HTML structure (see frontend/index.html)
 *   3. Pointing BACKEND_URL at your running Flask proxy
 * 
 * Expected backend response shape:
 *   {
 *     success: bool,
 *     events: [{timestamp, technique, type, notes}],
 *     overall_score: int,
 *     technique_ratings: {Jab: int, Hook: int, ...},
 *     highlights: [string],
 *     flaws: [string],
 *     history_count: int,
 *     coaching_output: string (full Markdown)
 *   }
 */

const BACKEND_URL = 'http://localhost:5001';

// ── DOM references (adjust selectors to match your HTML) ──
const statusEl     = document.getElementById('status');
const resultsEl    = document.getElementById('results');
const videoInput   = document.getElementById('videoUrl');
const analyzeBtn   = document.getElementById('analyzeBtn');

// ── Status helpers ──
function setStatus(type, msg) {
  statusEl.className = type;          // 'loading' | 'error' | 'success'
  statusEl.textContent = msg;
  statusEl.style.display = 'block';
}
function clearStatus() {
  statusEl.style.display = 'none';
  statusEl.className = '';
}

// ── Core analysis call ──
async function analyzeVideo() {
  const url = videoInput.value.trim();
  if (!url) {
    setStatus('error', '⚠️ Paste a YouTube URL first.');
    return;
  }

  clearStatus();
  resultsEl.style.display = 'none';
  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = '<span class="spinner"></span> Analyzing...';
  setStatus('loading', '⏳ Sending to POGIBOT backend...');

  try {
    const resp = await fetch(`${BACKEND_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_url: url }),
    });

    const data = await resp.json();

    if (!resp.ok) {
      setStatus('error', `❌ Backend error: ${data.error || resp.statusText}`);
      return;
    }
    if (!data.success) {
      setStatus('error', `❌ Analysis failed: ${data.error || 'Unknown'}`);
      return;
    }

    // Populate each UI section
    renderOverallScore(data.overall_score);
    renderTechniqueRatings(data.technique_ratings);
    renderEvents(data.events);
    renderHighlights(data.highlights);
    renderFlaws(data.flaws);
    renderVerdict(data.coaching_output);
    renderHistory(data);

    resultsEl.style.display = 'grid';
    setStatus('success', `✅ Done — ${data.events.length} events.`);
  } catch (err) {
    setStatus('error', `❌ Connection failed: ${err.message}`);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = '🔥 ANALYZE';
  }
}

// ── Render each card ──

function renderOverallScore(score) {
  const el = document.getElementById('overallScore');
  const num = el.querySelector('.number');
  num.textContent = score ?? '—';
  // Colour by tier
  if (score >= 80) num.style.color = '#00c853';
  else if (score >= 60) num.style.color = '#ffd600';
  else num.style.color = '#ff1744';
}

function renderTechniqueRatings(ratings) {
  const container = document.getElementById('ratingsContainer');
  if (!ratings || Object.keys(ratings).length === 0) {
    container.innerHTML = '<p class="empty">No technique data.</p>';
    return;
  }
  container.innerHTML = '';
  for (const [technique, value] of Object.entries(ratings)) {
    const isNA = String(value).toUpperCase() === 'N/A';
    const pct = isNA ? 0 : Number(value);
    let color = '#555';
    if (!isNA && pct >= 80) color = '#00c853';
    else if (!isNA && pct >= 60) color = '#ffd600';
    else if (!isNA) color = '#ff1744';

    const bar = document.createElement('div');
    bar.className = 'rating-bar';
    bar.innerHTML = `
      <span class="label">${technique}</span>
      <div class="track">
        <div class="fill" style="width:${pct}%;background:${color};"></div>
      </div>
      <span class="value" style="color:${color}">${isNA ? 'N/A' : pct}</span>
    `;
    container.appendChild(bar);
  }
}

function renderEvents(events) {
  const list = document.getElementById('eventsList');
  if (!events || events.length === 0) {
    list.innerHTML = '<li class="empty">No events.</li>';
    return;
  }
  list.innerHTML = events.map(e => {
    const typeClass = (e.type || '').toLowerCase() === 'highlight' ? 'highlight' : 'flaw';
    const tagClass  = typeClass === 'highlight' ? 'tag-highlight' : 'tag-flaw';
    return `<li>
      <span class="ts">${e.timestamp || '??:??'}</span>
      <strong>${e.technique || '?'}</strong>
      <span class="tag ${tagClass}">${e.type || 'Event'}</span><br/>
      <span>${e.notes || ''}</span>
    </li>`;
  }).join('');
}

function renderHighlights(highlights) {
  const list = document.getElementById('highlightsList');
  list.innerHTML = (!highlights || highlights.length === 0)
    ? '<li class="empty">None identified.</li>'
    : highlights.map(h => `<li>✅ ${h}</li>`).join('');
}

function renderFlaws(flaws) {
  const list = document.getElementById('flawsList');
  list.innerHTML = (!flaws || flaws.length === 0)
    ? '<li class="empty">None identified.</li>'
    : flaws.map(f => `<li>❌ ${f}</li>`).join('');
}

function renderVerdict(verdict) {
  const el = document.getElementById('verdictText');
  el.textContent = (verdict && verdict.trim()) ? verdict : '— No verdict.';
}

function renderHistory(data) {
  const container = document.getElementById('historyContainer');
  const count = data.history_count || 0;
  if (count === 0) {
    container.innerHTML = '<p class="empty">First session — no history.</p>';
    return;
  }
  // Extract PROGRESSION TRAJECTORY from coaching_output
  const match = (data.coaching_output || '').match(
    /##\s*PROGRESSION\s*TRAJECTORY\s*(.*?)(?=##|$)/i
  );
  const trajectory = match ? match[1].trim() : 'Data available.';
  const trendClass = trajectory.toLowerCase().includes('improv') ? 'trend-up'
    : (trajectory.toLowerCase().includes('regress') || trajectory.toLowerCase().includes('declin')) ? 'trend-down'
    : 'trend-same';
  const emoji = trendClass === 'trend-up' ? '📈' : trendClass === 'trend-down' ? '📉' : '📊';

  container.innerHTML = `
    <p style="margin-bottom:12px;color:var(--text-dim);">
      Based on <strong>${count}</strong> prior session(s).
    </p>
    <p style="line-height:1.6;">
      <span class="${trendClass}">${emoji}</span> ${trajectory}
    </p>
  `;
}
