const startBtn = document.getElementById('startBtn');
const clearBtn = document.getElementById('clearBtn');
const downloadBtn = document.getElementById('downloadBtn');
const fileInput = document.getElementById('fileInput');
const manualUrls = document.getElementById('manualUrls');
const dropZone = document.getElementById('dropZone');
const fileInfo = document.getElementById('fileInfo');
const fileNameDisplay = document.getElementById('fileName');

const consoleBox = document.getElementById('console');
const progressBar = document.getElementById('progressBar');
const progressBadge = document.getElementById('progressBadge');
const resultsTableBody = document.querySelector('#resultsTable tbody');
const emptyState = document.getElementById('emptyState');

// Settings Elements
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeSettings = document.getElementById('closeSettings');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const modelSelect = document.getElementById('modelSelect');
const saveGemini = document.getElementById('saveGemini');
const saveMistral = document.getElementById('saveMistral');

let eventSource = null;
let uploadedUrls = [];

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    lucide.createIcons();
});

function log(message, type = 'system') {
    const line = document.createElement('div');
    line.className = `console-line ${type}`;
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    line.textContent = `[${time}] ${message}`;
    consoleBox.appendChild(line);
    consoleBox.scrollTop = consoleBox.scrollHeight;
}

window.switchTab = function(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    if (tab === 'upload') {
        document.getElementById('tabUpload').classList.add('active');
        document.getElementById('uploadSection').classList.add('active');
    } else {
        document.getElementById('tabPaste').classList.add('active');
        document.getElementById('pasteSection').classList.add('active');
    }
};

function updateProgress(index, total) {
    const percent = (index / total) * 100;
    progressBar.style.width = `${percent}%`;
    progressBadge.textContent = `${index}/${total} URLs`;
}

function addResultToTable(data) {
    emptyState.style.display = 'none';
    const row = document.createElement('tr');
    
    const emails = data.emails && data.emails.length > 0 ? data.emails.join(', ') : 'No emails found';
    const phones = data.phones && data.phones.length > 0 ? data.phones.join(', ') : 'No phones found';
    
    const statusPill = data.error ? '⚠️ Fallback' : '✅ AI Extracted';

    row.innerHTML = `
        <td class="row-url">${data.url}</td>
        <td><div class="row-business">${data.business_name || 'N/A'}</div></td>
        <td><div class="row-owner">${data.owner_name || 'N/A'}</div></td>
        <td><div class="row-contacts">📧 ${emails}</div></td>
        <td><div class="row-contacts">📞 ${phones}</div></td>
        <td><div class="row-contacts">📍 ${data.address || 'N/A'}</div></td>
        <td>
            <span class="status-pill">${statusPill}</span>
        </td>
    `;
    
    resultsTableBody.appendChild(row);
    lucide.createIcons(); // Re-initialize icons for new rows
}



// Settings Logic
function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('extractorSettings') || '{}');
    if (modelSelect) modelSelect.value = settings.activeModel || 'gemini/gemini-2.5-flash';
    if (saveMistral) saveMistral.value = settings.mistral || '';
    if (saveGemini) saveGemini.value = settings.gemini || '';
}

function saveSettings() {
    const settings = {
        activeModel: modelSelect.value,
        mistral: saveMistral.value.trim(),
        gemini: saveGemini.value.trim()
    };
    localStorage.setItem('extractorSettings', JSON.stringify(settings));
    log('Settings updated successfully.', 'success');
    settingsModal.style.display = 'none';
}

function getActiveKey() {
    const settings = JSON.parse(localStorage.getItem('extractorSettings') || '{}');
    const model = modelSelect.value;
    if (model.startsWith('mistral')) return settings.mistral;
    if (model.startsWith('gemini')) return settings.gemini;
    return null;
}

// File Upload Logic
function handleFile(file) {
    if (!file || !file.name.endsWith('.txt')) {
        log('Error: Please upload a valid .txt file.', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target.result;
        uploadedUrls = text.split('\n').map(u => u.trim()).filter(u => u);
        
        if (uploadedUrls.length > 0) {
            fileNameDisplay.textContent = `${file.name} (${uploadedUrls.length} URLs)`;
            fileInfo.style.display = 'flex';
            log(`Loaded ${uploadedUrls.length} URLs from ${file.name}`, 'success');
        } else {
            log('Error: The file is empty.', 'error');
        }
    };
    reader.readAsText(file);
}

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    handleFile(file);
});

fileInput.addEventListener('change', (e) => {
    handleFile(e.target.files[0]);
});

clearBtn.addEventListener('click', () => {
    uploadedUrls = [];
    manualUrls.value = '';
    fileInfo.style.display = 'none';
    resultsTableBody.innerHTML = '';
    emptyState.style.display = 'block';
    progressBar.style.width = '0%';
    progressBadge.textContent = 'Idle';
    log('Dashboard cleared.', 'system');
});

settingsBtn.addEventListener('click', () => {
    loadSettings();
    settingsModal.style.display = 'flex';
});

closeSettings.addEventListener('click', () => {
    settingsModal.style.display = 'none';
});

saveSettingsBtn.addEventListener('click', saveSettings);

startBtn.addEventListener('click', async () => {
    const apiKey = getActiveKey();
    const model = modelSelect.value;

    let urlsToProcess = [];
    const isPasteTab = document.getElementById('tabPaste').classList.contains('active');
    
    if (isPasteTab) {
        urlsToProcess = manualUrls.value.split('\n').map(u => u.trim()).filter(u => u);
    } else {
        urlsToProcess = uploadedUrls;
    }

    if (!apiKey) {
        log(`Error: No API key found for ${model}. Please check Settings.`, 'error');
        return;
    }

    if (urlsToProcess.length === 0) {
        log('Error: No URLs found. Please upload a file or paste websites.', 'error');
        return;
    }

    // Reset UI for run
    resultsTableBody.innerHTML = '';
    emptyState.style.display = 'block';
    log(`Starting extraction with ${model}...`, 'system');
    startBtn.disabled = true;
    clearBtn.disabled = true;
    downloadBtn.disabled = true;

    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                urls: urlsToProcess, 
                api_key: apiKey,
                model: model 
            })
        });

        if (!response.ok) throw new Error('Failed to connect to server.');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.replace('data: ', ''));
                    
                    if (data.type === 'progress') {
                        const status = data.status;
                        let logType = 'progress';
                        if (status.includes('Fetched')) logType = 'success';
                        if (status.includes('Error')) logType = 'error';
                        
                        log(`${data.url}: ${status}`, logType);
                        updateProgress(data.index, data.total);
                    } else if (data.type === 'result') {
                        log(`Done: ${data.data.url}`, 'success');
                        addResultToTable(data.data);
                    } else if (data.type === 'complete') {
                        log('Extraction complete!', 'success');
                        startBtn.disabled = false;
                        clearBtn.disabled = false;
                        downloadBtn.disabled = false;
                        progressBadge.textContent = 'Complete';
                    }
                }
            }
        }
    } catch (err) {
        log(`Error: ${err.message}`, 'error');
        startBtn.disabled = false;
        clearBtn.disabled = false;
    }
});

downloadBtn.addEventListener('click', () => {
    window.location.href = '/api/download';
});
