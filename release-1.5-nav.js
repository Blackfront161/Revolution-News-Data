
/* WRN 1.5 – app-like navigation and swipe tabs */
'use strict';

(() => {
  if (window.__wrnAppNav15Loaded) return;
  window.__wrnAppNav15Loaded = true;

  const TABS = [
    {
      key: 'start',
      label: 'Start',
      kind: 'home',
      activate: () => {
        closeAuxiliaryPanels();
        if (typeof ladeKontinentNews === 'function') ladeKontinentNews('Global');
        setActiveOriginalNav('Global');
      }
    },
    {
      key: 'regions',
      label: 'Regionen',
      kind: 'subnav',
      subTabs: [
        ['Global','Global'], ['Europe','Europa'], ['Africa','Afrika'],
        ['North America','Nordamerika'], ['Latin America','Lateinamerika'],
        ['Asia','Asien'], ['Australia & NZ','Australien']
      ],
      activate: (subKey) => {
        closeAuxiliaryPanels();
        const target = subKey || state.subSelections.regions || 'Global';
        state.subSelections.regions = target;
        if (typeof ladeKontinentNews === 'function') ladeKontinentNews(target);
        setActiveOriginalNav(target);
      }
    },
    {
      key: 'topics',
      label: 'Themen',
      kind: 'subnav',
      subTabs: [
        ['Labor Struggles','Arbeit'], ['Antifascism','Antifa'], ['Antiracism','Antirassismus'],
        ['Queer-Feminism','Queer'], ['No Borders','No Borders'], ['Squatting & Housing','Wohnen'],
        ['Eco-Anarchism','Klima'], ['Anti-Imperialism','Anti-Imp'], ['Theory & Strategy','Theorie']
      ],
      activate: (subKey) => {
        closeAuxiliaryPanels();
        const target = subKey || state.subSelections.topics || 'Labor Struggles';
        state.subSelections.topics = target;
        if (typeof ladeKontinentNews === 'function') ladeKontinentNews(target);
        setActiveOriginalNav(target);
      }
    },
    {
      key: 'events',
      label: 'Termine',
      kind: 'action',
      activate: () => {
        closeAuxiliaryPanels();
        if (typeof ladeKontinentNews === 'function') ladeKontinentNews('Radar');
        setActiveOriginalNav('Radar');
        const panel = document.getElementById('event-filter-panel');
        if (panel) panel.hidden = false;
      }
    },
    {
      key: 'audio',
      label: 'Audio',
      kind: 'subnav-action',
      subTabs: [
        ['original','Original-Podcasts'],
        ['generated','Erzeugte Podcasts'],
        ['radio','Live-Radio']
      ],
      activate: (subKey) => {
        closeAuxiliaryPanels();
        const target = subKey || state.subSelections.audio || 'original';
        state.subSelections.audio = target;
        if (typeof openAudioHub === 'function') openAudioHub(target);
      }
    },
    {
      key: 'saved',
      label: 'Gespeichert',
      kind: 'subnav-action',
      subTabs: [
        ['bookmarks','Später lesen'],
        ['read','Gelesen']
      ],
      activate: (subKey) => {
        closeAuxiliaryPanels();
        const target = subKey || state.subSelections.saved || 'bookmarks';
        state.subSelections.saved = target;
        if (target === 'bookmarks' && typeof ladeBookmarks === 'function') ladeBookmarks();
        if (target === 'read' && typeof ladeReadArticles === 'function') ladeReadArticles();
      }
    },
    {
      key: 'zine',
      label: 'Zine',
      kind: 'action',
      activate: () => {
        closeAuxiliaryPanels();
        if (typeof openZineManager === 'function') openZineManager();
      }
    }
  ];

  const state = {
    activeTab: 'start',
    subSelections: {
      regions: 'Global',
      topics: 'Labor Struggles',
      audio: 'original',
      saved: 'bookmarks'
    }
  };

  function $(sel, root=document) { return root.querySelector(sel); }
  function $all(sel, root=document) { return Array.from(root.querySelectorAll(sel)); }

  function closeAuxiliaryPanels() {
    const panel = document.getElementById('event-filter-panel');
    if (panel) panel.hidden = true;
  }

  function setActiveOriginalNav(label) {
    const all = $all('.nav-bar .btn-nav');
    all.forEach(btn => btn.classList.remove('active'));
    const byText = all.find(btn => (btn.textContent || '').trim().toLowerCase() === String(label).trim().toLowerCase());
    if (byText) byText.classList.add('active');
  }

  function injectHeaderControls(header) {
    if (!header || $('.wrn-header-actions', header)) return;
    const right = header.querySelector('.header-controls') || document.createElement('div');
    right.classList.add('header-controls');

    const actionBox = document.createElement('div');
    actionBox.className = 'wrn-header-actions';

    const searchBtn = document.createElement('button');
    searchBtn.className = 'wrn-header-icon';
    searchBtn.type = 'button';
    searchBtn.innerHTML = '🔎';
    searchBtn.title = 'Suche';
    searchBtn.onclick = () => {
      const panel = document.querySelector('.wrn-search-panel');
      const input = panel?.querySelector('.wrn-search-input');
      if (!panel || !input) return;
      panel.hidden = !panel.hidden;
      if (!panel.hidden) setTimeout(() => input.focus(), 80);
    };

    const menuBtn = document.createElement('button');
    menuBtn.className = 'wrn-header-icon';
    menuBtn.type = 'button';
    menuBtn.innerHTML = '☰';
    menuBtn.title = 'Menü';
    menuBtn.onclick = () => {
      if (typeof openSourcesModal === 'function') openSourcesModal();
    };

    actionBox.appendChild(menuBtn);
    actionBox.appendChild(searchBtn);

    if (!right.parentElement) header.appendChild(right);
    right.appendChild(actionBox);
  }

  function injectBrand(header) {
    const first = header?.querySelector('div');
    if (!first || $('.wrn-brand', first)) return;

    const title = first.querySelector('h1');
    if (!title) return;

    const wrap = document.createElement('div');
    wrap.className = 'wrn-brand';

    const img = document.createElement('img');
    img.src = './wrn-logo.webp?v=151';
    img.alt = 'World Revolution News Logo';

    const textWrap = document.createElement('div');
    textWrap.className = 'wrn-brand-text';

    title.parentNode.insertBefore(wrap, title);
    wrap.appendChild(img);
    wrap.appendChild(textWrap);
    textWrap.appendChild(title);
    const version = first.querySelector('.app-version-inline');
    if (version) textWrap.appendChild(version);
  }

  function buildTopTabs() {
    if (document.querySelector('.wrn-top-tabs')) return;
    const header = document.querySelector('header');
    if (!header) return;

    const topTabs = document.createElement('div');
    topTabs.className = 'wrn-top-tabs';
    topTabs.setAttribute('role', 'tablist');
    topTabs.setAttribute('aria-label', 'Hauptnavigation');

    TABS.forEach(tab => {
      const btn = document.createElement('button');
      btn.className = 'wrn-top-tab';
      btn.type = 'button';
      btn.dataset.key = tab.key;
      btn.textContent = tab.label;
      btn.onclick = () => activateTab(tab.key);
      topTabs.appendChild(btn);
    });

    header.insertAdjacentElement('afterend', topTabs);

    const subWrap = document.createElement('div');
    subWrap.className = 'wrn-subtabs-wrap';
    subWrap.hidden = true;
    subWrap.innerHTML = '<div class="wrn-subtabs" role="tablist" aria-label="Unterkategorien"></div>';
    topTabs.insertAdjacentElement('afterend', subWrap);

    const searchPanel = document.createElement('div');
    searchPanel.className = 'wrn-search-panel';
    searchPanel.hidden = true;
    searchPanel.innerHTML = `
      <input class="wrn-search-input" type="search" placeholder="Artikel durchsuchen…" aria-label="Artikel durchsuchen">
      <button class="wrn-search-clear" type="button" aria-label="Suche leeren">×</button>
    `;
    subWrap.insertAdjacentElement('afterend', searchPanel);

    const searchInput = searchPanel.querySelector('.wrn-search-input');
    const clearButton = searchPanel.querySelector('.wrn-search-clear');

    searchInput.addEventListener('input', () => {
      const original = document.getElementById('search-input');
      if (original) original.value = searchInput.value;
      if (typeof applyFilters === 'function') applyFilters();
    });

    clearButton.addEventListener('click', () => {
      searchInput.value = '';
      const original = document.getElementById('search-input');
      if (original) original.value = '';
      if (typeof applyFilters === 'function') applyFilters();
      searchInput.focus();
    });
  }

  function renderSubTabs(tab) {
    const wrap = document.querySelector('.wrn-subtabs-wrap');
    const bar = wrap?.querySelector('.wrn-subtabs');
    if (!wrap || !bar) return;
    bar.innerHTML = '';

    if (!tab || !Array.isArray(tab.subTabs) || !tab.subTabs.length) {
      wrap.hidden = true;
      return;
    }

    const selected = state.subSelections[tab.key] || tab.subTabs[0][0];
    tab.subTabs.forEach(([key, label]) => {
      const btn = document.createElement('button');
      btn.className = 'wrn-subtab' + (selected === key ? ' active' : '');
      btn.type = 'button';
      btn.textContent = label;
      btn.dataset.subkey = key;
      btn.onclick = () => {
        state.subSelections[tab.key] = key;
        renderSubTabs(tab);
        tab.activate(key);
      };
      bar.appendChild(btn);
    });
    wrap.hidden = false;
  }

  function activateTab(key, fromSwipe = false) {
    const tab = TABS.find(t => t.key === key);
    if (!tab) return;
    state.activeTab = key;
    document.body.dataset.wrnTab = key;

    const searchPanel = document.querySelector('.wrn-search-panel');
    if (searchPanel && key !== 'start' && key !== 'regions' && key !== 'topics') {
      searchPanel.hidden = true;
    }

    $all('.wrn-top-tab').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.key === key);
      if (btn.dataset.key === key) {
        btn.scrollIntoView({ behavior: fromSwipe ? 'smooth' : 'auto', inline: 'center', block: 'nearest' });
      }
    });

    renderSubTabs(tab);
    try { tab.activate(); } catch (e) { console.error(e); }
  }

  function attachSwipe() {
    if (window.__wrnSwipeBound) return;
    window.__wrnSwipeBound = true;

    let startX = 0;
    let startY = 0;
    let tracking = false;

    const interactiveSelectors = 'button, a, input, select, textarea, summary, .wrn-top-tabs, .wrn-subtabs, .podcast-options-modal, .feedback-modal, .global-media-bar';

    document.addEventListener('touchstart', (ev) => {
      const touch = ev.changedTouches?.[0];
      if (!touch) return;
      if (ev.target.closest(interactiveSelectors)) return;
      startX = touch.clientX;
      startY = touch.clientY;
      tracking = true;
    }, { passive: true });

    document.addEventListener('touchend', (ev) => {
      if (!tracking) return;
      tracking = false;
      const touch = ev.changedTouches?.[0];
      if (!touch) return;
      const dx = touch.clientX - startX;
      const dy = touch.clientY - startY;
      if (Math.abs(dx) < 70 || Math.abs(dx) < Math.abs(dy) * 1.4) return;

      const idx = TABS.findIndex(tab => tab.key === state.activeTab);
      if (idx === -1) return;
      if (dx < 0 && idx < TABS.length - 1) activateTab(TABS[idx + 1].key, true);
      if (dx > 0 && idx > 0) activateTab(TABS[idx - 1].key, true);
    }, { passive: true });
  }

  function init() {
    const header = document.querySelector('header');
    if (!header) return;
    injectBrand(header);
    injectHeaderControls(header);
    buildTopTabs();
    attachSwipe();

    const startKey = location.hash?.replace('#tab=', '');
    if (startKey && TABS.some(t => t.key === startKey)) state.activeTab = startKey;
    activateTab(state.activeTab);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  // Re-apply after language/theme rerenders if needed.
  window.addEventListener('load', () => setTimeout(init, 200));
})();
