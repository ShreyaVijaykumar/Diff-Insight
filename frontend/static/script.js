// ── HEALTH CHECK ──────────────────────────────────────────────────────────────

async function checkHealth() {
  try {
    const res  = await fetch('/health')
    const data = await res.json()
    const dot  = (id, ok) => {
      const el = document.getElementById(id)
      if (!el) return
      el.classList.add(ok ? 'dot-ok' : 'dot-err')
      el.title = el.title + (ok ? ' — OK' : ' — NOT AVAILABLE')
    }
    dot('dotOllama', data.groq)
    dot('dotVault',  data.github)
  } catch (_) {}
}

checkHealth()


// ── NAVIGATION ────────────────────────────────────────────────────────────────

function activate(section) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'))
  document.querySelectorAll('.nav-item').forEach(p => p.classList.remove('active'))
  document.getElementById(section + '-section').classList.add('active')
  document.getElementById('nav-' + section).classList.add('active')
}

document.getElementById('nav-diff').onclick      = () => activate('diff')
document.getElementById('nav-assistant').onclick = () => activate('assistant')
document.getElementById('nav-github').onclick    = () => activate('github')
document.getElementById('nav-heatmap').onclick   = () => activate('heatmap')


// ── INPUT TOGGLE (Diff Analyzer) ──────────────────────────────────────────────

function switchInput(mode) {
  const fileEl   = document.getElementById('inputFile')
  const pasteEl  = document.getElementById('inputPaste')
  const btnFile  = document.getElementById('toggleFile')
  const btnPaste = document.getElementById('togglePaste')

  if (mode === 'file') {
    fileEl.style.display  = 'flex'
    pasteEl.style.display = 'none'
    btnFile.classList.add('active')
    btnPaste.classList.remove('active')
  } else {
    fileEl.style.display  = 'none'
    pasteEl.style.display = 'flex'
    btnPaste.classList.add('active')
    btnFile.classList.remove('active')
  }
}

document.getElementById('toggleFile').onclick  = () => switchInput('file')
document.getElementById('togglePaste').onclick = () => switchInput('paste')


// ── LOADING TIMER ─────────────────────────────────────────────────────────────

function startTimer(labelId, prefix) {
  const start = Date.now()
  const el    = document.getElementById(labelId)
  if (el) el.textContent = `${prefix} 0s`
  return setInterval(() => {
    if (el) el.textContent = `${prefix} ${((Date.now() - start) / 1000).toFixed(0)}s`
  }, 500)
}


// ── CHANGE INTELLIGENCE RENDERER ─────────────────────────────────────────────

const LAYER_ICONS = {
  'LLM / AI':        '🤖',
  'Security':        '🔒',
  'Services':        '🔌',
  'Utilities':       '🔧',
  'Backend':         '⚙️',
  'Frontend JS/CSS': '🎨',
  'Frontend HTML':   '🖼️',
  'Frontend':        '💻',
  'Tests':           '🧪',
  'Config / Infra':  '📦',
  'Database':        '🗄️',
  'Docs':            '📄',
  'Other':           '📁',
}

const CHANGE_TYPE_STYLE = {
  'new':        { label: 'NEW',        color: '#34d399' },
  'deleted':    { label: 'DELETED',    color: '#f87171' },
  'refactored': { label: 'REFACTORED', color: '#fb923c' },
  'expanded':   { label: 'EXPANDED',   color: '#60a5fa' },
  'modified':   { label: 'MODIFIED',   color: '#a78bfa' },
}

const RISK_STYLE = {
  'High':   { color: '#f87171', bg: 'rgba(248,113,113,0.10)' },
  'Medium': { color: '#fb923c', bg: 'rgba(251,146,60,0.10)'  },
  'Low':    { color: '#34d399', bg: 'rgba(52,211,153,0.08)'  },
}

const OVERALL_TYPE_LABEL = {
  'additive':    { icon: '➕', label: 'Additive',    color: '#34d399' },
  'refactor':    { icon: '♻️', label: 'Refactor',    color: '#fb923c' },
  'mixed':       { icon: '🔀', label: 'Mixed',        color: '#60a5fa' },
  'destructive': { icon: '🗑️', label: 'Destructive', color: '#f87171' },
  'unknown':     { icon: '❓', label: 'Unknown',      color: '#6b7280' },
}

