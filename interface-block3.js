/* World Revolution News 1.8.3 – Block 3 interface recovery */
'use strict';

(() => {
  if (typeof window === 'undefined' || window.WRNInterfaceBlock3) return;

  const VERSION = '1.8.3-b3';
  const CORRUPTION_CATEGORY = 'WRN Corruption';
  const SOURCE_BAR_ID = 'wrn-source-range-bar-183';
  const ZINE_EDITOR_CLASS = 'wrn-zine-editor-183';
  const DAY_MS = 86400000;

  const TEXTS = Object.freeze({
    en: {
      corruption: 'Corruption', sources: 'Sources', allSources: 'All sources', period: 'Period',
      hours24: 'Last 24 hours', days7: 'Last 7 days', days30: 'Last 30 days',
      apply: 'Apply', reset: 'Reset', loading30: 'Loading the full 30-day archive…',
      loaded30: '30-day archive loaded', loadFailed: 'The archive could not be loaded. Current data remains available.',
      selected: 'selected', translate: 'Translate', zineTitle: 'Edit Zine before printing',
      title: 'Title', text: 'Article text', up: 'Move up', down: 'Move down', remove: 'Remove',
      saved: 'Changes saved locally', switching: 'Opening developments…'
    },
    de: {
      corruption: 'Korruption', sources: 'Quellen', allSources: 'Alle Quellen', period: 'Zeitraum',
      hours24: 'Letzte 24 Stunden', days7: 'Letzte 7 Tage', days30: 'Letzte 30 Tage',
      apply: 'Anwenden', reset: 'Zurücksetzen', loading30: 'Vollständiges 30-Tage-Archiv wird geladen…',
      loaded30: '30-Tage-Archiv geladen', loadFailed: 'Das Archiv konnte nicht geladen werden. Die aktuellen Daten bleiben erhalten.',
      selected: 'ausgewählt', translate: 'Übersetzen', zineTitle: 'Zine vor dem Druck bearbeiten',
      title: 'Titel', text: 'Artikeltext', up: 'Nach oben', down: 'Nach unten', remove: 'Entfernen',
      saved: 'Änderungen lokal gespeichert', switching: 'Entwicklungen werden geöffnet…'
    },
    es: {
      corruption: 'Corrupción', sources: 'Fuentes', allSources: 'Todas las fuentes', period: 'Periodo',
      hours24: 'Últimas 24 horas', days7: 'Últimos 7 días', days30: 'Últimos 30 días',
      apply: 'Aplicar', reset: 'Restablecer', loading30: 'Cargando el archivo completo de 30 días…',
      loaded30: 'Archivo de 30 días cargado', loadFailed: 'No se pudo cargar el archivo. Los datos actuales siguen disponibles.',
      selected: 'seleccionadas', translate: 'Traducir', zineTitle: 'Editar el zine antes de imprimir',
      title: 'Título', text: 'Texto del artículo', up: 'Subir', down: 'Bajar', remove: 'Eliminar',
      saved: 'Cambios guardados localmente', switching: 'Abriendo desarrollos…'
    },
    fr: {
      corruption: 'Corruption', sources: 'Sources', allSources: 'Toutes les sources', period: 'Période',
      hours24: 'Dernières 24 heures', days7: '7 derniers jours', days30: '30 derniers jours',
      apply: 'Appliquer', reset: 'Réinitialiser', loading30: 'Chargement de l’archive complète sur 30 jours…',
      loaded30: 'Archive de 30 jours chargée', loadFailed: 'L’archive n’a pas pu être chargée. Les données actuelles restent disponibles.',
      selected: 'sélectionnées', translate: 'Traduire', zineTitle: 'Modifier le zine avant impression',
      title: 'Titre', text: 'Texte de l’article', up: 'Monter', down: 'Descendre', remove: 'Retirer',
      saved: 'Modifications enregistrées localement', switching: 'Ouverture des évolutions…'
    },
    it: {
      corruption: 'Corruzione', sources: 'Fonti', allSources: 'Tutte le fonti', period: 'Periodo',
      hours24: 'Ultime 24 ore', days7: 'Ultimi 7 giorni', days30: 'Ultimi 30 giorni',
      apply: 'Applica', reset: 'Reimposta', loading30: 'Caricamento dell’archivio completo di 30 giorni…',
      loaded30: 'Archivio di 30 giorni caricato', loadFailed: 'Impossibile caricare l’archivio. I dati attuali restano disponibili.',
      selected: 'selezionate', translate: 'Traduci', zineTitle: 'Modifica lo zine prima della stampa',
      title: 'Titolo', text: 'Testo dell’articolo', up: 'Sposta su', down: 'Sposta giù', remove: 'Rimuovi',
      saved: 'Modifiche salvate localmente', switching: 'Apertura sviluppi…'
    },
    pt: {
      corruption: 'Corrupção', sources: 'Fontes', allSources: 'Todas as fontes', period: 'Período',
      hours24: 'Últimas 24 horas', days7: 'Últimos 7 dias', days30: 'Últimos 30 dias',
      apply: 'Aplicar', reset: 'Repor', loading30: 'A carregar o arquivo completo de 30 dias…',
      loaded30: 'Arquivo de 30 dias carregado', loadFailed: 'Não foi possível carregar o arquivo. Os dados atuais continuam disponíveis.',
      selected: 'selecionadas', translate: 'Traduzir', zineTitle: 'Editar o zine antes de imprimir',
      title: 'Título', text: 'Texto do artigo', up: 'Mover para cima', down: 'Mover para baixo', remove: 'Remover',
      saved: 'Alterações guardadas localmente', switching: 'A abrir desenvolvimentos…'
    },
    ru: {
      corruption: 'Коррупция', sources: 'Источники', allSources: 'Все источники', period: 'Период',
      hours24: 'Последние 24 часа', days7: 'Последние 7 дней', days30: 'Последние 30 дней',
      apply: 'Применить', reset: 'Сбросить', loading30: 'Загружается полный архив за 30 дней…',
      loaded30: 'Архив за 30 дней загружен', loadFailed: 'Не удалось загрузить архив. Текущие данные остаются доступными.',
      selected: 'выбрано', translate: 'Перевести', zineTitle: 'Редактировать зин перед печатью',
      title: 'Заголовок', text: 'Текст статьи', up: 'Выше', down: 'Ниже', remove: 'Удалить',
      saved: 'Изменения сохранены локально', switching: 'Открываются события…'
    },
    el: {
      corruption: 'Διαφθορά', sources: 'Πηγές', allSources: 'Όλες οι πηγές', period: 'Περίοδος',
      hours24: 'Τελευταίες 24 ώρες', days7: 'Τελευταίες 7 ημέρες', days30: 'Τελευταίες 30 ημέρες',
      apply: 'Εφαρμογή', reset: 'Επαναφορά', loading30: 'Φόρτωση πλήρους αρχείου 30 ημερών…',
      loaded30: 'Το αρχείο 30 ημερών φορτώθηκε', loadFailed: 'Δεν ήταν δυνατή η φόρτωση του αρχείου. Τα τρέχοντα δεδομένα παραμένουν διαθέσιμα.',
      selected: 'επιλεγμένες', translate: 'Μετάφραση', zineTitle: 'Επεξεργασία zine πριν από την εκτύπωση',
      title: 'Τίτλος', text: 'Κείμενο άρθρου', up: 'Πάνω', down: 'Κάτω', remove: 'Αφαίρεση',
      saved: 'Οι αλλαγές αποθηκεύτηκαν τοπικά', switching: 'Άνοιγμα εξελίξεων…'
    },
    tr: {
      corruption: 'Yolsuzluk', sources: 'Kaynaklar', allSources: 'Tüm kaynaklar', period: 'Dönem',
      hours24: 'Son 24 saat', days7: 'Son 7 gün', days30: 'Son 30 gün',
      apply: 'Uygula', reset: 'Sıfırla', loading30: 'Tam 30 günlük arşiv yükleniyor…',
      loaded30: '30 günlük arşiv yüklendi', loadFailed: 'Arşiv yüklenemedi. Mevcut veriler kullanılabilir durumda.',
      selected: 'seçili', translate: 'Çevir', zineTitle: 'Yazdırmadan önce zine’i düzenle',
      title: 'Başlık', text: 'Makale metni', up: 'Yukarı taşı', down: 'Aşağı taşı', remove: 'Kaldır',
      saved: 'Değişiklikler yerel olarak kaydedildi', switching: 'Gelişmeler açılıyor…'
    }
  });

  const CORRUPTION_TERMS = Object.freeze([
    'corruption', 'corrupt', 'bribery', 'bribe', 'embezzlement', 'kickback', 'graft', 'nepotism', 'cronyism',
    'korruption', 'korrupt', 'bestechung', 'bestechlich', 'veruntreuung', 'vetternwirtschaft', 'nepotismus',
    'corrupción', 'corrupcion', 'soborno', 'cohecho', 'malversación', 'malversacion',
    'corruption', 'pot-de-vin', 'pots-de-vin', 'détournement', 'detournement',
    'corruzione', 'tangente', 'tangenti', 'concussione', 'peculato',
    'corrupção', 'corrupcao', 'suborno', 'peculato',
    'коррупц', 'взятк', 'хищен', 'непотизм',
    'διαφθορ', 'δωροδοκ', 'υπεξαίρεσ',
    'yolsuzluk', 'rüşvet', 'rusvet', 'zimmet', 'kayırma', 'kayirma'
  ]);

  const state = {
    selectedSources: new Set(),
    pendingDays: 7,
    appliedDays: 0,
    fullArchiveLoaded: false,
    archiveLoading: false,
    lastCategory: '',
    storySwitching: false
  };

  const language = () => {
    const raw = String(
      window.WRNI18n?.currentLanguage?.()
      || document.getElementById('ui-language')?.value
      || document.documentElement.lang
      || 'en'
    ).toLowerCase().split(/[-_]/)[0];
    return TEXTS[raw] ? raw : 'en';
  };

  const text = () => TEXTS[language()] || TEXTS.en;
  const clean = value => String(value ?? '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  const normalize = value => clean(value).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();

  function currentCategory() {
    try { return String(activeKontinent || 'Global'); } catch { return 'Global'; }
  }

  function articles() {
    try { return Array.isArray(allNewsData) ? allNewsData : []; } catch { return []; }
  }

  function currentItems() {
    try { return Array.isArray(currentFilteredItems) ? currentFilteredItems : []; } catch { return []; }
  }

  function sourceName(item) {
    return clean(item?.quelleName || item?.sourceName || item?.source || item?.author || '');
  }

  function articleKey(item) {
    return clean(
      item?.link
      || item?.id
      || `${sourceName(item)}::${item?.title || ''}::${item?.pubDate || item?.published || ''}`
    );
  }

  function dateMs(item) {
    const raw = item?.eventStart || item?.pubDate || item?.published || item?.date || item?.createdAt;
    const value = raw ? new Date(raw).getTime() : 0;
    return Number.isFinite(value) ? value : 0;
  }

  function matchesCorruption(item) {
    const values = [
      item?.title, item?.summary, item?.description, item?.content,
      item?.kategorie, item?.category, item?.categories, item?.topics, item?.tags
    ];
    const haystack = normalize(values.flatMap(value => Array.isArray(value) ? value : [value]).join(' '));
    return CORRUPTION_TERMS.some(term => haystack.includes(normalize(term)));
  }

  function rowsForCategory(input, category = currentCategory()) {
    const rows = Array.isArray(input) ? input : [];
    if (category === CORRUPTION_CATEGORY) return rows.filter(matchesCorruption);
    if (category === 'Global' || !category) return rows;
    if (['Bookmarks', 'Read'].includes(category)) return [];
    if (typeof articleMatchesCategory === 'function') {
      try { return rows.filter(item => articleMatchesCategory(item, category)); } catch {}
    }
    return rows;
  }

  function baseArticlesForCategory(category = currentCategory()) {
    return rowsForCategory(articles(), category);
  }

  function filterRows(input, options = {}) {
    const rows = Array.isArray(input) ? input : [];
    const category = String(options.category || currentCategory());
    if (['Bookmarks', 'Read', 'Radar'].includes(category)) return [...rows];

    const selected = options.selectedSources === undefined
      ? state.selectedSources
      : new Set(options.selectedSources || []);
    const days = Number(options.days === undefined ? state.appliedDays : options.days) || 0;
    let result = category === CORRUPTION_CATEGORY
      ? rows.filter(matchesCorruption)
      : [...rows];

    if (selected.size) result = result.filter(item => selected.has(sourceName(item)));
    if (days > 0) {
      const now = Number(options.now || Date.now());
      const cutoff = now - days * DAY_MS;
      result = result.filter(item => dateMs(item) >= cutoff);
    }
    return result;
  }

  function shouldShowSourceBar() {
    const tab = document.body?.dataset?.wrnTab || '';
    return ['start', 'regions', 'topics'].includes(tab)
      && !document.body.classList.contains('wrn-detail-open');
  }

  function status(message, kind = '') {
    const node = document.querySelector(`#${SOURCE_BAR_ID} [data-source-range-status]`);
    if (!node) return;
    node.textContent = message || '';
    node.dataset.kind = kind;
  }

  function mergeRows(existing, incoming) {
    const map = new Map();
    [...existing, ...incoming].forEach(item => {
      if (!item || typeof item !== 'object') return;
      const key = articleKey(item);
      if (!key) return;
      const previous = map.get(key);
      if (!previous || dateMs(item) >= dateMs(previous)) map.set(key, item);
    });
    return [...map.values()];
  }

  function fetchJsonWithXhr(url) {
    return new Promise((resolve, reject) => {
      const request = new XMLHttpRequest();
      request.open('GET', url, true);
      request.responseType = 'json';
      request.timeout = 45000;
      request.setRequestHeader('Accept', 'application/json');
      request.onload = () => {
        if (request.status < 200 || request.status >= 300) {
          reject(new Error(`HTTP ${request.status}`));
          return;
        }
        const data = request.response;
        if (!Array.isArray(data)) {
          reject(new Error('JSON is not a list.'));
          return;
        }
        resolve(data);
      };
      request.onerror = () => reject(new Error('Network error'));
      request.ontimeout = () => reject(new Error('Timeout'));
      request.send();
    });
  }

  async function ensureThirtyDayArchive() {
    if (state.fullArchiveLoaded || state.archiveLoading) return state.fullArchiveLoaded;
    state.archiveLoading = true;
    status(text().loading30, 'loading');
    const configuredArchive = window.WRN_CONFIG?.dataUrls?.newsArchive;
    const currentFeed = window.WRN_CONFIG?.dataUrls?.news || './news-feed.json';
    const baseUrl = configuredArchive || currentFeed.replace(/news-feed\.json(?:\?.*)?$/i, 'news.json');
    const separator = baseUrl.includes('?') ? '&' : '?';
    const url = `${baseUrl}${separator}v=${Date.now()}`;

    try {
      const rows = await fetchJsonWithXhr(url);
      const cutoff = Date.now() - 31 * DAY_MS;
      const recent = rows.filter(item => {
        const value = dateMs(item);
        return value > 0 && value >= cutoff;
      });
      const merged = mergeRows(articles(), recent);
      try { allNewsData = merged; } catch {}
      window.WRNSourceProfiles?.setArticles?.(merged);
      try {
        window.WRNStorage?.putDataset?.('news-30-day', recent).catch?.(() => false);
      } catch {}
      state.fullArchiveLoaded = true;
      status(`${text().loaded30}: ${recent.length}`, 'ok');
      return true;
    } catch (error) {
      console.warn('WRN 30-day archive:', error);
      status(text().loadFailed, 'error');
      return false;
    } finally {
      state.archiveLoading = false;
    }
  }

  function sourceUniverse() {
    return [...new Set(baseArticlesForCategory().map(sourceName).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, language()))
      .slice(0, 200);
  }

  function renderSourceChoices() {
    const container = document.querySelector(`#${SOURCE_BAR_ID} [data-source-range-choices]`);
    const count = document.querySelector(`#${SOURCE_BAR_ID} [data-source-range-count]`);
    if (!container) return;
    const names = sourceUniverse();
    container.textContent = '';

    names.forEach(name => {
      const label = document.createElement('label');
      label.className = 'wrn-source-range-chip-183';
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.value = name;
      input.checked = state.selectedSources.has(name);
      input.addEventListener('change', () => {
        if (input.checked) state.selectedSources.add(name);
        else state.selectedSources.delete(name);
        updateSourceCount();
      });
      const span = document.createElement('span');
      span.textContent = name;
      label.append(input, span);
      container.appendChild(label);
    });

    if (count) count.textContent = String(names.length);
    updateSourceCount();
  }

  function updateSourceCount() {
    const toggle = document.querySelector(`#${SOURCE_BAR_ID} [data-source-range-toggle]`);
    if (!toggle) return;
    const number = state.selectedSources.size;
    toggle.textContent = number
      ? `${text().sources}: ${number} ${text().selected}`
      : `${text().sources}: ${text().allSources}`;
  }

  function ensureSourceBar() {
    let bar = document.getElementById(SOURCE_BAR_ID);
    if (bar) return bar;

    bar = document.createElement('aside');
    bar.id = SOURCE_BAR_ID;
    bar.className = 'wrn-source-range-bar-183';
    bar.hidden = true;
    bar.innerHTML = `
      <button type="button" data-source-range-toggle aria-expanded="false"></button>
      <section data-source-range-panel hidden>
        <header>
          <strong data-source-range-heading></strong>
          <span><span data-source-range-count>0</span></span>
        </header>
        <div data-source-range-choices class="wrn-source-range-choices-183"></div>
        <div class="wrn-source-range-controls-183">
          <label><span data-source-range-period></span>
            <select data-source-range-days>
              <option value="1"></option>
              <option value="7"></option>
              <option value="30"></option>
            </select>
          </label>
          <button type="button" data-source-range-apply></button>
          <button type="button" data-source-range-reset></button>
        </div>
        <p data-source-range-status aria-live="polite"></p>
      </section>`;

    bar.addEventListener('click', event => {
      const toggle = event.target.closest('[data-source-range-toggle]');
      if (toggle) {
        const panel = bar.querySelector('[data-source-range-panel]');
        panel.hidden = !panel.hidden;
        toggle.setAttribute('aria-expanded', String(!panel.hidden));
        if (!panel.hidden) renderSourceChoices();
        return;
      }
      if (event.target.closest('[data-source-range-apply]')) void applySourceRange();
      if (event.target.closest('[data-source-range-reset]')) resetSourceRange();
    });

    bar.querySelector('[data-source-range-days]').addEventListener('change', event => {
      state.pendingDays = Number(event.target.value || 7);
    });

    document.body.appendChild(bar);
    refreshSourceBarLanguage();
    return bar;
  }

  function refreshSourceBarLanguage() {
    const bar = ensureSourceBar();
    const copy = text();
    bar.querySelector('[data-source-range-heading]').textContent = copy.sources;
    bar.querySelector('[data-source-range-period]').textContent = copy.period;
    const options = bar.querySelector('[data-source-range-days]').options;
    options[0].textContent = copy.hours24;
    options[1].textContent = copy.days7;
    options[2].textContent = copy.days30;
    bar.querySelector('[data-source-range-apply]').textContent = copy.apply;
    bar.querySelector('[data-source-range-reset]').textContent = copy.reset;
    updateSourceCount();
  }

  async function applySourceRange() {
    const days = Number(
      document.querySelector(`#${SOURCE_BAR_ID} [data-source-range-days]`)?.value
      || state.pendingDays
      || 7
    );
    state.pendingDays = days;
    if (days === 30) await ensureThirtyDayArchive();
    state.appliedDays = days;
    try { window.applyFilters?.(); } catch (error) { console.error(error); }
    renderSourceChoices();
  }

  function resetSourceRange() {
    state.selectedSources.clear();
    state.pendingDays = 7;
    state.appliedDays = 0;
    const select = document.querySelector(`#${SOURCE_BAR_ID} [data-source-range-days]`);
    if (select) select.value = '7';
    status('');
    try { window.applyFilters?.(); } catch (error) { console.error(error); }
    renderSourceChoices();
  }

  function installFilterWrapper() {
    if (window.__wrnBlock3FilterWrapped || typeof window.applyFilters !== 'function') return;
    window.__wrnBlock3FilterWrapped = true;
    const originalApplyFilters = window.applyFilters;

    window.applyFilters = function(...args) {
      const result = originalApplyFilters.apply(this, args);
      queueCardDecoration();
      queueSourceBarRefresh();
      return result;
    };
  }

  function installCategoryWrapper() {
    if (window.__wrnBlock3CategoryWrapped || typeof window.ladeKontinentNews !== 'function') return;
    window.__wrnBlock3CategoryWrapped = true;
    const originalLoad = window.ladeKontinentNews;

    window.ladeKontinentNews = function(category, ...rest) {
      const value = String(category || 'Global');
      if (state.lastCategory && state.lastCategory !== value) {
        state.selectedSources.clear();
        state.appliedDays = 0;
        status('');
      }
      state.lastCategory = value;
      const result = originalLoad.call(this, value, ...rest);
      queueSourceBarRefresh();
      queueCorruptionTab();
      return result;
    };
  }

  function corruptionLabel() {
    return text().corruption;
  }

  function installCorruptionTab() {
    if (document.body?.dataset?.wrnTab !== 'topics') return;
    const bar = document.querySelector('.wrn-subtabs');
    if (!bar) return;

    let button = bar.querySelector('[data-subkey="wrn-corruption"]');
    if (!button) {
      button = document.createElement('button');
      button.type = 'button';
      button.className = 'wrn-subtab';
      button.dataset.subkey = 'wrn-corruption';
      button.addEventListener('click', () => {
        bar.querySelectorAll('.wrn-subtab').forEach(node => node.classList.remove('active'));
        button.classList.add('active');
        state.lastCategory = CORRUPTION_CATEGORY;
        window.ladeKontinentNews?.(CORRUPTION_CATEGORY);
      });
      bar.appendChild(button);
    }
    button.textContent = corruptionLabel();
    if (currentCategory() === CORRUPTION_CATEGORY) {
      bar.querySelectorAll('.wrn-subtab').forEach(node => node.classList.toggle('active', node === button));
    }
  }

  function queueCorruptionTab() {
    window.setTimeout(installCorruptionTab, 0);
    window.setTimeout(installCorruptionTab, 120);
  }

  function actionType(node) {
    if (!node || node.dataset.wrnCardOnly === 'true') return '';
    const label = normalize(node.textContent || '');
    const id = String(node.id || '').toLocaleLowerCase();
    const classes = String(node.className || '').toLocaleLowerCase();

    /* The historic generic class name "btn-translate" is used for nearly
       every article action. It must never decide the action type by itself. */
    if (node.matches('.btn-expand, [id^="expand-"]') || /weiterlesen|read more|collapse|zuklappen/.test(label)) return 'expand';
    if (id.startsWith('podcast-') || classes.includes('btn-podcast') || /podcast|audio|vorlesen|listen/.test(label)) return 'podcast';
    if (id.startsWith('bmark-') || classes.includes('btn-read-later') || /spater|later|bookmark|merken|save|favor/.test(label)) return 'later';
    if (id.startsWith('zine-') || classes.includes('btn-zine-article') || /zine/.test(label)) return 'zine';
    if (id.startsWith('readstate-') || classes.includes('btn-read-state') || /gelesen|mark read|\bread\b|leido|okun/.test(label)) return 'read';
    if (/share|teilen|partag|compart|condiv|paylas|κοινο/.test(label)) return 'share';
    if (node.matches('a[href], [data-link], [data-url]') && /original|quelle|source/.test(label)) return 'original';
    if (id.startsWith('btn-') || /ubersetz|translate|traduc|tradu|перев|μεταφ|cevir/.test(label)) return 'translate';
    return '';
  }

  function compactTranslateLabel(original) {
    const value = clean(original?.textContent || text().translate).replace(/^\[|\]$/g, '').trim();
    return value || text().translate;
  }

  function decorateCard(card) {
    if (!(card instanceof Element)) return;
    const row = card.querySelector('.button-row');
    const meta = card.querySelector('.meta');
    if (!row || !meta) return;

    const typed = new Map();
    [...row.children].forEach(node => {
      const type = actionType(node);
      if (!type || typed.has(type)) return;
      typed.set(type, node);
      node.dataset.wrnArticleAction = type;
    });

    const order = ['expand', 'translate', 'podcast', 'later', 'zine', 'read', 'share', 'original'];
    order.forEach(type => {
      const node = typed.get(type);
      if (node) row.appendChild(node);
    });

    const originalTranslate = typed.get('translate');
    if (originalTranslate) {
      originalTranslate.dataset.wrnTranslatePrimary = 'true';
      let compact = meta.querySelector('[data-wrn-card-only="true"]');
      if (!compact) {
        compact = document.createElement('button');
        compact.type = 'button';
        compact.className = 'wrn-card-language-action-183';
        compact.dataset.wrnCardOnly = 'true';
        compact.textContent = '文';
        compact.addEventListener('click', event => {
          event.preventDefault();
          event.stopPropagation();
          originalTranslate.click();
        });
        meta.appendChild(compact);
      }
      const sync = () => {
        compact.dataset.label = compactTranslateLabel(originalTranslate);
        compact.title = compact.dataset.label;
        compact.setAttribute('aria-label', compact.dataset.label);
      };
      sync();
      if (!originalTranslate.dataset.wrnCompactObserver) {
        originalTranslate.dataset.wrnCompactObserver = '183';
        new MutationObserver(sync).observe(originalTranslate, { childList: true, characterData: true, subtree: true });
      }
    }
    card.dataset.wrnBlock3Decorated = VERSION;
  }

  let decorateQueued = false;
  function queueCardDecoration() {
    if (decorateQueued) return;
    decorateQueued = true;
    window.requestAnimationFrame(() => {
      decorateQueued = false;
      document.querySelectorAll('#feed-container .card, #archive-container .card, .wrn-detail-host .card')
        .forEach(decorateCard);
    });
  }

  function zineStorageKey() {
    try { return typeof ZINE_KEY !== 'undefined' ? ZINE_KEY : 'wrn_zine_articles'; }
    catch { return 'wrn_zine_articles'; }
  }

  function zineItems() {
    try {
      if (typeof zineArticles !== 'undefined' && Array.isArray(zineArticles)) return zineArticles;
      const parsed = JSON.parse(localStorage.getItem(zineStorageKey()) || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch { return []; }
  }

  function snapshotArticle(item) {
    if (!item || typeof item !== 'object') return null;
    try { return structuredClone(item); } catch {}
    try { return JSON.parse(JSON.stringify(item)); } catch { return { ...item }; }
  }

  function commitZine(items) {
    const safe = (Array.isArray(items) ? items : []).filter(item => item && typeof item === 'object');
    try { zineArticles = safe; } catch {}
    try {
      if (typeof saveZineArticles === 'function') saveZineArticles();
      else localStorage.setItem(zineStorageKey(), JSON.stringify(safe));
    } catch (error) {
      console.warn('WRN Zine save:', error);
    }
    try { if (typeof updateZineUi === 'function') updateZineUi(); } catch {}
    return safe;
  }

  function visibleArticleKey(item) {
    try { return clean(window.WRNReading?.articleKey?.(item) || articleKey(item)); }
    catch { return articleKey(item); }
  }

  function exactArticleForCard(index) {
    let candidate = currentItems()[index] || null;
    const card = document.getElementById(`card-${index}`);
    const expected = clean(card?.dataset?.articleKey || '');
    if (candidate && (!expected || visibleArticleKey(candidate) === expected)) return candidate;
    if (expected) {
      candidate = currentItems().find(item => visibleArticleKey(item) === expected)
        || articles().find(item => visibleArticleKey(item) === expected)
        || null;
    }
    return candidate;
  }

  function installZineSelectionFix() {
    if (window.__wrnBlock3ZineSelectionWrapped || typeof window.toggleZine !== 'function') return;
    window.__wrnBlock3ZineSelectionWrapped = true;
    window.toggleZine = function(index) {
      const article = exactArticleForCard(Number(index));
      if (!article) return;
      const key = articleKey(article);
      const list = [...zineItems()];
      const existing = list.findIndex(item => articleKey(item) === key);
      if (existing >= 0) list.splice(existing, 1);
      else list.push(snapshotArticle(article));
      commitZine(list);
    };
  }

  function syncZineEditor() {
    const list = [...zineItems()];
    document.querySelectorAll(`#zine-list .${ZINE_EDITOR_CLASS}`).forEach(row => {
      const index = Number(row.dataset.zineIndex);
      if (!Number.isInteger(index) || !list[index]) return;
      const title = row.querySelector('[data-zine-edit-title]')?.value;
      const content = row.querySelector('[data-zine-edit-content]')?.value;
      if (typeof title === 'string') list[index].title = title;
      if (typeof content === 'string') list[index].content = content;
    });
    commitZine(list);
    return list;
  }

  function renderZineEditor() {
    const container = document.getElementById('zine-list');
    if (!container) return;
    container.classList.add('zine-preview', 'wrn-zine-edit-list-183');
    const copy = text();
    const items = [...zineItems()];
    container.textContent = '';

    if (!items.length) {
      const empty = document.createElement('p');
      empty.className = 'zine-empty';
      empty.textContent = language() === 'de' ? 'Das Zine ist noch leer.' : 'The Zine is empty.';
      container.appendChild(empty);
    }

    items.forEach((article, index) => {
      const row = document.createElement('article');
      row.className = ZINE_EDITOR_CLASS;
      row.dataset.zineIndex = String(index);

      const heading = document.createElement('div');
      heading.className = 'wrn-zine-editor-heading-183';
      const number = document.createElement('strong');
      number.textContent = `${index + 1}. ${sourceName(article)}`;
      const actions = document.createElement('div');

      const makeMove = (label, delta, disabled) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = label;
        button.disabled = disabled;
        button.addEventListener('click', () => {
          syncZineEditor();
          const current = [...zineItems()];
          const target = index + delta;
          if (target < 0 || target >= current.length) return;
          [current[index], current[target]] = [current[target], current[index]];
          commitZine(current);
          renderZineEditor();
        });
        return button;
      };

      actions.append(
        makeMove(`↑ ${copy.up}`, -1, index === 0),
        makeMove(`↓ ${copy.down}`, 1, index === items.length - 1)
      );
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'danger';
      remove.textContent = copy.remove;
      remove.addEventListener('click', () => {
        syncZineEditor();
        const current = [...zineItems()];
        current.splice(index, 1);
        commitZine(current);
        renderZineEditor();
      });
      actions.appendChild(remove);
      heading.append(number, actions);

      const titleLabel = document.createElement('label');
      const titleSpan = document.createElement('span');
      titleSpan.textContent = copy.title;
      const titleInput = document.createElement('input');
      titleInput.type = 'text';
      titleInput.value = String(article.title || '');
      titleInput.dataset.zineEditTitle = 'true';
      titleLabel.append(titleSpan, titleInput);

      const textLabel = document.createElement('label');
      const textSpan = document.createElement('span');
      textSpan.textContent = copy.text;
      const textarea = document.createElement('textarea');
      textarea.rows = 8;
      textarea.value = String(article.content || article.description || article.summary || '');
      textarea.dataset.zineEditContent = 'true';
      textLabel.append(textSpan, textarea);

      const saved = document.createElement('small');
      saved.className = 'wrn-zine-editor-saved-183';
      const saveOnChange = () => {
        syncZineEditor();
        saved.textContent = copy.saved;
        window.setTimeout(() => { saved.textContent = ''; }, 1200);
      };
      titleInput.addEventListener('change', saveOnChange);
      textarea.addEventListener('change', saveOnChange);

      row.append(heading, titleLabel, textLabel, saved);
      container.appendChild(row);
    });

    document.getElementById('zine-modal')?.classList.add('wrn-zine-modal-editor-183');
    try { window.WRNZineDesigner1719?.install?.(); } catch {}
  }

  function installZineEditor() {
    if (window.__wrnBlock3ZineEditorInstalled) return;
    window.__wrnBlock3ZineEditorInstalled = true;
    const originalOpen = window.openZineManager;
    const originalPrint = window.printZine;

    window.renderZineList = renderZineEditor;
    window.openZineManager = function(...args) {
      const result = typeof originalOpen === 'function' ? originalOpen.apply(this, args) : undefined;
      const title = document.getElementById('zine-modal-title');
      if (title) title.textContent = text().zineTitle;
      window.setTimeout(renderZineEditor, 0);
      return result;
    };
    window.printZine = function(...args) {
      syncZineEditor();
      return typeof originalPrint === 'function' ? originalPrint.apply(this, args) : undefined;
    };
  }

  function showStoriesIndicator(button) {
    document.querySelectorAll('.wrn-top-tab').forEach(node => {
      node.classList.toggle('active', node === button);
    });
    document.body.dataset.wrnTab = 'stories';
    let indicator = document.getElementById('wrn-stories-switch-indicator-183');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'wrn-stories-switch-indicator-183';
      indicator.className = 'wrn-stories-switch-indicator-183';
      document.body.appendChild(indicator);
    }
    indicator.textContent = text().switching;
    indicator.hidden = false;
  }

  function installImmediateStoriesSwitch() {
    if (window.__wrnBlock3StoriesSwitch) return;
    window.__wrnBlock3StoriesSwitch = true;
    document.addEventListener('click', event => {
      const button = event.target.closest?.('.wrn-top-tab[data-key="stories"]');
      if (!button || state.storySwitching || document.body.dataset.wrnTab === 'stories') return;
      event.preventDefault();
      event.stopImmediatePropagation();
      state.storySwitching = true;
      showStoriesIndicator(button);
      window.requestAnimationFrame(() => {
        window.setTimeout(() => {
          try { window.WRNActivateTab?.('stories'); }
          finally {
            window.setTimeout(() => {
              const indicator = document.getElementById('wrn-stories-switch-indicator-183');
              if (indicator) indicator.hidden = true;
              state.storySwitching = false;
            }, 120);
          }
        }, 0);
      });
    }, true);
  }

  let sourceRefreshQueued = false;
  function queueSourceBarRefresh() {
    if (sourceRefreshQueued) return;
    sourceRefreshQueued = true;
    window.requestAnimationFrame(() => {
      sourceRefreshQueued = false;
      const bar = ensureSourceBar();
      bar.hidden = !shouldShowSourceBar();
      if (!bar.hidden) renderSourceChoices();
      queueCorruptionTab();
    });
  }

  function installObservers() {
    const observer = new MutationObserver(records => {
      let cards = false;
      let navigation = false;
      for (const record of records) {
        for (const node of record.addedNodes) {
          if (!(node instanceof Element)) continue;
          if (node.matches?.('.card') || node.querySelector?.('.card')) cards = true;
          if (node.matches?.('.wrn-subtabs, .wrn-top-tabs') || node.querySelector?.('.wrn-subtabs, .wrn-top-tabs')) navigation = true;
        }
      }
      if (cards) queueCardDecoration();
      if (navigation) queueSourceBarRefresh();
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });

    const bodyObserver = new MutationObserver(() => queueSourceBarRefresh());
    bodyObserver.observe(document.body, { attributes: true, attributeFilter: ['data-wrn-tab', 'class'] });
  }

  function refreshLanguage() {
    refreshSourceBarLanguage();
    queueCorruptionTab();
    queueCardDecoration();
    if (document.getElementById('zine-modal')?.style.display === 'block') renderZineEditor();
  }

  function init() {
    ensureSourceBar();
    installFilterWrapper();
    installCategoryWrapper();
    installZineSelectionFix();
    installZineEditor();
    installImmediateStoriesSwitch();
    installObservers();
    queueCardDecoration();
    queueSourceBarRefresh();
    queueCorruptionTab();
    window.addEventListener('wrn-language-change', refreshLanguage);
    document.getElementById('ui-language')?.addEventListener('change', () => window.setTimeout(refreshLanguage, 0));
  }

  window.WRNInterfaceBlock3 = Object.freeze({
    version: VERSION,
    applySourceRange,
    resetSourceRange,
    ensureThirtyDayArchive,
    rowsForCategory,
    filterRows,
    matchesCorruption,
    renderZineEditor,
    state: () => ({
      selectedSources: [...state.selectedSources],
      pendingDays: state.pendingDays,
      appliedDays: state.appliedDays,
      fullArchiveLoaded: state.fullArchiveLoaded
    }),
    test: Object.freeze({ actionType, mergeRows, articleKey, rowsForCategory, filterRows })
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
