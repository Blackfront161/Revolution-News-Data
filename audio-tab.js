/* World Revolution News 1.7.19 – Audio direkt im Hauptreiter */
'use strict';

(() => {
    if (window.WRNAudioTab1719) return;

    const state = {
        activeView: 'original',
        original: [],
        generated: [],
        radio: [],
        loaded: false,
        loading: false,
        query: '',
        language: 'all',
        current: null
    };

    const hiddenNodes = new Map();
    let panel = null;
    let audio = null;
    let playerBar = null;

    const text = () => {
        const de = String(
            document.getElementById('ui-language')?.value
            || document.documentElement.lang
            || ''
        ).toLowerCase().startsWith('de');

        return de
            ? {
                title: 'Audio',
                original: 'Original-Podcasts',
                generated: 'Erzeugte Podcasts',
                radio: 'Live-Radio',
                search: 'Audio durchsuchen …',
                allLanguages: 'Alle Sprachen',
                play: 'Abspielen',
                pause: 'Pause',
                stop: 'Stop',
                open: 'Original öffnen',
                loading: 'Audiodaten werden geladen …',
                empty: 'Keine passenden Einträge gefunden.',
                failed: 'Audiodaten konnten nicht geladen werden.',
                retry: 'Erneut laden',
                noDescription: 'Eine aktuelle Folge dieser unabhängigen Quelle.',
                external: 'Extern öffnen',
                live: 'LIVE'
            }
            : {
                title: 'Audio',
                original: 'Original podcasts',
                generated: 'Generated podcasts',
                radio: 'Live radio',
                search: 'Search audio …',
                allLanguages: 'All languages',
                play: 'Play',
                pause: 'Pause',
                stop: 'Stop',
                open: 'Open original',
                loading: 'Loading audio data …',
                empty: 'No matching items found.',
                failed: 'Audio data could not be loaded.',
                retry: 'Reload',
                noDescription: 'A current episode from this independent source.',
                external: 'Open externally',
                live: 'LIVE'
            };
    };

    const escapeHtml = value => String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');

    const asArray = data => {
        if (Array.isArray(data)) return data;
        if (!data || typeof data !== 'object') return [];

        for (const key of [
            'items', 'episodes', 'podcasts', 'stations',
            'sources', 'results', 'entries'
        ]) {
            if (Array.isArray(data[key])) return data[key];
        }

        return Object.entries(data)
            .filter(([, value]) => value && typeof value === 'object')
            .map(([key, value]) => ({ __key: key, ...value }));
    };

    const first = (item, fields) => {
        for (const field of fields) {
            const value = item?.[field];

            if (value && typeof value === 'object') {
                for (const nested of ['url', 'href', 'src']) {
                    if (value[nested]) return String(value[nested]).trim();
                }
            }

            if (value) return String(value).trim();
        }

        return '';
    };

    const cleanText = value => String(value || '')
        .replace(/<[^>]*>/g, ' ')
        .replace(/&nbsp;/gi, ' ')
        .replace(/&amp;/gi, '&')
        .replace(/&quot;/gi, '"')
        .replace(/&#39;/g, "'")
        .replace(/\s+/g, ' ')
        .trim();

    const oneSentence = value => {
        const t = text();
        const clean = cleanText(value);

        if (!clean) return t.noDescription;

        const match = clean.match(/^(.{25,220}?[.!?])(?:\s|$)/);
        const sentence = match ? match[1] : clean.slice(0, 180);

        return sentence.length < clean.length && !/[.!?]$/.test(sentence)
            ? `${sentence.trim()} …`
            : sentence.trim();
    };

    const normalLanguage = item => {
        const raw = first(item, [
            'language', 'lang', 'sprache', 'locale'
        ]).toLowerCase();

        if (!raw) return 'und';
        return raw.split(/[-_]/)[0].slice(0, 3);
    };

    const normalizePodcast = (item, generated = false) => ({
        id: first(item, ['id', 'guid', '__key'])
            || `${generated ? 'g' : 'o'}-${Math.random()}`,
        kind: generated ? 'generated' : 'original',
        title: first(item, ['title', 'name', 'episodeTitle'])
            || 'Podcast',
        source: first(item, [
            'sourceName', 'podcastName', 'podcast', 'show',
            'quelleName', 'source', 'author'
        ]) || (generated ? 'World Revolution News' : 'Podcast'),
        description: oneSentence(first(item, [
            'description', 'summary', 'content', 'teaser',
            'subtitle', 'excerpt'
        ])),
        audioUrl: first(item, [
            'audioUrl', 'audio_url', 'enclosureUrl',
            'enclosure', 'mediaUrl', 'file', 'url'
        ]),
        originalUrl: first(item, [
            'originalUrl', 'link', 'homepage', 'sourceUrl', 'webUrl'
        ]),
        date: first(item, ['pubDate', 'publishedAt', 'date', 'published']),
        duration: first(item, ['duration', 'length', 'runtime']),
        language: normalLanguage(item)
    });

    const normalizeRadio = item => ({
        id: first(item, ['id', '__key'])
            || `r-${Math.random()}`,
        kind: 'radio',
        title: first(item, ['name', 'station', 'title', 'label'])
            || 'Live-Radio',
        source: first(item, ['country', 'region', 'city', 'source'])
            || text().live,
        description: oneSentence(first(item, [
            'description', 'summary', 'tagline', 'content'
        ])),
        audioUrl: first(item, [
            'streamUrl', 'stream_url', 'audioUrl',
            'playlistUrl', 'stream', 'url'
        ]),
        originalUrl: first(item, ['homepage', 'website', 'link']),
        language: normalLanguage(item)
    });

    const fetchJson = async url => {
        const response = await fetch(
            `${url}${url.includes('?') ? '&' : '?'}v=${Date.now()}`,
            { cache: 'no-store' }
        );

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    };

    const fetchFirst = async urls => {
        for (const url of urls.filter(Boolean)) {
            try {
                return await fetchJson(url);
            } catch {
                // Try next known filename.
            }
        }
        return [];
    };

    const load = async force => {
        if (state.loading) return;
        if (state.loaded && !force) return;

        state.loading = true;
        renderLoading();

        const urls = window.WRN_CONFIG?.dataUrls || {};

        const [original, generated, radio] = await Promise.all([
            fetchFirst([urls.podcasts, './podcasts.json']),
            fetchFirst([
                urls.generatedPodcasts,
                './generated-podcasts.json',
                './generated_podcasts.json',
                './podcast-feed.json'
            ]),
            fetchFirst([urls.radio, './radio-stations.json'])
        ]);

        state.original = asArray(original)
            .map(item => normalizePodcast(item, false))
            .filter(item => item.audioUrl)
            .slice(0, 180);

        state.generated = asArray(generated)
            .map(item => normalizePodcast(item, true))
            .filter(item => item.audioUrl)
            .slice(0, 80);

        state.radio = asArray(radio)
            .map(normalizeRadio)
            .filter(item => item.audioUrl)
            .slice(0, 120);

        state.loaded = true;
        state.loading = false;
        render();
    };

    const ensureAudio = () => {
        if (audio) return audio;

        audio = document.createElement('audio');
        audio.preload = 'none';
        audio.crossOrigin = 'anonymous';

        audio.addEventListener('play', updatePlayer);
        audio.addEventListener('pause', updatePlayer);
        audio.addEventListener('ended', () => {
            state.current = null;
            updatePlayer();
            renderCards();
        });
        audio.addEventListener('error', () => {
            playerBar?.classList.add('wrn-audio-player-error');
        });

        document.body.appendChild(audio);
        return audio;
    };

    const playableUrl = raw => {
        const url = String(raw || '').trim();

        if (!url.startsWith('http://')) return url;

        const proxy = window.WRN_CONFIG?.proxyUrl;
        return proxy
            ? `${proxy}?url=${encodeURIComponent(url)}`
            : url;
    };

    const play = async item => {
        const media = ensureAudio();

        if (
            state.current?.id === item.id
            && !media.paused
        ) {
            if (item.kind === 'radio') {
                media.pause();
                media.removeAttribute('src');
                media.load();
                state.current = null;
            } else {
                media.pause();
            }

            updatePlayer();
            renderCards();
            return;
        }

        if (
            state.current?.id === item.id
            && media.paused
            && media.currentSrc
        ) {
            await media.play();
            updatePlayer();
            renderCards();
            return;
        }

        state.current = item;
        media.src = playableUrl(item.audioUrl);
        media.load();

        try {
            await media.play();

            if ('mediaSession' in navigator) {
                navigator.mediaSession.metadata = new MediaMetadata({
                    title: item.title,
                    artist: item.source,
                    album: item.kind === 'radio'
                        ? text().radio
                        : text().original
                });

                navigator.mediaSession.setActionHandler(
                    'play',
                    () => media.play()
                );
                navigator.mediaSession.setActionHandler(
                    'pause',
                    () => media.pause()
                );
                navigator.mediaSession.setActionHandler(
                    'stop',
                    () => stop()
                );
            }
        } catch (error) {
            console.warn('WRN audio playback:', error);
        }

        updatePlayer();
        renderCards();
    };

    const stop = () => {
        if (!audio) return;

        audio.pause();
        audio.removeAttribute('src');
        audio.load();
        state.current = null;
        updatePlayer();
        renderCards();
    };

    const ensurePlayer = () => {
        if (playerBar) return playerBar;

        playerBar = document.createElement('aside');
        playerBar.id = 'wrn-audio-player-1719';
        playerBar.className = 'wrn-audio-player-1719';
        playerBar.hidden = true;
        playerBar.innerHTML = `
            <div>
                <strong id="wrn-audio-player-title"></strong>
                <span id="wrn-audio-player-source"></span>
            </div>
            <button type="button" data-player-action="toggle"></button>
            <button type="button" data-player-action="stop">■</button>
        `;

        playerBar.addEventListener('click', event => {
            const action = event.target.closest(
                '[data-player-action]'
            )?.dataset.playerAction;

            if (action === 'toggle' && audio) {
                if (audio.paused) {
                    void audio.play();
                } else {
                    audio.pause();
                }
            }

            if (action === 'stop') stop();
        });

        document.body.appendChild(playerBar);
        return playerBar;
    };

    const updatePlayer = () => {
        const bar = ensurePlayer();
        const t = text();

        if (!state.current) {
            bar.hidden = true;
            return;
        }

        bar.hidden = false;
        bar.classList.remove('wrn-audio-player-error');
        bar.querySelector('#wrn-audio-player-title')
            .textContent = state.current.title;
        bar.querySelector('#wrn-audio-player-source')
            .textContent = state.current.source;
        bar.querySelector('[data-player-action="toggle"]')
            .textContent = audio?.paused ? `▶ ${t.play}` : `Ⅱ ${t.pause}`;
        bar.querySelector('[data-player-action="stop"]')
            .title = t.stop;
    };

    const ensurePanel = () => {
        if (panel) return panel;

        panel = document.createElement('section');
        panel.id = 'wrn-audio-tab-panel-1719';
        panel.className = 'wrn-audio-tab-panel-1719';
        panel.hidden = true;
        panel.innerHTML = `
            <header class="wrn-audio-tab-head-1719">
                <div>
                    <h2></h2>
                    <p id="wrn-audio-tab-count"></p>
                </div>
                <button
                    type="button"
                    data-audio-tab-action="reload"
                    aria-label="Neu laden"
                >↻</button>
            </header>

            <div class="wrn-audio-tab-controls-1719">
                <nav id="wrn-audio-subtabs-1719"></nav>
                <div>
                    <input
                        type="search"
                        id="wrn-audio-search-1719"
                    >
                    <select id="wrn-audio-language-1719"></select>
                </div>
            </div>

            <div
                id="wrn-audio-tab-status-1719"
                aria-live="polite"
            ></div>
            <div id="wrn-audio-tab-list-1719"></div>
        `;

        panel.addEventListener('click', event => {
            const view = event.target.closest(
                '[data-audio-view]'
            )?.dataset.audioView;

            if (view) {
                state.activeView = view;
                render();
                return;
            }

            const itemId = event.target.closest(
                '[data-audio-play]'
            )?.dataset.audioPlay;

            if (itemId) {
                const item = currentItems().find(row => row.id === itemId);
                if (item) void play(item);
            }

            if (
                event.target.closest(
                    '[data-audio-tab-action="reload"]'
                )
            ) {
                void load(true);
            }
        });

        panel.querySelector('#wrn-audio-search-1719')
            .addEventListener('input', event => {
                state.query = String(event.target.value || '')
                    .trim()
                    .toLowerCase();
                renderCards();
            });

        panel.querySelector('#wrn-audio-language-1719')
            .addEventListener('change', event => {
                state.language = String(event.target.value || 'all');
                renderCards();
            });

        const feed = document.getElementById('feed-container');

        if (feed?.parentElement) {
            feed.parentElement.insertBefore(panel, feed);
        } else {
            document.body.appendChild(panel);
        }

        return panel;
    };

    const currentItems = () => {
        if (state.activeView === 'generated') return state.generated;
        if (state.activeView === 'radio') return state.radio;
        return state.original;
    };

    const filteredItems = () => currentItems().filter(item => {
        if (
            state.language !== 'all'
            && item.language !== state.language
        ) {
            return false;
        }

        if (!state.query) return true;

        return [
            item.title,
            item.source,
            item.description,
            item.language
        ].some(value => String(value || '')
            .toLowerCase()
            .includes(state.query));
    });

    const renderLoading = () => {
        const node = ensurePanel();
        const t = text();

        node.querySelector('h2').textContent = t.title;
        node.querySelector('#wrn-audio-tab-status-1719')
            .textContent = t.loading;
        node.querySelector('#wrn-audio-tab-list-1719')
            .innerHTML = '';
    };

    const renderCards = () => {
        if (!panel) return;

        const t = text();
        const items = filteredItems();
        const list = panel.querySelector('#wrn-audio-tab-list-1719');
        const count = panel.querySelector('#wrn-audio-tab-count');

        count.textContent = `${items.length} / ${currentItems().length}`;

        if (!items.length) {
            list.innerHTML = `
                <p class="wrn-audio-empty-1719">${escapeHtml(t.empty)}</p>
            `;
            return;
        }

        list.innerHTML = items.map(item => {
            const isCurrent = state.current?.id === item.id;
            const isPlaying = isCurrent && audio && !audio.paused;
            const actionLabel = item.kind === 'radio'
                ? (isPlaying ? t.stop : t.play)
                : (isPlaying ? t.pause : t.play);

            return `
                <article
                    class="wrn-audio-card-1719"
                    data-kind="${escapeHtml(item.kind)}"
                    data-playing="${isPlaying ? 'true' : 'false'}"
                >
                    <div class="wrn-audio-card-meta-1719">
                        <span>${escapeHtml(item.source)}</span>
                        <span>${escapeHtml(item.language.toUpperCase())}</span>
                        ${item.kind === 'radio'
                            ? `<span class="wrn-live-badge-1719">${t.live}</span>`
                            : ''}
                    </div>

                    <h3>${escapeHtml(item.title)}</h3>
                    <p>${escapeHtml(item.description)}</p>

                    <div class="wrn-audio-card-actions-1719">
                        <button
                            type="button"
                            data-audio-play="${escapeHtml(item.id)}"
                        >${escapeHtml(actionLabel)}</button>

                        ${item.originalUrl ? `
                            <a
                                href="${escapeHtml(item.originalUrl)}"
                                target="_blank"
                                rel="noopener noreferrer"
                            >${escapeHtml(t.open)}</a>
                        ` : ''}
                    </div>
                </article>
            `;
        }).join('');
    };

    const render = () => {
        const node = ensurePanel();
        const t = text();

        node.querySelector('h2').textContent = t.title;
        node.querySelector('#wrn-audio-search-1719')
            .placeholder = t.search;

        const tabs = [
            ['original', t.original, state.original.length],
            ['generated', t.generated, state.generated.length],
            ['radio', t.radio, state.radio.length]
        ];

        node.querySelector('#wrn-audio-subtabs-1719')
            .innerHTML = tabs.map(([key, label, count]) => `
                <button
                    type="button"
                    data-audio-view="${key}"
                    class="${state.activeView === key ? 'active' : ''}"
                >${escapeHtml(label)} <span>${count}</span></button>
            `).join('');

        const languageSelect = node.querySelector(
            '#wrn-audio-language-1719'
        );
        const languages = [...new Set(
            currentItems().map(item => item.language).filter(Boolean)
        )].sort();

        languageSelect.innerHTML = [
            `<option value="all">${escapeHtml(t.allLanguages)}</option>`,
            ...languages.map(language => `
                <option value="${escapeHtml(language)}">
                    ${escapeHtml(language.toUpperCase())}
                </option>
            `)
        ].join('');
        languageSelect.value = languages.includes(state.language)
            ? state.language
            : 'all';
        state.language = languageSelect.value;

        node.querySelector('#wrn-audio-tab-status-1719')
            .textContent = '';

        renderCards();
        updatePlayer();
    };

    const hideRegularContent = () => {
        [
            document.getElementById('feed-container'),
            document.getElementById('archive-container'),
            document.getElementById('event-filter-panel'),
            document.getElementById('txt-archive-title')
        ].filter(Boolean).forEach(node => {
            if (!hiddenNodes.has(node)) {
                hiddenNodes.set(node, node.style.display || '');
            }
            node.style.display = 'none';
        });
    };

    const restoreRegularContent = () => {
        hiddenNodes.forEach((display, node) => {
            if (display) {
                node.style.display = display;
            } else {
                node.style.removeProperty('display');
            }
        });
        hiddenNodes.clear();
    };

    const open = () => {
        const node = ensurePanel();
        hideRegularContent();
        node.hidden = false;
        node.scrollIntoView({ block: 'start' });

        if (!state.loaded && !state.loading) {
            void load(false);
        } else {
            render();
        }
    };

    const close = () => {
        if (panel) panel.hidden = true;
        restoreRegularContent();
    };

    document.addEventListener('click', event => {
        const audioTab = event.target.closest?.(
            '.wrn-top-tab[data-key="audio"]'
        );

        if (audioTab) {
            event.preventDefault();
            event.stopImmediatePropagation();

            document.querySelectorAll('.wrn-top-tab')
                .forEach(tab => tab.classList.remove('active'));

            audioTab.classList.add('active');
            open();
            return;
        }

        const otherTab = event.target.closest?.('.wrn-top-tab');

        if (otherTab && otherTab.dataset.key !== 'audio') {
            close();
        }
    }, true);

    window.WRNAudioTab1719 = Object.freeze({
        open,
        close,
        reload: () => load(true),
        stop
    });
})();
