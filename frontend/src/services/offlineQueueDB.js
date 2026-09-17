// IndexedDB Offline Queue Service for NERIS Incidents
const DB_NAME = 'NERIS_Offline_DB';
const DB_VERSION = 1;
const STORE_NAME = 'incident_queue';

let dbPromise = null;

const initDB = () => {
  if (dbPromise) return dbPromise;

  dbPromise = new Promise((resolve, reject) => {
    if (!window.indexedDB) {
      console.warn('IndexedDB not supported in this browser. Falling back to memory queue.');
      resolve(null);
      return;
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'localQueueId' });
        store.createIndex('clientIncidentId', 'clientIncidentId', { unique: true });
        store.createIndex('status', 'status', { unique: false });
        store.createIndex('createdAt', 'createdAt', { unique: false });
      }
    };

    request.onsuccess = (event) => {
      resolve(event.target.result);
    };

    request.onerror = (event) => {
      console.error('IndexedDB open error:', event.target.error);
      resolve(null);
    };
  });

  return dbPromise;
};

export const offlineQueueDB = {
  // Add a new incident item to IndexedDB queue
  enqueueIncident: async (incidentPayload) => {
    const db = await initDB();
    const nowIso = new Date().toISOString();
    const localQueueId = `local_q_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    const clientIncidentId = incidentPayload.clientIncidentId || incidentPayload.id || `INC-CLI-${Date.now()}`;

    const queueItem = {
      localQueueId,
      clientIncidentId,
      payload: {
        ...incidentPayload,
        clientIncidentId,
        id: clientIncidentId
      },
      createdAt: nowIso,
      attemptCount: 0,
      status: 'PENDING SYNC',
      lastAttemptAt: null,
      error: null
    };

    if (!db) {
      // Memory/localStorage fallback if IndexedDB is unavailable
      const saved = JSON.parse(localStorage.getItem('ner_indexeddb_fallback_queue') || '[]');
      saved.unshift(queueItem);
      localStorage.setItem('ner_indexeddb_fallback_queue', JSON.stringify(saved));
      return queueItem;
    }

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const req = store.add(queueItem);

      req.onsuccess = () => resolve(queueItem);
      req.onerror = (e) => {
        console.error('IndexedDB enqueue error:', e.target.error);
        // If duplicate clientIncidentId, put (update) instead
        const putReq = store.put(queueItem);
        putReq.onsuccess = () => resolve(queueItem);
        putReq.onerror = () => reject(e.target.error);
      };
    });
  },

  // Get all queued incidents from IndexedDB
  getAllQueuedIncidents: async () => {
    const db = await initDB();

    if (!db) {
      const saved = JSON.parse(localStorage.getItem('ner_indexeddb_fallback_queue') || '[]');
      return saved;
    }

    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();

      req.onsuccess = () => {
        const items = req.result || [];
        // Sort newest createdAt first
        items.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        resolve(items);
      };
      req.onerror = () => resolve([]);
    });
  },

  // Update item in IndexedDB
  updateQueuedIncident: async (localQueueId, updates) => {
    const db = await initDB();

    if (!db) {
      const saved = JSON.parse(localStorage.getItem('ner_indexeddb_fallback_queue') || '[]');
      const updated = saved.map(item => item.localQueueId === localQueueId ? { ...item, ...updates } : item);
      localStorage.setItem('ner_indexeddb_fallback_queue', JSON.stringify(updated));
      return;
    }

    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const getReq = store.get(localQueueId);

      getReq.onsuccess = () => {
        const item = getReq.result;
        if (!item) {
          resolve(null);
          return;
        }
        const updatedItem = { ...item, ...updates };
        const putReq = store.put(updatedItem);
        putReq.onsuccess = () => resolve(updatedItem);
        putReq.onerror = (e) => reject(e.target.error);
      };
      getReq.onerror = (e) => reject(e.target.error);
    });
  },

  // Remove queued incident from IndexedDB upon successful sync
  removeQueuedIncident: async (localQueueId) => {
    const db = await initDB();

    if (!db) {
      const saved = JSON.parse(localStorage.getItem('ner_indexeddb_fallback_queue') || '[]');
      const filtered = saved.filter(item => item.localQueueId !== localQueueId);
      localStorage.setItem('ner_indexeddb_fallback_queue', JSON.stringify(filtered));
      return;
    }

    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const req = store.delete(localQueueId);
      req.onsuccess = () => resolve(true);
      req.onerror = () => resolve(false);
    });
  },

  // Clear all synced incidents
  clearSyncedIncidents: async () => {
    const db = await initDB();

    if (!db) {
      const saved = JSON.parse(localStorage.getItem('ner_indexeddb_fallback_queue') || '[]');
      const pending = saved.filter(item => item.status !== 'SYNCED');
      localStorage.setItem('ner_indexeddb_fallback_queue', JSON.stringify(pending));
      return;
    }

    const items = await offlineQueueDB.getAllQueuedIncidents();
    for (const item of items) {
      if (item.status === 'SYNCED') {
        await offlineQueueDB.removeQueuedIncident(item.localQueueId);
      }
    }
  }
};