function renderIntelligence(intel) {
  const container = document.getElementById('intelligencePanel')
  if (!intel || !intel.file_changes || intel.file_changes.length === 0) {
    container.innerHTML = `
      <div class="intel-empty">
        <span style="font-size:32px">📂</span>
        <p>No file changes detected in this diff.</p>
      </div>`
    return
  }

  const ot     = OVERALL_TYPE_LABEL[intel.overall_type] || OVERALL_TYPE_LABEL['unknown']
  const layers = Object.entries(intel.layer_summary)
  const exts   = Object.entries(intel.ext_breakdown)

  // Summary bar
  let html = `
    <div class="intel-summary-bar">
      <span class="intel-type-badge" style="background:${ot.color}1a; color:${ot.color}; border:1px solid ${ot.color}33">
        ${ot.icon} ${ot.label}
      </span>
      <span class="intel-summary-text">${intel.summary_line}</span>
    </div>`

  // Layers
  html += `<div class="intel-section-title">Layers Touched</div><div class="intel-layers">`
  for (const [layer, count] of layers) {
    html += `
      <div class="intel-layer-chip">
        <span>${LAYER_ICONS[layer] || '📁'} ${layer}</span>
        <span class="intel-chip-count">${count} file${count !== 1 ? 's' : ''}</span>
      </div>`
  }
  html += `</div>`

  // Merge conflict candidates
  if (intel.at_risk_files && intel.at_risk_files.length > 0) {
    html += `<div class="intel-section-title">⚠️ Merge Conflict Candidates</div><div class="intel-risk-list">`
    for (const f of intel.at_risk_files) {
      const rs = RISK_STYLE[f.conflict_risk]
      html += `
        <div class="intel-risk-item" style="border-left-color:${rs.color}; background:${rs.bg}">
          <span class="intel-risk-path">${f.path}</span>
          <span class="intel-risk-badge" style="color:${rs.color}">${f.conflict_risk} risk</span>
          <span class="intel-risk-churn">+${f.added} / -${f.removed}</span>
        </div>`
    }
    html += `</div>`
  }

  // Per-file breakdown
  html += `<div class="intel-section-title">File Breakdown</div><div class="intel-file-list">`
  for (const f of intel.file_changes) {
    const ct  = CHANGE_TYPE_STYLE[f.change_type] || CHANGE_TYPE_STYLE['modified']
    const rs  = RISK_STYLE[f.conflict_risk]
    const bar = Math.min(100, Math.round((f.churn / (intel.total_churn || 1)) * 100))
    html += `
      <div class="intel-file-card">
        <div class="intel-file-header">
          <span class="intel-file-type-badge" style="color:${ct.color}">${ct.label}</span>
          <span class="intel-file-path">${f.path}</span>
          <span class="intel-file-layer">${LAYER_ICONS[f.layer] || ''} ${f.layer}</span>
        </div>
        <div class="intel-file-meta">
          <span class="intel-added">+${f.added}</span>
          <span class="intel-removed">-${f.removed}</span>
          <span class="intel-conflict" style="color:${rs.color}">${f.conflict_risk} conflict risk</span>
        </div>
        <div class="intel-churn-bar-bg">
          <div class="intel-churn-bar-fill" style="width:${bar}%"></div>
        </div>
      </div>`
  }
  html += `</div>`

  // Extensions
  if (exts.length > 0) {
    html += `<div class="intel-section-title">File Types</div><div class="intel-ext-row">`
    for (const [ext, count] of exts) {
      html += `<div class="intel-ext-chip">.${ext} <strong>${count}</strong></div>`
    }
    html += `</div>`
  }

  container.innerHTML = html
}


// ── DIFF ANALYSIS ─────────────────────────────────────────────────────────────

