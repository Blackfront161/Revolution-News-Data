/* World Revolution News – transparente Übersetzungsansichten und Abschnitts-Cache */
'use strict';

(() => {
    const records = new Map();
    let activeReportId = null;

    const texts = {
        en: {
            original: 'Original', translation: 'Translation', compare: 'Compare', report: 'Report translation',
            translatedView: 'Translated view', originalView: 'Original view', teaserOnly: 'Preview translated', full: 'Full article translated',
            originalLanguage: 'Original language', targetLanguage: 'Target language', provider: 'Provider', unknown: 'Unknown',
            compareTitle: 'Compare original and translation', originalColumn: 'Original', translatedColumn: 'Machine translation',
            compareHint: 'The comparison stays on this device and does not send article text anywhere.', close: 'Close',
            reportTitle: 'Report a translation problem', reportIntro: 'Only the article metadata, your selected problem and your note are prepared for an email. The article text is not attached.',
            issueLabel: 'Problem', issueWrongMeaning: 'Meaning is wrong', issueMissing: 'Text is missing', issueNames: 'Names or quotations changed',
            issueLanguage: 'Wrong target language', issueFormatting: 'Formatting or paragraphs are broken', issueOther: 'Other problem',
            noteLabel: 'Optional note', notePlaceholder: 'Briefly describe the problem…', send: 'Prepare email',
            cache: 'Sections already translated are reused locally.'
        },
        de: {
            original: 'Original', translation: 'Übersetzung', compare: 'Vergleichen', report: 'Übersetzung melden',
            translatedView: 'Übersetzte Ansicht', originalView: 'Originalansicht', teaserOnly: 'Vorschau übersetzt', full: 'Ganzer Artikel übersetzt',
            originalLanguage: 'Originalsprache', targetLanguage: 'Zielsprache', provider: 'Anbieter', unknown: 'Unbekannt',
            compareTitle: 'Original und Übersetzung vergleichen', originalColumn: 'Original', translatedColumn: 'Maschinelle Übersetzung',
            compareHint: 'Der Vergleich bleibt auf diesem Gerät und sendet keinen Artikeltext weiter.', close: 'Schließen',
            reportTitle: 'Übersetzungsproblem melden', reportIntro: 'Für die E-Mail werden nur Artikeldaten, die ausgewählte Fehlerart und deine Notiz vorbereitet. Der Artikeltext wird nicht angehängt.',
            issueLabel: 'Problem', issueWrongMeaning: 'Bedeutung ist falsch', issueMissing: 'Text fehlt', issueNames: 'Namen oder Zitate wurden verändert',
            issueLanguage: 'Falsche Zielsprache', issueFormatting: 'Formatierung oder Absätze sind beschädigt', issueOther: 'Anderes Problem',
            noteLabel: 'Optionale Notiz', notePlaceholder: 'Beschreibe das Problem kurz …', send: 'E-Mail vorbereiten',
            cache: 'Bereits übersetzte Abschnitte werden lokal wiederverwendet.'
        }
    };

    function currentLanguage() {
        try {
            return typeof currentLang !== 'undefined' ? currentLang : (document.documentElement.lang || 'en');
        } catch {
            return document.documentElement.lang || 'en';
        }
    }

    function textSet() {
        return texts[currentLanguage()] || texts.en;
    }

    function articleAt(idNum) {
        try {
            return Array.isArray(currentFilteredItems) ? currentFilteredItems[idNum] : null;
        } catch {
            return null;
        }
    }

    function articleKey(article) {
        return String(article?.link || article?.guid || article?.id || article?.title || 'article').trim();
    }

    function hashText(value) {
        let hash = 2166136261;
        const text = String(value ?? '');
        for (let index = 0; index < text.length; index += 1) {
            hash ^= text.charCodeAt(index);
            hash = Math.imul(hash, 16777619);
        }
        return (hash >>> 0).toString(36);
    }

    function articleFingerprint(article) {
        return hashText(`${article?.title || ''}\n${article?.content || ''}\n${article?.updatedAt || article?.modifiedAt || ''}`);
    }

    function chunkCacheKey(article, language, index, sourceText) {
        const firstTitle = Number(index) === 0 ? String(article?.title || '') : '';
        const fingerprint = hashText(`${firstTitle}\n${sourceText}`);
        return `translation-chunk::${articleKey(article)}::${language}::${index}::${fingerprint}`;
    }

    async function getCachedChunk(article, language, index, sourceText) {
        if (!window.WRNStorage?.getTranslation) return null;
        try {
            const value = await window.WRNStorage.getTranslation(chunkCacheKey(article, language, index, sourceText));
            if (!value || typeof value.text !== 'string' || !value.text.trim()) return null;
            return { error: false, ...value, cached: true };
        } catch (error) {
            console.warn('Übersetzungsabschnitt konnte nicht gelesen werden:', error);
            return null;
        }
    }

    async function putCachedChunk(article, language, index, sourceText, result) {
        if (!window.WRNStorage?.putTranslation || !result?.text) return;
        try {
            await window.WRNStorage.putTranslation(
                chunkCacheKey(article, language, index, sourceText),
                {
                    text: String(result.text),
                    provider: String(result.provider || ''),
                    cachedAt: new Date().toISOString()
                }
            );
        } catch (error) {
            console.warn('Übersetzungsabschnitt konnte nicht gespeichert werden:', error);
        }
    }

    function originalTeaser(article) {
        const fullText = String(article?.content || '').trim();
        const sentence = fullText.match(/[^.!?]+[.!?]+/)?.[0];
        return sentence || `${fullText.slice(0, 100)}${fullText.length > 100 ? '…' : ''}`;
    }

    function translatedTeaser(record) {
        if (record.teaser) return record.teaser;
        const text = String(record.text || '');
        return text.match(/[^.!?]+[.!?]+/)?.[0] || `${text.slice(0, 180)}${text.length > 180 ? '…' : ''}`;
    }

    function recordKey(article, language) {
        return `${articleKey(article)}::${language}`;
    }

    function findRecord(idNum) {
        const article = articleAt(idNum);
        if (!article) return null;
        return records.get(recordKey(article, currentLanguage())) || null;
    }

    function setPressed(container, mode) {
        container?.querySelectorAll('[data-translation-view]').forEach(button => {
            const active = button.dataset.translationView === mode;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
    }

    function applyCardValues(idNum, mode) {
        const article = articleAt(idNum);
        const record = findRecord(idNum);
        const card = document.getElementById(`card-${idNum}`);
        const title = document.getElementById(`title-${idNum}`);
        const teaser = document.getElementById(`teaser-${idNum}`);
        const content = document.getElementById(`content-${idNum}`);
        const controls = document.getElementById(`translation-tools-${idNum}`);
        if (!article || !record || !card || !title || !teaser || !content) return;

        if (mode === 'original') {
            title.textContent = String(article.title || '');
            teaser.textContent = originalTeaser(article);
            content.textContent = String(article.content || '');
            title.classList.remove('translated');
            card.dataset.translationView = 'original';
        } else {
            title.textContent = String(record.title || article.title || '');
            teaser.textContent = translatedTeaser(record);
            content.textContent = record.scope === 'full' ? String(record.text || '') : String(article.content || '');
            title.classList.add('translated');
            card.dataset.translationView = 'translated';
        }

        const expanded = card.dataset.expanded === 'true';
        teaser.style.display = expanded ? 'none' : 'block';
        content.style.display = expanded ? 'block' : 'none';
        setPressed(controls, mode);
    }

    function showOriginal(idNum) {
        applyCardValues(idNum, 'original');
    }

    function showTranslated(idNum) {
        applyCardValues(idNum, 'translated');
    }

    function originalLanguage(article) {
        const value = String(article?.language || article?.lang || article?.originalLanguage || '').trim();
        return value ? value.toUpperCase() : textSet().unknown;
    }

    function ensureControls(idNum, record) {
        const container = document.getElementById(`translation-tools-${idNum}`);
        if (!container) return;
        const t = textSet();
        container.hidden = false;
        container.textContent = '';

        const buttonRow = document.createElement('div');
        buttonRow.className = 'translation-view-buttons';

        const makeButton = (label, view, handler) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'translation-view-button';
            button.textContent = label;
            if (view) button.dataset.translationView = view;
            button.addEventListener('click', handler);
            return button;
        };

        buttonRow.append(
            makeButton(t.original, 'original', () => showOriginal(idNum)),
            makeButton(t.translation, 'translated', () => showTranslated(idNum)),
            makeButton(t.compare, '', () => openCompare(idNum)),
            makeButton(t.report, '', () => openReport(idNum))
        );

        const meta = document.createElement('div');
        meta.className = 'translation-view-meta';
        const scopeLabel = record.scope === 'full' ? t.full : t.teaserOnly;
        const provider = record.provider ? ` · ${t.provider}: ${record.provider}` : '';
        meta.textContent = `${scopeLabel} · ${t.originalLanguage}: ${originalLanguage(record.article)} · ${t.targetLanguage}: ${String(record.language || '').toUpperCase()}${provider}`;

        const cacheNote = document.createElement('div');
        cacheNote.className = 'translation-cache-note';
        cacheNote.textContent = t.cache;

        container.append(buttonRow, meta, cacheNote);
    }

    function registerTranslation(idNum, article, translated, scope = 'full') {
        if (!article || !translated) return;
        const language = String(translated.language || currentLanguage());
        const record = {
            article,
            language,
            scope,
            title: String(translated.title || article.title || ''),
            teaser: String(translated.teaser || ''),
            text: String(translated.text || ''),
            provider: Array.isArray(translated.providers)
                ? translated.providers.filter(Boolean).join(', ')
                : String(translated.provider || ''),
            translatedAt: translated.translatedAt || new Date().toISOString()
        };
        records.set(recordKey(article, language), record);
        ensureControls(idNum, record);
        showTranslated(idNum);
    }

    function showModal(id) {
        const overlay = document.getElementById('fb-overlay');
        const modal = document.getElementById(id);
        if (overlay) overlay.style.display = 'block';
        if (modal) modal.style.display = 'block';
    }

    function openCompare(idNum) {
        const record = findRecord(idNum);
        if (!record) return;
        const t = textSet();
        const article = record.article;
        const originalText = record.scope === 'full' ? String(article.content || '') : originalTeaser(article);
        const translatedText = record.scope === 'full' ? String(record.text || '') : translatedTeaser(record);

        const setText = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };
        setText('translation-compare-title', t.compareTitle);
        setText('translation-compare-meta', `${originalLanguage(article)} → ${String(record.language || '').toUpperCase()}`);
        setText('translation-compare-original-heading', t.originalColumn);
        setText('translation-compare-translated-heading', t.translatedColumn);
        setText('translation-compare-original-title', String(article.title || ''));
        setText('translation-compare-translated-title', record.title);
        setText('translation-compare-original-text', originalText);
        setText('translation-compare-translated-text', translatedText);
        setText('translation-compare-hint', t.compareHint);
        setText('btn-translation-compare-close', t.close);
        showModal('translation-compare-modal');
    }

    function fillReportOptions() {
        const t = textSet();
        const select = document.getElementById('translation-report-issue');
        if (!select) return;
        const options = [
            ['wrong-meaning', t.issueWrongMeaning],
            ['missing', t.issueMissing],
            ['names-quotes', t.issueNames],
            ['wrong-language', t.issueLanguage],
            ['formatting', t.issueFormatting],
            ['other', t.issueOther]
        ];
        select.textContent = '';
        options.forEach(([value, label]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            select.append(option);
        });
    }

    function openReport(idNum) {
        const record = findRecord(idNum);
        if (!record) return;
        activeReportId = idNum;
        const t = textSet();
        const setText = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };
        setText('translation-report-title', t.reportTitle);
        setText('translation-report-intro', t.reportIntro);
        setText('translation-report-issue-label', t.issueLabel);
        setText('translation-report-note-label', t.noteLabel);
        setText('btn-translation-report-send', t.send);
        setText('btn-translation-report-close', t.close);
        fillReportOptions();
        const note = document.getElementById('translation-report-note');
        if (note) {
            note.value = '';
            note.placeholder = t.notePlaceholder;
        }
        showModal('translation-report-modal');
    }

    function sendReport() {
        if (!Number.isInteger(activeReportId)) return;
        const record = findRecord(activeReportId);
        if (!record) return;
        const select = document.getElementById('translation-report-issue');
        const note = document.getElementById('translation-report-note');
        const article = record.article;
        const issue = select?.options?.[select.selectedIndex]?.text || select?.value || '';
        const body = [
            'Übersetzungsproblem in World Revolution News',
            '',
            `Artikel: ${article?.title || ''}`,
            `Quelle: ${article?.quelleName || article?.sourceName || ''}`,
            `Link: ${article?.link || ''}`,
            `Originalsprache: ${originalLanguage(article)}`,
            `Zielsprache: ${String(record.language || '').toUpperCase()}`,
            `Umfang: ${record.scope}`,
            `Problem: ${issue}`,
            '',
            `Notiz: ${String(note?.value || '').trim() || '-'}`,
            '',
            'Der Artikeltext wurde aus Datenschutzgründen nicht automatisch angehängt.'
        ].join('\n');
        const subject = `Übersetzung melden: ${String(article?.title || '').slice(0, 90)}`;
        window.location.href = `mailto:worldrevnews@brief.li?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
        closeModals();
    }

    function closeModals() {
        ['translation-compare-modal', 'translation-report-modal'].forEach(id => {
            const modal = document.getElementById(id);
            if (modal) modal.style.display = 'none';
        });
        const overlay = document.getElementById('fb-overlay');
        if (overlay) overlay.style.display = 'none';
        activeReportId = null;
    }

    function refreshTexts() {
        records.forEach(record => {
            if (record.language !== currentLanguage()) return;
            document.querySelectorAll('[id^="translation-tools-"]').forEach(container => {
                const idNum = Number(container.id.replace('translation-tools-', ''));
                const matching = findRecord(idNum);
                if (matching) ensureControls(idNum, matching);
            });
        });
    }

    window.closeTranslationModals = closeModals;
    window.sendTranslationReport = sendReport;
    window.WRNTranslationTools = {
        articleFingerprint,
        getCachedChunk,
        putCachedChunk,
        registerTranslation,
        showOriginal,
        showTranslated,
        openCompare,
        openReport,
        closeModals,
        refreshTexts
    };
})();
