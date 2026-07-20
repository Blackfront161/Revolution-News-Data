/* World Revolution News 1.7.17 – runtime self-test */
'use strict';

(() => {
    if (window.WRNRuntimeSelfTest) return;

    const count = data => {
        if (Array.isArray(data)) return data.length;
        if (!data || typeof data !== 'object') return 0;
        for (const key of ['items','entries','episodes','stations','sources']) {
            if (Array.isArray(data[key])) return data[key].length;
        }
        return Object.keys(data).length;
    };

    const checkJson = async url => {
        try {
            const response = await fetch(
                `${url}${url.includes('?') ? '&' : '?'}test=${Date.now()}`,
                { cache: 'no-store' }
            );
            if (!response.ok) return { status: 'error', detail: `HTTP ${response.status}` };
            const data = await response.json();
            const total = count(data);
            return {
                status: total > 0 ? 'ok' : 'warning',
                detail: `${total} entries`
            };
        } catch (error) {
            return { status: 'error', detail: String(error) };
        }
    };

    async function run() {
        const urls = window.WRN_CONFIG?.dataUrls || {};
        const results = [
            {
                name: 'Version',
                status: window.WRN_CONFIG?.version === '1.7.17' ? 'ok' : 'warning',
                detail: window.WRN_CONFIG?.version || 'missing'
            },
            {
                name: 'Navigation',
                status: document.querySelectorAll('.wrn-top-tab').length >= 6
                    ? 'ok' : 'warning',
                detail: `${document.querySelectorAll('.wrn-top-tab').length} tabs`
            },
            {
                name: 'Bedienung',
                status: getComputedStyle(document.documentElement).pointerEvents === 'none'
                    ? 'error' : 'ok',
                detail: getComputedStyle(document.documentElement).pointerEvents
            }
        ];

        for (const [name, url] of [
            ['Nachrichten', urls.news || './news-feed.json'],
            ['Termine', urls.events || './events-feed.json'],
            ['Original-Podcasts', urls.podcasts || './podcasts.json'],
            ['Live-Radio', urls.radio || './radio-stations.json'],
            ['Audio-Status', urls.audioHealth || './audio-health.json']
        ]) {
            results.push({ name, ...await checkJson(url) });
        }

        return results;
    }

    function open() {
        void run().then(results => {
            const text = results
                .map(item => `${item.status.toUpperCase()}: ${item.name} – ${item.detail}`)
                .join('\n');
            window.alert(text);
        });
    }

    const install = () => {
        if (document.getElementById('wrn-selftest-open')) return true;
        const target = document.querySelector('.wrn-more-grid');
        if (!target) return false;

        const button = document.createElement('button');
        button.id = 'wrn-selftest-open';
        button.type = 'button';
        button.className = 'wrn-selftest-open';
        button.textContent = 'App-Selbsttest';
        button.addEventListener('click', open);
        target.appendChild(button);
        return true;
    };

    const init = () => {
        if (install()) return;
        let attempts = 0;
        const timer = setInterval(() => {
            attempts += 1;
            if (install() || attempts >= 30) clearInterval(timer);
        }, 250);
    };

    window.WRNRuntimeSelfTest = Object.freeze({ run, open });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
})();
