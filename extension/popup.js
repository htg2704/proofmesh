chrome.storage.local.get(['enabled', 'apiToken']).then(s => { document.getElementById('enabled').checked = Boolean(s.enabled); document.getElementById('token').value = s.apiToken || ''; });
document.getElementById('save').addEventListener('click', async () => { await chrome.storage.local.set({ enabled: document.getElementById('enabled').checked, apiToken: document.getElementById('token').value }); document.getElementById('status').textContent = 'Saved. The extension uses http://127.0.0.1:8000.'; });

