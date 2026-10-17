let settings = {};
const cloud = 'https://proofmesh-2god3tua3a-el.a.run.app';
const $ = id => document.getElementById(id);
function showToken() { document.querySelector('a').href=$('origin').value==='cloud'?cloud:'http://127.0.0.1:8000/'; $('token').value = $('origin').value === 'cloud' ? settings.cloudToken || '' : settings.apiToken || ''; }
chrome.storage.local.get(['enabled','apiToken','cloudToken','apiOrigin']).then(s => { settings=s; $('enabled').checked=Boolean(s.enabled); $('origin').value=s.apiOrigin || 'local'; showToken(); });
$('origin').addEventListener('change', showToken);
$('save').addEventListener('click', async () => { const key=$('origin').value==='cloud'?'cloudToken':'apiToken'; settings[key]=$('token').value.trim(); await chrome.storage.local.set({enabled:$('enabled').checked, apiOrigin:$('origin').value,[key]:settings[key]}); $('status').textContent='Saved. Using '+($('origin').value==='cloud'?cloud:'http://127.0.0.1:8000')+'. Reload the feed after changing servers.'; });
