/* World Revolution News 1.8.3 – datensparsamer Video-Hub */
'use strict';

(() => {
  if (window.WRNVideoHub) return;

  const VIEW_ID = 'wrn-video-hub';
  const state = { search: '', platform: 'all', region: 'all' };
  const hiddenNodes = new Map();
  let root = null;
  let active = false;

  const TEXTS = {
    de: {
      title:'Video-Hub', intro:'Videos aus den vorhandenen Nachrichten werden lokal erkannt. Externe Anbieter laden erst nach einem Klick.',
      search:'Videos durchsuchen…', allPlatforms:'Alle Plattformen', allRegions:'Alle Regionen', global:'Global',
      europe:'Europa', africa:'Afrika', northAmerica:'Nordamerika', latinAmerica:'Lateinamerika', asia:'Asien', oceania:'Ozeanien',
      play:'Vorschau laden', close:'Vorschau schließen', open:'Beim Original öffnen', empty:'Keine passenden Videos gefunden.',
      privacy:'Datenschutz: Kein Video startet automatisch.', found:'Videos', source:'Quelle', date:'Datum'
    },
    en: {
      title:'Video hub', intro:'Videos are detected locally in the available news. External providers load only after a click.',
      search:'Search videos…', allPlatforms:'All platforms', allRegions:'All regions', global:'Global',
      europe:'Europe', africa:'Africa', northAmerica:'North America', latinAmerica:'Latin America', asia:'Asia', oceania:'Oceania',
      play:'Load preview', close:'Close preview', open:'Open original', empty:'No matching videos found.',
      privacy:'Privacy: No video starts automatically.', found:'videos', source:'Source', date:'Date'
    },
    es: {
      title:'Centro de vídeo', intro:'Los vídeos se detectan localmente en las noticias disponibles. Los proveedores externos solo cargan tras un clic.',
      search:'Buscar vídeos…', allPlatforms:'Todas las plataformas', allRegions:'Todas las regiones', global:'Global',
      europe:'Europa', africa:'África', northAmerica:'Norteamérica', latinAmerica:'Latinoamérica', asia:'Asia', oceania:'Oceanía',
      play:'Cargar vista previa', close:'Cerrar vista previa', open:'Abrir original', empty:'No se encontraron vídeos.',
      privacy:'Privacidad: ningún vídeo se inicia automáticamente.', found:'vídeos', source:'Fuente', date:'Fecha'
    },
    fr: {
      title:'Espace vidéo', intro:'Les vidéos sont détectées localement dans les actualités disponibles. Les fournisseurs externes ne chargent qu’après un clic.',
      search:'Rechercher des vidéos…', allPlatforms:'Toutes les plateformes', allRegions:'Toutes les régions', global:'Global',
      europe:'Europe', africa:'Afrique', northAmerica:'Amérique du Nord', latinAmerica:'Amérique latine', asia:'Asie', oceania:'Océanie',
      play:'Charger l’aperçu', close:'Fermer l’aperçu', open:'Ouvrir l’original', empty:'Aucune vidéo correspondante.',
      privacy:'Confidentialité : aucune vidéo ne démarre automatiquement.', found:'vidéos', source:'Source', date:'Date'
    },
    it: {
      title:'Hub video', intro:'I video vengono rilevati localmente nelle notizie disponibili. I fornitori esterni si caricano solo dopo un clic.',
      search:'Cerca video…', allPlatforms:'Tutte le piattaforme', allRegions:'Tutte le regioni', global:'Globale',
      europe:'Europa', africa:'Africa', northAmerica:'Nord America', latinAmerica:'America Latina', asia:'Asia', oceania:'Oceania',
      play:'Carica anteprima', close:'Chiudi anteprima', open:'Apri originale', empty:'Nessun video corrispondente.',
      privacy:'Privacy: nessun video parte automaticamente.', found:'video', source:'Fonte', date:'Data'
    },
    pt: {
      title:'Central de vídeo', intro:'Os vídeos são detetados localmente nas notícias disponíveis. Os fornecedores externos só carregam após um clique.',
      search:'Pesquisar vídeos…', allPlatforms:'Todas as plataformas', allRegions:'Todas as regiões', global:'Global',
      europe:'Europa', africa:'África', northAmerica:'América do Norte', latinAmerica:'América Latina', asia:'Ásia', oceania:'Oceânia',
      play:'Carregar pré-visualização', close:'Fechar pré-visualização', open:'Abrir original', empty:'Nenhum vídeo correspondente.',
      privacy:'Privacidade: nenhum vídeo inicia automaticamente.', found:'vídeos', source:'Fonte', date:'Data'
    },
    ru: {
      title:'Видеоцентр', intro:'Видео распознаются локально в доступных новостях. Внешние сервисы загружаются только после нажатия.',
      search:'Поиск видео…', allPlatforms:'Все платформы', allRegions:'Все регионы', global:'Весь мир',
      europe:'Европа', africa:'Африка', northAmerica:'Северная Америка', latinAmerica:'Латинская Америка', asia:'Азия', oceania:'Океания',
      play:'Загрузить просмотр', close:'Закрыть просмотр', open:'Открыть оригинал', empty:'Подходящих видео нет.',
      privacy:'Конфиденциальность: видео не запускаются автоматически.', found:'видео', source:'Источник', date:'Дата'
    },
    el: {
      title:'Κέντρο βίντεο', intro:'Τα βίντεο εντοπίζονται τοπικά στις διαθέσιμες ειδήσεις. Οι εξωτερικοί πάροχοι φορτώνουν μόνο μετά από κλικ.',
      search:'Αναζήτηση βίντεο…', allPlatforms:'Όλες οι πλατφόρμες', allRegions:'Όλες οι περιοχές', global:'Παγκόσμια',
      europe:'Ευρώπη', africa:'Αφρική', northAmerica:'Βόρεια Αμερική', latinAmerica:'Λατινική Αμερική', asia:'Ασία', oceania:'Ωκεανία',
      play:'Φόρτωση προεπισκόπησης', close:'Κλείσιμο προεπισκόπησης', open:'Άνοιγμα πρωτοτύπου', empty:'Δεν βρέθηκαν σχετικά βίντεο.',
      privacy:'Απόρρητο: κανένα βίντεο δεν ξεκινά αυτόματα.', found:'βίντεο', source:'Πηγή', date:'Ημερομηνία'
    },
    tr: {
      title:'Video merkezi', intro:'Videolar mevcut haberlerde yerel olarak algılanır. Harici sağlayıcılar yalnızca tıklamadan sonra yüklenir.',
      search:'Video ara…', allPlatforms:'Tüm platformlar', allRegions:'Tüm bölgeler', global:'Küresel',
      europe:'Avrupa', africa:'Afrika', northAmerica:'Kuzey Amerika', latinAmerica:'Latin Amerika', asia:'Asya', oceania:'Okyanusya',
      play:'Önizlemeyi yükle', close:'Önizlemeyi kapat', open:'Orijinali aç', empty:'Eşleşen video bulunamadı.',
      privacy:'Gizlilik: hiçbir video otomatik başlamaz.', found:'video', source:'Kaynak', date:'Tarih'
    }
  };

  const language = () => window.WRNI18n?.currentLanguage?.() || document.documentElement.lang || 'en';
  const text = () => TEXTS[language()] || TEXTS.en;
  const clean = value => String(value || '').replace(/<[^>]*>/g, ' ').replace(/&amp;/gi, '&').replace(/\s+/g, ' ').trim();
  const escapeHtml = value => String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');

  function articles() {
    try { return Array.isArray(allNewsData) ? allNewsData : []; } catch { return []; }
  }

  function safeUrl(value) {
    try {
      const url = new URL(String(value || '').replaceAll('&amp;', '&'));
      return ['http:','https:'].includes(url.protocol) ? url : null;
    } catch { return null; }
  }

  function safeId(value) {
    const id = String(value || '').trim();
    return /^[A-Za-z0-9_-]{6,80}$/.test(id) ? id : '';
  }

  function hostMatches(host, domain) {
    return host === domain || host.endsWith(`.${domain}`);
  }

  function extractUrls(article) {
    const values = [article.link, article.videoUrl, article.video, article.content, article.contentComplete]
      .filter(Boolean).map(String);
    const found = [];
    for (const value of values) {
      const decoded = value.replaceAll('&amp;', '&');
      if (/^https?:\/\//i.test(decoded.trim())) found.push(decoded.trim());
      const matches = decoded.match(/https?:\/\/[^\s"'<>]+/gi) || [];
      found.push(...matches);
    }
    return [...new Set(found.map(value => value.replace(/[),.;\]}]+$/, '')))];
  }

  function identify(raw) {
    const url = safeUrl(raw);
    if (!url) return null;
    const host = url.hostname.toLowerCase().replace(/^www\./, '');
    const path = url.pathname;

    if (host === 'youtu.be') {
      const id = safeId(path.split('/').filter(Boolean)[0]);
      return id ? {
        platform:'YouTube', key:`youtube:${id}`, url:url.href,
        embed:`https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?rel=0`
      } : null;
    }

    if (hostMatches(host, 'youtube.com') || hostMatches(host, 'youtube-nocookie.com')) {
      const id = safeId(url.searchParams.get('v') || path.match(/\/(?:embed|shorts|live|v)\/([^/?]+)/)?.[1]);
      return id ? {
        platform:'YouTube', key:`youtube:${id}`, url:url.href,
        embed:`https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?rel=0`
      } : null;
    }

    if (hostMatches(host, 'vimeo.com')) {
      const id = path.match(/\/(?:video\/)?(\d+)(?:$|\/)/)?.[1] || '';
      return id ? {
        platform:'Vimeo', key:`vimeo:${id}`, url:url.href,
        embed:`https://player.vimeo.com/video/${encodeURIComponent(id)}?dnt=1`
      } : null;
    }

    const peerTubeId = safeId(
      path.match(/^\/videos\/(?:watch|embed)\/([^/?]+)/)?.[1]
      || path.match(/^\/w\/([^/?]+)/)?.[1]
    );
    const securePeerTube = url.protocol === 'https:' || ['localhost','127.0.0.1'].includes(host);
    if (peerTubeId && securePeerTube) {
      return {
        platform:'PeerTube', key:`peertube:${url.origin}:${peerTubeId}`, url:url.href,
        embed:`${url.origin}/videos/embed/${encodeURIComponent(peerTubeId)}`
      };
    }

    return null;
  }

  function regionOf(article) {
    return window.WRNAudioRegionCore?.canonicalRegion?.(
      article.kontinent || article.region || article.continent,
      article.country
    ) || 'unknown';
  }

  function videoRows() {
    const seen = new Set();
    const rows = [];
    for (const article of articles()) {
      const match = extractUrls(article).map(identify).find(Boolean);
      if (!match || seen.has(match.key)) continue;
      seen.add(match.key);
      rows.push({
        ...match,
        title: clean(article.title) || match.platform,
        source: clean(article.quelleName || article.sourceName || article.source) || match.platform,
        summary: clean(article.content).slice(0, 260),
        articleUrl: safeUrl(article.link)?.href || match.url,
        date: article.pubDate || article.published || article.date || '',
        region: regionOf(article)
      });
    }
    return rows.sort((a,b) => new Date(b.date || 0) - new Date(a.date || 0));
  }

  function regionLabel(key) {
    const t = text();
    return ({ all:t.allRegions, global:t.global, europe:t.europe, africa:t.africa,
      'north-america':t.northAmerica, 'latin-america':t.latinAmerica,
      asia:t.asia, oceania:t.oceania, unknown:t.global })[key] || key;
  }

  function filteredRows() {
    const query = state.search.toLowerCase();
    return videoRows().filter(row => {
      if (state.platform !== 'all' && row.platform !== state.platform) return false;
      if (state.region !== 'all' && row.region !== state.region) return false;
      if (!query) return true;
      return `${row.title} ${row.source} ${row.summary}`.toLowerCase().includes(query);
    });
  }

  function closeFrame(frame) {
    if (!frame) return;
    const card = frame.closest('.wrn-video-card');
    const button = card?.querySelector('[data-video-preview]');
    frame.replaceChildren();
    frame.dataset.open = 'false';
    if (button) {
      button.textContent = text().play;
      button.setAttribute('aria-expanded', 'false');
    }
  }

  function closeAllFrames(except = null) {
    root?.querySelectorAll('.wrn-video-frame[data-open="true"]').forEach(frame => {
      if (frame !== except) closeFrame(frame);
    });
  }

  function ensureRoot() {
    if (root) return root;
    root = document.createElement('section');
    root.id = VIEW_ID;
    root.className = 'wrn-video-hub';
    root.hidden = true;
    const feed = document.getElementById('feed-container');
    if (feed?.parentElement) feed.parentElement.insertBefore(root, feed);
    else document.body.appendChild(root);

    root.addEventListener('click', event => {
      const button = event.target.closest('[data-video-preview]');
      if (!button) return;
      const card = button.closest('.wrn-video-card');
      const frame = card?.querySelector('.wrn-video-frame');
      if (!frame) return;

      if (frame.dataset.open === 'true') {
        closeFrame(frame);
        return;
      }

      const preview = safeUrl(button.dataset.videoPreview);
      if (!preview || preview.protocol !== 'https:') return;

      closeAllFrames(frame);
      const iframe = document.createElement('iframe');
      iframe.src = preview.href;
      iframe.loading = 'eager';
      iframe.allow = 'encrypted-media; fullscreen; picture-in-picture';
      iframe.allowFullscreen = true;
      iframe.referrerPolicy = 'strict-origin';
      iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-presentation allow-popups');
      iframe.title = card.querySelector('h3')?.textContent || 'Video';
      frame.replaceChildren(iframe);
      frame.dataset.open = 'true';
      button.textContent = text().close;
      button.setAttribute('aria-expanded', 'true');
    });
    return root;
  }

  function render() {
    const view = ensureRoot();
    const t = text();
    const all = videoRows();
    const rows = filteredRows();
    const platforms = [...new Set(all.map(row => row.platform))].sort();
    const regions = [...new Set(all.map(row => row.region).filter(region => region !== 'unknown'))];

    view.innerHTML = `
      <header class="wrn-video-head">
        <div><h2>${escapeHtml(t.title)}</h2><p>${escapeHtml(t.intro)}</p></div>
        <strong>${rows.length} ${escapeHtml(t.found)}</strong>
      </header>
      <div class="wrn-video-controls">
        <input type="search" data-video-search placeholder="${escapeHtml(t.search)}" value="${escapeHtml(state.search)}">
        <select data-video-platform>
          <option value="all">${escapeHtml(t.allPlatforms)}</option>
          ${platforms.map(value => `<option value="${escapeHtml(value)}" ${state.platform === value ? 'selected' : ''}>${escapeHtml(value)}</option>`).join('')}
        </select>
        <select data-video-region>
          <option value="all">${escapeHtml(t.allRegions)}</option>
          ${regions.map(value => `<option value="${escapeHtml(value)}" ${state.region === value ? 'selected' : ''}>${escapeHtml(regionLabel(value))}</option>`).join('')}
        </select>
      </div>
      <p class="wrn-video-privacy">${escapeHtml(t.privacy)}</p>
      <div class="wrn-video-list">
        ${rows.length ? rows.slice(0,120).map((row, index) => `
          <article class="wrn-video-card">
            <div class="wrn-video-card-meta"><span>${escapeHtml(row.platform)}</span><span>${escapeHtml(regionLabel(row.region))}</span></div>
            <h3>${escapeHtml(row.title)}</h3>
            <p>${escapeHtml(row.summary)}</p>
            <small>${escapeHtml(t.source)}: ${escapeHtml(row.source)}${row.date ? ` · ${escapeHtml(new Date(row.date).toLocaleDateString(language()))}` : ''}</small>
            <div class="wrn-video-actions">
              <button type="button" data-video-preview="${escapeHtml(row.embed)}" aria-controls="wrn-video-frame-${index}" aria-expanded="false">${escapeHtml(t.play)}</button>
              <a href="${escapeHtml(row.articleUrl)}" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer">${escapeHtml(t.open)}</a>
            </div>
            <div class="wrn-video-frame" id="wrn-video-frame-${index}" data-open="false"></div>
          </article>`).join('') : `<p class="wrn-video-empty">${escapeHtml(t.empty)}</p>`}
      </div>`;

    view.querySelector('[data-video-search]')?.addEventListener('input', event => {
      state.search = String(event.target.value || ''); render();
    });
    view.querySelector('[data-video-platform]')?.addEventListener('change', event => {
      state.platform = event.target.value; render();
    });
    view.querySelector('[data-video-region]')?.addEventListener('change', event => {
      state.region = event.target.value; render();
    });
  }

  function hideNews() {
    [document.getElementById('feed-container'), document.getElementById('archive-container'),
      document.getElementById('event-filter-panel'), document.getElementById('txt-archive-title')]
      .filter(Boolean).forEach(node => {
        if (!hiddenNodes.has(node)) hiddenNodes.set(node, node.style.display || '');
        node.style.display = 'none';
      });
  }

  function showNewsAgain() {
    hiddenNodes.forEach((display,node) => display ? (node.style.display = display) : node.style.removeProperty('display'));
    hiddenNodes.clear();
  }

  function show() {
    active = true;
    hideNews();
    const view = ensureRoot();
    view.hidden = false;
    document.body.classList.add('wrn-video-active');
    render();
  }

  function hide() {
    active = false;
    document.body.classList.remove('wrn-video-active');
    closeAllFrames();
    if (root) root.hidden = true;
    showNewsAgain();
  }

  window.addEventListener('wrn-language-change', () => { if (active) render(); });
  window.WRNVideoHub = Object.freeze({ version:'1.8.3', show, hide, render, rows:videoRows, identify });
})();
