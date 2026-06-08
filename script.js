/* ============================================================================
   TRACEROOT - JAVASCRIPT (CLIENT-SIDE)
   ============================================================================ */

let allBugs = [];
let currentBugId = null;

/**
 * Helper function to get date parameters from URL or document context
 */
function getDateParameters() {
    const params = new URLSearchParams(window.location.search);
    let startDate = params.get('start_date');
    let endDate = params.get('end_date');
    let month = params.get('month') || '1';
    
    // Validate date values
    if (!startDate || startDate === 'None' || startDate === '') startDate = null;
    if (!endDate || endDate === 'None' || endDate === '') endDate = null;
    if (!month || month === 'None' || month === '') month = null;
    
    console.log('Date parameters:', { startDate, endDate, month });
    
    return { startDate, endDate, month };
}

/**
 * Render all bugs in the grid
 */
function renderBugs(bugs) {
    const grid = document.getElementById('bugGrid');
    
    if (!grid) return; // Not on results page
    
    if (bugs.length === 0) {
        grid.innerHTML = '<div class="no-results" style="grid-column: 1 / -1;">No bugs found for this date range.</div>';
        return;
    }
    
    // Group bugs and incidents
    const bugsList = bugs.filter(b => b.type === 'bugs' || !b.type);
    const incidentsList = bugs.filter(b => b.type === 'incidents');
    
    let html = '';
    
    if (bugsList.length > 0) {
        html += '<div style="grid-column: 1 / -1; font-size: 18px; font-weight: bold; color: #0ea5e9; margin-top: 20px; margin-bottom: 10px;">🐞 Bugs</div>';
        html += bugsList.map(bug => `
            <div class="bug-card" onclick="showBugModal('${bug.bug_id}')">
                <div class="bug-id">${bug.bug_id}</div>
                <div class="bug-title">${bug.title}</div>
                <div class="bug-meta">
                    <span class="badge status-${bug.status.toLowerCase().replace(' ', '-')}">${bug.status}</span>
                    <span class="badge priority-${bug.priority.toLowerCase()}">${bug.priority}</span>
                </div>
                <div class="right-content">
                    <span class="assigned">👤 ${bug.assigned_to}</span>
                </div>
            </div>
        `).join('');
    }
    
    if (incidentsList.length > 0) {
        html += '<div style="grid-column: 1 / -1; font-size: 18px; font-weight: bold; color: #ef4444; margin-top: 20px; margin-bottom: 10px;">🚨 Incidents</div>';
        html += incidentsList.map(incident => `
            <div class="bug-card" onclick="showBugModal('${incident.bug_id}')">
                <div class="bug-id">${incident.bug_id}</div>
                <div class="bug-title">${incident.title}</div>
                <div class="bug-meta">
                    <span class="badge status-${incident.status.toLowerCase().replace(' ', '-')}">${incident.status}</span>
                    <span class="badge priority-${incident.priority.toLowerCase()}">${incident.priority}</span>
                </div>
                <div class="right-content">
                    <span class="assigned">👤 ${incident.assigned_to}</span>
                </div>
            </div>
        `).join('');
    }
    
    grid.innerHTML = html;
}

/**
 * Update statistics display
 */
function updateStats(bugs) {
    const total = bugs.length;
    const critical = bugs.filter(b => b.priority === 'P1' || b.priority === 'CRITICAL').length;
    const high = bugs.filter(b => b.priority === 'P2' || b.priority === 'HIGH').length;
    const resolved = bugs.filter(b => b.status === 'Resolved' || b.status === 'RESOLVED').length;
    
    const totalEl = document.getElementById('totalCount');
    const criticalEl = document.getElementById('criticalCount');
    const highEl = document.getElementById('highCount');
    const resolvedEl = document.getElementById('resolvedCount');
    
    if (totalEl) totalEl.textContent = total;
    if (criticalEl) criticalEl.textContent = critical;
    if (highEl) highEl.textContent = high;
    if (resolvedEl) resolvedEl.textContent = resolved;
}

/**
 * Live search filter
 */
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const query = this.value.toLowerCase();
            const filtered = allBugs.filter(bug => 
                bug.bug_id.toLowerCase().includes(query) ||
                bug.title.toLowerCase().includes(query)
            );
            renderBugs(filtered);
        });
    }
});

/**
 * Show bug details modal
 */
