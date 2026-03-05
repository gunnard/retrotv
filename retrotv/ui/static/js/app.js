/**
 * RetroTV Channel Builder - Web Interface
 */

const API_BASE = '/api';

// State management
const state = {
  guides: [],
  schedules: [],
  libraryStatus: [],
  currentPage: 'dashboard'
};

// API helpers
async function api(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'API Error');
  }
  
  return response.json();
}

// Toast notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;margin-left:auto;">&times;</button>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

// Loading state
function setLoading(element, loading) {
  if (loading) {
    element.classList.add('loading');
    element.innerHTML = '<div class="spinner"></div>';
  } else {
    element.classList.remove('loading');
  }
}

// Format date
function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// Format duration
function formatDuration(seconds) {
  if (!seconds) return '-';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Dashboard
async function loadDashboard() {
  try {
    const [guides, schedules, libraryStatus] = await Promise.all([
      api('/guides'),
      api('/schedules'),
      api('/library/status')
    ]);
    
    state.guides = guides;
    state.schedules = schedules;
    state.libraryStatus = libraryStatus;
    
    renderDashboard();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function renderDashboard() {
  const libStatus = state.libraryStatus[0] || {};
  
  document.getElementById('stat-guides').textContent = state.guides.length;
  document.getElementById('stat-schedules').textContent = state.schedules.length;
  document.getElementById('stat-series').textContent = libStatus.total_series || 0;
  document.getElementById('stat-movies').textContent = libStatus.total_movies || 0;
  
  // Recent guides
  const recentGuides = state.guides.slice(0, 5);
  const guidesBody = document.getElementById('recent-guides-body');
  
  if (recentGuides.length === 0) {
    guidesBody.innerHTML = '<tr><td colspan="4" class="text-muted text-center">No guides imported yet</td></tr>';
  } else {
    guidesBody.innerHTML = recentGuides.map(g => `
      <tr>
        <td class="font-mono text-sm">${g.id.substring(0, 8)}</td>
        <td>${g.channel_name}</td>
        <td>${g.broadcast_date}</td>
        <td><span class="badge badge-purple">${g.entry_count} entries</span></td>
      </tr>
    `).join('');
  }
  
  // Recent schedules
  const recentSchedules = state.schedules.slice(0, 5);
  const schedulesBody = document.getElementById('recent-schedules-body');
  
  if (recentSchedules.length === 0) {
    schedulesBody.innerHTML = '<tr><td colspan="5" class="text-muted text-center">No schedules created yet</td></tr>';
  } else {
    schedulesBody.innerHTML = recentSchedules.map(s => `
      <tr>
        <td class="font-mono text-sm">${s.id.substring(0, 8)}</td>
        <td>${s.channel_name}</td>
        <td>${s.broadcast_date}</td>
        <td>
          <span class="badge badge-success">${s.matched_count}</span>
          <span class="badge badge-info">${s.substituted_count}</span>
          <span class="badge badge-danger">${s.missing_count}</span>
        </td>
        <td>${s.coverage_percent.toFixed(1)}%</td>
      </tr>
    `).join('');
  }
}

// Guides page
async function loadGuides() {
  try {
    state.guides = await api('/guides');
    renderGuides();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function renderGuides() {
  const tbody = document.getElementById('guides-table-body');
  
  if (state.guides.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center">
          <div class="empty-state">
            <p>No guides imported yet</p>
            <button class="btn btn-primary mt-2" onclick="openImportModal()">Import Guide</button>
          </div>
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = state.guides.map(g => `
    <tr>
      <td class="font-mono text-sm">${g.id.substring(0, 8)}</td>
      <td>
        <span class="guide-name" id="name-${g.id}" ondblclick="editGuideName('${g.id}')">${g.name || g.channel_name + ' - ' + g.broadcast_date}</span>
        <input type="text" class="form-input guide-name-input" id="input-${g.id}" style="display:none;" 
               value="${g.name || ''}" 
               onblur="saveGuideName('${g.id}')" 
               onkeydown="if(event.key==='Enter')saveGuideName('${g.id}');if(event.key==='Escape')cancelEditName('${g.id}')">
      </td>
      <td>${g.channel_name}</td>
      <td>${g.broadcast_date}</td>
      <td><span class="badge badge-purple">${g.decade}</span></td>
      <td>${g.entry_count}</td>
      <td>
        <button class="btn btn-sm btn-secondary" onclick="viewGuide('${g.id}')">View</button>
        <button class="btn btn-sm btn-primary" onclick="createScheduleFromGuide('${g.id}')">Create Schedule</button>
        <button class="btn btn-sm btn-danger" onclick="deleteGuide('${g.id}')">Delete</button>
      </td>
    </tr>
  `).join('');
}

function editGuideName(guideId) {
  document.getElementById(`name-${guideId}`).style.display = 'none';
  const input = document.getElementById(`input-${guideId}`);
  input.style.display = 'block';
  input.focus();
  input.select();
}

function cancelEditName(guideId) {
  document.getElementById(`name-${guideId}`).style.display = 'inline';
  document.getElementById(`input-${guideId}`).style.display = 'none';
}

async function saveGuideName(guideId) {
  const input = document.getElementById(`input-${guideId}`);
  const nameSpan = document.getElementById(`name-${guideId}`);
  const newName = input.value.trim();
  
  if (!newName) {
    cancelEditName(guideId);
    return;
  }
  
  try {
    await api(`/guides/${guideId}`, {
      method: 'PATCH',
      body: JSON.stringify({ name: newName })
    });
    nameSpan.textContent = newName;
    nameSpan.style.display = 'inline';
    input.style.display = 'none';
    showToast('Guide name updated', 'success');
  } catch (error) {
    showToast(error.message, 'error');
    cancelEditName(guideId);
  }
}

function openImportModal() {
  document.getElementById('import-modal').classList.add('active');
}

function closeImportModal() {
  document.getElementById('import-modal').classList.remove('active');
}

async function uploadGuide(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch(`${API_BASE}/guides`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('Upload failed');
    }
    
    const guide = await response.json();
    showToast(`Guide imported: ${guide.channel_name}`, 'success');
    closeImportModal();
    loadGuides();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function viewGuide(guideId) {
  try {
    const entries = await api(`/guides/${guideId}/entries`);
    const guide = state.guides.find(g => g.id.startsWith(guideId));
    
    const modal = document.getElementById('view-guide-modal');
    document.getElementById('view-guide-title').textContent = `${guide.channel_name} - ${guide.broadcast_date}`;
    
    const tbody = document.getElementById('guide-entries-body');
    tbody.innerHTML = entries.map(e => `
      <tr>
        <td>${e.start_time ? e.start_time.substring(11, 16) : '-'}</td>
        <td><strong>${e.title}</strong></td>
        <td>${e.episode_title || '-'}</td>
        <td>${e.duration_minutes || '-'} min</td>
        <td>${e.genre || '-'}</td>
      </tr>
    `).join('');
    
    modal.classList.add('active');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function closeViewGuideModal() {
  document.getElementById('view-guide-modal').classList.remove('active');
}

async function deleteGuide(guideId) {
  if (!confirm('Delete this guide?')) return;
  
  try {
    await api(`/guides/${guideId}`, { method: 'DELETE' });
    showToast('Guide deleted', 'success');
    loadGuides();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// Schedules page
async function loadSchedules() {
  try {
    state.schedules = await api('/schedules');
    renderSchedules();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function renderSchedules() {
  const tbody = document.getElementById('schedules-table-body');
  
  if (state.schedules.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center">
          <div class="empty-state">
            <p>No schedules created yet</p>
            <p class="text-sm text-muted mt-1">Import a guide first, then create a schedule</p>
          </div>
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = state.schedules.map(s => `
    <tr>
      <td class="font-mono text-sm">${s.id.substring(0, 8)}</td>
      <td><strong>${s.channel_name}</strong></td>
      <td>${s.broadcast_date}</td>
      <td><span class="badge badge-purple">${s.decade}</span></td>
      <td>
        <span class="badge badge-success" title="Matched">${s.matched_count}</span>
        <span class="badge badge-info" title="Substituted">${s.substituted_count}</span>
        <span class="badge badge-danger" title="Missing">${s.missing_count}</span>
      </td>
      <td>
        <div class="progress-bar" style="width:80px;">
          <div class="progress-fill" style="width:${s.coverage_percent}%"></div>
        </div>
        <span class="text-sm">${s.coverage_percent.toFixed(1)}%</span>
      </td>
      <td>${s.total_ad_gap_minutes} min</td>
      <td>
        <button class="btn btn-sm btn-secondary" onclick="viewSchedule('${s.id}')">View</button>
        <button class="btn btn-sm btn-success" onclick="exportSchedule('${s.id}', 'ersatztv')">Export</button>
        <button class="btn btn-sm btn-danger" onclick="deleteSchedule('${s.id}')">Delete</button>
      </td>
    </tr>
  `).join('');
}

function createScheduleFromGuide(guideId) {
  const guide = state.guides.find(g => g.id.startsWith(guideId));
  document.getElementById('create-schedule-guide-id').value = guideId;
  document.getElementById('create-schedule-info').innerHTML = guide 
    ? `<strong>${guide.channel_name}</strong> - ${guide.broadcast_date} (${guide.entry_count} entries)`
    : '';
  document.getElementById('create-schedule-modal').classList.add('active');
}

function closeCreateScheduleModal() {
  document.getElementById('create-schedule-modal').classList.remove('active');
}

async function confirmCreateSchedule() {
  const guideId = document.getElementById('create-schedule-guide-id').value;
  const autoSub = document.getElementById('create-auto-substitute').checked;
  
  closeCreateScheduleModal();
  
  try {
    showToast('Creating schedule...', 'info');
    const schedule = await api('/schedules', {
      method: 'POST',
      body: JSON.stringify({
        guide_id: guideId,
        auto_substitute: autoSub
      })
    });
    
    showToast(`Schedule created: ${schedule.coverage_percent.toFixed(1)}% coverage`, 'success');
    navigateTo('schedules');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

let currentScheduleId = null;
let currentSlots = [];

async function viewSchedule(scheduleId) {
  try {
    currentScheduleId = scheduleId;
    const slots = await api(`/schedules/${scheduleId}/slots`);
    currentSlots = slots;
    const schedule = state.schedules.find(s => s.id.startsWith(scheduleId));
    
    const modal = document.getElementById('view-schedule-modal');
    document.getElementById('view-schedule-title').textContent = `${schedule.channel_name} - ${schedule.broadcast_date}`;
    
    // Summary stats
    const matched = slots.filter(s => s.match_status === 'matched').length;
    const partial = slots.filter(s => s.match_status === 'partial').length;
    const substituted = slots.filter(s => s.match_status === 'substituted').length;
    const missing = slots.filter(s => s.match_status === 'missing').length;
    
    document.getElementById('schedule-summary').innerHTML = `
      <span class="badge badge-success">${matched} Matched</span>
      <span class="badge badge-warning">${partial} Partial</span>
      <span class="badge badge-info">${substituted} Substituted</span>
      <span class="badge badge-danger">${missing} Missing</span>
    `;
    
    renderScheduleSlots(slots);
    modal.classList.add('active');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function renderScheduleSlots(slots) {
  const tbody = document.getElementById('schedule-slots-body');
  tbody.innerHTML = slots.map((s, idx) => {
    let statusBadge, rowClass = '';
    switch (s.match_status) {
      case 'matched': 
        statusBadge = '<span class="badge badge-success">Matched</span>'; 
        break;
      case 'partial': 
        statusBadge = '<span class="badge badge-warning">Partial</span>'; 
        rowClass = 'row-warning';
        break;
      case 'substituted': 
        statusBadge = '<span class="badge badge-info">Subbed</span>'; 
        break;
      case 'missing': 
        statusBadge = '<span class="badge badge-danger">Missing</span>'; 
        rowClass = 'row-danger';
        break;
      default: 
        statusBadge = '<span class="badge">' + s.match_status + '</span>';
    }
    
    const matchedDisplay = s.matched_title || '<span class="text-muted">—</span>';
    const confidence = s.match_confidence > 0 ? `${s.match_confidence.toFixed(0)}%` : '—';
    
    // Action buttons based on status
    let actions = '';
    if (s.match_status === 'missing' || s.match_status === 'partial') {
      actions = `<button class="btn btn-sm btn-primary" onclick="openSubstitutePicker('${s.id}', ${idx})">Find</button>`;
    } else if (s.match_status === 'substituted') {
      actions = `<button class="btn btn-sm btn-secondary" onclick="openSubstitutePicker('${s.id}', ${idx})">Change</button>`;
    } else {
      actions = `<span class="text-muted text-sm">OK</span>`;
    }
    
    return `
      <tr class="${rowClass}">
        <td>${s.scheduled_start.substring(11, 16)}</td>
        <td><strong>${s.original_title || 'Unknown'}</strong></td>
        <td>${statusBadge}</td>
        <td>${confidence}</td>
        <td class="text-sm">${matchedDisplay}</td>
        <td>${actions}</td>
      </tr>
    `;
  }).join('');
}

function closeViewScheduleModal() {
  document.getElementById('view-schedule-modal').classList.remove('active');
  currentScheduleId = null;
  currentSlots = [];
}

function exportCurrentSchedule() {
  if (currentScheduleId) {
    exportSchedule(currentScheduleId, 'ersatztv');
  }
}

// Substitute picker
let currentSlotId = null;
let currentSlotIndex = null;

async function openSubstitutePicker(slotId, slotIndex) {
  currentSlotId = slotId;
  currentSlotIndex = slotIndex;
  const slot = currentSlots[slotIndex];
  
  document.getElementById('sub-original-title').textContent = slot.original_title || 'Unknown';
  document.getElementById('sub-expected-runtime').textContent = formatDuration(slot.expected_runtime_seconds);
  document.getElementById('substitute-candidates').innerHTML = '<p class="text-muted">Loading candidates...</p>';
  document.getElementById('substitute-modal').classList.add('active');
  
  try {
    const candidates = await api(`/schedules/slots/${slotId}/candidates`);
    renderSubstituteCandidates(candidates);
  } catch (error) {
    document.getElementById('substitute-candidates').innerHTML = `<p class="text-danger">Error loading candidates: ${error.message}</p>`;
  }
}

function renderSubstituteCandidates(candidates) {
  const container = document.getElementById('substitute-candidates');
  
  if (!candidates || candidates.length === 0) {
    container.innerHTML = '<p class="text-muted">No suitable candidates found in your library.</p>';
    return;
  }
  
  container.innerHTML = `
    <table class="w-100">
      <thead>
        <tr>
          <th>Title</th>
          <th>Runtime</th>
          <th>Score</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        ${candidates.map(c => `
          <tr>
            <td>
              <strong>${c.title}</strong>
              ${c.episode_title ? `<br><span class="text-sm text-muted">${c.episode_title}</span>` : ''}
            </td>
            <td>${c.runtime_minutes} min</td>
            <td>
              <span class="badge ${c.score >= 0.7 ? 'badge-success' : c.score >= 0.5 ? 'badge-warning' : 'badge-gray'}">
                ${(c.score * 100).toFixed(0)}%
              </span>
            </td>
            <td>
              <button class="btn btn-sm btn-primary" onclick="applySubstitute('${c.media_item_id}')">Use</button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

async function applySubstitute(mediaItemId) {
  try {
    await api(`/schedules/slots/${currentSlotId}/substitute`, {
      method: 'POST',
      body: JSON.stringify({ media_item_id: mediaItemId })
    });
    
    showToast('Substitute applied', 'success');
    closeSubstituteModal();
    
    // Refresh the schedule view
    if (currentScheduleId) {
      viewSchedule(currentScheduleId);
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function closeSubstituteModal() {
  document.getElementById('substitute-modal').classList.remove('active');
  currentSlotId = null;
  currentSlotIndex = null;
}

async function exportSchedule(scheduleId, format) {
  try {
    lastExportedScheduleId = scheduleId;
    const result = await api(`/schedules/${scheduleId}/export?format=${format}`, {
      method: 'POST'
    });
    
    // Show success with download option
    const exportPath = result.path;
    showToast(`Exported to ${exportPath}`, 'success');
    
    // Show export instructions modal
    showExportInstructions(format, exportPath);
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function showExportInstructions(format, filePath) {
  const instructions = format === 'ersatztv' ? `
    <h4>📁 Export Complete</h4>
    <p><strong>File:</strong> <code>${filePath}</code></p>
    
    <h4 class="mt-3">🚀 Deployment Options</h4>
    
    <div class="card mb-2" style="padding:1rem;">
      <h5>Option 1: Same Server (Local Copy)</h5>
      <p class="text-sm text-muted">If RetroTV runs on the same machine as ErsatzTV:</p>
      <code class="d-block p-2 bg-dark">cp ${filePath} /path/to/ersatztv/config/</code>
    </div>
    
    <div class="card mb-2" style="padding:1rem;">
      <h5>Option 2: Remote Server (SCP)</h5>
      <p class="text-sm text-muted">Copy to a remote ErsatzTV server:</p>
      <code class="d-block p-2 bg-dark">scp ${filePath} user@ersatztv-host:/config/</code>
    </div>
    
    <div class="card mb-2" style="padding:1rem;">
      <h5>Option 3: Docker Container</h5>
      <p class="text-sm text-muted">Copy directly into the ErsatzTV Docker container:</p>
      <code class="d-block p-2 bg-dark">docker cp ${filePath} ersatztv:/config/</code>
    </div>
    
    <h4 class="mt-3">🐍 NEW: Scripted Schedule (Recommended)</h4>
    <p class="text-sm">ErsatzTV now supports Python scripted schedules:</p>
    <ol class="text-sm">
      <li>Click <strong>"ErsatzTV Script"</strong> below to generate a .py file</li>
      <li>Copy it to <code>ErsatzTV/config/scripts/</code></li>
      <li>Create a <strong>Scripted Schedule</strong> playout in ErsatzTV</li>
      <li>Update the CONTENT_KEYS mapping to match your collections</li>
    </ol>
    
    <h4 class="mt-3">📋 Alternative: Manual Setup</h4>
    <p class="text-sm">Or use the Setup Guide/CSV to manually recreate in ErsatzTV UI.</p>
  ` : `
    <h4>Tunarr Setup Instructions</h4>
    <ol>
      <li><strong>File Location:</strong> <code>${filePath}</code></li>
      <li><strong>In Tunarr:</strong> Import the channel configuration</li>
    </ol>
  `;
  
  const modal = document.createElement('div');
  modal.className = 'modal-overlay active';
  modal.innerHTML = `
    <div class="modal" style="max-width:600px;">
      <div class="modal-header">
        <h3 class="modal-title">📺 Export Complete</h3>
        <button onclick="this.closest('.modal-overlay').remove()" class="btn btn-secondary">&times;</button>
      </div>
      <div class="modal-body" style="max-height:70vh;overflow-y:auto;">
        ${instructions}
        <div class="mt-3" style="display:flex;gap:0.5rem;flex-wrap:wrap;">
          <button class="btn btn-primary" onclick="copyToClipboard('${filePath}');this.textContent='Copied!'">
            Copy File Path
          </button>
          <button class="btn btn-secondary" onclick="exportAdditionalFormat('ersatztv_script')">
            🐍 ErsatzTV Script
          </button>
          <button class="btn btn-secondary" onclick="exportAdditionalFormat('setup_guide')">
            📄 Setup Guide
          </button>
          <button class="btn btn-secondary" onclick="exportAdditionalFormat('csv')">
            📊 CSV
          </button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text);
  showToast('Path copied to clipboard', 'info');
}

let lastExportedScheduleId = null;

async function exportAdditionalFormat(format) {
  if (!lastExportedScheduleId) {
    showToast('No schedule selected', 'error');
    return;
  }
  
  try {
    const result = await api(`/schedules/${lastExportedScheduleId}/export?format=${format}`, {
      method: 'POST'
    });
    showToast(`${format} exported to ${result.path}`, 'success');
    
    // Open the file if it's a text format
    if (format === 'setup_guide' || format === 'csv') {
      window.open(`/exports/${result.path.split('/').pop()}`, '_blank');
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function deleteSchedule(scheduleId) {
  if (!confirm('Delete this schedule?')) return;
  
  try {
    await api(`/schedules/${scheduleId}`, { method: 'DELETE' });
    showToast('Schedule deleted', 'success');
    loadSchedules();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// Library page
async function loadLibrary() {
  try {
    state.libraryStatus = await api('/library/status');
    renderLibrary();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function renderLibrary() {
  const container = document.getElementById('library-status');
  
  if (state.libraryStatus.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>Library not synced yet</p>
        <button class="btn btn-primary mt-2" onclick="syncLibrary()">Sync Library</button>
      </div>
    `;
    return;
  }
  
  container.innerHTML = state.libraryStatus.map(lib => `
    <div class="card mb-2">
      <div class="card-header">
        <h3 class="card-title">${lib.source.charAt(0).toUpperCase() + lib.source.slice(1)}</h3>
        <span class="text-sm text-muted">Last synced: ${formatDate(lib.last_synced)}</span>
      </div>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">${lib.total_series}</div>
          <div class="stat-label">Series</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${lib.total_movies}</div>
          <div class="stat-label">Movies</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${lib.total_episodes}</div>
          <div class="stat-label">Episodes</div>
        </div>
      </div>
    </div>
  `).join('');
}

async function syncLibrary() {
  try {
    showToast('Library sync started...', 'info');
    await api('/library/sync?source=all', { method: 'POST' });
    showToast('Sync in progress. Refresh in a moment.', 'success');
    setTimeout(loadLibrary, 3000);
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function searchLibrary() {
  const query = document.getElementById('library-search').value;
  if (query.length < 2) return;
  
  try {
    const results = await api(`/library/search?q=${encodeURIComponent(query)}`);
    const container = document.getElementById('search-results');
    
    if (results.length === 0) {
      container.innerHTML = '<p class="text-muted">No results found</p>';
      return;
    }
    
    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Series</th>
            <th>Episode</th>
            <th>Title</th>
            <th>Year</th>
            <th>Runtime</th>
            <th>Genre</th>
          </tr>
        </thead>
        <tbody>
          ${results.map(r => {
            const episodeNum = r.type === 'episode' && r.season_number != null 
              ? `S${String(r.season_number).padStart(2,'0')}E${String(r.episode_number || 0).padStart(2,'0')}`
              : '-';
            const displayTitle = r.type === 'episode' 
              ? (r.episode_title || r.title)
              : r.title;
            const seriesTitle = r.series_title || (r.type === 'movie' ? '-' : r.title);
            return `
              <tr>
                <td><span class="badge badge-${r.type === 'episode' ? 'info' : 'purple'}">${r.type}</span></td>
                <td><strong>${seriesTitle}</strong></td>
                <td class="font-mono">${episodeNum}</td>
                <td>${displayTitle}</td>
                <td>${r.year || '-'}</td>
                <td>${r.runtime_minutes} min</td>
                <td>${r.genres || '-'}</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
      <p class="text-muted text-sm mt-2">${results.length} result${results.length !== 1 ? 's' : ''} found</p>
    `;
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// Create Guide page
let presetsData = [];

async function loadCreatePage() {
  try {
    // Load presets
    const presets = await api('/sources/presets');
    presetsData = presets.presets;
    const presetSelect = document.getElementById('preset-select');
    presetSelect.innerHTML = '<option value="">Select a preset...</option>' +
      presetsData.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    
    // Load networks
    const networks = await api('/sources/networks');
    const networkSelect = document.getElementById('gen-network');
    networkSelect.innerHTML = '<option value="">Select network...</option>' +
      networks.networks.map(n => `<option value="${n}">${n}</option>`).join('');
    
    // Load genres
    const genres = await api('/sources/genres');
    const genreFilter = document.getElementById('shows-genre-filter');
    genreFilter.innerHTML = '<option value="">All Genres</option>' +
      genres.genres.map(g => `<option value="${g}">${g}</option>`).join('');
    
    // Load shows
    await filterShows();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function applyPreset() {
  const presetId = document.getElementById('preset-select').value;
  const descEl = document.getElementById('preset-description');
  
  if (!presetId) {
    descEl.style.display = 'none';
    return;
  }
  
  const preset = presetsData.find(p => p.id === presetId);
  if (!preset) return;
  
  // Show description
  descEl.textContent = `${preset.description} (${preset.year_range[0]}-${preset.year_range[1]})`;
  descEl.style.display = 'block';
  
  // Set network (use first available network from preset)
  const networkSelect = document.getElementById('gen-network');
  const availableNetwork = preset.networks.find(n => 
    Array.from(networkSelect.options).some(opt => opt.value === n)
  );
  
  if (availableNetwork) {
    networkSelect.value = availableNetwork;
    await loadNetworkYears();
    
    // Set recommended year
    const yearSelect = document.getElementById('gen-year');
    yearSelect.value = String(preset.recommended_year);
    await loadNetworkDays();
    
    // Set day
    const daySelect = document.getElementById('gen-day');
    daySelect.value = preset.day;
    
    // Update preview
    await updatePreview();
  }
  
  showToast(`Applied "${preset.name}" preset`, 'success');
}

async function loadNetworkYears() {
  const network = document.getElementById('gen-network').value;
  const yearSelect = document.getElementById('gen-year');
  const daySelect = document.getElementById('gen-day');
  
  // Preserve current selections
  const currentYear = yearSelect.value;
  const currentDay = daySelect.value;
  
  yearSelect.innerHTML = '<option value="">Select year...</option>';
  daySelect.innerHTML = '<option value="">Select day...</option>';
  yearSelect.disabled = true;
  daySelect.disabled = true;
  
  if (!network) return;
  
  try {
    const data = await api(`/sources/networks/${network}/years`);
    yearSelect.innerHTML = '<option value="">Select year...</option>' +
      data.years.map(y => `<option value="${y}">${y}</option>`).join('');
    yearSelect.disabled = false;
    
    // Try to restore previous year, or find closest match
    if (currentYear && data.years.includes(currentYear)) {
      yearSelect.value = currentYear;
      await loadNetworkDays(currentDay);
    } else if (currentYear) {
      // Find closest year
      const targetYear = parseInt(currentYear);
      const closest = data.years.reduce((prev, curr) => 
        Math.abs(parseInt(curr) - targetYear) < Math.abs(parseInt(prev) - targetYear) ? curr : prev
      );
      yearSelect.value = closest;
      await loadNetworkDays(currentDay);
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function loadNetworkDays(preserveDay = null) {
  const network = document.getElementById('gen-network').value;
  const year = document.getElementById('gen-year').value;
  const daySelect = document.getElementById('gen-day');
  
  // Preserve current day if not passed
  const currentDay = preserveDay || daySelect.value;
  
  daySelect.innerHTML = '<option value="">Select day...</option>';
  daySelect.disabled = true;
  
  if (!network || !year) return;
  
  try {
    const data = await api(`/sources/networks/${network}/${year}/days`);
    daySelect.innerHTML = '<option value="">Select day...</option>' +
      data.days.map(d => `<option value="${d}">${d.charAt(0).toUpperCase() + d.slice(1)}</option>`).join('');
    daySelect.disabled = false;
    
    // Try to restore previous day selection
    if (currentDay && data.days.includes(currentDay.toLowerCase())) {
      daySelect.value = currentDay.toLowerCase();
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function updatePreview() {
  const network = document.getElementById('gen-network').value;
  const year = document.getElementById('gen-year').value;
  const day = document.getElementById('gen-day').value;
  const fullDay = document.getElementById('gen-fullday').checked;
  const previewContainer = document.getElementById('schedule-preview');
  
  if (!network || !year || !day) {
    previewContainer.innerHTML = '<p class="text-muted">Select network, year, and day to see preview</p>';
    return;
  }
  
  previewContainer.innerHTML = '<p class="text-muted">Loading preview...</p>';
  
  try {
    const data = await api(`/sources/preview?network=${network}&year=${year}&day_of_week=${day}&full_day=${fullDay}`);
    
    if (!data.entries || data.entries.length === 0) {
      previewContainer.innerHTML = `<p class="text-muted">${data.message || 'No template available'}</p>`;
      return;
    }
    
    let totalMinutes = 0;
    data.entries.forEach(e => totalMinutes += e.duration_minutes);
    const hours = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    
    previewContainer.innerHTML = `
      <div class="mb-2" style="display:flex;gap:1rem;flex-wrap:wrap;">
        <span class="badge badge-purple">${network}</span>
        <span class="badge badge-info">${year}</span>
        <span class="badge badge-success">${day.charAt(0).toUpperCase() + day.slice(1)}</span>
        <span class="text-sm text-muted">${data.entry_count} shows • ${hours}h ${mins}m</span>
      </div>
      <div class="table-container" style="max-height:300px;overflow-y:auto;">
        <table>
          <thead>
            <tr>
              <th style="width:60px;">Time</th>
              <th>Title</th>
              <th style="width:50px;">Mins</th>
              <th style="width:80px;">Genre</th>
            </tr>
          </thead>
          <tbody>
            ${data.entries.map(e => `
              <tr>
                <td class="font-mono text-sm">${e.start_time}</td>
                <td><strong>${e.title}</strong></td>
                <td>${e.duration_minutes}</td>
                <td><span class="badge badge-gray">${e.genre || '-'}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (error) {
    previewContainer.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
  }
}

async function generateFromTemplate() {
  const network = document.getElementById('gen-network').value;
  const year = document.getElementById('gen-year').value;
  const day = document.getElementById('gen-day').value;
  const date = document.getElementById('gen-date').value;
  const fullDay = document.getElementById('gen-fullday').checked;
  
  if (!network || !year || !day) {
    showToast('Please select network, year, and day', 'error');
    return;
  }
  
  try {
    showToast('Generating schedule...', 'info');
    const result = await api('/sources/generate', {
      method: 'POST',
      body: JSON.stringify({
        network,
        year: parseInt(year),
        day_of_week: day,
        broadcast_date: date || null,
        full_day: fullDay
      })
    });
    
    showToast(`Generated: ${result.channel_name} with ${result.entry_count} entries`, 'success');
    navigateTo('guides');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function addCustomEntry() {
  const container = document.getElementById('custom-entries');
  const row = document.createElement('div');
  row.className = 'entry-row';
  row.style.cssText = 'display:flex;gap:0.5rem;margin-bottom:0.5rem;';
  row.innerHTML = `
    <input type="time" class="form-input entry-time" style="width:100px;" value="20:30">
    <input type="text" class="form-input entry-title" placeholder="Show title" style="flex:1;">
    <input type="number" class="form-input entry-duration" style="width:70px;" value="30" min="1">
    <select class="form-select entry-genre" style="width:100px;">
      <option value="">Genre</option>
      <option value="Comedy">Comedy</option>
      <option value="Drama">Drama</option>
      <option value="Action">Action</option>
      <option value="Sci-Fi">Sci-Fi</option>
      <option value="News">News</option>
      <option value="Movie">Movie</option>
    </select>
    <button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">×</button>
  `;
  container.appendChild(row);
}

async function buildCustomGuide() {
  const channel = document.getElementById('custom-channel').value;
  const date = document.getElementById('custom-date').value;
  
  if (!channel || !date) {
    showToast('Please enter channel name and date', 'error');
    return;
  }
  
  const rows = document.querySelectorAll('#custom-entries .entry-row');
  const entries = [];
  
  rows.forEach(row => {
    const time = row.querySelector('.entry-time').value;
    const title = row.querySelector('.entry-title').value;
    const duration = row.querySelector('.entry-duration').value;
    const genre = row.querySelector('.entry-genre').value;
    
    if (title) {
      entries.push({ time, title, duration: parseInt(duration), genre: genre || null });
    }
  });
  
  if (entries.length === 0) {
    showToast('Please add at least one entry', 'error');
    return;
  }
  
  try {
    showToast('Building guide...', 'info');
    const result = await api('/sources/build', {
      method: 'POST',
      body: JSON.stringify({
        channel_name: channel,
        broadcast_date: date,
        entries
      })
    });
    
    showToast(`Created: ${result.channel_name} with ${result.entry_count} entries`, 'success');
    navigateTo('guides');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function filterShows() {
  const genre = document.getElementById('shows-genre-filter').value;
  const network = document.getElementById('shows-network-filter').value;
  
  try {
    let url = '/sources/shows?';
    if (genre) url += `genre=${genre}&`;
    if (network) url += `network=${network}&`;
    
    const data = await api(url);
    const tbody = document.getElementById('shows-table-body');
    
    if (data.shows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted text-center">No shows found</td></tr>';
      return;
    }
    
    tbody.innerHTML = data.shows.map(s => `
      <tr>
        <td><strong>${s.title}</strong></td>
        <td><span class="badge badge-purple">${s.network}</span></td>
        <td>${s.years}</td>
        <td>${s.genre}</td>
        <td>${s.runtime} min</td>
        <td><button class="btn btn-sm btn-secondary" onclick="addShowToCustom('${s.title}', ${s.runtime}, '${s.genre}')">Add</button></td>
      </tr>
    `).join('');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function addShowToCustom(title, runtime, genre) {
  const container = document.getElementById('custom-entries');
  const lastRow = container.querySelector('.entry-row:last-child');
  const lastTime = lastRow ? lastRow.querySelector('.entry-time').value : '20:00';
  
  // Calculate next time slot
  const [hours, mins] = lastTime.split(':').map(Number);
  const lastDuration = lastRow ? parseInt(lastRow.querySelector('.entry-duration').value) : 0;
  let newHours = hours;
  let newMins = mins + lastDuration;
  if (newMins >= 60) {
    newHours += Math.floor(newMins / 60);
    newMins = newMins % 60;
  }
  const newTime = `${String(newHours).padStart(2,'0')}:${String(newMins).padStart(2,'0')}`;
  
  const row = document.createElement('div');
  row.className = 'entry-row';
  row.style.cssText = 'display:flex;gap:0.5rem;margin-bottom:0.5rem;';
  row.innerHTML = `
    <input type="time" class="form-input entry-time" style="width:100px;" value="${newTime}">
    <input type="text" class="form-input entry-title" style="flex:1;" value="${title}">
    <input type="number" class="form-input entry-duration" style="width:70px;" value="${runtime}" min="1">
    <select class="form-select entry-genre" style="width:100px;">
      <option value="">Genre</option>
      <option value="Comedy" ${genre === 'Comedy' ? 'selected' : ''}>Comedy</option>
      <option value="Drama" ${genre === 'Drama' ? 'selected' : ''}>Drama</option>
      <option value="Action" ${genre === 'Action' ? 'selected' : ''}>Action</option>
      <option value="Sci-Fi" ${genre === 'Sci-Fi' ? 'selected' : ''}>Sci-Fi</option>
      <option value="News" ${genre === 'News' ? 'selected' : ''}>News</option>
      <option value="Movie" ${genre === 'Movie' ? 'selected' : ''}>Movie</option>
    </select>
    <button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">×</button>
  `;
  container.appendChild(row);
  showToast(`Added "${title}" to custom guide`, 'success');
}

// Navigation
function navigateTo(page) {
  state.currentPage = page;
  
  document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
  document.getElementById(`page-${page}`).style.display = 'block';
  
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`[data-page="${page}"]`).classList.add('active');
  
  switch (page) {
    case 'dashboard': loadDashboard(); break;
    case 'guides': loadGuides(); break;
    case 'schedules': loadSchedules(); break;
    case 'library': loadLibrary(); break;
    case 'create': loadCreatePage(); break;
    case 'settings': loadSettings(); break;
  }
}

// Settings page
async function loadSettings() {
  try {
    const settings = await api('/settings');
    
    // Jellyfin
    document.getElementById('jellyfin-url').value = settings.jellyfin?.url || '';
    document.getElementById('jellyfin-user-id').value = settings.jellyfin?.user_id || '';
    const jellyfinStatus = document.getElementById('jellyfin-status');
    if (settings.jellyfin?.configured) {
      jellyfinStatus.textContent = 'Connected';
      jellyfinStatus.className = 'badge badge-green';
    } else {
      jellyfinStatus.textContent = 'Not configured';
      jellyfinStatus.className = 'badge badge-gray';
    }
    
    // Plex
    document.getElementById('plex-url').value = settings.plex?.url || '';
    const plexStatus = document.getElementById('plex-status');
    if (settings.plex?.configured) {
      plexStatus.textContent = 'Connected';
      plexStatus.className = 'badge badge-green';
    } else {
      plexStatus.textContent = 'Not configured';
      plexStatus.className = 'badge badge-gray';
    }
    
    // Matching
    document.getElementById('match-min-score').value = settings.matching?.min_score || 80;
    const titleWeight = (settings.matching?.title_weight || 0.8) * 100;
    document.getElementById('match-title-weight').value = titleWeight;
    updateWeightDisplay();
    
    // Export
    document.getElementById('export-dir').value = settings.export?.output_dir || './exports';
    document.getElementById('export-ersatztv').checked = settings.export?.ersatztv_format !== false;
    document.getElementById('export-tunarr').checked = settings.export?.tunarr_format !== false;
    
    // ErsatzTV
    document.getElementById('ersatztv-url').value = settings.ersatztv?.url || '';
    document.getElementById('ersatztv-enabled').checked = settings.ersatztv?.enabled || false;
    const ersatztvStatus = document.getElementById('ersatztv-status');
    if (settings.ersatztv?.configured) {
      ersatztvStatus.textContent = 'Configured';
      ersatztvStatus.className = 'badge badge-green';
    } else {
      ersatztvStatus.textContent = 'Not configured';
      ersatztvStatus.className = 'badge badge-gray';
    }
    
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function updateWeightDisplay() {
  const titleWeight = parseInt(document.getElementById('match-title-weight').value);
  document.getElementById('title-weight-val').textContent = titleWeight + '%';
  document.getElementById('year-weight-val').textContent = (100 - titleWeight) + '%';
}

async function testJellyfin() {
  const url = document.getElementById('jellyfin-url').value;
  const apiKey = document.getElementById('jellyfin-api-key').value;
  
  if (!url || !apiKey) {
    alert('Please enter URL and API key');
    return;
  }
  
  try {
    showToast('Testing connection...', 'info');
    const result = await api('/settings/jellyfin/test', {
      method: 'POST',
      body: JSON.stringify({ url, api_key: apiKey })
    });
    
    if (result.success) {
      alert(`✓ Connected to ${result.server_name} (v${result.version})`);
      showToast(`Connected to ${result.server_name} (v${result.version})`, 'success');
      document.getElementById('jellyfin-status').textContent = 'Connected';
      document.getElementById('jellyfin-status').className = 'badge badge-green';
    } else {
      alert(`✗ Connection failed: ${result.error}`);
      showToast(`Connection failed: ${result.error}`, 'error');
    }
  } catch (error) {
    alert(`✗ Error: ${error.message}`);
    showToast(error.message, 'error');
  }
}

async function saveJellyfin() {
  const url = document.getElementById('jellyfin-url').value;
  const apiKey = document.getElementById('jellyfin-api-key').value;
  const userId = document.getElementById('jellyfin-user-id').value;
  
  if (!url || !apiKey) {
    showToast('Please enter URL and API key', 'error');
    return;
  }
  
  try {
    await api('/settings/jellyfin', {
      method: 'POST',
      body: JSON.stringify({ url, api_key: apiKey, user_id: userId || null })
    });
    showToast('Jellyfin settings saved', 'success');
    loadSettings();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function testPlex() {
  const url = document.getElementById('plex-url').value;
  const token = document.getElementById('plex-token').value;
  
  if (!url || !token) {
    showToast('Please enter URL and token', 'error');
    return;
  }
  
  try {
    showToast('Testing connection...', 'info');
    const result = await api('/settings/plex/test', {
      method: 'POST',
      body: JSON.stringify({ url, token })
    });
    
    if (result.success) {
      showToast(`Connected to ${result.server_name} (v${result.version})`, 'success');
      document.getElementById('plex-status').textContent = 'Connected';
      document.getElementById('plex-status').className = 'badge badge-green';
    } else {
      showToast(`Connection failed: ${result.error}`, 'error');
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function savePlex() {
  const url = document.getElementById('plex-url').value;
  const token = document.getElementById('plex-token').value;
  
  if (!url || !token) {
    showToast('Please enter URL and token', 'error');
    return;
  }
  
  try {
    await api('/settings/plex', {
      method: 'POST',
      body: JSON.stringify({ url, token })
    });
    showToast('Plex settings saved', 'success');
    loadSettings();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function testErsatzTV() {
  const url = document.getElementById('ersatztv-url').value;
  
  if (!url) {
    showToast('Please enter ErsatzTV URL', 'error');
    return;
  }
  
  try {
    showToast('Testing ErsatzTV connection...', 'info');
    const result = await api('/settings/ersatztv/test', {
      method: 'POST',
      body: JSON.stringify({ url, enabled: true })
    });
    
    if (result.success) {
      showToast(`Connected! ${result.channels} channels, ${result.collections} collections`, 'success');
      document.getElementById('ersatztv-status').textContent = 'Connected';
      document.getElementById('ersatztv-status').className = 'badge badge-green';
      
      // Show info panel
      document.getElementById('ersatztv-info').style.display = 'block';
      document.getElementById('ersatztv-channels-count').textContent = result.channels;
      document.getElementById('ersatztv-playouts-count').textContent = result.playouts;
      document.getElementById('ersatztv-collections-count').textContent = result.collections;
    } else {
      showToast(`Connection failed: ${result.error}`, 'error');
      document.getElementById('ersatztv-info').style.display = 'none';
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function saveErsatzTV() {
  const url = document.getElementById('ersatztv-url').value;
  const enabled = document.getElementById('ersatztv-enabled').checked;
  
  try {
    await api('/settings/ersatztv', {
      method: 'POST',
      body: JSON.stringify({ url, enabled })
    });
    showToast('ErsatzTV settings saved', 'success');
    loadSettings();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function saveMatchingSettings() {
  const minScore = parseInt(document.getElementById('match-min-score').value);
  const titleWeight = parseInt(document.getElementById('match-title-weight').value) / 100;
  
  try {
    await api('/settings/matching', {
      method: 'POST',
      body: JSON.stringify({
        min_score: minScore,
        title_weight: titleWeight,
        year_weight: 1 - titleWeight
      })
    });
    showToast('Matching settings saved', 'success');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function saveExportSettings() {
  const outputDir = document.getElementById('export-dir').value;
  const ersatztv = document.getElementById('export-ersatztv').checked;
  const tunarr = document.getElementById('export-tunarr').checked;
  
  try {
    await api('/settings/export', {
      method: 'POST',
      body: JSON.stringify({
        output_dir: outputDir,
        ersatztv_format: ersatztv,
        tunarr_format: tunarr
      })
    });
    showToast('Export settings saved', 'success');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function scrapeGuide() {
  const source = document.getElementById('scrape-source').value;
  const network = document.getElementById('scrape-network').value;
  const year = parseInt(document.getElementById('scrape-year').value);
  const season = document.getElementById('scrape-season').value;
  
  const resultsDiv = document.getElementById('scrape-results');
  resultsDiv.innerHTML = '<p class="text-muted">Scraping... This may take a moment.</p>';
  
  try {
    const result = await api('/sources/scrape', {
      method: 'POST',
      body: JSON.stringify({ source, network, year, season })
    });
    
    if (result.success) {
      resultsDiv.innerHTML = `
        <div class="alert alert-success">
          <strong>Success!</strong> Found ${result.entry_count} entries for ${network} ${year} ${season}.
          <br><a href="#" onclick="navigateTo('guides'); return false;">View in Guides →</a>
        </div>
      `;
      showToast(`Scraped ${result.entry_count} entries`, 'success');
    } else {
      resultsDiv.innerHTML = `<div class="alert alert-error">Scraping failed: ${result.error}</div>`;
    }
  } catch (error) {
    resultsDiv.innerHTML = `<div class="alert alert-error">${error.message}</div>`;
    showToast(error.message, 'error');
  }
}

async function resetSettings() {
  if (!confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
    return;
  }
  
  try {
    await api('/settings/reset', { method: 'DELETE' });
    showToast('Settings reset to defaults', 'success');
    loadSettings();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// File drag & drop
function setupFileUpload() {
  const dropzone = document.getElementById('file-dropzone');
  const fileInput = document.getElementById('file-input');
  
  if (!dropzone) return;
  
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });
  
  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });
  
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) uploadGuide(file);
  });
  
  dropzone.addEventListener('click', () => fileInput.click());
  
  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) uploadGuide(fileInput.files[0]);
  });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setupFileUpload();
  navigateTo('dashboard');
});

// Expose functions to global scope for onclick handlers
window.navigateTo = navigateTo;
window.loadDashboard = loadDashboard;
window.loadGuides = loadGuides;
window.loadSchedules = loadSchedules;
window.loadLibrary = loadLibrary;
window.loadCreatePage = loadCreatePage;
window.loadSettings = loadSettings;
window.openImportModal = openImportModal;
window.closeImportModal = closeImportModal;
window.viewGuide = viewGuide;
window.closeViewGuideModal = closeViewGuideModal;
window.createScheduleFromGuide = createScheduleFromGuide;
window.deleteGuide = deleteGuide;
window.editGuideName = editGuideName;
window.cancelEditName = cancelEditName;
window.saveGuideName = saveGuideName;
window.viewSchedule = viewSchedule;
window.closeViewScheduleModal = closeViewScheduleModal;
window.exportSchedule = exportSchedule;
window.showExportInstructions = showExportInstructions;
window.copyToClipboard = copyToClipboard;
window.exportAdditionalFormat = exportAdditionalFormat;
window.deleteSchedule = deleteSchedule;
window.syncLibrary = syncLibrary;
window.searchLibrary = searchLibrary;
window.loadNetworkYears = loadNetworkYears;
window.loadNetworkDays = loadNetworkDays;
window.applyPreset = applyPreset;
window.generateFromTemplate = generateFromTemplate;
window.addCustomEntry = addCustomEntry;
window.buildCustomGuide = buildCustomGuide;
window.filterShows = filterShows;
window.addShowToCustom = addShowToCustom;
window.testJellyfin = testJellyfin;
window.saveJellyfin = saveJellyfin;
window.testPlex = testPlex;
window.savePlex = savePlex;
window.testErsatzTV = testErsatzTV;
window.saveErsatzTV = saveErsatzTV;
window.saveMatchingSettings = saveMatchingSettings;
window.saveExportSettings = saveExportSettings;
window.updateWeightDisplay = updateWeightDisplay;
window.scrapeGuide = scrapeGuide;
window.resetSettings = resetSettings;
