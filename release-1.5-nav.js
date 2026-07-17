/* WRN 1.5.2 – Reiter, Mehr-Menü und Artikel-Einzelansicht */
'use strict';

(() => {
  if (window.__wrnAppNav152Loaded) return;
  window.__wrnAppNav152Loaded = true;

  const NAV_TEXTS = {
    de: {
      start: 'Start', regions: 'Regionen', topics: 'Themen', events: 'Termine',
      audio: 'Audio', saved: 'Gespeichert', zine: 'Zine', more: 'Mehr',
      search: 'Suche', menu: 'Quellen', settings: 'Mehr & Einstellungen',
      back: 'Zurück', article: 'Artikel', language: 'Sprache', design: 'Design',
      fontSize: 'Schriftgröße', view: 'Artikelansicht', format: 'Format',
      sort: 'Sortierung', info: 'Info', contact: 'Kontakt', donate: 'Spenden',
      storage: 'Speicher', status: 'Status', clear: 'App zurücksetzen'
    },
    en: {
      start: 'Start', regions: 'Regions', topics: 'Topics', events: 'Events',
      audio: 'Audio', saved: 'Saved', zine: 'Zine', more: 'More',
      search: 'Search', menu: 'Sources', settings: 'More & settings',
      back: 'Back', article: 'Article', language: 'Language', design: 'Design',
      fontSize: 'Font size', view: 'Article view', format: 'Format',
      sort: 'Sorting', info: 'Info', contact: 'Contact', donate: 'Donate',
      storage: 'Storage', status: 'Status', clear: 'Reset app'
    }
  };

  const TABS = [
    {
      key: 'start',
      activate: () => {
        closeAuxiliaryPanels();
        if (typeof ladeKontinentNews === 'function') ladeKontinentNews('Global');
      }
    },
    {
      key: 'regions',
      subTabs: [
        ['Global','Global'], ['Europe','Europa'], ['Africa','Afrika'],
        ['North America','Nordamerika'], ['Latin America','Lateinamerika'],
        ['Asia','Asien'], ['Australia & NZ','Australien']
      ],
      activate: subKey => {
        closeAuxiliaryPanels();
        const target = subKey || state.subSelections.regions || 'Global';
        state.subSelections.regions = target;
        if (typeof ladeKontinentNews === 'function') ladeKontinentNews(target);
      }
    },
    {
      key: 'topics',
      subTabs: [
        ['Labor Struggles','Arbeit'], ['Antifascism','Antifa'],
        ['Antiracism','Antirassismus'], ['Queer-Feminism','Queer'],
        ['No Borders','No Borders'], ['Squatting & Housing','Wohnen'],
        ['Eco-Anarchism','Klima'], ['Anti-Imperialism','Anti-Imp'],
        ['Theory & Strategy','Theorie']
      ],
      activate: subKey => {
        closeAuxiliaryPanels();
        const target = subKey || state.subSelections.topics || 'Labor Struggles';
        state.subSelections.topics = target;
        if (typeof ladeKontinentNews === 'function') ladeKontinentNews(target);
      }
    },
    {
      key: 'events',
      activate: () => {
        closeAuxiliaryPanels();
        if (typeof ladeKontinentNews === 'function') ladeKontinentNews('Radar');
        const panel = document.getElementById('event-filter-panel');
        if (panel) panel.hidden = false;
      }
    },
    {
      key: 'audio',
      subTabs: [
        ['original','Original-Podcasts'],
        ['generated','Erzeugte Podcasts'],
        ['radio','Live-Radio']
      ],
      activate: subKey => {
        closeAuxiliaryPanels();
        const target = subKey || state.subSelections.audio || 'original';
        state.subSelections.audio = target;
        if (typeof openAudioHub === 'function') openAudioHub(target);
      }
    },
    {
      key: 'saved',
      subTabs: [
        ['bookmarks','Später lesen'],
        ['read','Gelesen']
      ],
      activate: subKey => {
        closeAuxiliaryPanels();
        const target = subKey || state.subSelections.saved || 'bookmarks';
        state.subSelections.saved = target;
        if (target === 'bookmarks' && typeof ladeBookmarks === 'function') ladeBookmarks();
        if (target === 'read' && typeof ladeReadArticles === 'function') ladeReadArticles();
      }
    },
    {
      key: 'zine',
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

  let detailState = null;

  function $(selector, root = document) {
    return root.querySelector(selector);
  }

  function $all(selector, root = document) {
    return Array.from(root.querySelectorAll(selector));
  }

  function languageKey() {
    const value = document.documentElement.lang
      || document.getElementById('ui-language')?.value
      || 'de';
    return String(value).toLowerCase().startsWith('de') ? 'de' : 'en';
  }

  function texts() {
    return NAV_TEXTS[languageKey()] || NAV_TEXTS.de;
  }

  function closeAuxiliaryPanels() {
    const panel = document.getElementById('event-filter-panel');
    if (panel) panel.hidden = true;
  }

  function makeButton(className, text, title) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = className;
    button.textContent = text;
    if (title) button.title = title;
    return button;
  }

  function injectBrand(header) {
    const first = header?.querySelector('div');
    if (!first || $('.wrn-brand', first)) return;

    const title = first.querySelector('h1');
    if (!title) return;

    const brand = document.createElement('div');
    brand.className = 'wrn-brand';

    const logo = document.createElement('img');
    logo.src = './wrn-logo.webp?v=152';
    logo.alt = 'World Revolution News Logo';

    const textWrap = document.createElement('div');
    textWrap.className = 'wrn-brand-text';

    title.parentNode.insertBefore(brand, title);
    brand.append(logo, textWrap);
    textWrap.appendChild(title);

    const version = first.querySelector('.app-version-inline');
    if (version) textWrap.appendChild(version);
  }

  function buildSearchPanel(referenceNode) {
    if ($('.wrn-search-panel')) return $('.wrn-search-panel');

    const panel = document.createElement('div');
    panel.className = 'wrn-search-panel';
    panel.hidden = true;
    panel.innerHTML = `
      <input class="wrn-search-input" type="search" placeholder="Artikel durchsuchen…" aria-label="Artikel durchsuchen">
      <button class="wrn-search-clear" type="button" aria-label="Suche leeren">×</button>
    `;
    referenceNode.insertAdjacentElement('afterend', panel);

    const input = $('.wrn-search-input', panel);
    const clear = $('.wrn-search-clear', panel);

    input.addEventListener('input', () => {
      const original = document.getElementById('search-input');
      if (original) original.value = input.value;
      if (typeof applyFilters === 'function') applyFilters();
    });

    clear.addEventListener('click', () => {
      input.value = '';
      const original = document.getElementById('search-input');
      if (original) original.value = '';
      if (typeof applyFilters === 'function') applyFilters();
      input.focus();
    });

    return panel;
  }

  function copyOptions(source, target) {
    target.textContent = '';
    if (!source) return;
    Array.from(source.options).forEach(option => {
      const clone = document.createElement('option');
      clone.value = option.value;
      clone.textContent = option.textContent;
      clone.disabled = option.disabled;
      target.appendChild(clone);
    });
    target.value = source.value;
  }

  function makeProxyField(labelText, originalId, handler) {
    const field = document.createElement('label');
    field.className = 'wrn-more-field';

    const label = document.createElement('span');
    label.textContent = labelText;

    const select = document.createElement('select');
    select.dataset.originalId = originalId;
    copyOptions(document.getElementById(originalId), select);

    select.addEventListener('change', () => {
      const original = document.getElementById(originalId);
      if (original) original.value = select.value;
      try {
        handler(select.value, original);
      } catch (error) {
        console.error(error);
      }
    });

    field.append(label, select);
    return field;
  }

  function actionButton(label, callback) {
    const button = makeButton('wrn-more-action', label);
    button.addEventListener('click', () => {
      closeMorePanel();
      try {
        callback();
      } catch (error) {
        console.error(error);
      }
    });
    return button;
  }

  function buildMorePanel() {
    if ($('.wrn-more-panel')) return $('.wrn-more-panel');

    const panel = document.createElement('section');
    panel.className = 'wrn-more-panel';
    panel.hidden = true;
    panel.setAttribute('aria-label', texts().settings);

    const head = document.createElement('div');
    head.className = 'wrn-more-head';

    const heading = document.createElement('strong');
    heading.className = 'wrn-more-title';
    heading.textContent = texts().settings;

    const close = makeButton('wrn-more-close', '×', 'Schließen');
    close.addEventListener('click', closeMorePanel);
    head.append(heading, close);

    const grid = document.createElement('div');
    grid.className = 'wrn-more-grid';

    grid.append(
      makeProxyField(texts().language, 'ui-language', () => {
        if (typeof changeLanguage === 'function') changeLanguage();
        window.setTimeout(updateLanguage, 0);
      }),
      makeProxyField(texts().design, 'ui-theme', value => {
        if (typeof changeTheme === 'function') changeTheme(value);
      }),
      makeProxyField(texts().fontSize, 'ui-fontsize', value => {
        if (typeof changeFontSize === 'function') changeFontSize(value);
      }),
      makeProxyField(texts().view, 'ui-news-view', value => {
        if (typeof changeNewsView === 'function') changeNewsView(value);
      }),
      makeProxyField(texts().format, 'content-type-filter', () => {
        if (typeof applyFilters === 'function') applyFilters();
      }),
      makeProxyField(texts().sort, 'sort-select', () => {
        if (typeof applyFilters === 'function') applyFilters();
      })
    );

    const actions = document.createElement('div');
    actions.className = 'wrn-more-actions';
    actions.append(
      actionButton(texts().info, () => typeof openInfo === 'function' && openInfo()),
      actionButton(texts().contact, () => typeof openFeedback === 'function' && openFeedback()),
      actionButton(texts().donate, () => typeof openDonate === 'function' && openDonate()),
      actionButton(texts().storage, () => typeof openDataControl === 'function' && openDataControl()),
      actionButton(texts().status, () => typeof openSystemStatus === 'function' && openSystemStatus()),
      actionButton(texts().clear, () => typeof clearAllData === 'function' && clearAllData())
    );

    panel.append(head, grid, actions);
    document.body.appendChild(panel);
    return panel;
  }

  function syncMoreControls() {
    const panel = $('.wrn-more-panel');
    if (!panel) return;

    $all('select[data-original-id]', panel).forEach(select => {
      const original = document.getElementById(select.dataset.originalId);
      if (!original) return;
      if (select.options.length !== original.options.length) copyOptions(original, select);
      select.value = original.value;
    });
  }

  function closeMorePanel() {
    const panel = $('.wrn-more-panel');
    const button = $('.wrn-header-button-more');
    if (panel) panel.hidden = true;
    if (button) button.setAttribute('aria-expanded', 'false');
  }

  function toggleMorePanel() {
    const panel = buildMorePanel();
    const button = $('.wrn-header-button-more');
    const search = $('.wrn-search-panel');

    if (search) search.hidden = true;
    panel.hidden = !panel.hidden;
    if (!panel.hidden) syncMoreControls();
    if (button) button.setAttribute('aria-expanded', String(!panel.hidden));
  }

  function injectHeaderControls(header) {
    if (!header || $('.wrn-header-actions', header)) return;

    const right = header.querySelector('.header-controls') || document.createElement('div');
    right.classList.add('header-controls');

    const actions = document.createElement('div');
    actions.className = 'wrn-header-actions';

    const sourcesButton = makeButton(
      'wrn-header-button wrn-header-button-icon',
      '☰',
      texts().menu
    );
    sourcesButton.setAttribute('aria-label', texts().menu);
    sourcesButton.addEventListener('click', () => {
      closeMorePanel();
      if (typeof openSourcesModal === 'function') openSourcesModal();
    });

    const searchButton = makeButton(
      'wrn-header-button wrn-header-button-icon',
      '⌕',
      texts().search
    );
    searchButton.setAttribute('aria-label', texts().search);
    searchButton.addEventListener('click', () => {
      closeMorePanel();
      const panel = $('.wrn-search-panel');
      const input = $('.wrn-search-input', panel);
      if (!panel || !input) return;
      panel.hidden = !panel.hidden;
      if (!panel.hidden) window.setTimeout(() => input.focus(), 70);
    });

    const moreButton = makeButton(
      'wrn-header-button wrn-header-button-more',
      texts().more,
      texts().settings
    );
    moreButton.setAttribute('aria-expanded', 'false');
    moreButton.addEventListener('click', toggleMorePanel);

    actions.append(sourcesButton, searchButton, moreButton);

    if (!right.parentElement) header.appendChild(right);
    right.appendChild(actions);
  }

  function buildTopNavigation() {
    if ($('.wrn-top-tabs')) return;

    const header = document.querySelector('header');
    if (!header) return;

    const topTabs = document.createElement('nav');
    topTabs.className = 'wrn-top-tabs';
    topTabs.setAttribute('aria-label', 'Hauptnavigation');

    TABS.forEach(tab => {
      const button = makeButton('wrn-top-tab', texts()[tab.key] || tab.key);
      button.dataset.key = tab.key;
      button.addEventListener('click', () => activateTab(tab.key));
      topTabs.appendChild(button);
    });

    header.insertAdjacentElement('afterend', topTabs);

    const subWrap = document.createElement('div');
    subWrap.className = 'wrn-subtabs-wrap';
    subWrap.hidden = true;
    subWrap.innerHTML = '<div class="wrn-subtabs" aria-label="Unterkategorien"></div>';
    topTabs.insertAdjacentElement('afterend', subWrap);

    buildSearchPanel(subWrap);
  }

  function renderSubTabs(tab) {
    const wrap = $('.wrn-subtabs-wrap');
    const bar = $('.wrn-subtabs', wrap);
    if (!wrap || !bar) return;

    bar.textContent = '';
    if (!tab?.subTabs?.length) {
      wrap.hidden = true;
      return;
    }

    const selected = state.subSelections[tab.key] || tab.subTabs[0][0];
    tab.subTabs.forEach(([key, label]) => {
      const button = makeButton(
        `wrn-subtab${selected === key ? ' active' : ''}`,
        label
      );
      button.dataset.subkey = key;
      button.addEventListener('click', () => {
        state.subSelections[tab.key] = key;
        renderSubTabs(tab);
        tab.activate(key);
      });
      bar.appendChild(button);
    });

    wrap.hidden = false;
    const active = $('.wrn-subtab.active', bar);
    active?.scrollIntoView({ block: 'nearest', inline: 'center' });
  }

  function activateTab(key, fromSwipe = false) {
    if (detailState) closeArticleDetail(false);

    const tab = TABS.find(item => item.key === key);
    if (!tab) return;

    state.activeTab = key;
    document.body.dataset.wrnTab = key;
    closeMorePanel();

    const search = $('.wrn-search-panel');
    if (search && !search.hidden) search.hidden = true;

    $all('.wrn-top-tab').forEach(button => {
      const active = button.dataset.key === key;
      button.classList.toggle('active', active);
      if (active) {
        button.scrollIntoView({
          behavior: fromSwipe ? 'smooth' : 'auto',
          inline: 'center',
          block: 'nearest'
        });
      }
    });

    renderSubTabs(tab);
    try {
      tab.activate();
    } catch (error) {
      console.error(error);
    }
  }

  function updateLanguage() {
    const copy = texts();

    $all('.wrn-top-tab').forEach(button => {
      button.textContent = copy[button.dataset.key] || button.dataset.key;
    });

    const moreButton = $('.wrn-header-button-more');
    if (moreButton) moreButton.textContent = copy.more;

    const sourcesButton = $('.wrn-header-actions button:nth-child(1)');
    const searchButton = $('.wrn-header-actions button:nth-child(2)');
    if (sourcesButton) {
      sourcesButton.title = copy.menu;
      sourcesButton.setAttribute('aria-label', copy.menu);
    }
    if (searchButton) {
      searchButton.title = copy.search;
      searchButton.setAttribute('aria-label', copy.search);
    }

    const morePanel = $('.wrn-more-panel');
    if (morePanel) morePanel.remove();
  }

  function buildDetailView() {
    if ($('.wrn-article-detail')) return $('.wrn-article-detail');

    const detail = document.createElement('section');
    detail.className = 'wrn-article-detail';
    detail.hidden = true;
    detail.setAttribute('aria-label', texts().article);
    detail.innerHTML = `
      <div class="wrn-detail-topbar">
        <button class="wrn-detail-back" type="button">← ${texts().back}</button>
        <div class="wrn-detail-heading">${texts().article}</div>
        <img class="wrn-detail-logo" src="./wrn-logo.webp?v=152" alt="">
      </div>
      <div class="wrn-detail-scroll">
        <div class="wrn-detail-host"></div>
      </div>
    `;

    $('.wrn-detail-back', detail).addEventListener('click', () => {
      if (detailState?.historyPushed) history.back();
      else closeArticleDetail(false);
    });

    document.body.appendChild(detail);
    return detail;
  }

  function articleIndex(card) {
    const match = String(card?.id || '').match(/^card-(\d+)$/);
    return match ? Number(match[1]) : null;
  }

  function openArticleDetail(card) {
    if (!card || detailState) return;

    const index = articleIndex(card);
    if (!Number.isInteger(index)) return;

    const detail = buildDetailView();
    const host = $('.wrn-detail-host', detail);
    const heading = $('.wrn-detail-heading', detail);
    const placeholder = document.createElement('div');
    placeholder.className = 'wrn-card-placeholder';

    card.parentNode.insertBefore(placeholder, card);
    const savedScrollY = window.scrollY;

    if (card.dataset.expanded !== 'true' && typeof toggleArticle === 'function') {
      toggleArticle(index);
    }

    card.classList.add('wrn-detail-card');
    card.setAttribute('role', 'article');
    card.removeAttribute('tabindex');

    const title = card.querySelector('.title')?.textContent?.trim() || texts().article;
    if (heading) heading.textContent = title;

    host.appendChild(card);
    detail.hidden = false;
    document.body.classList.add('wrn-detail-open');
    $('.wrn-detail-scroll', detail).scrollTop = 0;

    detailState = {
      card,
      placeholder,
      index,
      savedScrollY,
      historyPushed: false
    };

    try {
      history.pushState({ wrnArticleDetail: true }, '', location.href);
      detailState.historyPushed = true;
    } catch {
      detailState.historyPushed = false;
    }
  }

  function closeArticleDetail(restoreScroll = true) {
    if (!detailState) return;

    const { card, placeholder, index, savedScrollY } = detailState;
    const detail = $('.wrn-article-detail');

    if (card?.dataset.expanded === 'true' && typeof toggleArticle === 'function') {
      toggleArticle(index);
    }

    card?.classList.remove('wrn-detail-card');
    card?.setAttribute('role', 'button');
    card?.setAttribute('tabindex', '0');

    if (placeholder?.parentNode && card) {
      placeholder.parentNode.replaceChild(card, placeholder);
    }

    if (detail) detail.hidden = true;
    document.body.classList.remove('wrn-detail-open');
    detailState = null;

    if (restoreScroll) {
      window.setTimeout(() => window.scrollTo({ top: savedScrollY, behavior: 'auto' }), 0);
    }
  }

  function decorateCard(card) {
    if (!card || card.dataset.wrnDetailReady === 'true') return;
    card.dataset.wrnDetailReady = 'true';
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
    card.setAttribute('aria-label', `${texts().article}: ${card.querySelector('.title')?.textContent || ''}`);

    card.addEventListener('keydown', event => {
      if ((event.key === 'Enter' || event.key === ' ') && !detailState) {
        event.preventDefault();
        openArticleDetail(card);
      }
    });
  }

  function decorateExistingCards() {
    $all('#feed-container .card, #archive-container .card').forEach(decorateCard);
  }

  function attachCardHandling() {
    decorateExistingCards();

    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (!(node instanceof Element)) return;
          if (node.matches?.('.card')) decorateCard(node);
          $all('.card', node).forEach(decorateCard);
        });
      });
    });

    ['feed-container', 'archive-container'].forEach(id => {
      const container = document.getElementById(id);
      if (container) observer.observe(container, { childList: true, subtree: true });
    });

    document.addEventListener('click', event => {
      if (detailState) return;
      const card = event.target.closest?.('#feed-container .card, #archive-container .card');
      if (!card) return;
      if (event.target.closest('button, a, input, select, textarea, summary, label')) return;
      openArticleDetail(card);
    });
  }

  function attachSwipe() {
    if (window.__wrnSwipe152Bound) return;
    window.__wrnSwipe152Bound = true;

    let startX = 0;
    let startY = 0;
    let tracking = false;

    const interactive = [
      'button', 'a', 'input', 'select', 'textarea', 'summary', 'label',
      '.wrn-top-tabs', '.wrn-subtabs', '.wrn-more-panel',
      '.wrn-article-detail', '.feedback-modal', '.global-media-bar'
    ].join(', ');

    document.addEventListener('touchstart', event => {
      if (detailState) return;
      const touch = event.changedTouches?.[0];
      if (!touch || event.target.closest(interactive)) return;
      startX = touch.clientX;
      startY = touch.clientY;
      tracking = true;
    }, { passive: true });

    document.addEventListener('touchend', event => {
      if (!tracking || detailState) return;
      tracking = false;

      const touch = event.changedTouches?.[0];
      if (!touch) return;

      const dx = touch.clientX - startX;
      const dy = touch.clientY - startY;
      if (Math.abs(dx) < 72 || Math.abs(dx) < Math.abs(dy) * 1.45) return;

      const index = TABS.findIndex(tab => tab.key === state.activeTab);
      if (index < 0) return;

      if (dx < 0 && index < TABS.length - 1) activateTab(TABS[index + 1].key, true);
      if (dx > 0 && index > 0) activateTab(TABS[index - 1].key, true);
    }, { passive: true });
  }

  function patchLanguageFunction() {
    if (window.__wrnLanguage152Patched) return;
    window.__wrnLanguage152Patched = true;

    const original = window.changeLanguage;
    if (typeof original !== 'function') return;

    window.changeLanguage = function(...args) {
      const result = original.apply(this, args);
      window.setTimeout(updateLanguage, 0);
      return result;
    };
  }

  function init() {
    const header = document.querySelector('header');
    if (!header) return;

    injectBrand(header);
    buildTopNavigation();
    injectHeaderControls(header);
    buildMorePanel();
    buildDetailView();
    attachCardHandling();
    attachSwipe();
    patchLanguageFunction();
    updateLanguage();

    const hashKey = location.hash?.replace('#tab=', '');
    if (hashKey && TABS.some(tab => tab.key === hashKey)) state.activeTab = hashKey;
    activateTab(state.activeTab);
  }

  window.addEventListener('popstate', () => {
    if (detailState) closeArticleDetail(true);
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      if (detailState) {
        if (detailState.historyPushed) history.back();
        else closeArticleDetail(true);
      } else {
        closeMorePanel();
      }
    }
  });

  document.addEventListener('click', event => {
    const panel = $('.wrn-more-panel');
    const button = $('.wrn-header-button-more');
    if (!panel || panel.hidden) return;
    if (panel.contains(event.target) || button?.contains(event.target)) return;
    closeMorePanel();
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }

  window.addEventListener('load', () => window.setTimeout(init, 180), { once: true });
})();
