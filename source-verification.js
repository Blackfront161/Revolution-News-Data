/* World Revolution News 1.7.15 – vollständige Quellenübersicht */
'use strict';

(() => {
    if (window.WRNSourceVerification) return;

    const config = window.WRN_CONFIG || {};
    const urls = config.dataUrls || {};

    const state = {
        rows: [],
        filter: 'all',
        search: '',
        loadedAt: '',
        loading: false,
        summary: {
            total: 0,
            ok: 0,
            warning: 0,
            error: 0,
            unknown: 0
        }
    };

    const TEXT = {
        de: {
            title: 'Quellenprüfung',
            open: 'Quellenprüfung',
            refresh: 'Neu prüfen',
            close: 'Schließen',
            search: 'Quelle suchen …',
            all: 'Alle',
            ok: 'Erreichbar',
            warning: 'Eingeschränkt',
            error: 'Defekt',
            unknown: 'Nicht geprüft',
            total: 'Quellen',
            empty: 'Keine passenden Quellen gefunden.',
            loading: 'Quellen werden geprüft …',
            updated: 'Geprüft',
            news: 'Nachrichten',
            podcast: 'Podcasts',
            radio: 'Radio',
            catalog: 'Katalog',
            unavailable: 'Statusdatei nicht erreichbar',
            limited: 'Aus Leistungsgründen werden höchstens 300 Einträge angezeigt.'
        },
        en: {
            title: 'Source verification',
            open: 'Source verification',
            refresh: 'Check again',
            close: 'Close',
            search: 'Search sources …',
            all: 'All',
            ok: 'Available',
            warning: 'Limited',
            error: 'Broken',
            unknown: 'Not checked',
            total: 'Sources',
            empty: 'No matching sources found.',
            loading: 'Checking sources …',
            updated: 'Checked',
            news: 'News',
            podcast: 'Podcasts',
            radio: 'Radio',
            catalog: 'Catalog',
            unavailable: 'Status file unavailable',
            limited: 'For performance, no more than 300 entries are shown.'
        }
    };

    const language = () => {
        const raw = document.getElementById('ui-language')?.value
            || document.documentElement.lang
            || 'en';
        return String(raw).toLowerCase().startsWith('de') ? 'de' : 'en';
    };

    const t = () => TEXT[language()] || TEXT.en;

    const escapeHtml = value => String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');

    const timeoutFetch = async (url, milliseconds = 9000) => {
        const controller = new AbortController();
        const timer = window.setTimeout(
            () => controller.abort(),
            milliseconds
        );

        try {
            const separator = url.includes('?') ? '&' : '?';
            const response = await fetch(
                `${url}${separator}verify=${Date.now()}`,
                {
                    cache: 'no-store',
                    headers: { Accept: 'application/json' },
                    signal: controller.signal
                }
            );

            if (!response.ok) {
                const error = new Error(`HTTP ${response.status}`);
                error.status = response.status;
                throw error;
            }

            return await response.json();
        } finally {
            window.clearTimeout(timer);
        }
    };

    const asArray = data => {
        if (Array.isArray(data)) return data;

        if (!data || typeof data !== 'object') return [];

        for (const key of [
            'sources',
            'items',
            'results',
            'entries',
            'checks'
        ]) {
            if (Array.isArray(data[key])) return data[key];
        }

        return Object.entries(data)
            .filter(([, value]) => value && typeof value === 'object')
            .map(([key, value]) => ({
                __key: key,
                ...value
            }));
    };

    const statusOf = item => {
        const raw = String(
            item.status
            || item.state
            || item.result
            || item.health
            || ''
        ).toLowerCase();

        const message = String(
            item.error
            || item.warning
            || item.message
            || item.reason
            || item.detail
            || ''
        ).toLowerCase();

        const combined = `${raw} ${message}`;

        const httpStatus = Number(
            item.httpStatus
            || item.statusCode
            || item.code
            || 0
        );

        if (
            item.ok === true
            || ['ok', 'online', 'success', 'healthy', 'available']
                .includes(raw)
            || (
                httpStatus >= 200
                && httpStatus < 400
                && !combined.includes('certificate')
                && !combined.includes('tls')
            )
        ) {
            return 'ok';
        }

        if (
            raw.includes('warn')
            || raw.includes('partial')
            || raw.includes('slow')
            || raw.includes('redirect')
            || raw.includes('blocked')
            || raw.includes('timeout')
            || raw.includes('rate')
            || combined.includes('certificate')
            || combined.includes('tls')
            || combined.includes('ssl')
            || combined.includes('timeout')
            || combined.includes('tempor')
            || combined.includes('max retries')
            || [401, 403, 408, 429].includes(httpStatus)
            || httpStatus >= 500
        ) {
            return 'warning';
        }

        if (
            raw.includes('error')
            || raw.includes('fail')
            || raw.includes('offline')
            || combined.includes('not found')
            || combined.includes('name resolution')
            || combined.includes('dns')
            || combined.includes('no feed')
            || combined.includes('invalid feed')
            || [404, 410].includes(httpStatus)
        ) {
            return 'error';
        }

        if (item.ok === false) return 'warning';

        return 'unknown';
    };

    const nameOf = (item, fallback = '') => String(
        item.name
        || item.sourceName
        || item.source
        || item.quelleName
        || item.title
        || item.label
        || item.__key
        || fallback
        || 'Unbekannte Quelle'
    ).trim();

    const urlOf = item => String(
        item.url
        || item.feedUrl
        || item.feed
        || item.link
        || item.homepage
        || ''
    ).trim();

    const detailOf = item => {
        const parts = [];

        const httpStatus = Number(
            item.httpStatus
            || item.statusCode
            || item.code
            || 0
        );

        if (httpStatus) parts.push(`HTTP ${httpStatus}`);

        const message = String(
            item.error
            || item.message
            || item.reason
            || item.detail
            || ''
        ).trim();

        if (message) parts.push(message.slice(0, 240));

        const date = String(
            item.checkedAt
            || item.updatedAt
            || item.lastCheck
            || ''
        ).trim();

        if (date) parts.push(date);

        return parts.join(' · ');
    };

    const normalize = (data, kind, fallbackStatus = 'unknown') =>
        asArray(data).map((item, index) => {
            const source = item && typeof item === 'object'
                ? item
                : { name: String(item || '') };

            const derived = statusOf(source);

            return {
                id: `${kind}-${index}-${nameOf(source, index)}`,
                kind,
                name: nameOf(source, `${kind} ${index + 1}`),
                url: urlOf(source),
                status: derived === 'unknown'
                    ? fallbackStatus
                    : derived,
                detail: detailOf(source)
            };
        });

    const canonicalUrl = value => {
        const raw = String(value || '').trim();

        if (!raw) return '';

        try {
            const url = new URL(raw);
            const host = url.hostname
                .toLowerCase()
                .replace(/^www\./, '');

            const path = url.pathname
                .replace(/\/+/g, '/')
                .replace(/\/$/, '') || '/';

            const params = [...url.searchParams.entries()]
                .sort(([a], [b]) => a.localeCompare(b));

            const query = new URLSearchParams(params).toString();

            return `${host}${path}${query ? `?${query}` : ''}`;
        } catch {
            return raw
                .toLowerCase()
                .replace(/^https?:\/\//, '')
                .replace(/^www\./, '')
                .replace(/\/$/, '');
        }
    };

    const canonicalName = value => String(value || '')
        .toLowerCase()
        .normalize('NFKD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/\([^)]*\)/g, '')
        .replace(/[^a-z0-9]+/g, '');

    const dedupeRows = rows => {
        const byKey = new Map();

        rows.forEach(row => {
            const urlKey = canonicalUrl(row.url);
            const nameKey = canonicalName(row.name);
            const key = urlKey || nameKey || row.id;

            if (!byKey.has(key)) {
                byKey.set(key, { ...row });
                return;
            }

            const current = byKey.get(key);
            const priority = {
                error: 4,
                warning: 3,
                ok: 2,
                unknown: 1
            };

            if (
                (priority[row.status] || 0)
                > (priority[current.status] || 0)
            ) {
                current.status = row.status;
            }

            if (!current.url && row.url) {
                current.url = row.url;
            }

            if (
                row.detail
                && !String(current.detail || '')
                    .includes(row.detail)
            ) {
                current.detail = [
                    current.detail,
                    row.detail
                ].filter(Boolean).join(' · ');
            }
        });

        return [...byKey.values()];
    };

    const mergeCatalog = (catalogRows, healthRows) => {
        const healthByUrl = new Map();
        const healthByName = new Map();

        dedupeRows(healthRows).forEach(row => {
            const urlKey = canonicalUrl(row.url);
            const nameKey = canonicalName(row.name);

            if (urlKey) healthByUrl.set(urlKey, row);
            if (nameKey) healthByName.set(nameKey, row);
        });

        const merged = [];

        dedupeRows(catalogRows).forEach(catalog => {
            const urlKey = canonicalUrl(catalog.url);
            const nameKey = canonicalName(catalog.name);

            const health = (
                (urlKey && healthByUrl.get(urlKey))
                || (nameKey && healthByName.get(nameKey))
            );

            if (health) {
                merged.push({
                    ...catalog,
                    ...health,
                    name: health.name || catalog.name,
                    url: health.url || catalog.url
                });

                if (urlKey) healthByUrl.delete(urlKey);
                if (nameKey) healthByName.delete(nameKey);
            } else {
                merged.push(catalog);
            }
        });

        const leftovers = dedupeRows([
            ...healthByUrl.values(),
            ...healthByName.values()
        ]);

        return dedupeRows([
            ...merged,
            ...leftovers
        ]);
    };

    const summarize = rows => {
        const result = {
            total: rows.length,
            ok: 0,
            warning: 0,
            error: 0,
            unknown: 0
        };

        rows.forEach(row => {
            if (result[row.status] === undefined) {
                result.unknown += 1;
            } else {
                result[row.status] += 1;
            }
        });

        return result;
    };

    const ensureModal = () => {
        let modal = document.getElementById(
            'wrn-source-verification-modal'
        );

        if (modal) return modal;

        const overlay = document.createElement('div');
        overlay.id = 'wrn-source-verification-overlay';
        overlay.className = 'wrn-source-verification-overlay';
        overlay.hidden = true;

        modal = document.createElement('section');
        modal.id = 'wrn-source-verification-modal';
        modal.className = 'wrn-source-verification-modal';
        modal.hidden = true;
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute(
            'aria-labelledby',
            'wrn-source-verification-title'
        );

        modal.innerHTML = `
            <div class="wrn-source-verification-head">
                <div>
                    <h2 id="wrn-source-verification-title"></h2>
                    <p id="wrn-source-verification-updated"></p>
                </div>
                <button
                    type="button"
                    class="wrn-source-close"
                    data-source-action="close"
                >×</button>
            </div>

            <div
                class="wrn-source-summary"
                id="wrn-source-summary"
            ></div>

            <div class="wrn-source-controls">
                <input
                    type="search"
                    id="wrn-source-search"
                    autocomplete="off"
                >
                <div
                    class="wrn-source-filter-row"
                    id="wrn-source-filter-row"
                ></div>
            </div>

            <div
                id="wrn-source-status"
                class="wrn-source-status"
                aria-live="polite"
            ></div>

            <div
                id="wrn-source-list"
                class="wrn-source-list"
            ></div>

            <div class="wrn-source-footer">
                <small id="wrn-source-limit-note"></small>
                <div>
                    <button
                        type="button"
                        data-source-action="refresh"
                    ></button>
                    <button
                        type="button"
                        data-source-action="close"
                    ></button>
                </div>
            </div>
        `;

        document.body.append(overlay, modal);

        overlay.addEventListener('click', close);

        modal.addEventListener('click', event => {
            const button = event.target.closest(
                '[data-source-action]'
            );

            if (!button) return;

            if (button.dataset.sourceAction === 'close') close();
            if (button.dataset.sourceAction === 'refresh') {
                void refresh();
            }

            const filter = button.dataset.sourceFilter;
            if (filter) {
                state.filter = filter;
                render();
            }
        });

        modal.querySelector('#wrn-source-search')
            ?.addEventListener('input', event => {
                state.search = String(event.target.value || '')
                    .trim()
                    .toLowerCase();
                renderList();
            });

        return modal;
    };

    const insertButton = () => {
        if (document.getElementById('wrn-source-verification-open')) {
            return true;
        }

        const button = document.createElement('button');
        button.type = 'button';
        button.id = 'wrn-source-verification-open';
        button.className = 'wrn-source-verification-open';
        button.textContent = t().open;
        button.addEventListener('click', open);

        const moreGrid = document.querySelector('.wrn-more-grid');

        if (moreGrid) {
            moreGrid.appendChild(button);
            return true;
        }

        const headerButtons = document.querySelector(
            '.wrn-header-actions, .header-controls, header'
        );

        if (headerButtons) {
            headerButtons.appendChild(button);
            return true;
        }

        return false;
    };

    const renderSummary = () => {
        const labels = t();
        const summary = state.summary;
        const node = document.getElementById('wrn-source-summary');

        if (!node) return;

        node.innerHTML = [
            ['total', labels.total, summary.total],
            ['ok', labels.ok, summary.ok],
            ['warning', labels.warning, summary.warning],
            ['error', labels.error, summary.error],
            ['unknown', labels.unknown, summary.unknown]
        ].map(([kind, label, value]) => `
            <div class="wrn-source-metric" data-state="${kind}">
                <span>${escapeHtml(label)}</span>
                <strong>${Number(value) || 0}</strong>
            </div>
        `).join('');
    };

    const renderFilters = () => {
        const labels = t();
        const node = document.getElementById(
            'wrn-source-filter-row'
        );

        if (!node) return;

        const filters = [
            ['all', labels.all],
            ['ok', labels.ok],
            ['warning', labels.warning],
            ['error', labels.error],
            ['unknown', labels.unknown]
        ];

        node.innerHTML = filters.map(([key, label]) => `
            <button
                type="button"
                data-source-filter="${key}"
                class="${state.filter === key ? 'active' : ''}"
            >${escapeHtml(label)}</button>
        `).join('');
    };

    const visibleRows = () => {
        const search = state.search;

        return state.rows.filter(row => {
            if (
                state.filter !== 'all'
                && row.status !== state.filter
            ) {
                return false;
            }

            if (!search) return true;

            return [
                row.name,
                row.url,
                row.detail,
                row.kind
            ].some(value => String(value || '')
                .toLowerCase()
                .includes(search));
        });
    };

    const renderList = () => {
        const labels = t();
        const node = document.getElementById('wrn-source-list');

        if (!node) return;

        const rows = visibleRows().slice(0, 300);

        if (!rows.length) {
            node.innerHTML = `
                <p class="wrn-source-empty">
                    ${escapeHtml(labels.empty)}
                </p>
            `;
            return;
        }

        node.innerHTML = rows.map(row => `
            <article
                class="wrn-source-row"
                data-state="${escapeHtml(row.status)}"
            >
                <div class="wrn-source-row-main">
                    <strong>${escapeHtml(row.name)}</strong>
                    <span>
                        ${escapeHtml(
                            row.kind === 'podcast'
                                ? labels.podcast
                                : row.kind === 'radio'
                                    ? labels.radio
                                    : row.kind === 'catalog'
                                        ? labels.catalog
                                        : labels.news
                        )}
                    </span>
                </div>

                <span class="wrn-source-badge">
                    ${escapeHtml(labels[row.status] || labels.unknown)}
                </span>

                ${row.detail ? `
                    <p>${escapeHtml(row.detail)}</p>
                ` : ''}

                ${row.url ? `
                    <a
                        href="${escapeHtml(row.url)}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >${escapeHtml(row.url)}</a>
                ` : ''}
            </article>
        `).join('');
    };

    const render = () => {
        const labels = t();
        const modal = ensureModal();

        modal.querySelector('#wrn-source-verification-title')
            .textContent = labels.title;

        modal.querySelector('#wrn-source-verification-updated')
            .textContent = state.loadedAt
                ? `${labels.updated}: ${state.loadedAt}`
                : '';

        const search = modal.querySelector('#wrn-source-search');
        search.placeholder = labels.search;

        modal.querySelector('#wrn-source-limit-note')
            .textContent = labels.limited;

        modal.querySelectorAll('[data-source-action="refresh"]')
            .forEach(button => {
                button.textContent = labels.refresh;
            });

        modal.querySelectorAll('[data-source-action="close"]')
            .forEach(button => {
                if (!button.classList.contains('wrn-source-close')) {
                    button.textContent = labels.close;
                }
            });

        renderSummary();
        renderFilters();
        renderList();
    };

    async function refresh() {
        if (state.loading) return;

        state.loading = true;
        ensureModal();

        const status = document.getElementById('wrn-source-status');
        if (status) status.textContent = t().loading;

        const endpoints = [
            ['news', urls.sourceHealth],
            ['catalog', urls.sourceCatalog],
            ['podcast', urls.podcastHealth],
            ['radio', urls.radioHealth]
        ].filter(([, url]) => Boolean(url));

        const settled = await Promise.allSettled(
            endpoints.map(async ([kind, url]) => ({
                kind,
                data: await timeoutFetch(url)
            }))
        );

        const grouped = {
            news: [],
            catalog: [],
            podcast: [],
            radio: []
        };

        settled.forEach((result, index) => {
            const kind = endpoints[index][0];

            if (result.status === 'fulfilled') {
                grouped[kind] = normalize(
                    result.value.data,
                    kind,
                    kind === 'catalog' ? 'unknown' : 'unknown'
                );
            } else {
                grouped[kind] = [{
                    id: `${kind}-unavailable`,
                    kind,
                    name: t().unavailable,
                    url: endpoints[index][1],
                    status: 'error',
                    detail: String(
                        result.reason?.message || result.reason
                    )
                }];
            }
        });

        const news = mergeCatalog(
            grouped.catalog,
            grouped.news
        );

        state.rows = dedupeRows([
            ...news,
            ...grouped.podcast,
            ...grouped.radio
        ]).sort((a, b) => {
            const priority = {
                error: 0,
                warning: 1,
                unknown: 2,
                ok: 3
            };

            return (
                priority[a.status] - priority[b.status]
                || a.name.localeCompare(b.name)
            );
        });

        state.summary = summarize(state.rows);
        state.loadedAt = new Intl.DateTimeFormat(
            language() === 'de' ? 'de-DE' : 'en-GB',
            {
                dateStyle: 'medium',
                timeStyle: 'short'
            }
        ).format(new Date());

        state.loading = false;

        if (status) status.textContent = '';
        render();
    }

    function open() {
        const modal = ensureModal();
        const overlay = document.getElementById(
            'wrn-source-verification-overlay'
        );

        modal.hidden = false;
        overlay.hidden = false;
        document.documentElement.classList.add(
            'wrn-source-modal-open'
        );

        render();

        if (!state.loadedAt && !state.loading) {
            void refresh();
        }
    }

    function close() {
        const modal = document.getElementById(
            'wrn-source-verification-modal'
        );
        const overlay = document.getElementById(
            'wrn-source-verification-overlay'
        );

        if (modal) modal.hidden = true;
        if (overlay) overlay.hidden = true;

        document.documentElement.classList.remove(
            'wrn-source-modal-open'
        );
    }

    function init() {
        ensureModal();

        if (!insertButton()) {
            let attempts = 0;
            const timer = window.setInterval(() => {
                attempts += 1;

                if (insertButton() || attempts >= 30) {
                    window.clearInterval(timer);
                }
            }, 250);
        }

        document.getElementById('ui-language')
            ?.addEventListener('change', () => {
                const button = document.getElementById(
                    'wrn-source-verification-open'
                );
                if (button) button.textContent = t().open;
                render();
            });
    }

    window.WRNSourceVerification = Object.freeze({
        open,
        close,
        refresh,
        summary: () => ({ ...state.summary }),
        rows: () => state.rows.map(row => ({ ...row }))
    });

    window.openSourceVerification = open;

    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            init,
            { once: true }
        );
    } else {
        init();
    }
})();
