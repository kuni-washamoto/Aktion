"""
Aktion Dashboard — read-only local web UI
Run: python3 app.py
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import sqlite_vec
from flask import Flask, jsonify, render_template_string

DB_PATH = Path.home() / ".aktion" / "aktion.db"

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.row_factory = sqlite3.Row
    return conn


def jloads(s):
    if not s:
        return s
    try:
        return json.loads(s)
    except Exception:
        return s


def fmt_ts(ts):
    if not ts:
        return "—"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts


TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aktion Dashboard</title>
<style>
  :root {
    --bg: #0d0f14;
    --surface: #161a22;
    --surface2: #1e2330;
    --border: #2a3040;
    --accent: #4f8ef7;
    --accent2: #7c3aed;
    --green: #22c55e;
    --yellow: #eab308;
    --red: #ef4444;
    --orange: #f97316;
    --muted: #8a97a8;
    --text: #f0f4f8;
    --text2: #b8c6d8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'SF Mono', 'Fira Code', monospace; font-size: 14px; line-height: 1.6; }

  header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 12px 24px; display: flex; align-items: center; gap: 16px; position: sticky; top: 0; z-index: 100; }
  header h1 { font-size: 16px; font-weight: 700; letter-spacing: 0.05em; color: var(--accent); }
  header .posture-badge { padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; }
  header .ts { margin-left: auto; color: var(--muted); font-size: 11px; }

  nav { background: var(--surface); border-bottom: 1px solid var(--border); padding: 0 24px; display: flex; gap: 0; overflow-x: auto; }
  nav a { padding: 10px 16px; text-decoration: none; color: var(--text2); font-size: 12px; border-bottom: 2px solid transparent; white-space: nowrap; transition: color 0.15s; }
  nav a:hover, nav a.active { color: var(--accent); border-bottom-color: var(--accent); }

  main { padding: 24px; max-width: 1400px; margin: 0 auto; }

  .section { display: none; }
  .section.active { display: block; }

  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
  .grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }

  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
  .card h3 { font-size: 11px; font-weight: 600; letter-spacing: 0.1em; color: var(--muted); text-transform: uppercase; margin-bottom: 12px; }

  .stat-big { font-size: 32px; font-weight: 700; color: var(--text); }
  .stat-label { font-size: 11px; color: var(--muted); margin-top: 2px; }

  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; padding: 8px 10px; font-size: 12px; font-weight: 600; color: var(--text2); text-transform: uppercase; border-bottom: 1px solid var(--border); white-space: nowrap; }
  td { padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top; font-size: 13px; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: var(--surface2); }

  .badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; }
  .badge-green { background: rgba(34,197,94,0.15); color: var(--green); }
  .badge-yellow { background: rgba(234,179,8,0.15); color: var(--yellow); }
  .badge-red { background: rgba(239,68,68,0.15); color: var(--red); }
  .badge-blue { background: rgba(79,142,247,0.15); color: var(--accent); }
  .badge-purple { background: rgba(124,58,237,0.15); color: #a78bfa; }
  .badge-orange { background: rgba(249,115,22,0.15); color: var(--orange); }
  .badge-muted { background: rgba(107,114,128,0.15); color: var(--muted); }

  .progress-bar { background: var(--border); border-radius: 4px; height: 6px; overflow: hidden; }
  .progress-fill { height: 100%; border-radius: 4px; background: var(--accent); }

  .text-muted { color: var(--muted); }
  .text-sm { font-size: 11px; }
  .truncate { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .truncate-sm { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .pill-row { display: flex; flex-wrap: wrap; gap: 4px; }

  .log-entry { padding: 8px 0; border-bottom: 1px solid var(--border); display: flex; gap: 12px; align-items: flex-start; }
  .log-entry:last-child { border-bottom: none; }
  .log-ts { color: var(--muted); font-size: 11px; white-space: nowrap; min-width: 110px; }
  .log-agent { font-size: 11px; }
  .log-body { font-size: 12px; color: var(--text2); }

  .entity-node { background: var(--surface2); border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; }
  .entity-node .etype { font-size: 10px; color: var(--muted); margin-bottom: 4px; }
  .entity-node .elabel { font-weight: 600; font-size: 13px; }

  .ir-card { background: var(--surface2); border: 1px solid var(--border); border-radius: 6px; padding: 12px; margin-bottom: 8px; }
  .ir-card .ir-meta { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; flex-wrap: wrap; }
  .ir-card .ir-summary { font-size: 12px; color: var(--text2); }
  .ir-card .ir-judgments { margin-top: 8px; }
  .ir-card .ir-judgment { font-size: 11px; padding: 4px 0; border-top: 1px solid var(--border); color: var(--text); }

  .section-title { font-size: 18px; font-weight: 700; margin-bottom: 20px; color: var(--text); }
  .subsection { margin-top: 24px; }
  .subsection-title { font-size: 13px; font-weight: 600; color: var(--text2); margin-bottom: 12px; letter-spacing: 0.05em; }

  .refresh-btn { margin-left: auto; background: none; border: 1px solid var(--border); color: var(--text2); padding: 5px 12px; border-radius: 4px; cursor: pointer; font-family: inherit; font-size: 11px; }
  .refresh-btn:hover { border-color: var(--accent); color: var(--accent); }

  .empty { color: var(--muted); font-size: 12px; padding: 16px 0; }

  /* ── Hamburger nav ── */
  .hamburger { display: none; background: none; border: 1px solid var(--border); color: var(--text2); padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 16px; line-height: 1; }
  .hamburger:hover { border-color: var(--accent); color: var(--accent); }
  .nav-drawer { display: flex; }

  /* ── Tablet ── */
  @media (max-width: 900px) {
    .grid3, .grid4 { grid-template-columns: 1fr 1fr; }
    .grid2 { grid-template-columns: 1fr; }
    main { padding: 16px; }
  }

  /* ── Mobile ── */
  @media (max-width: 600px) {
    header { padding: 10px 14px; flex-wrap: wrap; gap: 8px; }
    header h1 { font-size: 14px; }
    header .ts { margin-left: 0; width: 100%; order: 4; font-size: 10px; }
    header .refresh-btn { order: 3; }
    header .hamburger { display: inline-block; order: 2; margin-left: auto; }

    /* Collapsible nav drawer */
    nav { position: relative; }
    .nav-drawer { flex-direction: column; display: none; background: var(--surface); border-bottom: 1px solid var(--border); }
    .nav-drawer.open { display: flex; }
    .nav-drawer a { border-bottom: none; border-left: 3px solid transparent; padding: 11px 20px; font-size: 13px; }
    .nav-drawer a.active, .nav-drawer a:hover { border-left-color: var(--accent); border-bottom: none; }

    main { padding: 12px; }

    .grid2, .grid3, .grid4 { grid-template-columns: 1fr; }

    .section-title { font-size: 15px; margin-bottom: 14px; }

    .card { padding: 12px; }

    /* Tables: horizontal scroll on mobile */
    .card table, .table-wrap { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }

    .stat-big { font-size: 26px; }

    th, td { white-space: nowrap; }
    th { font-size: 10px; padding: 6px 8px; }
    td { font-size: 11px; padding: 6px 8px; }

    .truncate { max-width: 160px; }
    .truncate-sm { max-width: 100px; }

    .ir-card { padding: 10px; }

    .log-entry { flex-wrap: wrap; gap: 6px; }
    .log-ts { min-width: unset; }

    /* Stack IR meta items */
    .ir-meta { gap: 5px; }

    .pill-row { gap: 3px; }
    .badge { font-size: 9px; padding: 2px 5px; }

    /* Actors table: hide low-priority columns */
    #actors-content table th:nth-child(2),  /* Channel */
    #actors-content table td:nth-child(2),
    #actors-content table th:nth-child(6),  /* Recv */
    #actors-content table td:nth-child(6),
    #actors-content table th:nth-child(8),  /* Fail */
    #actors-content table td:nth-child(8),
    #actors-content table th:nth-child(10), /* Flags */
    #actors-content table td:nth-child(10),
    #actors-content table th:nth-child(11), /* Rec */
    #actors-content table td:nth-child(11) { display: none; }

    /* Directives table: hide Payload and Deadline columns */
    #directives-content table th:nth-child(4),
    #directives-content table td:nth-child(4),
    #directives-content table th:nth-child(5),
    #directives-content table td:nth-child(5) { display: none; }
  }
</style>
</head>
<body>

<header>
  <h1>⚡ AKTION</h1>
  <span id="posture-badge" class="posture-badge"></span>
  <button class="hamburger" id="nav-toggle" aria-label="Menu">☰</button>
  <button class="refresh-btn" onclick="loadAll()">↻ Refresh</button>
  <span class="ts" id="header-ts"></span>
</header>

<nav>
  <div class="nav-drawer" id="nav-drawer">
    <a href="#" class="active" data-section="overview">Overview</a>
    <a href="#" data-section="goals">Goals</a>
    <a href="#" data-section="directives">Directives</a>
    <a href="#" data-section="state">State</a>
    <a href="#" data-section="intel">Intel</a>
    <a href="#" data-section="actors">Actors</a>
    <a href="#" data-section="influence">Influence</a>
    <a href="#" data-section="governance">Governance</a>
    <a href="#" data-section="log">Log</a>
  </div>
</nav>

<main>

<div id="overview" class="section active">
  <div class="section-title">Overview</div>
  <div class="grid4" id="overview-stats"></div>
  <div class="grid2" style="margin-top:16px">
    <div class="card">
      <h3>Active Goals</h3>
      <div id="overview-goals"></div>
    </div>
    <div class="card">
      <h3>Directive Pipeline</h3>
      <div id="overview-directives"></div>
    </div>
  </div>
  <div class="grid2" style="margin-top:16px">
    <div class="card">
      <h3>Current Phase</h3>
      <div id="overview-phase"></div>
    </div>
    <div class="card">
      <h3>Recent Log</h3>
      <div id="overview-log"></div>
    </div>
  </div>
</div>

<div id="goals" class="section">
  <div class="section-title">Goals</div>
  <div id="goals-content"></div>
</div>

<div id="directives" class="section">
  <div class="section-title">Directives</div>
  <div id="directives-content"></div>
</div>

<div id="state" class="section">
  <div class="section-title">State (S)</div>
  <div class="subsection">
    <div class="subsection-title">Entities</div>
    <div id="state-entities"></div>
  </div>
  <div class="subsection">
    <div class="subsection-title">Relations</div>
    <div id="state-relations"></div>
  </div>
  <div class="subsection">
    <div class="subsection-title">Assertions</div>
    <div id="state-assertions"></div>
  </div>
</div>

<div id="intel" class="section">
  <div class="section-title">Intelligence</div>
  <div class="grid2">
    <div>
      <div class="subsection-title">Collection Requirements</div>
      <div id="intel-crs"></div>
    </div>
    <div>
      <div class="subsection-title">Sources</div>
      <div id="intel-sources"></div>
    </div>
  </div>
  <div class="subsection">
    <div class="subsection-title">Intelligence Reports</div>
    <div id="intel-irs"></div>
  </div>
</div>

<div id="actors" class="section">
  <div class="section-title">Actors</div>
  <div id="actors-content"></div>
</div>

<div id="influence" class="section">
  <div class="section-title">Influence Operations</div>
  <div class="subsection">
    <div class="subsection-title">IO Campaigns</div>
    <div id="influence-campaigns"></div>
  </div>
  <div class="subsection">
    <div class="subsection-title">Social Media Profiles</div>
    <div id="influence-profiles"></div>
  </div>
</div>

<div id="governance" class="section">
  <div class="section-title">Governance</div>
  <div class="grid2">
    <div>
      <div class="subsection-title">Constitutional Proposals</div>
      <div id="gov-proposals"></div>
    </div>
    <div>
      <div class="subsection-title">Escalation Postures</div>
      <div id="gov-postures"></div>
    </div>
  </div>
  <div class="subsection">
    <div class="subsection-title">Posture Log</div>
    <div id="gov-posture-log"></div>
  </div>
  <div class="subsection">
    <div class="subsection-title">Referral Tokens</div>
    <div id="gov-tokens"></div>
  </div>
</div>

<div id="log" class="section">
  <div class="section-title">Canonical Log</div>
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:14px;flex-wrap:wrap">
    <select id="log-filter-agent" style="background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:5px 8px;border-radius:4px;font-family:inherit;font-size:12px">
      <option value="">All agents</option>
    </select>
    <select id="log-filter-type" style="background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:5px 8px;border-radius:4px;font-family:inherit;font-size:12px">
      <option value="">All event types</option>
    </select>
    <button onclick="applyLogFilter()" style="background:var(--surface2);border:1px solid var(--border);color:var(--text2);padding:5px 12px;border-radius:4px;font-family:inherit;font-size:12px;cursor:pointer">Filter</button>
    <button onclick="clearLogFilter()" style="background:none;border:none;color:var(--muted);font-family:inherit;font-size:12px;cursor:pointer;text-decoration:underline">Clear</button>
    <span id="log-count" class="text-muted text-sm"></span>
  </div>
  <div id="log-content"></div>
</div>

</main>

<script>
const SECTIONS = ['overview','goals','directives','state','intel','actors','influence','governance','log'];
let data = {};

// Nav routing
const drawer = document.getElementById('nav-drawer');
document.getElementById('nav-toggle').addEventListener('click', () => {
  drawer.classList.toggle('open');
});

document.querySelectorAll('.nav-drawer a').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    document.querySelectorAll('.nav-drawer a').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    SECTIONS.forEach(s => document.getElementById(s).classList.remove('active'));
    const sec = a.dataset.section;
    document.getElementById(sec).classList.add('active');
    // Close drawer on mobile after selection
    drawer.classList.remove('open');
  });
});

// Helpers
function badge(text, cls) {
  return `<span class="badge badge-${cls}">${text}</span>`;
}
function statusBadge(s) {
  if (!s) return badge('—', 'muted');
  const m = {
    active: 'green', completed: 'green', satisfied: 'green', approved: 'green',
    pending: 'yellow', pending_confirmation: 'yellow', in_progress: 'blue',
    issued: 'blue', acknowledged: 'blue',
    failed: 'red', flagged: 'red', suspended: 'red', expired: 'red',
    inactive: 'muted', cancelled: 'muted', draft: 'muted'
  };
  return badge(s, m[s] || 'muted');
}
function priorityBadge(p) {
  const m = {critical:'red', high:'orange', medium:'yellow', low:'muted'};
  return badge(p, m[p] || 'muted');
}
function admiraltyBadge(r, c) {
  const rb = badge(r||'?', 'blue');
  const cb = badge(c||'?', 'purple');
  return rb + ' ' + cb;
}
function fmt(ts) {
  if (!ts) return '<span class="text-muted">—</span>';
  try {
    return new Date(ts).toLocaleString('en-GB', {dateStyle:'short', timeStyle:'short'});
  } catch(e) { return ts; }
}
function trunc(s, n=60) {
  if (!s) return '<span class="text-muted">—</span>';
  s = String(s);
  return s.length > n ? `<span title="${s.replace(/"/g,'&quot;')}">${s.slice(0,n)}…</span>` : s;
}
function pills(arr) {
  if (!arr || !arr.length) return '<span class="text-muted">—</span>';
  return '<div class="pill-row">' + arr.map(x => badge(x,'blue')).join('') + '</div>';
}
function jp(s) {
  if (!s) return null;
  try { return JSON.parse(s); } catch(e) { return s; }
}

function toggleDirExpand(rowId) {
  const row = document.getElementById(rowId);
  if (!row) return;
  row.style.display = row.style.display === 'none' ? '' : 'none';
}

async function loadAll() {
  const res = await fetch('/api/all');
  data = await res.json();
  document.getElementById('header-ts').textContent = 'Updated ' + new Date().toLocaleTimeString();
  renderOverview();
  renderGoals();
  renderDirectives();
  renderState();
  renderIntel();
  renderActors();
  renderInfluence();
  renderGovernance();
  renderLog();
}

function renderOverview() {
  const d = data;
  const activeGoals = (d.goals||[]).filter(g => g.status === 'active').length;
  const activeActors = (d.actors||[]).filter(a => a.status === 'active').length;
  const pendingDirectives = (d.directives||[]).filter(x => ['issued','acknowledged'].includes(x.status)).length;
  const pendingIRs = (d.irs||[]).length;

  const ep = d.escalation_policy;
  const posture = ep ? ep.current_posture_level : '?';
  const postures = ep ? jp(ep.postures) : [];
  const postureInfo = Array.isArray(postures) ? postures.find(p => p.level === posture) : null;
  const postureLabel = postureInfo ? postureInfo.label : 'Unknown';
  const postureCls = posture <= 1 ? 'badge-green' : posture <= 2 ? 'badge-yellow' : posture <= 3 ? 'badge-orange' : 'badge-red';

  const badge_el = document.getElementById('posture-badge');
  badge_el.textContent = `P${posture} — ${postureLabel}`;
  badge_el.className = 'posture-badge badge ' + postureCls;

  document.getElementById('overview-stats').innerHTML = `
    <div class="card"><div class="stat-big">${activeGoals}</div><div class="stat-label">Active Goals</div></div>
    <div class="card"><div class="stat-big">${activeActors}</div><div class="stat-label">Active Actors</div></div>
    <div class="card"><div class="stat-big">${pendingDirectives}</div><div class="stat-label">Pending Directives</div></div>
    <div class="card"><div class="stat-big">${pendingIRs}</div><div class="stat-label">Intel Reports</div></div>
  `;

  const activeGoalList = (d.goals||[]).filter(g => g.status === 'active');
  document.getElementById('overview-goals').innerHTML = activeGoalList.length === 0
    ? '<div class="empty">No active goals</div>'
    : activeGoalList.map(g => `
      <div style="margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid var(--border)">
        <div style="display:flex;gap:6px;align-items:center;margin-bottom:4px">
          ${priorityBadge(g.priority)} ${statusBadge(g.status)}
        </div>
        <div style="font-size:12px">${trunc(g.description, 80)}</div>
        <div class="text-muted text-sm" style="margin-top:2px">Deadline: ${fmt(g.deadline)}</div>
      </div>
    `).join('');

  const byStatus = {};
  (d.directives||[]).forEach(x => { byStatus[x.status] = (byStatus[x.status]||0)+1; });
  document.getElementById('overview-directives').innerHTML = Object.entries(byStatus).length === 0
    ? '<div class="empty">No directives</div>'
    : Object.entries(byStatus).map(([s,n]) => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--border)">
        ${statusBadge(s)} <span style="font-weight:600">${n}</span>
      </div>
    `).join('');

  const phase = (d.phases||[]).find(p => p.status === 'active');
  document.getElementById('overview-phase').innerHTML = phase
    ? `<div style="font-weight:600;margin-bottom:6px">${phase.name}</div>
       <div class="text-muted text-sm">${trunc(phase.description,120)}</div>
       <div style="margin-top:8px">${statusBadge(phase.status)}</div>`
    : '<div class="empty">No active phase</div>';

  const recentLog = (d.log||[]).slice(0,8);
  document.getElementById('overview-log').innerHTML = recentLog.length === 0
    ? '<div class="empty">No log entries</div>'
    : recentLog.map(e => `
      <div class="log-entry">
        <span class="log-ts">${fmt(e.timestamp)}</span>
        <span class="log-agent text-muted">${e.agent||'—'}</span>
        <span class="log-body">${trunc(e.event_type, 40)}</span>
      </div>
    `).join('');
}

function renderGoals() {
  const goals = data.goals || [];
  if (goals.length === 0) { document.getElementById('goals-content').innerHTML = '<div class="empty">No goals</div>'; return; }

  // Build tree
  const roots = goals.filter(g => !g.parent_goal_id);
  const children = {};
  goals.forEach(g => { if (g.parent_goal_id) { (children[g.parent_goal_id] = children[g.parent_goal_id]||[]).push(g); } });

  function renderGoal(g, depth=0) {
    const criteria = jp(g.success_criteria) || [];
    const criteriaHtml = Array.isArray(criteria) && criteria.length
      ? `<ul style="margin:6px 0 0 16px;color:var(--text2);font-size:11px">${criteria.map(c=>`<li>${c}</li>`).join('')}</ul>` : '';
    const childGoals = (children[g.id]||[]).map(c => renderGoal(c, depth+1)).join('');
    return `
      <div style="margin-left:${depth*20}px;margin-bottom:12px">
        <div class="card">
          <div style="display:flex;gap:6px;align-items:center;margin-bottom:8px;flex-wrap:wrap">
            <code style="font-size:10px;color:var(--muted)">${g.id.slice(0,8)}</code>
            ${priorityBadge(g.priority)} ${statusBadge(g.status)}
            <span class="text-muted text-sm" style="margin-left:auto">Deadline: ${fmt(g.deadline)}</span>
          </div>
          <div style="font-size:13px;font-weight:600;margin-bottom:6px">${g.description||'—'}</div>
          ${criteriaHtml}
        </div>
        ${childGoals}
      </div>
    `;
  }

  document.getElementById('goals-content').innerHTML = roots.map(g => renderGoal(g)).join('') +
    goals.filter(g => g.parent_goal_id && !goals.find(gg => gg.id === g.parent_goal_id))
      .map(g => renderGoal(g)).join('');
}

function renderDirectives() {
  const dirs = data.directives || [];
  if (dirs.length === 0) { document.getElementById('directives-content').innerHTML = '<div class="empty">No directives</div>'; return; }

  const actorMap = {};
  (data.actors||[]).forEach(a => { actorMap[a.id] = a.channel_username || a.channel_user_id || a.id.slice(0,8); });

  const groups = {issued:[], acknowledged:[], completed:[], failed:[], other:[]};
  dirs.forEach(d => {
    if (d.status === 'issued') groups.issued.push(d);
    else if (d.status === 'acknowledged') groups.acknowledged.push(d);
    else if (d.status === 'completed') groups.completed.push(d);
    else if (d.status === 'failed') groups.failed.push(d);
    else groups.other.push(d);
  });

  function dirTable(list) {
    if (!list.length) return '<div class="empty text-sm">None</div>';
    return `<table>
      <tr><th>ID</th><th>Type</th><th>Actor</th><th>Payload</th><th>Deadline</th><th>Status</th></tr>
      ${list.map((d, i) => {
        const payload = jp(d.payload);
        const payloadStr = typeof payload === 'object' ? JSON.stringify(payload).slice(0,60) : String(payload||'').slice(0,60);
        const payloadFull = typeof payload === 'object' ? JSON.stringify(payload, null, 2) : String(payload||'');
        const hasMore = payloadFull.length > 60;
        const rowId = `dir-expand-${d.id.slice(0,8)}-${i}`;
        return `<tr style="cursor:${hasMore?'pointer':'default'}" onclick="${hasMore?`toggleDirExpand('${rowId}')`:''}" title="${hasMore?'Click to expand payload':''}">
          <td><code class="text-muted" style="font-size:10px">${d.id.slice(0,8)}</code></td>
          <td>${badge(d.type||'task','purple')}</td>
          <td>${actorMap[d.target_actor_id] || d.target_actor_id?.slice(0,8) || '—'}</td>
          <td class="truncate">${payloadStr}${hasMore?` <span style="color:var(--accent);font-size:10px">▼</span>`:''}</td>
          <td>${fmt(d.deadline)}</td>
          <td>${statusBadge(d.status)}</td>
        </tr>
        ${hasMore ? `<tr id="${rowId}" style="display:none"><td colspan="6"><pre style="white-space:pre-wrap;word-break:break-all;font-size:11px;color:var(--text2);padding:8px;background:var(--surface2);border-radius:4px;margin:4px 0">${payloadFull}</pre></td></tr>` : ''}`;
      }).join('')}
    </table>`;
  }

  const html = Object.entries({
    'In Flight (Issued)': groups.issued,
    'Acknowledged': groups.acknowledged,
    'Completed': groups.completed,
    'Failed': groups.failed,
    'Other': groups.other,
  }).filter(([,list]) => list.length > 0).map(([label, list]) => `
    <div class="subsection">
      <div class="subsection-title">${label} (${list.length})</div>
      <div class="card">${dirTable(list)}</div>
    </div>
  `).join('');

  document.getElementById('directives-content').innerHTML = html || '<div class="empty">No directives</div>';
}

function renderState() {
  const entities = data.entities || [];
  const relations = data.relations || [];
  const assertions = data.assertions || [];

  // Entities by type
  const byType = {};
  entities.forEach(e => { (byType[e.type] = byType[e.type]||[]).push(e); });

  const entHtml = Object.entries(byType).length === 0
    ? '<div class="empty">No entities</div>'
    : Object.entries(byType).map(([type, list]) => `
      <div class="subsection-title" style="margin-top:12px">${type} (${list.length})</div>
      <div class="grid3">
        ${list.map(e => {
          const attrs = jp(e.attributes);
          const attrsStr = attrs && typeof attrs === 'object' ? Object.entries(attrs).slice(0,3).map(([k,v])=>`<div class="text-sm text-muted">${k}: ${String(v).slice(0,40)}</div>`).join('') : '';
          return `<div class="entity-node">
            <div class="etype">${e.type}</div>
            <div class="elabel">${e.label}</div>
            <code style="font-size:9px;color:var(--muted)">${e.id.slice(0,8)}</code>
            ${attrsStr}
          </div>`;
        }).join('')}
      </div>
    `).join('');

  document.getElementById('state-entities').innerHTML = entHtml;

  const entityLabel = {};
  entities.forEach(e => { entityLabel[e.id] = e.label; });

  document.getElementById('state-relations').innerHTML = relations.length === 0
    ? '<div class="empty">No relations</div>'
    : `<div class="card"><table>
      <tr><th>From</th><th>Type</th><th>To</th><th>Updated</th></tr>
      ${relations.map(r => `<tr>
        <td>${entityLabel[r.from_entity] || r.from_entity?.slice(0,8) || '—'}</td>
        <td>${badge(r.type,'blue')}</td>
        <td>${entityLabel[r.to_entity] || r.to_entity?.slice(0,8) || '—'}</td>
        <td>${fmt(r.updated_at)}</td>
      </tr>`).join('')}
    </table></div>`;

  document.getElementById('state-assertions').innerHTML = assertions.length === 0
    ? '<div class="empty">No assertions</div>'
    : `<div class="card"><table>
      <tr><th>Entity</th><th>Claim</th><th>Value</th><th>Timestamp</th></tr>
      ${assertions.map(a => `<tr>
        <td>${entityLabel[a.entity_id] || a.entity_id?.slice(0,8) || '—'}</td>
        <td class="truncate-sm">${a.claim||'—'}</td>
        <td class="truncate">${a.value||'—'}</td>
        <td>${fmt(a.timestamp)}</td>
      </tr>`).join('')}
    </table></div>`;
}

function renderIntel() {
  const crs = data.crs || [];
  const sources = data.sources || [];
  const irs = data.irs || [];

  document.getElementById('intel-crs').innerHTML = crs.length === 0
    ? '<div class="empty">No CRs</div>'
    : `<div class="card"><table>
      <tr><th>Question</th><th>Priority</th><th>Status</th><th>Required By</th></tr>
      ${crs.map(c => `<tr>
        <td class="truncate">${c.question||'—'}</td>
        <td>${priorityBadge(c.priority)}</td>
        <td>${statusBadge(c.status)}</td>
        <td>${fmt(c.required_by)}</td>
      </tr>`).join('')}
    </table></div>`;

  document.getElementById('intel-sources').innerHTML = sources.length === 0
    ? '<div class="empty">No sources</div>'
    : `<div class="card"><table>
      <tr><th>Label</th><th>Type</th><th>R</th><th>C</th><th>Reports</th></tr>
      ${sources.map(s => `<tr>
        <td>${s.label||'—'}</td>
        <td>${s.type||'—'}</td>
        <td>${badge(s.reliability||'?','blue')}</td>
        <td>${badge(s.credibility||'?','purple')}</td>
        <td>${s.report_count||0}</td>
      </tr>`).join('')}
    </table></div>`;

  document.getElementById('intel-irs').innerHTML = irs.length === 0
    ? '<div class="empty">No intelligence reports</div>'
    : irs.map(ir => {
        const kj = jp(ir.key_judgments);
        const kjHtml = Array.isArray(kj) && kj.length
          ? '<div class="ir-judgments">' + kj.map(j => `<div class="ir-judgment">• ${j}</div>`).join('') + '</div>' : '';
        return `<div class="ir-card">
          <div class="ir-meta">
            ${admiraltyBadge(ir.confidence?.split('/')[0], ir.confidence?.split('/')[1])}
            <span class="text-muted text-sm">${fmt(ir.produced_at)}</span>
            ${ir.triggers_state_proposal ? badge('triggers-state','orange') : ''}
          </div>
          <div class="ir-summary">${ir.summary||'—'}</div>
          ${kjHtml}
        </div>`;
      }).join('');
}

function renderActors() {
  const actors = data.actors || [];
  const ledger = data.ledger || [];
  const ledgerMap = {};
  ledger.forEach(l => { ledgerMap[l.actor_id] = l; });

  if (actors.length === 0) { document.getElementById('actors-content').innerHTML = '<div class="empty">No actors</div>'; return; }

  document.getElementById('actors-content').innerHTML = `<div class="card"><table>
    <tr><th>Username</th><th>Channel</th><th>Tier</th><th>Status</th><th>Capabilities</th><th>Recv</th><th>Done</th><th>Fail</th><th>Quality</th><th>Flags</th><th>Rec.</th></tr>
    ${actors.map(a => {
      const l = ledgerMap[a.id] || {};
      const caps = jp(a.capabilities_verified) || [];
      const quality = typeof l.quality_score === 'number' ? l.quality_score : null;
      const qBar = quality !== null
        ? `<div style="display:flex;align-items:center;gap:4px"><div class="progress-bar" style="width:50px"><div class="progress-fill" style="width:${Math.round(quality*100)}%;background:${quality>0.7?'var(--green)':quality>0.4?'var(--yellow)':'var(--red)'}"></div></div><span class="text-sm">${(quality*100).toFixed(0)}%</span></div>`
        : '—';
      return `<tr>
        <td>${a.channel_username || '—'}</td>
        <td>${a.channel||'—'}</td>
        <td>${badge(a.trust_tier||'standard', a.trust_tier==='elevated'?'purple':'muted')}</td>
        <td>${statusBadge(a.status)}</td>
        <td>${pills(Array.isArray(caps)?caps.slice(0,3):[])} ${caps.length>3?`<span class="text-muted text-sm">+${caps.length-3}</span>`:''}</td>
        <td>${l.directives_received||0}</td>
        <td>${l.directives_completed||0}</td>
        <td>${l.directives_failed||0}</td>
        <td>${qBar}</td>
        <td>${l.flag_count||0}</td>
        <td>${l.status_recommendation ? badge(l.status_recommendation,'yellow') : '—'}</td>
      </tr>`;
    }).join('')}
  </table></div>`;
}

function renderInfluence() {
  const campaigns = data.campaigns || [];
  const profiles = data.sm_profiles || [];

  document.getElementById('influence-campaigns').innerHTML = campaigns.length === 0
    ? '<div class="empty">No IO campaigns</div>'
    : campaigns.map(c => `
      <div class="card" style="margin-bottom:12px">
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap">
          <span style="font-weight:600">${c.name||'Unnamed'}</span>
          ${statusBadge(c.status)}
          <span class="text-muted text-sm" style="margin-left:auto">${fmt(c.start_at)} → ${fmt(c.end_at)}</span>
        </div>
        <div class="text-sm text-muted" style="margin-bottom:4px">Theme: ${c.narrative_theme||'—'}</div>
        <div class="text-sm text-muted">Audience: ${c.target_audience||'—'}</div>
        <div style="margin-top:8px">${pills(jp(c.platforms))}</div>
      </div>
    `).join('');

  document.getElementById('influence-profiles').innerHTML = profiles.length === 0
    ? '<div class="empty">No social media profiles</div>'
    : `<div class="card"><table>
      <tr><th>Actor</th><th>Platforms</th><th>Languages</th><th>Reach</th><th>Last Post</th></tr>
      ${profiles.map(p => {
        const actorMap = {};
        (data.actors||[]).forEach(a => { actorMap[a.id] = a.channel_username || a.channel_user_id; });
        return `<tr>
          <td>${actorMap[p.actor_id] || p.actor_id?.slice(0,8)}</td>
          <td>${pills(jp(p.platforms))}</td>
          <td>${pills(jp(p.languages))}</td>
          <td>${typeof p.reach_score === 'number' ? p.reach_score.toFixed(2) : '—'}</td>
          <td>${fmt(p.last_post_at)}</td>
        </tr>`;
      }).join('')}
    </table></div>`;
}

function renderGovernance() {
  const proposals = data.proposals || [];
  const ep = data.escalation_policy;
  const pLog = data.posture_log || [];
  const tokens = data.tokens || [];

  document.getElementById('gov-proposals').innerHTML = proposals.length === 0
    ? '<div class="empty">No proposals</div>'
    : proposals.map(p => {
        const confs = jp(p.confirmations) || [];
        return `<div class="card" style="margin-bottom:10px">
          <div style="display:flex;gap:6px;align-items:center;margin-bottom:6px">
            <code class="text-muted" style="font-size:10px">${p.id.slice(0,8)}</code>
            ${badge(p.action,'purple')} ${statusBadge(p.status)}
          </div>
          <div class="text-sm" style="margin-bottom:4px">${trunc(p.payload, 80)}</div>
          <div class="text-muted text-sm">Confirmations: ${confs.length} | Expires: ${fmt(p.expires_at)}</div>
        </div>`;
      }).join('');

  if (ep) {
    const postures = jp(ep.postures) || [];
    const current = ep.current_posture_level;
    document.getElementById('gov-postures').innerHTML = `<div class="card">
      ${Array.isArray(postures) ? postures.map(p => `
        <div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border)">
          <span style="font-weight:${p.level===current?'700':'400'};color:${p.level===current?'var(--accent)':'var(--text)'}">P${p.level} — ${p.label}</span>
          ${p.level===current ? badge('CURRENT','green') : ''}
          <span class="text-muted text-sm" style="margin-left:auto">×${p.directive_tempo_multiplier||1}</span>
        </div>
      `).join('') : '<div class="empty">No posture data</div>'}
    </div>`;
  } else {
    document.getElementById('gov-postures').innerHTML = '<div class="empty">No escalation policy</div>';
  }

  document.getElementById('gov-posture-log').innerHTML = pLog.length === 0
    ? '<div class="empty">No posture transitions</div>'
    : `<div class="card"><table>
      <tr><th>From</th><th>To</th><th>Signal</th><th>Authority</th><th>Time</th></tr>
      ${pLog.map(p => `<tr>
        <td>P${p.from_level}</td>
        <td>P${p.to_level}</td>
        <td class="truncate-sm">${p.trigger_signal||'—'}</td>
        <td>${p.authority||'—'}</td>
        <td>${fmt(p.timestamp)}</td>
      </tr>`).join('')}
    </table></div>`;

  document.getElementById('gov-tokens').innerHTML = tokens.length === 0
    ? '<div class="empty">No referral tokens</div>'
    : `<div class="card"><table>
      <tr><th>Token</th><th>Channel</th><th>Recruits</th><th>Depth</th><th>Status</th><th>Expires</th></tr>
      ${tokens.map(t => {
        const recruits = jp(t.recruits) || [];
        return `<tr>
          <td><code style="font-size:10px">${t.id.slice(0,12)}…</code></td>
          <td>${t.channel||'—'}</td>
          <td>${Array.isArray(recruits)?recruits.length:0}</td>
          <td>${t.depth||0}</td>
          <td>${statusBadge(t.status)}</td>
          <td>${fmt(t.expires_at)}</td>
        </tr>`;
      }).join('')}
    </table></div>`;
}

function renderLog() {
  const log = data.log || [];

  // Populate filter dropdowns (deduplicate)
  const agents = [...new Set(log.map(e => e.agent).filter(Boolean))].sort();
  const types  = [...new Set(log.map(e => e.event_type).filter(Boolean))].sort();

  const agentSel = document.getElementById('log-filter-agent');
  const typeSel  = document.getElementById('log-filter-type');
  const agentVal = agentSel.value;
  const typeVal  = typeSel.value;

  agentSel.innerHTML = '<option value="">All agents</option>' +
    agents.map(a => `<option value="${a}" ${a===agentVal?'selected':''}>${a}</option>`).join('');
  typeSel.innerHTML = '<option value="">All event types</option>' +
    types.map(t => `<option value="${t}" ${t===typeVal?'selected':''}>${t}</option>`).join('');

  applyLogFilter();
}

function applyLogFilter() {
  const log = data.log || [];
  const agentVal = document.getElementById('log-filter-agent').value;
  const typeVal  = document.getElementById('log-filter-type').value;
  const filtered = log.filter(e =>
    (!agentVal || e.agent === agentVal) &&
    (!typeVal  || e.event_type === typeVal)
  );
  document.getElementById('log-count').textContent = `${filtered.length} / ${log.length} entries`;
  document.getElementById('log-content').innerHTML = filtered.length === 0
    ? '<div class="empty">No matching entries</div>'
    : `<div class="card">
      ${filtered.map(e => {
        const payload = jp(e.payload);
        const payloadStr = typeof payload === 'object' ? JSON.stringify(payload, null, 0).slice(0, 120) : String(payload||'').slice(0,120);
        return `<div class="log-entry">
          <span class="log-ts">${fmt(e.timestamp)}</span>
          <span class="log-agent">${badge(e.agent||'sys','muted')}</span>
          <div>
            <div style="font-size:12px;font-weight:600;color:var(--text)">${e.event_type||'—'}</div>
            <div class="log-body">${payloadStr}</div>
          </div>
        </div>`;
      }).join('')}
    </div>`;
}

function clearLogFilter() {
  document.getElementById('log-filter-agent').value = '';
  document.getElementById('log-filter-type').value = '';
  applyLogFilter();
}

loadAll();
setInterval(loadAll, 60000);
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(TEMPLATE)


@app.route("/api/all")
def api_all():
    conn = get_db()
    c = conn.cursor()

    def rows(table, order=None, limit=None):
        q = f"SELECT * FROM {table}"
        if order:
            q += f" ORDER BY {order}"
        if limit:
            q += f" LIMIT {limit}"
        c.execute(q)
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

    result = {
        "goals": rows("goals", "priority ASC, created_at DESC"),
        "actors": rows("actors", "registered_at DESC"),
        "directives": rows("directives", "issued_at DESC", 200),
        "entities": rows("state_entities", "updated_at DESC"),
        "relations": rows("state_relations", "updated_at DESC"),
        "assertions": rows("state_assertions", "timestamp DESC"),
        "crs": rows("collection_requirements", "issued_at DESC"),
        "sources": rows("intelligence_sources", "last_report_at DESC"),
        "irs": rows("intelligence_reports", "produced_at DESC"),
        "campaigns": rows("io_campaigns", "start_at DESC"),
        "sm_profiles": rows("social_media_actor_profiles"),
        "ledger": rows("performance_ledger"),
        "proposals": rows("constitutional_proposals", "proposed_at DESC"),
        "posture_log": rows("posture_log", "timestamp DESC", 50),
        "tokens": rows("referral_tokens", "issued_at DESC"),
        "phases": rows("operational_phases", "sequence ASC"),
        "log": rows("canonical_log", "timestamp DESC", 100),
    }

    # Escalation policy — single row
    c.execute("SELECT * FROM escalation_policy ORDER BY version DESC LIMIT 1")
    cols = [d[0] for d in c.description]
    row = c.fetchone()
    result["escalation_policy"] = dict(zip(cols, row)) if row else None

    conn.close()
    return jsonify(result)


def start_cloudflare_tunnel(port: int = 5050) -> str | None:
    """Start a cloudflared quick tunnel and return the public HTTPS URL.

    cloudflared exposes a local metrics API at localhost:20241 that reliably
    returns the assigned trycloudflare.com URL — more robust than stderr parsing.
    """
    import re
    import subprocess
    import time
    import urllib.error
    import urllib.request

    METRICS_PORT = 20241

    subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}",
         "--no-autoupdate", "--metrics", f"localhost:{METRICS_PORT}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Poll metrics API until the URL appears (usually within 5s)
    deadline = time.time() + 20
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(
                f"http://localhost:{METRICS_PORT}/metrics", timeout=2
            ) as resp:
                body = resp.read().decode()
            m = re.search(r"https://[a-z0-9\-]+\.trycloudflare\.com", body)
            if m:
                return m.group(0)
        except (urllib.error.URLError, OSError):
            pass

    return None


def notify_telegram(url: str):
    """Send the tunnel URL to the keyholder via Telegram."""
    import sqlite3 as _sqlite3
    import urllib.parse
    import urllib.request

    db = Path.home() / ".aktion" / "aktion.db"
    if not db.exists():
        return

    try:
        conn = _sqlite3.connect(str(db))
        cur = conn.cursor()

        # Bot token
        cur.execute("SELECT value FROM system_config WHERE key = 'telegram_bot_token'")
        row = cur.fetchone()
        if not row:
            return
        token = row[0]

        # All keyholder chat IDs on Telegram
        cur.execute(
            "SELECT channel_chat_id FROM keyholders WHERE channel = 'telegram'"
        )
        chat_ids = [r[0] for r in cur.fetchall()]
        conn.close()
    except Exception:
        return

    msg = f"📊 Aktion Dashboard\n{url}"
    for chat_id in chat_ids:
        try:
            payload = urllib.parse.urlencode({"chat_id": chat_id, "text": msg})
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=payload.encode(),
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass


if __name__ == "__main__":
    import threading

    PORT = 5050

    # Start Flask in a daemon thread so the main thread can block on tunnel
    flask_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=PORT, debug=False),
        daemon=True,
    )
    flask_thread.start()

    # Give Flask a moment to bind
    import time
    time.sleep(1)

    print(f"Aktion Dashboard — http://localhost:{PORT}")

    # Start Cloudflare tunnel
    print("Starting Cloudflare tunnel...")
    url = start_cloudflare_tunnel(PORT)
    if url:
        print(f"Public URL — {url}")
        notify_telegram(url)
    else:
        print("Tunnel URL not captured — check cloudflared logs")

    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
