/*
 * World Revolution News – Offline-Speicher
 *
 * Große Datensätze und Übersetzungen werden in IndexedDB gespeichert.
 * Kleine Einstellungen und Lesezeichen dürfen weiterhin in localStorage bleiben.
 */
(() => {
    'use strict';

    const DB_NAME = 'world-revolution-news';
    const DB_VERSION = 1;
    const DATASET_STORE = 'datasets';
    const TRANSLATION_STORE = 'translations';

    let databasePromise = null;

    function openDatabase() {
        if (!('indexedDB' in window)) {
            return Promise.reject(new Error('IndexedDB wird von diesem Browser nicht unterstützt.'));
        }

        if (databasePromise) return databasePromise;

        databasePromise = new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onupgradeneeded = () => {
                const db = request.result;

                if (!db.objectStoreNames.contains(DATASET_STORE)) {
                    db.createObjectStore(DATASET_STORE, { keyPath: 'key' });
                }

                if (!db.objectStoreNames.contains(TRANSLATION_STORE)) {
                    const store = db.createObjectStore(TRANSLATION_STORE, { keyPath: 'key' });
                    store.createIndex('updatedAt', 'updatedAt', { unique: false });
                }
            };

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error || new Error('IndexedDB konnte nicht geöffnet werden.'));
            request.onblocked = () => reject(new Error('IndexedDB wird durch einen anderen geöffneten Tab blockiert.'));
        });

        return databasePromise;
    }

    async function runTransaction(storeName, mode, callback) {
        const db = await openDatabase();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction(storeName, mode);
            const store = transaction.objectStore(storeName);
            let result;

            try {
                result = callback(store);
            } catch (error) {
                transaction.abort();
                reject(error);
                return;
            }

            transaction.oncomplete = () => resolve(result);
            transaction.onerror = () => reject(transaction.error || new Error('IndexedDB-Transaktion fehlgeschlagen.'));
            transaction.onabort = () => reject(transaction.error || new Error('IndexedDB-Transaktion wurde abgebrochen.'));
        });
    }

    async function putDataset(key, data) {
        if (!key) throw new Error('Datensatzschlüssel fehlt.');
        await runTransaction(DATASET_STORE, 'readwrite', store => {
            store.put({ key, data, updatedAt: new Date().toISOString() });
        });
    }

    async function getDatasetRecord(key) {
        const db = await openDatabase();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction(DATASET_STORE, 'readonly');
            const request = transaction.objectStore(DATASET_STORE).get(key);
            request.onsuccess = () => resolve(request.result || null);
            request.onerror = () => reject(request.error || new Error('Datensatz konnte nicht gelesen werden.'));
        });
    }

    async function getDataset(key) {
        const record = await getDatasetRecord(key);
        return record?.data ?? null;
    }

    async function putTranslation(key, value) {
        if (!key) throw new Error('Übersetzungsschlüssel fehlt.');
        await runTransaction(TRANSLATION_STORE, 'readwrite', store => {
            store.put({ key, value, updatedAt: Date.now() });
        });
    }

    async function getTranslation(key) {
        const db = await openDatabase();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction(TRANSLATION_STORE, 'readonly');
            const request = transaction.objectStore(TRANSLATION_STORE).get(key);
            request.onsuccess = () => resolve(request.result?.value ?? null);
            request.onerror = () => reject(request.error || new Error('Übersetzung konnte nicht gelesen werden.'));
        });
    }


    async function getAllRecords(storeName) {
        const db = await openDatabase();
        return new Promise((resolve, reject) => {
            const transaction = db.transaction(storeName, 'readonly');
            const request = transaction.objectStore(storeName).getAll();
            request.onsuccess = () => resolve(Array.isArray(request.result) ? request.result : []);
            request.onerror = () => reject(request.error || new Error(`${storeName} konnte nicht gelesen werden.`));
        });
    }

    async function getAllDatasetRecords() {
        return getAllRecords(DATASET_STORE);
    }

    async function getAllTranslationRecords() {
        return getAllRecords(TRANSLATION_STORE);
    }

    async function clearStore(storeName) {
        const db = await openDatabase();
        return new Promise((resolve, reject) => {
            const transaction = db.transaction(storeName, 'readwrite');
            const request = transaction.objectStore(storeName).clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error || new Error(`${storeName} konnte nicht geleert werden.`));
        });
    }

    async function clearDatasets() {
        await clearStore(DATASET_STORE);
    }

    async function clearTranslations() {
        await clearStore(TRANSLATION_STORE);
    }

    async function replaceStoreRecords(storeName, records) {
        if (!Array.isArray(records)) throw new Error('Importdaten müssen eine Liste sein.');
        const safeRecords = records
            .filter(record => record && typeof record === 'object' && typeof record.key === 'string' && record.key.length <= 2000)
            .slice(0, 50000);
        const db = await openDatabase();
        return new Promise((resolve, reject) => {
            const transaction = db.transaction(storeName, 'readwrite');
            const store = transaction.objectStore(storeName);
            store.clear();
            safeRecords.forEach(record => store.put(record));
            transaction.oncomplete = () => resolve(safeRecords.length);
            transaction.onerror = () => reject(transaction.error || new Error(`${storeName} konnte nicht importiert werden.`));
            transaction.onabort = () => reject(transaction.error || new Error(`${storeName}-Import wurde abgebrochen.`));
        });
    }

    async function replaceDatasetRecords(records) {
        return replaceStoreRecords(DATASET_STORE, records);
    }

    async function replaceTranslationRecords(records) {
        return replaceStoreRecords(TRANSLATION_STORE, records);
    }

    function approximateBytes(value) {
        try {
            return new Blob([JSON.stringify(value)]).size;
        } catch {
            return 0;
        }
    }

    async function getStorageSummary() {
        const [datasets, translations] = await Promise.all([
            getAllDatasetRecords(),
            getAllTranslationRecords(),
        ]);
        return {
            datasetCount: datasets.length,
            translationCount: translations.length,
            datasetBytes: approximateBytes(datasets),
            translationBytes: approximateBytes(translations),
        };
    }

    async function clearAll() {
        const db = await openDatabase();
        const storeNames = [DATASET_STORE, TRANSLATION_STORE];

        await Promise.all(storeNames.map(storeName => new Promise((resolve, reject) => {
            const transaction = db.transaction(storeName, 'readwrite');
            const request = transaction.objectStore(storeName).clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error || new Error(`${storeName} konnte nicht geleert werden.`));
        })));
    }

    async function migrateLegacyLocalStorage() {
        const migrations = [
            ['news', 'cached_news_articles'],
            ['events', 'cached_event_data']
        ];

        for (const [datasetKey, oldKey] of migrations) {
            const existing = await getDataset(datasetKey).catch(() => null);
            if (Array.isArray(existing) && existing.length > 0) continue;

            try {
                const raw = localStorage.getItem(oldKey);
                if (!raw) continue;
                const parsed = JSON.parse(raw);
                if (!Array.isArray(parsed)) continue;
                await putDataset(datasetKey, parsed);
                localStorage.removeItem(oldKey);
            } catch (error) {
                console.warn(`Alter Cache ${oldKey} konnte nicht migriert werden:`, error);
            }
        }

        // Sehr alter gemeinsamer Cache: nur als Notfall migrieren.
        try {
            const oldCombinedRaw = localStorage.getItem('cached_news_data');
            if (oldCombinedRaw) {
                const oldCombined = JSON.parse(oldCombinedRaw);
                if (Array.isArray(oldCombined)) {
                    const news = oldCombined.filter(item => item?.kontinent !== 'Radar' && !(Array.isArray(item?.categories) && item.categories.includes('Radar')));
                    const events = oldCombined.filter(item => item?.kontinent === 'Radar' || (Array.isArray(item?.categories) && item.categories.includes('Radar')) || item?.sourceType === 'radar-api-meta');
                    const storedNews = await getDataset('news').catch(() => null);
                    const storedEvents = await getDataset('events').catch(() => null);
                    if ((!Array.isArray(storedNews) || storedNews.length === 0) && news.length) await putDataset('news', news);
                    if ((!Array.isArray(storedEvents) || storedEvents.length === 0) && events.length) await putDataset('events', events);
                }
                localStorage.removeItem('cached_news_data');
            }
        } catch (error) {
            console.warn('Alter kombinierter Cache konnte nicht migriert werden:', error);
        }
    }

    async function requestPersistentStorage() {
        if (!navigator.storage?.persist) return false;
        try {
            return await navigator.storage.persist();
        } catch {
            return false;
        }
    }

    window.WRNStorage = {
        openDatabase,
        putDataset,
        getDataset,
        getDatasetRecord,
        putTranslation,
        getTranslation,
        clearAll,
        clearDatasets,
        clearTranslations,
        getAllDatasetRecords,
        getAllTranslationRecords,
        replaceDatasetRecords,
        replaceTranslationRecords,
        getStorageSummary,
        migrateLegacyLocalStorage,
        requestPersistentStorage
    };
})();