document.getElementById('analyzeBtn').onclick = async () => {
  const reportEl  = document.getElementById('diffReport')
  const statsEl   = document.getElementById('stats')
  const loadingEl = document.getElementById('loadingReport')
  const modeTagEl = document.getElementById('modeTag')
  const modeVal   = document.getElementById('analyzeMode').value
  const isPaste   = document.getElementById('togglePaste').classList.contains('active')

  let fetchOpts = {}

  if (isPaste) {
    const text = document.getElementById('diffPaste').value.trim()
    if (!text) { alert('Please paste a diff first.'); return }
    fetchOpts = {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ diff: text, mode: modeVal }),
    }
  } else {
    const file = document.getElementById('diffFile').files[0]
    if (!file) { alert('Please upload a .diff, .patch, or .txt file.'); return }
    const formData = new FormData()
    formData.append('file', file)
    formData.append('mode', modeVal)
    fetchOpts = { method: 'POST', body: formData }
  }

  // Loading state
  reportEl.style.display  = 'none'
  loadingEl.style.display = 'flex'
  reportEl.classList.remove('error-text')
  document.getElementById('intelligencePanel').innerHTML =
    '<div class="intel-empty"><div class="spinner"></div><p>Analysing changes…</p></div>'

  const timer = startTimer('loadingTimer', 'Analyzing…')

  try {
    const res  = await fetch('/analyze', fetchOpts)
    const data = await res.json()

    clearInterval(timer)
    loadingEl.style.display = 'none'
    reportEl.style.display  = 'block'

    if (!res.ok) {
      reportEl.textContent = `❌ Error: ${data.detail || res.statusText}`
      reportEl.classList.add('error-text')
      return
    }

    reportEl.textContent = data.report

    // Show sanitisation warning if any secrets were stripped
    const warnEl = document.getElementById('sanitiseWarning')
    if (warnEl) {
      if (data.sanitise_warning) {
        warnEl.textContent = data.sanitise_warning
        warnEl.style.display = 'block'
      } else {
        warnEl.style.display = 'none'
      }
    }

    modeTagEl.textContent = data.mode === 'junior' ? '🎓 Junior Mentor' : '👔 Senior Reviewer'
    modeTagEl.className   = 'mode-tag mode-' + data.mode

    statsEl.textContent =
      `Files Changed:      ${data.stats.files}\n` +
      `Lines Added:        ${data.stats.added}\n` +
      `Lines Removed:      ${data.stats.removed}\n` +
      `Functions Modified: ${data.stats.functions}\n` +
      `Risk Level:         ${data.risk_level}`

    renderIntelligence(data.intelligence)

  } catch (err) {
    clearInterval(timer)
    loadingEl.style.display = 'none'
    reportEl.style.display  = 'block'
    reportEl.textContent    = `❌ Request failed: ${err.message}`
    reportEl.classList.add('error-text')
  }
}


// ── TECH ASSISTANT ────────────────────────────────────────────────────────────

document.getElementById('askBtn').onclick = async () => {
  const question  = document.getElementById('questionInput').value.trim()
  if (!question)  { alert('Please enter a question.'); return }

  const answerEl  = document.getElementById('assistantAnswer')
  const cardEl    = document.getElementById('assistantCard')
  const loadingEl = document.getElementById('loadingAssistant')
  const topicEl   = document.getElementById('detectedTopic')

  cardEl.style.display    = 'block'
  answerEl.style.display  = 'none'
  loadingEl.style.display = 'flex'
  topicEl.textContent     = ''
  answerEl.classList.remove('error-text')

  const timer = startTimer('loadingTimerAssistant', 'Thinking…')

  try {
    const res  = await fetch('/ask', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ question }),
    })
    const data = await res.json()

    clearInterval(timer)
    loadingEl.style.display = 'none'
    answerEl.style.display  = 'block'

    if (!res.ok) {
      answerEl.textContent = `❌ Error: ${data.detail || res.statusText}`
      answerEl.classList.add('error-text')
      return
    }

    answerEl.textContent = data.answer
    topicEl.textContent  = `Detected topic: ${data.topic}`

  } catch (err) {
    clearInterval(timer)
    loadingEl.style.display = 'none'
    answerEl.style.display  = 'block'
    answerEl.textContent    = `❌ Request failed: ${err.message}`
    answerEl.classList.add('error-text')
  }
}


