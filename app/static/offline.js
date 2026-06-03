// Offline data capture using IndexedDB
// Stores form submissions when offline, syncs when back online

const DB_NAME = 'sda-offline';
const DB_VERSION = 1;
const STORE_NAME = 'pending-sync';
const SYNC_URL = '/auth/api/sync';

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function saveOffline(data) {
  const db = await openDB();
  const tx = db.transaction(STORE_NAME, 'readwrite');
  tx.objectStore(STORE_NAME).add({ ...data, timestamp: new Date().toISOString() });
  return new Promise((resolve, reject) => { tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); });
}

async function getPendingItems() {
  const db = await openDB();
  const tx = db.transaction(STORE_NAME, 'readonly');
  const req = tx.objectStore(STORE_NAME).getAll();
  return new Promise((resolve, reject) => { req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error); });
}

async function clearPending(id) {
  const db = await openDB();
  const tx = db.transaction(STORE_NAME, 'readwrite');
  tx.objectStore(STORE_NAME).delete(id);
  return new Promise((resolve, reject) => { tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); });
}

async function syncPendingItems() {
  const items = await getPendingItems();
  if (items.length === 0) return 0;
  try {
    const resp = await fetch(SYNC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: items.map(i => ({ url: i.url, payload: i.payload })) })
    });
    if (resp.ok) {
      for (const item of items) await clearPending(item.id);
      return items.length;
    }
  } catch (e) { /* still offline */ }
  return 0;
}

// Watch for connectivity changes
let syncInterval = null;
function startSyncWatcher() {
  if (syncInterval) return;
  syncInterval = setInterval(async () => {
    if (navigator.onLine) {
      const pending = await getPendingItems();
      if (pending.length > 0) {
        const synced = await syncPendingItems();
        if (synced > 0) {
          updateOfflineBadge();
          showToast(`Synced ${synced} offline record(s)`, 'success');
        }
      }
    }
  }, 15000);
}

function showToast(msg, type) {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} position-fixed bottom-0 end-0 m-3 shadow`;
  toast.style.zIndex = '9999';
  toast.innerHTML = `<i class="bi bi-${type === 'success' ? 'cloud-upload' : 'cloud-download'} me-1"></i>${msg}`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

async function updateOfflineBadge() {
  const pending = await getPendingItems();
  const badge = document.getElementById('offline-badge');
  const countEl = document.getElementById('offline-count');
  if (!badge) return;
  if (pending.length > 0) {
    badge.classList.remove('d-none');
    if (countEl) countEl.textContent = pending.length;
  } else {
    badge.classList.add('d-none');
  }
}

// Intercept form submissions when offline
document.addEventListener('submit', async (e) => {
  if (navigator.onLine) return;
  const form = e.target;
  const action = form.getAttribute('action');
  if (!action) return;
  const capturePaths = ['/members/add', '/finances/tithe/add', '/finances/offering/add',
    '/baptisms/add', '/events/add', '/sabbath-school/attendance/'];
  if (!capturePaths.some(p => action.includes(p))) return;

  e.preventDefault();
  const formData = new FormData(form);
  const payload = {};
  formData.forEach((v, k) => payload[k] = v);
  await saveOffline({ url: action, payload });
  updateOfflineBadge();
  showToast('Saved offline. Will sync when connected.', 'warning');
});

// Register service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/sw.js').catch(() => {});
}

startSyncWatcher();
updateOfflineBadge();