function showBugModal(bugId) {
    currentBugId = bugId;
    const bug = allBugs.find(b => b.bug_id === bugId);
    
    if (!bug) return;
    
    // Populate modal with bug data
    const modalBugId = document.getElementById('modalBugId');
    const modalStatus = document.getElementById('modalStatus');
    const modalPriority = document.getElementById('modalPriority');
    const modalSeverity = document.getElementById('modalSeverity');
    const modalAssigned = document.getElementById('modalAssigned');
    const modalDate = document.getElementById('modalDate');
    const modalEnv = document.getElementById('modalEnv');
    const modalTitle = document.getElementById('modalTitle');
    const modalDescription = document.getElementById('modalDescription');
    const modalRepro = document.getElementById('modalRepro');
    
    if (modalBugId) modalBugId.textContent = bug.bug_id;
    if (modalStatus) modalStatus.textContent = bug.status;
    if (modalPriority) modalPriority.textContent = bug.priority;
    if (modalSeverity) modalSeverity.textContent = bug.severity + ' - ' + (bug.severity === 1 ? 'High' : bug.severity === 2 ? 'Medium' : 'Low');
    if (modalAssigned) modalAssigned.textContent = bug.assigned_to;
    if (modalDate) modalDate.textContent = bug.created_date;
    if (modalEnv) modalEnv.textContent = bug.environment;
    if (modalTitle) modalTitle.textContent = bug.title;
    if (modalDescription) modalDescription.textContent = bug.description;
    if (modalRepro) modalRepro.textContent = bug.repro_steps;
    
    // Show modal
    const modal = document.getElementById('bugModal');
    if (modal) {
        modal.classList.add('active');
    }
    
    // Fetch and display RCA
    generateRCA(bugId);
}

/**
 * Close bug details modal
 */
function closeBugModal() {
    const modal = document.getElementById('bugModal');
    if (modal) {
        modal.classList.remove('active');
    }
    currentBugId = null;
}

/**
 * Close modal when clicking outside
 */
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('bugModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeBugModal();
            }
        });
    }
});

/**
 * Generate and fetch RCA from backend
 */
function generateRCA(bugId) {
    const rcaDiv = document.getElementById('modalRCA');
    if (!rcaDiv) return;
    // If the modal already shows this bug's RCA, skip fetch
    if (rcaDiv.dataset.bugId === bugId && rcaDiv.classList.contains('rca-content') && rcaDiv.innerHTML.trim() !== '') {
        console.log('✅ Skipping fetch: RCA already displayed for bug', bugId);
        return;
    }

    // mark which bug the div is showing so subsequent opens fetch correctly
    rcaDiv.dataset.bugId = bugId;

    // If we already have RCAs from a bulk generation stored on the window, use them
    if (window.RCA_CACHE && window.RCA_CACHE[bugId]) {
        console.log('✅ Using cached RCA for bug', bugId);
        const data = { rca: window.RCA_CACHE[bugId] };
        // Reuse parsing/display logic below by simulating fetch resolution
        const rawRca = (data.rca || '').replace(/\r\n|\r/g, '\n');
        displayRcaFromRaw(rawRca, rcaDiv);
        return;
    }

    console.log('📡 Fetching RCA from backend for bug', bugId);
    rcaDiv.textContent = 'Generating RCA using Ollama...';
    rcaDiv.className = 'rca-loading';

    const encodedBugId = encodeURIComponent(bugId);
    fetch(`/api/rca/${encodedBugId}`)
        .then(r => r.json())
        .then(data => {
            const rawRca = (data.rca || '').replace(/\r\n|\r/g, '\n');
            displayRcaFromRaw(rawRca, rcaDiv);
        })
        .catch(err => {
            rcaDiv.textContent = 'Error generating RCA: ' + err.message;
            rcaDiv.className = 'rca-content';
        });
}

/**
 * Parse raw RCA text and render into the given element
 */
function displayRcaFromRaw(rawRca, rcaDiv) {
    const escapeHtml = (text) => text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Parse headings into structured fields
    function parseSections(text) {
        const t = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        const regex = /^(bug\s*type|classification|rca|root\s*cause(?:\s*analysis)?|resolution|recommendation)\s*[:\-–]\s*/gim;
        let m;
        const matches = [];
        while ((m = regex.exec(t)) !== null) {
            matches.push({ name: m[1].toLowerCase(), index: m.index, end: regex.lastIndex });
        }

        const out = { bug_type: '', rca: '', recommendation: '' };
        if (matches.length) {
            for (let i = 0; i < matches.length; i++) {
                const start = matches[i].end;
                const end = (i + 1 < matches.length) ? matches[i + 1].index : t.length;
                const val = t.substring(start, end).trim();
                const key = matches[i].name;
                if (key.includes('bug') || key.includes('classification')) out.bug_type = val;
                else if (key === 'rca' || key.startsWith('root')) out.rca = val;
                else if (key === 'resolution' || key === 'recommendation') out.recommendation = val;
            }
        } else {
            // Fallback: split by double newline
            const parts = t.split(/\n\n+/).map(p => p.trim()).filter(Boolean);
            if (parts.length === 1) out.rca = parts[0];
            else if (parts.length === 2) { out.bug_type = parts[0]; out.rca = parts[1]; }
            else if (parts.length >= 3) { out.bug_type = parts[0]; out.rca = parts[1]; out.recommendation = parts[2]; }
        }
        return out;
    }

    function truncateSentences(text, max) {
        if (!text) return '';
        const sentences = text.match(/[^.!?]+[.!?]*/g) || [text];
        return sentences.slice(0, max).join(' ').trim();
    }

    const sections = parseSections(rawRca);
    let bugType = sections.bug_type || '';
    const rcaText = truncateSentences(sections.rca || rawRca, 4);  // 4 sentences = 2-3 lines

    // Fallback: ensure bug_type is never empty
    if (!bugType) {
        bugType = 'Functional Bug';
    }

    const parts = [];
    parts.push(`<strong>BUG TYPE</strong><br>${escapeHtml(bugType)}`);
    if (rcaText) {
        parts.push(`<strong>RCA</strong><br>${escapeHtml(rcaText)}`);
    } else {
        // Fallback RCA if nothing could be extracted
        parts.push(`<strong>RCA</strong><br>${escapeHtml(truncateSentences(rawRca, 4) || 'RCA analysis not available')}`);
    }

    rcaDiv.innerHTML = parts.join('<br><br>');
    rcaDiv.className = 'rca-content';
    console.log('✅ RCA displayed:', parts.length, 'sections');
}