// ── GITHUB EXPLORER ───────────────────────────────────────────────────────────

document.getElementById('searchRepoBtn').onclick = () => {
  const topic    = document.getElementById('repoTopic').value.trim()
  const sort     = document.getElementById('repoSort').value || 'stars'
  const language = document.getElementById('repoLanguage').value.trim()
  if (!topic) { alert('Please enter a search topic.'); return }
  loadRepos(topic, sort, language)
}

async function loadRepos(topic, sort = 'stars', language = '') {
  const container = document.getElementById('repoResults')
  container.innerHTML = '<p class="loading-text">Fetching repositories and sorting…</p>'

  const url = `/repos/${encodeURIComponent(topic)}?sort=${sort}` +
              (language ? `&language=${encodeURIComponent(language)}` : '')

  try {
    const res  = await fetch(url)
    const data = await res.json()

    if (!res.ok) {
      container.innerHTML = `<div class="error-card">❌ ${data.detail || res.statusText}</div>`
      return
    }

    container.innerHTML = ''
    if (!data.length) {
      container.innerHTML = '<p class="loading-text">No repositories found.</p>'
      return
    }

    data.forEach((repo, index) => {
      const div = document.createElement('div')
      div.className = 'repo-card'
      div.innerHTML = `
        <div class="repo-header">
          <span class="repo-rank">#${index + 1}</span>
          <strong>${repo.name}</strong>
          <span class="repo-lang">${repo.language}</span>
        </div>
        <p>${repo.description}</p>
        <div class="repo-meta">
          <span>⭐ ${repo.stars.toLocaleString()}</span>
          <span>🍴 ${repo.forks.toLocaleString()}</span>
          <span>🐛 ${repo.issues.toLocaleString()} issues</span>
          <span>👁️ ${repo.watchers.toLocaleString()} watchers</span>
          <span>🕒 ${new Date(repo.updated).toLocaleDateString()}</span>
        </div>
        <a href="${repo.url}" target="_blank">Open on GitHub →</a>
      `
      container.appendChild(div)
    })

  } catch (err) {
    container.innerHTML = `<div class="error-card">❌ Request failed: ${err.message}</div>`
  }
}


// ── CHURN HEATMAP ─────────────────────────────────────────────────────────────

const hmSessions = []  // { label: string, diff: string }

const LAYER_ICONS_HM = {
  'LLM / AI':        '🤖',
  'Security':        '🔒',
  'Services':        '🔌',
  'Utilities':       '🔧',
  'Backend':         '⚙️',
  'Frontend JS/CSS': '🎨',
  'Frontend HTML':   '🖼️',
  'Frontend':        '💻',
  'Tests':           '🧪',
  'Config / Infra':  '📦',
  'Database':        '🗄️',
  'Docs':            '📄',
  'Other':           '📁',
}

const CHANGE_COLOURS = {
  'new':        '#34d399',
  'expanded':   '#60a5fa',
  'modified':   '#a78bfa',
  'refactored': '#fb923c',
  'deleted':    '#f87171',
}

function renderSessionList() {
  const el = document.getElementById('heatmapSessions')
  if (!hmSessions.length) {
    el.innerHTML = ''
    return
  }
  el.innerHTML = hmSessions.map((s, i) => `
    <div class="hm-session-chip">
      <span class="hm-chip-label">${s.label}</span>
      <span class="hm-chip-lines">${s.diff.split('\n').length} lines</span>
      <button class="hm-chip-remove" onclick="removeSession(${i})">✕</button>
    </div>
  `).join('')
}

function removeSession(i) {
  hmSessions.splice(i, 1)
  renderSessionList()
}

document.getElementById('hmAddBtn').onclick = () => {
  const label = document.getElementById('hmLabel').value.trim()
  const diff  = document.getElementById('hmDiff').value.trim()
  if (!diff) { alert('Paste a diff first.'); return }
  hmSessions.push({
    label: label || `diff-${hmSessions.length + 1}`,
    diff,
  })
  document.getElementById('hmLabel').value = ''
  document.getElementById('hmDiff').value  = ''
  renderSessionList()
}

