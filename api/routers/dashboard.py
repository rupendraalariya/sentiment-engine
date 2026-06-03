"""Dashboard router — serves the live monitoring UI at ``/dashboard``."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    """Serve the real-time sentiment analysis dashboard."""
    return HTMLResponse(content=_HTML)


_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Sentiment Analysis Engine — Dashboard</title>
<style>
  :root {
    --bg:       #0f172a;
    --card:     #1e293b;
    --border:   #334155;
    --text:     #f1f5f9;
    --muted:    #94a3b8;
    --pos:      #22c55e;
    --neg:      #ef4444;
    --neu:      #f59e0b;
    --accent:   #3b82f6;
    --radius:   12px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--bg); color: var(--text);
    min-height: 100vh; padding: 24px;
  }

  /* ── Header ── */
  header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 28px; flex-wrap: wrap; gap: 12px;
  }
  header h1 { font-size: 1.6rem; font-weight: 700; }
  header h1 span { color: var(--accent); }
  .live-badge {
    display: flex; align-items: center; gap: 6px;
    background: #166534; color: #bbf7d0;
    padding: 5px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 600;
  }
  .live-badge::before {
    content: ''; width: 8px; height: 8px; border-radius: 50%;
    background: #4ade80; animation: pulse 1.5s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

  /* ── Stats row ── */
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr)); gap: 16px; margin-bottom: 28px; }
  .stat-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 18px 20px;
  }
  .stat-card .label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px; }
  .stat-card .value { font-size: 1.9rem; font-weight: 700; }
  .stat-card .sub   { font-size: 0.72rem; color: var(--muted); margin-top: 4px; }
  .c-pos { color: var(--pos); }
  .c-neg { color: var(--neg); }
  .c-neu { color: var(--neu); }
  .c-acc { color: var(--accent); }

  /* ── Main grid ── */
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 28px; }
  @media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }

  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 20px;
  }
  .card h2 { font-size: 0.95rem; font-weight: 600; color: var(--muted); margin-bottom: 16px; text-transform: uppercase; letter-spacing: .05em; }

  /* ── Predict panel ── */
  textarea {
    width: 100%; background: #0f172a; color: var(--text);
    border: 1px solid var(--border); border-radius: 8px;
    padding: 12px; font-size: 0.9rem; resize: vertical;
    font-family: inherit; outline: none; transition: border .2s;
  }
  textarea:focus { border-color: var(--accent); }
  .btn-row { display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
  button {
    padding: 9px 20px; border-radius: 8px; border: none; cursor: pointer;
    font-size: 0.88rem; font-weight: 600; transition: opacity .2s;
  }
  button:hover { opacity: .85; }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-ghost   { background: var(--border); color: var(--text); }

  /* ── Result badge ── */
  #result-box {
    margin-top: 16px; padding: 16px; border-radius: 10px;
    display: none; animation: fadeIn .3s;
  }
  @keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:none} }
  #result-box.pos { background: #14532d; border: 1px solid var(--pos); }
  #result-box.neg { background: #7f1d1d; border: 1px solid var(--neg); }
  #result-box.neu { background: #78350f; border: 1px solid var(--neu); }
  .result-label  { font-size: 1.5rem; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; }
  .result-conf   { font-size: 0.85rem; color: var(--muted); margin-bottom: 12px; }
  .bar-row       { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; font-size: 0.8rem; }
  .bar-label     { width: 60px; color: var(--muted); }
  .bar-track     { flex: 1; background: var(--border); border-radius: 999px; height: 8px; overflow: hidden; }
  .bar-fill      { height: 100%; border-radius: 999px; transition: width .4s; }
  .bar-pct       { width: 42px; text-align: right; color: var(--muted); font-size: 0.75rem; }
  .result-ms     { margin-top: 10px; font-size: 0.75rem; color: var(--muted); }

  /* ── Examples ── */
  .examples { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
  .chip {
    padding: 5px 12px; background: var(--border); border-radius: 999px;
    font-size: 0.78rem; cursor: pointer; transition: background .2s;
    border: 1px solid transparent;
  }
  .chip:hover { background: var(--accent); color: #fff; }

  /* ── History table ── */
  .history-wrap { max-height: 260px; overflow-y: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  th { color: var(--muted); font-weight: 600; text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--border); }
  td { padding: 8px 10px; border-bottom: 1px solid #1e293b; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  .pill {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
  }
  .pill-pos { background: #14532d; color: var(--pos); }
  .pill-neg { background: #7f1d1d; color: var(--neg); }
  .pill-neu { background: #78350f; color: var(--neu); }

  /* ── Donut chart ── */
  .donut-wrap { display: flex; align-items: center; justify-content: center; gap: 28px; flex-wrap: wrap; }
  svg.donut { width: 130px; height: 130px; }
  .legend { display: flex; flex-direction: column; gap: 10px; }
  .leg-row { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; }
  .leg-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }

  /* ── Latency sparkline ── */
  #sparkline-wrap { height: 80px; position: relative; }
  canvas#sparkline { width: 100%; height: 100%; display: block; }

  /* ── Footer ── */
  footer { text-align: center; color: var(--muted); font-size: 0.75rem; margin-top: 24px; }
  footer a { color: var(--accent); text-decoration: none; }
</style>
</head>
<body>

<header>
  <h1>Sentiment <span>Engine</span> Dashboard</h1>
  <div class="live-badge">LIVE</div>
</header>

<!-- Stats row -->
<div class="stats">
  <div class="stat-card">
    <div class="label">Total Predictions</div>
    <div class="value c-acc" id="s-total">—</div>
    <div class="sub">since startup</div>
  </div>
  <div class="stat-card">
    <div class="label">Avg Latency</div>
    <div class="value c-acc" id="s-latency">—</div>
    <div class="sub">milliseconds</div>
  </div>
  <div class="stat-card">
    <div class="label">Throughput</div>
    <div class="value c-acc" id="s-pps">—</div>
    <div class="sub">predictions / sec</div>
  </div>
  <div class="stat-card">
    <div class="label">Uptime</div>
    <div class="value c-acc" id="s-uptime">—</div>
    <div class="sub">seconds</div>
  </div>
  <div class="stat-card">
    <div class="label">Model</div>
    <div class="value" id="s-model" style="font-size:0.95rem;word-break:break-all">—</div>
    <div class="sub" id="s-device">—</div>
  </div>
</div>

<!-- Main grid -->
<div class="grid">

  <!-- Predict panel -->
  <div class="card">
    <h2>Try It — Live Prediction</h2>
    <textarea id="inp" rows="4" placeholder="Type any text and click Analyze…"></textarea>
    <div class="btn-row">
      <button class="btn-primary" onclick="predict()">⚡ Analyze</button>
      <button class="btn-ghost"   onclick="clearResult()">Clear</button>
    </div>

    <div class="examples">
      <span class="chip" onclick="setEx(this)">I love this product!</span>
      <span class="chip" onclick="setEx(this)">Terrible quality, waste of money.</span>
      <span class="chip" onclick="setEx(this)">The item arrived on Monday.</span>
      <span class="chip" onclick="setEx(this)">Best customer service ever 😍</span>
      <span class="chip" onclick="setEx(this)">Broken on arrival, no response.</span>
    </div>

    <div id="result-box">
      <div class="result-label" id="r-label"></div>
      <div class="result-conf"  id="r-conf"></div>
      <div class="bar-row">
        <span class="bar-label">Positive</span>
        <div class="bar-track"><div class="bar-fill" id="b-pos" style="background:var(--pos)"></div></div>
        <span class="bar-pct" id="p-pos"></span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Neutral</span>
        <div class="bar-track"><div class="bar-fill" id="b-neu" style="background:var(--neu)"></div></div>
        <span class="bar-pct" id="p-neu"></span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Negative</span>
        <div class="bar-track"><div class="bar-fill" id="b-neg" style="background:var(--neg)"></div></div>
        <span class="bar-pct" id="p-neg"></span>
      </div>
      <div class="result-ms" id="r-ms"></div>
    </div>
  </div>

  <!-- Donut: session distribution -->
  <div class="card">
    <h2>Session Distribution</h2>
    <div class="donut-wrap">
      <svg class="donut" viewBox="0 0 42 42" id="donut-svg">
        <circle cx="21" cy="21" r="15.915" fill="none" stroke="#1e293b" stroke-width="6"/>
        <circle id="d-pos" cx="21" cy="21" r="15.915" fill="none"
                stroke="#22c55e" stroke-width="6"
                stroke-dasharray="0 100" stroke-linecap="round"
                transform="rotate(-90 21 21)"/>
        <circle id="d-neu" cx="21" cy="21" r="15.915" fill="none"
                stroke="#f59e0b" stroke-width="6"
                stroke-dasharray="0 100" stroke-linecap="round"
                transform="rotate(-90 21 21)"/>
        <circle id="d-neg" cx="21" cy="21" r="15.915" fill="none"
                stroke="#ef4444" stroke-width="6"
                stroke-dasharray="0 100" stroke-linecap="round"
                transform="rotate(-90 21 21)"/>
        <text x="21" y="24" text-anchor="middle" fill="#f1f5f9"
              font-size="5" font-weight="bold" id="donut-center">—</text>
      </svg>
      <div class="legend">
        <div class="leg-row"><div class="leg-dot" style="background:var(--pos)"></div><span id="leg-pos">Positive — 0</span></div>
        <div class="leg-row"><div class="leg-dot" style="background:var(--neu)"></div><span id="leg-neu">Neutral  — 0</span></div>
        <div class="leg-row"><div class="leg-dot" style="background:var(--neg)"></div><span id="leg-neg">Negative — 0</span></div>
      </div>
    </div>
  </div>

</div>

<!-- Bottom grid -->
<div class="grid">

  <!-- History -->
  <div class="card">
    <h2>Recent Predictions</h2>
    <div class="history-wrap">
      <table>
        <thead><tr><th>Text</th><th>Label</th><th>Conf</th><th>ms</th></tr></thead>
        <tbody id="history-body"></tbody>
      </table>
    </div>
  </div>

  <!-- Latency sparkline -->
  <div class="card">
    <h2>Latency History (last 30)</h2>
    <div id="sparkline-wrap">
      <canvas id="sparkline"></canvas>
    </div>
  </div>

</div>

<footer>
  Sentiment Analysis Engine &nbsp;·&nbsp;
  <a href="/docs" target="_blank">API Docs</a> &nbsp;·&nbsp;
  <a href="/health" target="_blank">Health</a>
</footer>

<script>
const API = '';   // same origin
let sessionCounts = {positive:0, neutral:0, negative:0};
let latencies = [];

/* ── Predict ── */
async function predict() {
  const text = document.getElementById('inp').value.trim();
  if (!text) return;
  const btn = document.querySelector('.btn-primary');
  btn.textContent = '…'; btn.disabled = true;
  try {
    const res = await fetch(API + '/predict', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({text})
    });
    if (!res.ok) { alert('API error: ' + res.status); return; }
    const d = await res.json();
    showResult(d, text);
    addHistory(text, d);
    sessionCounts[d.label]++;
    latencies.push(d.processing_time_ms);
    if (latencies.length > 30) latencies.shift();
    updateDonut();
    drawSparkline();
  } catch(e) { alert('Request failed: ' + e.message); }
  finally { btn.textContent = '⚡ Analyze'; btn.disabled = false; }
}

function showResult(d, text) {
  const box = document.getElementById('result-box');
  box.style.display = 'block';
  box.className = d.label === 'positive' ? 'pos' : d.label === 'negative' ? 'neg' : 'neu';
  document.getElementById('r-label').textContent = d.label;
  document.getElementById('r-conf').textContent =
    'Confidence: ' + (d.confidence * 100).toFixed(1) + '%';
  const s = d.scores;
  setBar('pos', s.positive  || 0);
  setBar('neu', s.neutral   || 0);
  setBar('neg', s.negative  || 0);
  document.getElementById('r-ms').textContent =
    'Response time: ' + d.processing_time_ms.toFixed(2) + ' ms';
}

function setBar(id, val) {
  const pct = (val * 100).toFixed(1);
  document.getElementById('b-' + id).style.width = pct + '%';
  document.getElementById('p-' + id).textContent = pct + '%';
}

function clearResult() {
  document.getElementById('inp').value = '';
  document.getElementById('result-box').style.display = 'none';
}

function setEx(el) {
  document.getElementById('inp').value = el.textContent;
  predict();
}

/* ── History ── */
function addHistory(text, d) {
  const tbody = document.getElementById('history-body');
  const cls = d.label === 'positive' ? 'pos' : d.label === 'negative' ? 'neg' : 'neu';
  const row = document.createElement('tr');
  row.innerHTML = `
    <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
        title="${text.replace(/"/g,'&quot;')}">${text.substring(0,40)}${text.length>40?'…':''}</td>
    <td><span class="pill pill-${cls}">${d.label}</span></td>
    <td>${(d.confidence*100).toFixed(0)}%</td>
    <td>${d.processing_time_ms.toFixed(1)}</td>`;
  tbody.insertBefore(row, tbody.firstChild);
  if (tbody.children.length > 50) tbody.removeChild(tbody.lastChild);
}

/* ── Donut ── */
function updateDonut() {
  const total = Object.values(sessionCounts).reduce((a,b)=>a+b,0);
  if (total === 0) return;
  const pos = sessionCounts.positive / total * 100;
  const neu = sessionCounts.neutral  / total * 100;
  const neg = sessionCounts.negative / total * 100;
  setDonutArc('d-pos', pos,       0);
  setDonutArc('d-neu', neu,       pos);
  setDonutArc('d-neg', neg,       pos + neu);
  document.getElementById('donut-center').textContent = total;
  document.getElementById('leg-pos').textContent = `Positive — ${sessionCounts.positive}`;
  document.getElementById('leg-neu').textContent = `Neutral  — ${sessionCounts.neutral}`;
  document.getElementById('leg-neg').textContent = `Negative — ${sessionCounts.negative}`;
}

function setDonutArc(id, pct, offset) {
  const el = document.getElementById(id);
  el.setAttribute('stroke-dasharray', pct + ' ' + (100 - pct));
  el.setAttribute('stroke-dashoffset', -offset);
  el.setAttribute('transform', 'rotate(-90 21 21)');
}

/* ── Sparkline ── */
function drawSparkline() {
  const canvas = document.getElementById('sparkline');
  const wrap   = document.getElementById('sparkline-wrap');
  canvas.width  = wrap.clientWidth;
  canvas.height = wrap.clientHeight;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (latencies.length < 2) return;
  const W = canvas.width, H = canvas.height;
  const max = Math.max(...latencies, 1);
  const pts = latencies.map((v,i) => [
    (i / (latencies.length - 1)) * W,
    H - (v / max) * (H - 16) - 4
  ]);
  // Fill
  const grad = ctx.createLinearGradient(0, 0, 0, H);
  grad.addColorStop(0, 'rgba(59,130,246,0.35)');
  grad.addColorStop(1, 'rgba(59,130,246,0.02)');
  ctx.beginPath();
  ctx.moveTo(pts[0][0], H);
  pts.forEach(p => ctx.lineTo(p[0], p[1]));
  ctx.lineTo(pts[pts.length-1][0], H);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();
  // Line
  ctx.beginPath();
  pts.forEach((p,i) => i === 0 ? ctx.moveTo(p[0],p[1]) : ctx.lineTo(p[0],p[1]));
  ctx.strokeStyle = '#3b82f6';
  ctx.lineWidth = 2;
  ctx.stroke();
  // Last point dot
  const last = pts[pts.length - 1];
  ctx.beginPath();
  ctx.arc(last[0], last[1], 4, 0, Math.PI * 2);
  ctx.fillStyle = '#3b82f6';
  ctx.fill();
}

/* ── Live metrics polling ── */
async function pollMetrics() {
  try {
    const [mRes, hRes] = await Promise.all([
      fetch(API + '/metrics'),
      fetch(API + '/health')
    ]);
    const m = await mRes.json();
    const h = await hRes.json();
    document.getElementById('s-total').textContent   = m.total_predictions.toLocaleString();
    document.getElementById('s-latency').textContent = m.average_latency_ms.toFixed(2) + ' ms';
    document.getElementById('s-pps').textContent     = m.predictions_per_second.toFixed(3);
    document.getElementById('s-uptime').textContent  = Math.round(m.uptime_seconds) + 's';
    document.getElementById('s-model').textContent   = h.model;
    document.getElementById('s-device').textContent  = h.device + ' · ' + h.status;
  } catch(e) { /* server temporarily unavailable */ }
}

/* ── Enter key support ── */
document.getElementById('inp').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.ctrlKey) predict();
});

/* ── Init ── */
pollMetrics();
setInterval(pollMetrics, 3000);
</script>
</body>
</html>
"""