/**
 * Generate RCA for all bugs in the selected month
 */
function generateAllRCAs() {
    const generateBtn = document.getElementById('generateBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const dateParams = getDateParameters();
    
    // Collect visible bug IDs from the grid to ensure we generate for exactly those bugs
    const visibleIds = Array.from(document.querySelectorAll('#bugGrid .bug-card .bug-id'))
        .map(el => el.textContent.trim())
        .filter(Boolean);
    
    // Show loading spinner and disable button
    console.log('🚀 Generating RCAs for', visibleIds.length, 'visible bugs:', visibleIds);
    loadingSpinner.classList.remove('hidden');
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating RCAs...';
    
    // Prepare request data based on date range or month
    const requestData = { ids: visibleIds };
    if (dateParams.startDate && dateParams.endDate) {
        requestData.start_date = dateParams.startDate;
        requestData.end_date = dateParams.endDate;
    } else {
        requestData.month = dateParams.month;
    }
    
    fetch('/api/generate-all-rcas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update RCA_CACHE with generated or cached RCAs
            if (data.results) {
                window.RCA_CACHE = window.RCA_CACHE || {};
                data.results.forEach(result => {
                    if (result.rca) {
                        window.RCA_CACHE[result.bug_id] = result.rca;
                    }
                });
                console.log('✅ RCA_CACHE populated with', Object.keys(window.RCA_CACHE).length, 'RCAs:', window.RCA_CACHE);
            }

            // Hide loading spinner and restore button
            loadingSpinner.classList.add('hidden');
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate RCA';

            // Show total RCA count from visible bugs
            const bugCount = document.querySelectorAll('#bugGrid .bug-card').length;
            showNotification(`Generated RCA: ${bugCount}. Click on bug to view!`, 'success');
        }
    })
    .catch(err => {
        console.error('Error:', err);
        loadingSpinner.classList.add('hidden');
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate RCA';
        showNotification('Error generating RCAs. Please try again.', 'error');
    });
}

/**
 * Export RCA data to Excel
 */
function exportToExcel() {
    const dateParams = getDateParameters();
    const exportBtn = document.getElementById('exportBtn');
    exportBtn.disabled = true;
    exportBtn.textContent = 'Exporting...';
    
    // Get all visible bug and incident IDs from the page
    const allIds = allBugs.map(b => b.bug_id);
    
    if (allIds.length === 0) {
        exportBtn.disabled = false;
        exportBtn.textContent = 'Export to Excel';
        showNotification('No items to export', 'error');
        return;
    }
    
    // Prepare export data with explicit IDs from current page
    const exportData = {
        ids: allIds,
        start_date: dateParams.startDate,
        end_date: dateParams.endDate
    };
    
    fetch('/api/export-rcas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Export failed');
            });
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Generate filename based on date range
        if (dateParams.startDate && dateParams.endDate) {
            a.download = `Bug_Report_${dateParams.startDate}_to_${dateParams.endDate}.xlsx`;
        } else {
            a.download = `Bug_Report.xlsx`;
        }
        
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        exportBtn.disabled = false;
        exportBtn.textContent = 'Export to Excel';
        showNotification('Excel file exported successfully! (' + allIds.length + ' items exported)', 'success');
    })
    .catch(err => {
        console.error('Error:', err);
        exportBtn.disabled = false;
        exportBtn.textContent = 'Export to Excel';
        showNotification('Error exporting data: ' + err.message, 'error');
    });
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

/**
 * Initialize event listeners for Generate and Export buttons
 */
document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generateBtn');
    const exportBtn = document.getElementById('exportBtn');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', generateAllRCAs);
    }
    
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToExcel);
    }
});