document.getElementById('hmClearBtn').onclick = () => {
  hmSessions.length = 0
  renderSessionList()
  document.getElementById('hmOutput').style.display  = 'none'
}

document.getElementById('hmRunBtn').onclick = async () => {
  if (hmSessions.length < 1) { alert('Add at least one diff first.'); return }

  document.getElementById('hmOutput').style.display  = 'none'
  document.getElementById('hmLoading').style.display = 'flex'

  try {
    const res  = await fetch('/heatmap', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ sessions: hmSessions }),
    })
    const data = await res.json()

    document.getElementById('hmLoading').style.display = 'none'

    if (!res.ok) {
      alert(`Heatmap error: ${data.detail || res.statusText}`)
      return
    }

    renderHeatmap(data)
    document.getElementById('hmOutput').style.display = 'block'

  } catch (err) {
    document.getElementById('hmLoading').style.display = 'none'
    alert(`Request failed: ${err.message}`)
  }
}

// Gamma-compressed heat colour: purple (low) → orange (high)
function heatColour(churn, maxChurn) {
  if (churn === 0 || maxChurn === 0) return 'rgba(255,255,255,0.03)'
  const t = Math.pow(churn / maxChurn, 0.55)
  const r = Math.round(124 + (234 - 124) * t)
  const g = Math.round(58  + (88  - 58)  * t)
  const b = Math.round(237 + (12  - 237) * t)
  return `rgba(${r},${g},${b},${(0.15 + t * 0.75).toFixed(2)})`
}

// Strip version prefix (v1/, v2/, v3/, or any vN/folder/ prefix) and
// show only the meaningful project-relative path e.g. backend/llm/tech_assistant.py
function _cleanPath(rawPath) {
  // Remove leading vN/ or vN/subfolder/ segments until we hit a known project dir
  const KNOWN_ROOTS = ['backend', 'frontend', 'tests', 'utils', 'static', 'templates', 'llm', 'security', 'services']
  const parts = rawPath.replace(/\\/g, '/').split('/')
  for (let i = 0; i < parts.length; i++) {
    if (KNOWN_ROOTS.includes(parts[i].toLowerCase())) {
      return parts.slice(i).join('/')
    }
  }
  // Fallback: just strip everything before the last 3 segments
  return parts.length > 3 ? parts.slice(-3).join('/') : rawPath
}

// Just the filename for tight spaces
function _fileName(rawPath) {
  const clean = _cleanPath(rawPath)
  return clean.split('/').pop()
}

// Short but readable: last 2 segments of cleaned path
function _shortPath(rawPath) {
  const clean = _cleanPath(rawPath)
  const parts = clean.split('/')
  return parts.length > 2 ? parts.slice(-2).join('/') : clean
}

