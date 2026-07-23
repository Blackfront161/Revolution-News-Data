/* World Revolution News 1.8.1 – Entwicklungen und Zeitleisten */
'use strict';

(() => {
  if (window.WRNStories) return;

  const VIEW_ID = 'wrn-stories-view';
  const WATCHLIST_KEY = 'wrn_story_watchlist_v1';
  const STATE_KEY = 'wrn_story_view_state_v1';

  const TEXTS = {
    de: {
      title: 'Entwicklungen verstehen', intro: 'Hier werden Berichte verschiedener Quellen zum selben Thema als verständlicher Verlauf zusammengefasst.',
      search: 'Thema oder Quelle suchen…', period: 'Zeitraum', sources: 'Mindestens Quellen', days7: '7 Tage', days14: '14 Tage', days30: '30 Tage',
      refresh: 'Neu laden', moreFilters: 'Weitere Filter', empty: 'Im gewählten Zeitraum wurde noch kein Thema von mehreren Quellen berichtet.', articles: 'Beiträge', perspectives: 'Was die Quellen unterschiedlich berichten',
      timeline: 'Zeitleiste', watch: 'Beobachten', watching: 'Beobachtet', share: 'Teilen', copy: 'Kopiert', open: 'Artikel öffnen',
      sourcesLabel: 'Quellen', first: 'Beginn', latest: 'Neuester Stand', local: 'Lokal analysiert', terms: 'Beobachtungsliste'
    },
    en: {
      title: 'Understand developments', intro: 'Reports from different sources about the same topic are combined into an easy-to-follow timeline.',
      search: 'Search developments…', period: 'Period', sources: 'Minimum sources', days7: '7 days', days14: '14 days', days30: '30 days',
      refresh: 'Reload', moreFilters: 'More filters', empty: 'No topic was reported by multiple sources in the selected period.', articles: 'articles', perspectives: 'How sources differ',
      timeline: 'Timeline', watch: 'Watch', watching: 'Watching', share: 'Share', copy: 'Copied', open: 'Open article',
      sourcesLabel: 'Sources', first: 'Beginning', latest: 'Latest', local: 'Analyzed locally', terms: 'Watchlist'
    },
    es: {
      title:'Desarrollos y cronologías', intro:'Varios informes se agrupan localmente. No se suben datos.', search:'Buscar desarrollos…', period:'Periodo',
      sources:'Fuentes mínimas', days7:'7 días', days14:'14 días', days30:'30 días', refresh:'Recalcular', empty:'Aún no hay un desarrollo con varias fuentes.',
      articles:'artículos', perspectives:'Comparar perspectivas', timeline:'Cronología', watch:'Seguir', watching:'Siguiendo', share:'Compartir', copy:'Copiado',
      open:'Abrir artículo', sourcesLabel:'Fuentes', first:'Inicio', latest:'Último estado', local:'Análisis local', terms:'Lista de seguimiento'
    },
    fr: {
      title:'Évolutions et chronologies', intro:'Plusieurs articles sont regroupés localement. Aucune donnée n’est envoyée.', search:'Rechercher…', period:'Période',
      sources:'Sources minimum', days7:'7 jours', days14:'14 jours', days30:'30 jours', refresh:'Recalculer', empty:'Aucune évolution multi-source trouvée.',
      articles:'articles', perspectives:'Comparer les perspectives', timeline:'Chronologie', watch:'Suivre', watching:'Suivi', share:'Partager', copy:'Copié',
      open:'Ouvrir l’article', sourcesLabel:'Sources', first:'Début', latest:'Dernier état', local:'Analyse locale', terms:'Liste de suivi'
    },
    it: {
      title:'Sviluppi e cronologie', intro:'Più articoli vengono raggruppati localmente. Nessun dato viene caricato.', search:'Cerca sviluppi…', period:'Periodo',
      sources:'Fonti minime', days7:'7 giorni', days14:'14 giorni', days30:'30 giorni', refresh:'Ricalcola', empty:'Nessuno sviluppo con più fonti trovato.',
      articles:'articoli', perspectives:'Confronto delle prospettive', timeline:'Cronologia', watch:'Segui', watching:'Seguita', share:'Condividi', copy:'Copiato',
      open:'Apri articolo', sourcesLabel:'Fonti', first:'Inizio', latest:'Ultimo stato', local:'Analisi locale', terms:'Lista osservata'
    },
    pt: {
      title:'Desenvolvimentos e cronologias', intro:'Várias notícias são agrupadas localmente. Nenhum dado é enviado.', search:'Pesquisar desenvolvimentos…', period:'Período',
      sources:'Fontes mínimas', days7:'7 dias', days14:'14 dias', days30:'30 dias', refresh:'Recalcular', empty:'Ainda não foi encontrado um desenvolvimento com várias fontes.',
      articles:'artigos', perspectives:'Comparar perspetivas', timeline:'Cronologia', watch:'Observar', watching:'Observada', share:'Partilhar', copy:'Copiado',
      open:'Abrir artigo', sourcesLabel:'Fontes', first:'Início', latest:'Último estado', local:'Análise local', terms:'Lista de observação'
    },
    ru: {
      title:'Развитие событий и хронология', intro:'Материалы группируются локально. Данные не загружаются.', search:'Поиск событий…', period:'Период',
      sources:'Минимум источников', days7:'7 дней', days14:'14 дней', days30:'30 дней', refresh:'Пересчитать', empty:'События из нескольких источников пока не найдены.',
      articles:'материалов', perspectives:'Сравнение взглядов', timeline:'Хронология', watch:'Наблюдать', watching:'Отслеживается', share:'Поделиться', copy:'Скопировано',
      open:'Открыть статью', sourcesLabel:'Источники', first:'Начало', latest:'Последнее', local:'Локальный анализ', terms:'Список наблюдения'
    },
    el: {
      title:'Εξελίξεις και χρονολόγια', intro:'Πολλαπλές αναφορές ομαδοποιούνται τοπικά. Δεν αποστέλλονται δεδομένα.', search:'Αναζήτηση εξελίξεων…', period:'Περίοδος',
      sources:'Ελάχιστες πηγές', days7:'7 ημέρες', days14:'14 ημέρες', days30:'30 ημέρες', refresh:'Επανυπολογισμός', empty:'Δεν βρέθηκε ακόμη εξέλιξη με πολλές πηγές.',
      articles:'άρθρα', perspectives:'Σύγκριση οπτικών', timeline:'Χρονολόγιο', watch:'Παρακολούθηση', watching:'Παρακολουθείται', share:'Κοινοποίηση', copy:'Αντιγράφηκε',
      open:'Άνοιγμα άρθρου', sourcesLabel:'Πηγές', first:'Αρχή', latest:'Τελευταία εξέλιξη', local:'Τοπική ανάλυση', terms:'Λίστα παρακολούθησης'
    },
    tr: {
      title:'Gelişmeler ve zaman çizelgeleri', intro:'Birden çok haber yerel olarak gruplanır. Veri yüklenmez.', search:'Gelişme ara…', period:'Dönem',
      sources:'En az kaynak', days7:'7 gün', days14:'14 gün', days30:'30 gün', refresh:'Yeniden hesapla', empty:'Henüz çok kaynaklı bir gelişme bulunamadı.',
      articles:'yazı', perspectives:'Bakış açılarını karşılaştır', timeline:'Zaman çizelgesi', watch:'İzle', watching:'İzleniyor', share:'Paylaş', copy:'Kopyalandı',
      open:'Makaleyi aç', sourcesLabel:'Kaynaklar', first:'Başlangıç', latest:'Son durum', local:'Yerel analiz', terms:'İzleme listesi'
    }
  };

  let root = null;
  let active = false;
  let state = readLocal(STATE_KEY, { days: 30, minSources: 2, search: '' });

  function language() {
    return window.WRNI18n?.currentLanguage?.()
      || document.documentElement.lang
      || 'en';
  }

  function text() {
    return TEXTS[language()] || TEXTS.en;
  }

  function readLocal(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key) || 'null');
      return value === null ? fallback : value;
    } catch {
      return fallback;
    }
  }

  function writeLocal(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
  }

  function articles() {
    try {
      return Array.isArray(allNewsData) ? allNewsData : [];
    } catch {
      return [];
    }
  }

  function currentWatchlist() {
    return window.WRNStoriesCore?.normalizeWatchTerms(
      readLocal(WATCHLIST_KEY, [])
    ) || [];
  }

  function setWatchlist(values) {
    const normalized = window.WRNStoriesCore?.normalizeWatchTerms(values) || [];
    writeLocal(WATCHLIST_KEY, normalized);
    window.dispatchEvent(new CustomEvent('wrn-watchlist-change', { detail: { terms: normalized } }));
    return normalized;
  }

  function watchStory(story) {
    const existing = currentWatchlist();
    const candidate = (story.keywords || []).slice(0, 3).join(' ');
    const normalized = setWatchlist([...existing, candidate]);
    render();
    return normalized;
  }

  function isWatching(story) {
    const normalized = currentWatchlist().map(value =>
      window.WRNStoriesCore.normalizeToken(value)
    );
    const haystack = window.WRNStoriesCore.normalizeToken(
      `${story.title} ${(story.keywords || []).join(' ')}`
    );
    return normalized.some(value => value && haystack.includes(value));
  }

  function ensureRoot() {
    root = document.getElementById(VIEW_ID);

    if (root) return root;

    root = document.createElement('main');
    root.id = VIEW_ID;
    root.className = 'wrn-stories-view';
    root.hidden = true;

    const feed = document.getElementById('feed-container');

    if (feed?.parentElement) {
      feed.parentElement.insertBefore(root, feed);
    } else {
      document.body.appendChild(root);
    }

    return root;
  }

  function hideNews() {
    [
      'feed-container',
      'archive-container',
      'txt-archive-title',
      'event-filter-panel',
      'status-container',
      'wrn-briefing-view',
      'wrn-briefing-loading-panel'
    ].forEach(id => {
      const node = document.getElementById(id);
      if (node) node.hidden = true;
    });
  }

  function showNewsAgain() {
    ['feed-container', 'status-container'].forEach(id => {
      const node = document.getElementById(id);
      if (node) node.hidden = false;
    });
  }

  function formatDate(value) {
    const date = new Date(value || 0);
    if (!Number.isFinite(date.getTime())) return '';
    try {
      return new Intl.DateTimeFormat(language(), { dateStyle: 'medium' }).format(date);
    } catch {
      return date.toISOString().slice(0, 10);
    }
  }

  function openArticle(item) {
    try {
      const index = articles().findIndex(article =>
        window.WRNStoriesCore.itemKey(article)
        === window.WRNStoriesCore.itemKey(item)
      );

      if (index >= 0 && typeof openArticleDetail === 'function') {
        openArticleDetail(index);
        return;
      }
    } catch {}

    const link = String(item?.link || '');

    if (/^https?:\/\//i.test(link)) {
      window.open(link, '_blank', 'noopener,noreferrer');
    }
  }

  function articleSummary(item) {
    const source = item?.summary || item?.description || item?.content || item?.title || '';

    try {
      const generated = window.WRNSummaryCore?.summarizeText?.(source, {
        title: item?.title || '',
        length: 'short',
        language: item?.language || 'en'
      });

      if (generated?.plainText) return generated.plainText;
    } catch {}

    return window.WRNStoriesCore.summarizeText(source, 320);
  }

  function usefulTitle(value) {
    const title = window.WRNStoriesCore?.cleanText?.(value) || '';
    return title && !/^(kein titel|ohne titel|no title|untitled|sans titre|sin t[ií]tulo)$/i.test(title)
      ? title
      : '';
  }

  function displayTitle(story) {
    return usefulTitle(story?.title)
      || story?.items?.map(item => usefulTitle(item?.title)).find(Boolean)
      || text().latest;
  }

  function shareStory(story, button) {
    const copy = text();
    const lines = [
      displayTitle(story),
      `${copy.sourcesLabel}: ${story.sources.join(', ')}`,
      ''
    ];

    for (const item of story.items) {
      lines.push(`${formatDate(window.WRNStoriesCore.dateMs(item))} · ${window.WRNStoriesCore.sourceName(item)}`);
      lines.push(window.WRNStoriesCore.cleanText(item.title));
      if (item.link) lines.push(item.link);
      lines.push('');
    }

    const payload = lines.join('\n').trim();

    if (navigator.share) {
      navigator.share({ title: displayTitle(story), text: payload }).catch(() => {});
      return;
    }

    navigator.clipboard?.writeText(payload).then(() => {
      const old = button.textContent;
      button.textContent = `✓ ${copy.copy}`;
      window.setTimeout(() => { button.textContent = old; }, 1200);
    }).catch(() => {});
  }

  function makeControls(container) {
    const copy = text();
    const controls = document.createElement('section');
    controls.className = 'wrn-stories-controls';

    const search = document.createElement('input');
    search.type = 'search';
    search.placeholder = copy.search;
    search.value = state.search || '';
    search.addEventListener('input', () => {
      state.search = search.value;
      writeLocal(STATE_KEY, state);
      renderStories();
    });

    const period = document.createElement('select');
    period.setAttribute('aria-label', copy.period);
    [
      [7, copy.days7],
      [14, copy.days14],
      [30, copy.days30]
    ].forEach(([value, label]) => {
      const option = document.createElement('option');
      option.value = String(value);
      option.textContent = label;
      period.appendChild(option);
    });
    period.value = String(state.days || 30);
    period.addEventListener('change', () => {
      state.days = Number(period.value);
      writeLocal(STATE_KEY, state);
      renderStories();
    });

    const advanced = document.createElement('details');
    advanced.className = 'wrn-stories-advanced';
    const advancedLabel = document.createElement('summary');
    advancedLabel.textContent = copy.moreFilters || copy.sources;
    const advancedBody = document.createElement('div');

    const minimum = document.createElement('select');
    minimum.setAttribute('aria-label', copy.sources);
    [2, 3, 4].forEach(value => {
      const option = document.createElement('option');
      option.value = String(value);
      option.textContent = `${copy.sources}: ${value}`;
      minimum.appendChild(option);
    });
    minimum.value = String(state.minSources || 2);
    minimum.addEventListener('change', () => {
      state.minSources = Number(minimum.value);
      writeLocal(STATE_KEY, state);
      renderStories();
    });

    const refresh = document.createElement('button');
    refresh.type = 'button';
    refresh.textContent = `↻ ${copy.refresh}`;
    refresh.addEventListener('click', renderStories);

    advancedBody.append(minimum, refresh);
    advanced.append(advancedLabel, advancedBody);
    controls.append(search, period, advanced);
    container.appendChild(controls);
  }

  function storyCard(story) {
    const copy = text();
    const card = document.createElement('article');
    card.className = 'wrn-story-card';
    card.dataset.storyId = story.id;

    const heading = document.createElement('div');
    heading.className = 'wrn-story-heading';

    const titleWrap = document.createElement('div');
    const title = document.createElement('h3');
    title.textContent = displayTitle(story);
    const meta = document.createElement('p');
    meta.className = 'wrn-story-meta';
    meta.textContent = `${story.itemCount} ${copy.articles} · ${story.sourceCount} ${copy.sourcesLabel.toLocaleLowerCase()} · ${formatDate(story.oldest)} → ${formatDate(story.newest)}`;
    titleWrap.append(title, meta);

    const actions = document.createElement('div');
    actions.className = 'wrn-story-actions';

    const watch = document.createElement('button');
    watch.type = 'button';
    watch.textContent = isWatching(story) ? `★ ${copy.watching}` : `☆ ${copy.watch}`;
    watch.setAttribute('aria-pressed', String(isWatching(story)));
    watch.addEventListener('click', () => watchStory(story));

    const share = document.createElement('button');
    share.type = 'button';
    share.textContent = `↗ ${copy.share}`;
    share.addEventListener('click', () => shareStory(story, share));

    actions.append(watch, share);
    heading.append(titleWrap, actions);
    card.appendChild(heading);

    const sourceLine = document.createElement('div');
    sourceLine.className = 'wrn-story-sources';
    sourceLine.textContent = `${copy.sourcesLabel}: ${story.sources.join(' · ')}`;
    card.appendChild(sourceLine);

    const timeline = document.createElement('details');
    timeline.open = false;
    const timelineSummary = document.createElement('summary');
    timelineSummary.textContent = copy.timeline;
    const list = document.createElement('ol');
    list.className = 'wrn-story-timeline';

    story.items.forEach((item, index) => {
      const row = document.createElement('li');
      const rowHead = document.createElement('div');
      rowHead.className = 'wrn-story-timeline-head';
      rowHead.textContent = `${index === 0 ? copy.first : (index === story.items.length - 1 ? copy.latest : formatDate(window.WRNStoriesCore.dateMs(item)))} · ${window.WRNStoriesCore.sourceName(item)}`;
      const rowTitle = document.createElement('strong');
      rowTitle.textContent = window.WRNStoriesCore.cleanText(item.title);
      const summary = document.createElement('p');
      summary.textContent = articleSummary(item);
      const open = document.createElement('button');
      open.type = 'button';
      open.textContent = copy.open;
      open.addEventListener('click', () => openArticle(item));
      row.append(rowHead, rowTitle, summary, open);
      list.appendChild(row);
    });

    timeline.append(timelineSummary, list);
    card.appendChild(timeline);

    const perspectives = document.createElement('details');
    const perspectiveSummary = document.createElement('summary');
    perspectiveSummary.textContent = copy.perspectives;
    const grid = document.createElement('div');
    grid.className = 'wrn-story-perspectives';

    window.WRNStoriesCore.perspectiveRows(story).forEach(row => {
      const column = document.createElement('section');
      const source = document.createElement('h4');
      source.textContent = row.source;
      const itemTitle = document.createElement('strong');
      itemTitle.textContent = row.title;
      const summary = document.createElement('p');
      summary.textContent = row.summary;
      column.append(source, itemTitle, summary);
      grid.appendChild(column);
    });

    perspectives.append(perspectiveSummary, grid);
    card.appendChild(perspectives);

    return card;
  }

  function renderStories() {
    const list = root?.querySelector('.wrn-stories-list');
    if (!list || !window.WRNStoriesCore) return;

    const stories = window.WRNStoriesCore.clusterStories(articles(), {
      days: Number(state.days || 30),
      minSources: Number(state.minSources || 2)
    });

    const query = window.WRNStoriesCore.normalizeToken(state.search || '');
    const filtered = query
      ? stories.filter(story =>
          window.WRNStoriesCore.normalizeToken(
            `${story.title} ${story.sources.join(' ')} ${story.keywords.join(' ')}`
          ).includes(query)
        )
      : stories;

    list.textContent = '';

    if (!filtered.length) {
      const empty = document.createElement('div');
      empty.className = 'wrn-stories-empty';
      empty.textContent = text().empty;
      list.appendChild(empty);
      return;
    }

    filtered.slice(0, 24).forEach(story => list.appendChild(storyCard(story)));
  }

  function render() {
    const view = ensureRoot();
    const copy = text();
    view.textContent = '';
    view.setAttribute('lang', language());

    const head = document.createElement('header');
    head.className = 'wrn-stories-topbar';
    const title = document.createElement('h2');
    title.textContent = copy.title;
    const intro = document.createElement('p');
    intro.textContent = `🔒 ${copy.intro}`;
    head.append(title, intro);
    view.appendChild(head);

    makeControls(view);

    const list = document.createElement('section');
    list.className = 'wrn-stories-list';
    list.setAttribute('aria-live', 'polite');
    view.appendChild(list);

    renderStories();
  }

  function show() {
    active = true;
    hideNews();
    const view = ensureRoot();
    view.hidden = false;
    document.body.classList.add('wrn-stories-active');
    render();
  }

  function hide() {
    active = false;
    document.body.classList.remove('wrn-stories-active');
    if (root) root.hidden = true;
    showNewsAgain();
  }

  function refreshLanguage() {
    if (active) render();
  }

  window.addEventListener('wrn-language-change', refreshLanguage);
  window.addEventListener('wrn-watchlist-change', () => {
    if (active) renderStories();
  });

  window.WRNStories = Object.freeze({
    show,
    hide,
    render,
    refreshLanguage,
    getWatchlist: currentWatchlist,
    setWatchlist,
    test: Object.freeze({
      clusterStories: (...args) => window.WRNStoriesCore.clusterStories(...args),
      isWatching
    })
  });
})();
