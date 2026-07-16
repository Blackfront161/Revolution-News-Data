/* World Revolution News – Datenschutz, Datensicherung und lokale Datenkontrolle */
'use strict';

(() => {
    const BACKUP_FORMAT = 'world-revolution-news-backup';
    const BACKUP_VERSION = 1;
    const MAX_IMPORT_BYTES = 50 * 1024 * 1024;
    const EXCLUDED_EXPORT_KEYS = new Set(['wrn_client_id']);

    const texts = {
        en: {
            button: '🔐 Data', title: 'Privacy & local data',
            intro: 'World Revolution News does not require an account. This panel shows and manages data stored by this browser for the app.',
            overview: 'Local overview', bookmarks: 'Read later', read: 'Read articles', audio: 'Audio entries',
            translations: 'Stored translations', offline: 'Offline datasets', localEntries: 'Local settings',
            storage: 'Browser storage', persistent: 'Persistent storage', persistentYes: 'granted', persistentNo: 'not granted', persistentUnknown: 'unknown',
            backup: 'Backup', backupHint: 'The backup is created locally in your browser. Server-side Cloudflare, Azure and R2 secrets are never included.',
            includeOffline: 'Include offline news and events', includeTranslations: 'Include stored translations',
            export: 'Export backup', import: 'Import backup',
            deleteTitle: 'Delete selected app data', deleteReading: 'Delete reading data', deleteAudio: 'Delete audio data',
            deleteTranslations: 'Delete translations', deleteOffline: 'Delete offline data', deleteInterface: 'Reset interface settings', deleteAll: 'Delete all app data',
            externalTitle: 'External connections', externalHint: 'This list explains when the browser may contact external providers. It is not a live network log.',
            external: [
                ['GitHub Pages', 'Loads news, events, source information and the app files.'],
                ['Cloudflare Worker', 'Contacted for translations and generated podcast functions.'],
                ['Microsoft Azure Speech', 'Contacted through the Worker only when a natural-voice podcast is generated.'],
                ['Podcast and radio providers', 'Contacted only after a stream is played.'],
                ['Article sources and images', 'May be contacted when images load or an original article is opened.'],
                ['PayPal', 'Contacted only after the PayPal link is opened.']
            ],
            close: 'Close', refresh: 'Refresh', ready: 'Ready.', working: 'Working…', exported: 'Backup downloaded.',
            imported: 'Backup imported. The app will reload.', importInvalid: 'This file is not a valid World Revolution News backup.',
            importLarge: 'The selected backup is too large.', importConfirm: 'Import this backup? Matching local app data will be replaced.',
            clearConfirm: 'Delete the selected local app data?', cleared: 'Selected data deleted.', clearFailed: 'Data could not be fully deleted.',
            exportFailed: 'Backup could not be created.', importFailed: 'Backup could not be imported.', noIndexedDb: 'IndexedDB unavailable',
            items: 'items', bytes: 'bytes'
        },
        de: {
            button: '🔐 Daten', title: 'Datenschutz & lokale Daten',
            intro: 'World Revolution News benötigt kein Konto. Hier siehst und verwaltest du Daten, die dieser Browser für die App speichert.',
            overview: 'Lokale Übersicht', bookmarks: 'Später lesen', read: 'Gelesene Artikel', audio: 'Audio-Einträge',
            translations: 'Gespeicherte Übersetzungen', offline: 'Offline-Datensätze', localEntries: 'Lokale Einstellungen',
            storage: 'Browser-Speicher', persistent: 'Dauerhafter Speicher', persistentYes: 'gewährt', persistentNo: 'nicht gewährt', persistentUnknown: 'unbekannt',
            backup: 'Datensicherung', backupHint: 'Die Sicherung wird lokal im Browser erzeugt. Serverseitige Cloudflare-, Azure- und R2-Secrets werden niemals aufgenommen.',
            includeOffline: 'Offline-Nachrichten und Events einschließen', includeTranslations: 'Gespeicherte Übersetzungen einschließen',
            export: 'Sicherung exportieren', import: 'Sicherung importieren',
            deleteTitle: 'Ausgewählte App-Daten löschen', deleteReading: 'Lesedaten löschen', deleteAudio: 'Audiodaten löschen',
            deleteTranslations: 'Übersetzungen löschen', deleteOffline: 'Offline-Daten löschen', deleteInterface: 'Oberfläche zurücksetzen', deleteAll: 'Alle App-Daten löschen',
            externalTitle: 'Externe Verbindungen', externalHint: 'Diese Liste erklärt, wann der Browser externe Anbieter kontaktieren kann. Sie ist kein Live-Netzwerkprotokoll.',
            external: [
                ['GitHub Pages', 'Lädt Nachrichten, Events, Quelleninformationen und die App-Dateien.'],
                ['Cloudflare Worker', 'Wird für Übersetzungen und erzeugte Podcast-Funktionen kontaktiert.'],
                ['Microsoft Azure Speech', 'Wird über den Worker nur beim Erzeugen eines Podcasts mit natürlicher Stimme kontaktiert.'],
                ['Podcast- und Radioanbieter', 'Werden erst beim Abspielen eines Streams kontaktiert.'],
                ['Artikelquellen und Bilder', 'Können beim Laden von Bildern oder Öffnen eines Originalartikels kontaktiert werden.'],
                ['PayPal', 'Wird erst nach dem Öffnen des PayPal-Links kontaktiert.']
            ],
            close: 'Schließen', refresh: 'Neu zählen', ready: 'Bereit.', working: 'Wird verarbeitet …', exported: 'Sicherung wurde heruntergeladen.',
            imported: 'Sicherung wurde importiert. Die App wird neu geladen.', importInvalid: 'Diese Datei ist keine gültige World-Revolution-News-Sicherung.',
            importLarge: 'Die ausgewählte Sicherung ist zu groß.', importConfirm: 'Diese Sicherung importieren? Gleichnamige lokale App-Daten werden ersetzt.',
            clearConfirm: 'Die ausgewählten lokalen App-Daten wirklich löschen?', cleared: 'Ausgewählte Daten wurden gelöscht.', clearFailed: 'Daten konnten nicht vollständig gelöscht werden.',
            exportFailed: 'Sicherung konnte nicht erstellt werden.', importFailed: 'Sicherung konnte nicht importiert werden.', noIndexedDb: 'IndexedDB nicht verfügbar',
            items: 'Einträge', bytes: 'Bytes'
        }
    };

    function language() {
        try {
            if (typeof currentLang !== 'undefined' && currentLang) return currentLang;
        } catch {}
        return document.documentElement.lang || 'en';
    }

    function t() {
        return texts[language()] || texts.en;
    }

    function setText(id, value) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }

    function formatBytes(value) {
        const bytes = Number(value) || 0;
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KiB`;
        if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MiB`;
        return `${(bytes / 1024 ** 3).toFixed(2)} GiB`;
    }

    function parseJsonKey(key, fallback) {
        try {
            const value = JSON.parse(localStorage.getItem(key) || 'null');
            return value ?? fallback;
        } catch {
            return fallback;
        }
    }

    function wrnLocalEntries() {
        const entries = [];
        for (let index = 0; index < localStorage.length; index += 1) {
            const key = localStorage.key(index);
            if (!key || !key.startsWith('wrn_')) continue;
            entries.push([key, localStorage.getItem(key) ?? '']);
        }
        return entries.sort((a, b) => a[0].localeCompare(b[0]));
    }

    function shouldExportKey(key) {
        return key.startsWith('wrn_')
            && !EXCLUDED_EXPORT_KEYS.has(key)
            && !/(secret|token|api[_-]?key)/i.test(key);
    }

    function keyCategory(key) {
        if (['wrn_bookmarks', 'wrn_read_list', 'wrn_read_positions'].includes(key)) return 'reading';
        if (/^wrn_(audio|media|podcast|last_audio|original_podcast|live_radio|radio)/.test(key)) return 'audio';
        if (/^wrn_translation/.test(key)) return 'translations';
        return 'interface';
    }

    function countCategory(category) {
        return wrnLocalEntries().filter(([key]) => keyCategory(key) === category).length;
    }

    function localStorageBytes() {
        return wrnLocalEntries().reduce((sum, [key, value]) => sum + new Blob([key, value]).size, 0);
    }

    function setStatus(message, kind = '') {
        const status = document.getElementById('data-control-status');
        if (!status) return;
        status.textContent = message;
        status.className = `data-control-status${kind ? ` ${kind}` : ''}`;
    }

    async function readStorageSummary() {
        let indexed = {
            datasetCount: 0,
            translationCount: 0,
            datasetBytes: 0,
            translationBytes: 0
        };
        try {
            if (window.WRNStorage?.getStorageSummary) indexed = await window.WRNStorage.getStorageSummary();
        } catch (error) {
            console.warn('Lokale IndexedDB-Übersicht konnte nicht gelesen werden:', error);
        }

        let estimate = { usage: 0, quota: 0 };
        try {
            if (navigator.storage?.estimate) estimate = await navigator.storage.estimate();
        } catch {}

        let persistent = null;
        try {
            if (navigator.storage?.persisted) persistent = await navigator.storage.persisted();
        } catch {}

        return { indexed, estimate, persistent };
    }

    async function refresh() {
        const locale = t();
        const bookmarks = parseJsonKey('wrn_bookmarks', []);
        const read = parseJsonKey('wrn_read_list', []);
        const summary = await readStorageSummary();

        setText('data-count-bookmarks', Array.isArray(bookmarks) ? String(bookmarks.length) : '0');
        setText('data-count-read', Array.isArray(read) ? String(read.length) : '0');
        setText('data-count-audio', String(countCategory('audio')));
        setText('data-count-translations', String(summary.indexed.translationCount || 0));
        setText('data-count-offline', String(summary.indexed.datasetCount || 0));
        setText('data-count-local', String(wrnLocalEntries().length));

        const knownBytes = localStorageBytes() + Number(summary.indexed.datasetBytes || 0) + Number(summary.indexed.translationBytes || 0);
        const usage = Number(summary.estimate?.usage || knownBytes);
        const quota = Number(summary.estimate?.quota || 0);
        setText('data-storage-total', quota ? `${formatBytes(usage)} / ${formatBytes(quota)}` : formatBytes(usage));
        setText('data-storage-persistence', summary.persistent === true
            ? locale.persistentYes
            : summary.persistent === false ? locale.persistentNo : locale.persistentUnknown);
    }

    function refreshLanguage() {
        const locale = t();
        setText('btn-open-data-control', locale.button);
        setText('data-control-title', locale.title);
        setText('data-control-intro', locale.intro);
        setText('data-overview-title', locale.overview);
        setText('data-label-bookmarks', locale.bookmarks);
        setText('data-label-read', locale.read);
        setText('data-label-audio', locale.audio);
        setText('data-label-translations', locale.translations);
        setText('data-label-offline', locale.offline);
        setText('data-label-local', locale.localEntries);
        setText('data-label-storage', locale.storage);
        setText('data-label-persistent', locale.persistent);
        setText('data-backup-title', locale.backup);
        setText('data-backup-hint', locale.backupHint);
        setText('data-export-offline-label', locale.includeOffline);
        setText('data-export-translations-label', locale.includeTranslations);
        setText('btn-data-export', locale.export);
        setText('btn-data-import', locale.import);
        setText('data-delete-title', locale.deleteTitle);
        setText('btn-data-clear-reading', locale.deleteReading);
        setText('btn-data-clear-audio', locale.deleteAudio);
        setText('btn-data-clear-translations', locale.deleteTranslations);
        setText('btn-data-clear-offline', locale.deleteOffline);
        setText('btn-data-clear-interface', locale.deleteInterface);
        setText('btn-data-clear-all', locale.deleteAll);
        setText('data-external-title', locale.externalTitle);
        setText('data-external-hint', locale.externalHint);
        setText('btn-data-refresh', locale.refresh);
        setText('btn-data-close', locale.close);

        const list = document.getElementById('data-external-list');
        if (list) {
            list.textContent = '';
            locale.external.forEach(([name, description]) => {
                const item = document.createElement('li');
                const strong = document.createElement('strong');
                strong.textContent = name;
                const text = document.createElement('span');
                text.textContent = description;
                item.append(strong, text);
                list.append(item);
            });
        }
    }

    function close() {
        const modal = document.getElementById('data-control-modal');
        if (modal) modal.style.display = 'none';
    }

    async function open() {
        if (typeof closeAllModals === 'function') closeAllModals();
        const overlay = document.getElementById('fb-overlay');
        const modal = document.getElementById('data-control-modal');
        if (overlay) overlay.style.display = 'block';
        if (modal) modal.style.display = 'block';
        refreshLanguage();
        setStatus(t().working);
        await refresh();
        setStatus(t().ready, 'success');
        window.setTimeout(() => document.getElementById('btn-data-export')?.focus(), 0);
    }

    async function exportBackup() {
        const locale = t();
        setStatus(locale.working);
        try {
            const includeOffline = Boolean(document.getElementById('data-export-offline')?.checked);
            const includeTranslations = Boolean(document.getElementById('data-export-translations')?.checked);
            const local = {};
            wrnLocalEntries().forEach(([key, value]) => {
                if (shouldExportKey(key)) local[key] = value;
            });

            const backup = {
                format: BACKUP_FORMAT,
                schemaVersion: BACKUP_VERSION,
                createdAt: new Date().toISOString(),
                appVersion: window.WRN_CONFIG?.version || '',
                included: { offline: includeOffline, translations: includeTranslations },
                localStorage: local,
                indexedDB: {}
            };

            if (includeOffline && window.WRNStorage?.getAllDatasetRecords) {
                backup.indexedDB.datasets = await window.WRNStorage.getAllDatasetRecords();
            }
            if (includeTranslations && window.WRNStorage?.getAllTranslationRecords) {
                backup.indexedDB.translations = await window.WRNStorage.getAllTranslationRecords();
            }

            const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
            const link = document.createElement('a');
            const date = new Date().toISOString().slice(0, 10);
            link.href = URL.createObjectURL(blob);
            link.download = `world-revolution-news-backup-${date}.json`;
            document.body.append(link);
            link.click();
            link.remove();
            window.setTimeout(() => URL.revokeObjectURL(link.href), 2000);
            setStatus(locale.exported, 'success');
            await refresh();
        } catch (error) {
            console.error(error);
            setStatus(`${locale.exportFailed} ${error?.message || error}`, 'error');
        }
    }

    function validateBackup(data) {
        if (!data || typeof data !== 'object') return false;
        if (data.format !== BACKUP_FORMAT || Number(data.schemaVersion) !== BACKUP_VERSION) return false;
        if (!data.localStorage || typeof data.localStorage !== 'object' || Array.isArray(data.localStorage)) return false;
        return true;
    }

    async function importBackupFile(file) {
        const locale = t();
        if (!file) return;
        if (file.size > MAX_IMPORT_BYTES) {
            setStatus(locale.importLarge, 'error');
            return;
        }

        setStatus(locale.working);
        try {
            const data = JSON.parse(await file.text());
            if (!validateBackup(data)) throw new Error(locale.importInvalid);
            if (!window.confirm(locale.importConfirm)) {
                setStatus(locale.ready);
                return;
            }

            Object.entries(data.localStorage).forEach(([key, value]) => {
                if (!shouldExportKey(key) || typeof value !== 'string') return;
                if (value.length > 5_000_000) return;
                localStorage.setItem(key, value);
            });

            const indexed = data.indexedDB || {};
            if (Array.isArray(indexed.datasets) && window.WRNStorage?.replaceDatasetRecords) {
                await window.WRNStorage.replaceDatasetRecords(indexed.datasets);
            }
            if (Array.isArray(indexed.translations) && window.WRNStorage?.replaceTranslationRecords) {
                await window.WRNStorage.replaceTranslationRecords(indexed.translations);
            }

            setStatus(locale.imported, 'success');
            window.setTimeout(() => window.location.reload(), 900);
        } catch (error) {
            console.error(error);
            const message = error?.message === locale.importInvalid ? locale.importInvalid : `${locale.importFailed} ${error?.message || error}`;
            setStatus(message, 'error');
        }
    }

    function removeLocalCategory(category) {
        const keys = wrnLocalEntries().map(([key]) => key);
        keys.forEach(key => {
            if (category === 'all' || keyCategory(key) === category) localStorage.removeItem(key);
        });
    }

    async function clearBrowserCaches() {
        if (!('caches' in window)) return;
        const names = await caches.keys();
        await Promise.all(names.map(name => caches.delete(name)));
    }

    async function clearCategory(category) {
        const locale = t();
        if (!window.confirm(locale.clearConfirm)) return;
        setStatus(locale.working);
        try {
            if (category === 'reading' || category === 'audio' || category === 'interface') {
                removeLocalCategory(category);
            } else if (category === 'translations') {
                removeLocalCategory('translations');
                await window.WRNStorage?.clearTranslations?.();
            } else if (category === 'offline') {
                await window.WRNStorage?.clearDatasets?.();
                await clearBrowserCaches();
            } else if (category === 'all') {
                removeLocalCategory('all');
                await window.WRNStorage?.clearAll?.();
                await clearBrowserCaches();
            }
            setStatus(locale.cleared, 'success');
            await refresh();
            if (category === 'all' || category === 'interface') {
                window.setTimeout(() => window.location.reload(), 700);
            }
        } catch (error) {
            console.error(error);
            setStatus(`${locale.clearFailed} ${error?.message || error}`, 'error');
        }
    }

    function initialize() {
        refreshLanguage();
        document.getElementById('btn-data-export')?.addEventListener('click', exportBackup);
        document.getElementById('btn-data-import')?.addEventListener('click', () => document.getElementById('data-import-file')?.click());
        document.getElementById('data-import-file')?.addEventListener('change', event => {
            const input = event.currentTarget;
            importBackupFile(input?.files?.[0]);
            if (input) input.value = '';
        });
        document.getElementById('btn-data-refresh')?.addEventListener('click', async () => {
            setStatus(t().working);
            await refresh();
            setStatus(t().ready, 'success');
        });
        document.querySelectorAll('[data-clear-category]').forEach(button => {
            button.addEventListener('click', () => clearCategory(button.dataset.clearCategory || ''));
        });
    }

    const api = { open, close, refresh, refreshLanguage, exportBackup, importBackupFile, clearCategory };
    window.WRNDataControl = api;
    window.openDataControl = open;

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, { once: true });
    else initialize();
})();