function renderHeatmap(data) {
  // ── Summary ────────────────────────────────────────────────────────────────
  // Rewrite summary with clean paths
  const topFile = data.hotspots[0] ? _cleanPath(data.hotspots[0].file) : '—'
  const topChurn = data.hotspots[0] ? data.hotspots[0].total : 0
  document.getElementById('hmSummary').innerHTML = `
    <span class="hm-summary-stat">${data.matrix.length}</span> unique files tracked across
    <span class="hm-summary-stat">${data.total_diffs}</span> diffs.
    Hottest file: <span class="hm-summary-hotfile">${topFile}</span>
    with <span class="hm-summary-stat">${topChurn.toLocaleString()}</span> total churn lines.`

  // ── Hotspot Leaderboard ────────────────────────────────────────────────────
  const medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
  document.getElementById('hmHotspots').innerHTML = data.hotspots.map((row, i) => {
    const pct       = Math.round((row.total / (data.hotspots[0].total || 1)) * 100)
    const icon      = LAYER_ICONS_HM[row.layer] || '📁'
    const cleanFile = _cleanPath(row.file)
    const fileName  = _fileName(row.file)
    const filePath  = _shortPath(row.file)

    return `
      <div class="hm-hotspot-row">
        <span class="hm-hotspot-rank">${medals[i] || (i + 1) + '.'}</span>
        <div class="hm-hotspot-info">
          <div class="hm-hotspot-name-row">
            <span class="hm-hotspot-icon">${icon}</span>
            <div class="hm-hotspot-names">
              <span class="hm-hotspot-filename">${fileName}</span>
              <span class="hm-hotspot-filepath" title="${cleanFile}">${filePath}</span>
            </div>
            <span class="hm-layer-tag">${row.layer}</span>
          </div>
          <div class="hm-hotspot-bar-bg">
            <div class="hm-hotspot-bar-fill" style="width:${pct}%">
              <span class="hm-bar-pct">${pct}%</span>
            </div>
          </div>
        </div>
        <div class="hm-hotspot-stats">
          <span class="hm-stat-total">${row.total.toLocaleString()}</span>
          <span class="hm-stat-label">lines churned</span>
          <span class="hm-stat-touches">${row.touches} of ${data.total_diffs} diffs</span>
        </div>
      </div>`
  }).join('')

  // ── Heatmap Table ──────────────────────────────────────────────────────────
  const maxC = data.max_churn || 1

  let table = `
    <div class="hm-table-wrap">
      <table class="hm-table">
        <thead>
          <tr>
            <th class="hm-th-layer"></th>
            <th class="hm-th-file">File</th>
            ${data.labels.map(l => `<th class="hm-th-col">${l}</th>`).join('')}
            <th class="hm-th-total">Total</th>
            <th class="hm-th-touches">Touches</th>
          </tr>
        </thead>
        <tbody>`

  for (const row of data.matrix) {
    const icon      = LAYER_ICONS_HM[row.layer] || '📁'
    const fileName  = _fileName(row.file)
    const filePath  = _shortPath(row.file)
    const fullClean = _cleanPath(row.file)

    table += `<tr>
      <td class="hm-td-layer" title="${row.layer}">${icon}</td>
      <td class="hm-td-file" title="${fullClean}">
        <span class="hm-file-name">${fileName}</span>
        <span class="hm-file-path">${filePath}</span>
      </td>`

    for (const cell of row.cells) {
      const bg      = heatColour(cell.churn, maxC)
      const dotCol  = cell.change_type ? (CHANGE_COLOURS[cell.change_type] || '#a78bfa') : null
      const tooltip = cell.churn > 0
        ? `${cell.churn} lines · ${cell.change_type || 'changed'}`
        : 'not touched'
      const isEmpty = cell.churn === 0
      table += `
        <td class="hm-td-cell ${isEmpty ? 'hm-td-empty' : ''}" style="background:${bg}" title="${tooltip}">
          ${!isEmpty ? `<span class="hm-cell-val">${cell.churn.toLocaleString()}</span>` : '<span class="hm-cell-dash">—</span>'}
          ${dotCol   ? `<span class="hm-cell-dot" style="background:${dotCol}"></span>` : ''}
        </td>`
    }

    const touchPct = Math.round((row.touches / data.total_diffs) * 100)
    table += `
      <td class="hm-td-total">${row.total.toLocaleString()}</td>
      <td class="hm-td-touches">
        <span class="hm-touch-fraction">${row.touches}/${data.total_diffs}</span>
        <span class="hm-touch-bar-bg"><span class="hm-touch-bar-fill" style="width:${touchPct}%"></span></span>
      </td>
    </tr>`
  }

  table += `</tbody></table></div>`

  // ── Legend ─────────────────────────────────────────────────────────────────
  table += `
    <div class="hm-legend">
      <div class="hm-legend-scale">
        <span class="hm-legend-label">Low churn</span>
        <div class="hm-legend-bar"></div>
        <span class="hm-legend-label">High churn</span>
      </div>
      <div class="hm-legend-types">
        ${Object.entries(CHANGE_COLOURS).map(([k, v]) => `
          <div class="hm-legend-type">
            <span class="hm-dot-legend" style="background:${v}"></span>
            <span class="hm-legend-label">${k}</span>
          </div>`
        ).join('')}
      </div>
    </div>`

  document.getElementById('hmGrid').innerHTML = table
}