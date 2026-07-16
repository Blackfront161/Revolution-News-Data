#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "tools" else SCRIPT_DIR

RELEASE_CSS = r'''/* World Revolution News 1.4 – mobile release polish */
.app-version-inline { display: none !important; }
.mobile-more-menu { display: none; }
.language-beta-note {
    margin: -8px 0 14px;
    padding: 8px 10px;
    border: 1px dashed var(--color-cyan);
    border-radius: 5px;
    color: var(--text-muted);
    background: rgba(0, 240, 255, 0.045);
    font-size: 0.72rem;
    line-height: 1.45;
}
.language-beta-note[hidden] { display: none !important; }

@media (max-width: 720px) {
    body { padding: 10px !important; }
    .top-action-bar { display: none !important; }
    .mobile-more-menu {
        display: block;
        margin: 0 0 10px;
        border: 1px solid var(--border-read);
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.025);
    }
    .mobile-more-menu > summary {
        min-height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 12px;
        color: var(--color-cyan);
        font-weight: 800;
        text-transform: uppercase;
        cursor: pointer;
        list-style: none;
    }
    .mobile-more-menu > summary::-webkit-details-marker { display: none; }
    .mobile-more-menu > summary::before { content: '☰'; margin-right: 8px; font-size: 1.05rem; }
    .mobile-more-menu[open] > summary::before { content: '×'; }
    .mobile-more-panel {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 7px;
        padding: 8px;
        border-top: 1px dashed var(--border-read);
    }
    .mobile-more-panel .btn-micro {
        width: 100%;
        min-height: 42px;
        white-space: normal;
        line-height: 1.25;
        padding: 7px 8px;
    }

    header {
        align-items: stretch !important;
        gap: 10px !important;
        margin-bottom: 14px !important;
    }
    header > div:first-child { width: 100%; }
    h1 { font-size: clamp(1rem, 5.5vw, 1.28rem) !important; line-height: 1.25; }
    .header-controls {
        width: 100%;
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px !important;
    }
    .header-controls .dropdown-container,
    .header-controls select { width: 100%; min-width: 0; }

    .quick-nav-bar {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 7px !important;
        padding: 2px 0 10px !important;
    }
    .quick-nav-bar .btn-nav {
        width: 100% !important;
        min-width: 0;
        min-height: 44px;
        white-space: normal !important;
        line-height: 1.2;
        padding: 7px 6px !important;
    }
    .quick-nav-bar #btn-open-zine { grid-column: 1 / -1; }

    .filter-bar {
        display: grid !important;
        grid-template-columns: 44px repeat(2, minmax(0, 1fr));
        gap: 7px !important;
        padding: 9px !important;
        align-items: stretch !important;
    }
    .filter-bar .filter-control,
    .filter-bar select {
        width: 100% !important;
        min-width: 0 !important;
        max-width: none !important;
        height: 40px !important;
    }
    .filter-bar .filter-control-menu { width: 44px !important; }
    .filter-bar .search-container {
        grid-column: 1 / -1;
        width: 100% !important;
        margin: 0 !important;
        min-width: 0 !important;
    }
    .filter-bar .search-input { min-height: 42px !important; font-size: 0.82rem !important; }
    #content-type-filter { grid-column: span 2; }

    .feedback-modal {
        width: calc(100vw - 20px) !important;
        max-height: calc(100vh - 24px) !important;
        padding: 14px !important;
        box-sizing: border-box;
    }
}

@media (max-width: 390px) {
    .mobile-more-panel { grid-template-columns: 1fr; }
    .quick-nav-bar { grid-template-columns: 1fr; }
    .quick-nav-bar #btn-open-zine { grid-column: auto; }
    .filter-bar { grid-template-columns: 44px minmax(0, 1fr); }
    #content-type-filter { grid-column: 1 / -1; }
    .header-controls { grid-template-columns: 1fr !important; }
}
'''

RELEASE_JS = r'''/* World Revolution News 1.4 – release compatibility and mobile navigation */
'use strict';

(() => {
    const BETA_LANGUAGES = new Set(['es', 'fr', 'it', 'pt', 'ru', 'el', 'tr']);
    const nativeNames = {
        en: 'English', de: 'Deutsch', es: 'Español', fr: 'Français', it: 'Italiano',
        pt: 'Português', ru: 'Русский', el: 'Ελληνικά', tr: 'Türkçe'
    };

    const releaseTexts = {
        en: { more:'More', beta:'Some technical areas still use the English fallback. Article translation works in the selected language.', sources:'Sources', storage:'Storage', status:'Status', filterMenu:'Open source and filter menu' },
        de: { more:'Mehr', beta:'Einige technische Bereiche verwenden noch den englischen Rückfalltext. Artikelübersetzungen funktionieren in der gewählten Sprache.', sources:'Quellen', storage:'Speicher', status:'Status', filterMenu:'Quellen- und Filtermenü öffnen' },
        es: { more:'Más', beta:'Algunas áreas técnicas todavía usan el texto alternativo en inglés. La traducción de artículos funciona en el idioma seleccionado.', sources:'Fuentes', storage:'Almacenamiento', status:'Estado', filterMenu:'Abrir fuentes y filtros' },
        fr: { more:'Plus', beta:'Certaines zones techniques utilisent encore le texte anglais de secours. La traduction des articles fonctionne dans la langue choisie.', sources:'Sources', storage:'Stockage', status:'État', filterMenu:'Ouvrir les sources et les filtres' },
        it: { more:'Altro', beta:'Alcune aree tecniche usano ancora il testo inglese di riserva. La traduzione degli articoli funziona nella lingua scelta.', sources:'Fonti', storage:'Memoria', status:'Stato', filterMenu:'Apri fonti e filtri' },
        pt: { more:'Mais', beta:'Algumas áreas técnicas ainda usam o texto alternativo em inglês. A tradução de artigos funciona no idioma selecionado.', sources:'Fontes', storage:'Armazenamento', status:'Estado', filterMenu:'Abrir fontes e filtros' },
        ru: { more:'Ещё', beta:'Некоторые технические разделы пока используют английский запасной текст. Перевод статей работает на выбранном языке.', sources:'Источники', storage:'Хранилище', status:'Статус', filterMenu:'Открыть источники и фильтры' },
        el: { more:'Περισσότερα', beta:'Ορισμένες τεχνικές ενότητες χρησιμοποιούν ακόμη αγγλικό εφεδρικό κείμενο. Η μετάφραση άρθρων λειτουργεί στην επιλεγμένη γλώσσα.', sources:'Πηγές', storage:'Αποθήκευση', status:'Κατάσταση', filterMenu:'Άνοιγμα πηγών και φίλτρων' },
        tr: { more:'Daha fazla', beta:'Bazı teknik bölümler hâlâ İngilizce yedek metni kullanıyor. Makale çevirisi seçilen dilde çalışır.', sources:'Kaynaklar', storage:'Depolama', status:'Durum', filterMenu:'Kaynakları ve filtreleri aç' }
    };

    const coreLocalePatches = {
        es: { langLabel:'Idioma:', themeLabel:'Diseño:', themeDark:'Oscuro', themeLight:'Claro', clearBtn:'Vaciar caché 🗑️', searchPlace:'Buscar artículos…', topBookmarks:'Leer después', sortNew:'Más recientes', sortOld:'Más antiguos', latestNews:'Últimas novedades:', filterAll:'Todas las fuentes', btnDonateTop:'Donar', btnDonateCancel:'Cerrar', btnPaypal:'Continuar a PayPal', fbTitle:'Contacto', fbPlace:'Escribe ideas, errores o nuevas fuentes…', fbCaptcha:'Captcha: ¿Cuánto es', fbCancel:'Cancelar', fbSend:'Enviar por correo', contactLabel:'Contacto:', archiveTitle:'🗄️ Archivo (> 3 meses)', btnExpand:'Leer más ⬇️', btnCollapse:'Cerrar ⬆️', btnReadMore:'Original', audioHub:'Podcasts y radio', audioHubTitle:'Podcasts y radio', tabOriginal:'Podcasts originales', tabGenerated:'Podcasts generados', tabRadio:'Radio en directo', podcastLibraryRefresh:'Actualizar', podcastClose:'Cerrar', searchPodcasts:'Buscar podcasts…', allSources:'Todas las fuentes', allLanguages:'Todos los idiomas', originalLoading:'Cargando…', originalEmpty:'No hay podcasts disponibles', listenOriginal:'Escuchar en la fuente', feedLink:'Feed' },
        fr: { langLabel:'Langue :', themeLabel:'Design :', themeDark:'Sombre', themeLight:'Clair', clearBtn:'Vider le cache 🗑️', searchPlace:'Rechercher des articles…', topBookmarks:'À lire plus tard', sortNew:'Plus récents', sortOld:'Plus anciens', latestNews:'Dernières mises à jour :', filterAll:'Toutes les sources', btnDonateTop:'Soutenir', btnDonateCancel:'Fermer', btnPaypal:'Continuer vers PayPal', fbTitle:'Contact', fbPlace:'Écrivez vos idées, erreurs ou nouvelles sources…', fbCaptcha:'Captcha : combien font', fbCancel:'Annuler', fbSend:'Envoyer par e-mail', contactLabel:'Contact :', archiveTitle:'🗄️ Archive (> 3 mois)', btnExpand:'Lire plus ⬇️', btnCollapse:'Réduire ⬆️', btnReadMore:'Original', audioHub:'Podcasts et radio', audioHubTitle:'Podcasts et radio', tabOriginal:'Podcasts originaux', tabGenerated:'Podcasts générés', tabRadio:'Radio en direct', podcastLibraryRefresh:'Actualiser', podcastClose:'Fermer', searchPodcasts:'Rechercher des podcasts…', allSources:'Toutes les sources', allLanguages:'Toutes les langues', originalLoading:'Chargement…', originalEmpty:'Aucun podcast disponible', listenOriginal:'Écouter à la source', feedLink:'Flux' },
        it: { langLabel:'Lingua:', themeLabel:'Design:', themeDark:'Scuro', themeLight:'Chiaro', clearBtn:'Svuota cache 🗑️', searchPlace:'Cerca articoli…', topBookmarks:'Leggi dopo', sortNew:'Più recenti', sortOld:'Più vecchi', latestNews:'Ultimi aggiornamenti:', filterAll:'Tutte le fonti', btnDonateTop:'Dona', btnDonateCancel:'Chiudi', btnPaypal:'Continua su PayPal', fbTitle:'Contatto', fbPlace:'Scrivi idee, errori o nuove fonti…', fbCaptcha:'Captcha: quanto fa', fbCancel:'Annulla', fbSend:'Invia via e-mail', contactLabel:'Contatto:', archiveTitle:'🗄️ Archivio (> 3 mesi)', btnExpand:'Leggi altro ⬇️', btnCollapse:'Riduci ⬆️', btnReadMore:'Originale', audioHub:'Podcast e radio', audioHubTitle:'Podcast e radio', tabOriginal:'Podcast originali', tabGenerated:'Podcast generati', tabRadio:'Radio in diretta', podcastLibraryRefresh:'Aggiorna', podcastClose:'Chiudi', searchPodcasts:'Cerca podcast…', allSources:'Tutte le fonti', allLanguages:'Tutte le lingue', originalLoading:'Caricamento…', originalEmpty:'Nessun podcast disponibile', listenOriginal:'Ascolta alla fonte', feedLink:'Feed' },
        pt: { langLabel:'Idioma:', themeLabel:'Design:', themeDark:'Escuro', themeLight:'Claro', clearBtn:'Limpar cache 🗑️', searchPlace:'Pesquisar artigos…', topBookmarks:'Ler depois', sortNew:'Mais recentes', sortOld:'Mais antigos', latestNews:'Atualizações recentes:', filterAll:'Todas as fontes', btnDonateTop:'Doar', btnDonateCancel:'Fechar', btnPaypal:'Continuar para PayPal', fbTitle:'Contato', fbPlace:'Escreva ideias, erros ou novas fontes…', fbCaptcha:'Captcha: quanto é', fbCancel:'Cancelar', fbSend:'Enviar por e-mail', contactLabel:'Contato:', archiveTitle:'🗄️ Arquivo (> 3 meses)', btnExpand:'Ler mais ⬇️', btnCollapse:'Recolher ⬆️', btnReadMore:'Original', audioHub:'Podcasts e rádio', audioHubTitle:'Podcasts e rádio', tabOriginal:'Podcasts originais', tabGenerated:'Podcasts gerados', tabRadio:'Rádio ao vivo', podcastLibraryRefresh:'Atualizar', podcastClose:'Fechar', searchPodcasts:'Pesquisar podcasts…', allSources:'Todas as fontes', allLanguages:'Todos os idiomas', originalLoading:'Carregando…', originalEmpty:'Nenhum podcast disponível', listenOriginal:'Ouvir na fonte', feedLink:'Feed' },
        ru: { langLabel:'Язык:', themeLabel:'Оформление:', themeDark:'Тёмное', themeLight:'Светлое', clearBtn:'Очистить кэш 🗑️', searchPlace:'Поиск статей…', topBookmarks:'Прочитать позже', sortNew:'Сначала новые', sortOld:'Сначала старые', latestNews:'Последние обновления:', filterAll:'Все источники', btnDonateTop:'Поддержать', btnDonateCancel:'Закрыть', btnPaypal:'Перейти к PayPal', fbTitle:'Связаться', fbPlace:'Напишите об идеях, ошибках или новых источниках…', fbCaptcha:'Проверка: сколько будет', fbCancel:'Отмена', fbSend:'Отправить письмом', contactLabel:'Контакт:', archiveTitle:'🗄️ Архив (> 3 месяцев)', btnExpand:'Читать далее ⬇️', btnCollapse:'Свернуть ⬆️', btnReadMore:'Оригинал', audioHub:'Подкасты и радио', audioHubTitle:'Подкасты и радио', tabOriginal:'Оригинальные подкасты', tabGenerated:'Созданные подкасты', tabRadio:'Прямой эфир', podcastLibraryRefresh:'Обновить', podcastClose:'Закрыть', searchPodcasts:'Поиск подкастов…', allSources:'Все источники', allLanguages:'Все языки', originalLoading:'Загрузка…', originalEmpty:'Подкасты недоступны', listenOriginal:'Слушать у источника', feedLink:'Лента' },
        el: { langLabel:'Γλώσσα:', themeLabel:'Σχεδίαση:', themeDark:'Σκούρο', themeLight:'Φωτεινό', clearBtn:'Εκκαθάριση cache 🗑️', searchPlace:'Αναζήτηση άρθρων…', topBookmarks:'Ανάγνωση αργότερα', sortNew:'Νεότερα', sortOld:'Παλαιότερα', latestNews:'Τελευταίες ενημερώσεις:', filterAll:'Όλες οι πηγές', btnDonateTop:'Δωρεά', btnDonateCancel:'Κλείσιμο', btnPaypal:'Συνέχεια στο PayPal', fbTitle:'Επικοινωνία', fbPlace:'Γράψτε ιδέες, σφάλματα ή νέες πηγές…', fbCaptcha:'Captcha: πόσο κάνει', fbCancel:'Ακύρωση', fbSend:'Αποστολή με e-mail', contactLabel:'Επικοινωνία:', archiveTitle:'🗄️ Αρχείο (> 3 μήνες)', btnExpand:'Περισσότερα ⬇️', btnCollapse:'Σύμπτυξη ⬆️', btnReadMore:'Πρωτότυπο', audioHub:'Podcast και ραδιόφωνο', audioHubTitle:'Podcast και ραδιόφωνο', tabOriginal:'Πρωτότυπα podcast', tabGenerated:'Δημιουργημένα podcast', tabRadio:'Ζωντανό ραδιόφωνο', podcastLibraryRefresh:'Ανανέωση', podcastClose:'Κλείσιμο', searchPodcasts:'Αναζήτηση podcast…', allSources:'Όλες οι πηγές', allLanguages:'Όλες οι γλώσσες', originalLoading:'Φόρτωση…', originalEmpty:'Δεν υπάρχουν διαθέσιμα podcast', listenOriginal:'Ακρόαση στην πηγή', feedLink:'Ροή' },
        tr: { langLabel:'Dil:', themeLabel:'Tasarım:', themeDark:'Koyu', themeLight:'Açık', clearBtn:'Önbelleği temizle 🗑️', searchPlace:'Makale ara…', topBookmarks:'Sonra oku', sortNew:'En yeni', sortOld:'En eski', latestNews:'Son güncellemeler:', filterAll:'Tüm kaynaklar', btnDonateTop:'Bağış yap', btnDonateCancel:'Kapat', btnPaypal:'PayPal’a devam et', fbTitle:'İletişim', fbPlace:'Fikirleri, hataları veya yeni kaynakları yazın…', fbCaptcha:'Doğrulama: kaç eder', fbCancel:'İptal', fbSend:'E-posta ile gönder', contactLabel:'İletişim:', archiveTitle:'🗄️ Arşiv (> 3 ay)', btnExpand:'Devamını oku ⬇️', btnCollapse:'Daralt ⬆️', btnReadMore:'Orijinal', audioHub:'Podcast ve radyo', audioHubTitle:'Podcast ve radyo', tabOriginal:'Orijinal podcastler', tabGenerated:'Oluşturulan podcastler', tabRadio:'Canlı radyo', podcastLibraryRefresh:'Yenile', podcastClose:'Kapat', searchPodcasts:'Podcast ara…', allSources:'Tüm kaynaklar', allLanguages:'Tüm diller', originalLoading:'Yükleniyor…', originalEmpty:'Kullanılabilir podcast yok', listenOriginal:'Kaynakta dinle', feedLink:'Akış' }
    };

    function lang() {
        try { return (typeof currentLang !== 'undefined' && currentLang) || document.documentElement.lang || 'en'; }
        catch { return document.documentElement.lang || 'en'; }
    }

    function text() { return releaseTexts[lang()] || releaseTexts.en; }
    function setText(id, value) { const node = document.getElementById(id); if (node && node.textContent !== value) node.textContent = value; }

    function mergeLocales() {
        try {
            Object.entries(coreLocalePatches).forEach(([code, values]) => {
                if (typeof uiTexte !== 'undefined' && uiTexte[code]) Object.assign(uiTexte[code], values);
            });
        } catch (error) { console.warn('Release locale patches could not be applied:', error); }
    }

    function createMobileMenu() {
        if (document.getElementById('mobile-more-menu')) return;
        const source = document.querySelector('.top-action-bar');
        if (!source) return;
        const details = document.createElement('details');
        details.id = 'mobile-more-menu';
        details.className = 'mobile-more-menu';
        const summary = document.createElement('summary');
        summary.id = 'mobile-more-summary';
        const panel = document.createElement('div');
        panel.className = 'mobile-more-panel';
        [...source.querySelectorAll('button')].forEach(original => {
            const clone = original.cloneNode(true);
            clone.querySelectorAll('[id]').forEach(node => node.removeAttribute('id'));
            clone.removeAttribute('id');
            clone.removeAttribute('onclick');
            clone.addEventListener('click', event => {
                event.preventDefault();
                details.open = false;
                original.click();
            });
            panel.append(clone);
        });
        details.append(summary, panel);
        source.after(details);

        const mirror = () => {
            const originals = [...source.querySelectorAll('button')];
            const clones = [...panel.querySelectorAll('button')];
            originals.forEach((button, index) => { if (clones[index]) clones[index].innerHTML = button.innerHTML; });
        };
        new MutationObserver(mirror).observe(source, { subtree: true, childList: true, characterData: true });
        mirror();
    }

    function ensureBetaNote() {
        let note = document.getElementById('language-beta-note');
        if (!note) {
            note = document.createElement('div');
            note.id = 'language-beta-note';
            note.className = 'language-beta-note';
            note.setAttribute('role', 'status');
            document.querySelector('header')?.after(note);
        }
        note.hidden = !BETA_LANGUAGES.has(lang());
        note.textContent = text().beta;
    }

    const statusByLanguage = {
        en:{title:'System status',refresh:'Check again',close:'Close',version:'App version',connection:'Connection',news:'News',events:'Events',podcasts:'Original podcasts',generated:'Generated podcasts',radio:'Live radio',sourceHealth:'News sources',podcastHealth:'Podcast sources',worker:'Azure / R2 / Worker'},
        de:{title:'Systemstatus',refresh:'Neu prüfen',close:'Schließen',version:'App-Version',connection:'Verbindung',news:'Nachrichten',events:'Termine',podcasts:'Original-Podcasts',generated:'Erzeugte Podcasts',radio:'Live-Radio',sourceHealth:'Nachrichtenquellen',podcastHealth:'Podcastquellen',worker:'Azure / R2 / Worker'},
        es:{title:'Estado del sistema',refresh:'Comprobar de nuevo',close:'Cerrar',version:'Versión de la app',connection:'Conexión',news:'Noticias',events:'Eventos',podcasts:'Podcasts originales',generated:'Podcasts generados',radio:'Radio en directo',sourceHealth:'Fuentes de noticias',podcastHealth:'Fuentes de podcasts',worker:'Azure / R2 / Worker'},
        fr:{title:'État du système',refresh:'Vérifier à nouveau',close:'Fermer',version:'Version de l’application',connection:'Connexion',news:'Actualités',events:'Événements',podcasts:'Podcasts originaux',generated:'Podcasts générés',radio:'Radio en direct',sourceHealth:'Sources d’actualités',podcastHealth:'Sources de podcasts',worker:'Azure / R2 / Worker'},
        it:{title:'Stato del sistema',refresh:'Controlla di nuovo',close:'Chiudi',version:'Versione app',connection:'Connessione',news:'Notizie',events:'Eventi',podcasts:'Podcast originali',generated:'Podcast generati',radio:'Radio in diretta',sourceHealth:'Fonti di notizie',podcastHealth:'Fonti podcast',worker:'Azure / R2 / Worker'},
        pt:{title:'Estado do sistema',refresh:'Verificar novamente',close:'Fechar',version:'Versão da aplicação',connection:'Ligação',news:'Notícias',events:'Eventos',podcasts:'Podcasts originais',generated:'Podcasts gerados',radio:'Rádio ao vivo',sourceHealth:'Fontes de notícias',podcastHealth:'Fontes de podcasts',worker:'Azure / R2 / Worker'},
        ru:{title:'Состояние системы',refresh:'Проверить снова',close:'Закрыть',version:'Версия приложения',connection:'Соединение',news:'Новости',events:'События',podcasts:'Оригинальные подкасты',generated:'Созданные подкасты',radio:'Прямой эфир',sourceHealth:'Источники новостей',podcastHealth:'Источники подкастов',worker:'Azure / R2 / Worker'},
        el:{title:'Κατάσταση συστήματος',refresh:'Νέος έλεγχος',close:'Κλείσιμο',version:'Έκδοση εφαρμογής',connection:'Σύνδεση',news:'Ειδήσεις',events:'Εκδηλώσεις',podcasts:'Πρωτότυπα podcast',generated:'Δημιουργημένα podcast',radio:'Ζωντανό ραδιόφωνο',sourceHealth:'Πηγές ειδήσεων',podcastHealth:'Πηγές podcast',worker:'Azure / R2 / Worker'},
        tr:{title:'Sistem durumu',refresh:'Tekrar kontrol et',close:'Kapat',version:'Uygulama sürümü',connection:'Bağlantı',news:'Haberler',events:'Etkinlikler',podcasts:'Orijinal podcastler',generated:'Oluşturulan podcastler',radio:'Canlı radyo',sourceHealth:'Haber kaynakları',podcastHealth:'Podcast kaynakları',worker:'Azure / R2 / Worker'}
    };

    function applyStatusLanguage() {
        const s = statusByLanguage[lang()] || statusByLanguage.en;
        setText('system-status-title', s.title);
        setText('btn-system-status-refresh', s.refresh);
        setText('btn-system-status-close', s.close);
        setText('system-status-version-label', s.version);
        const rows = {
            'system-status-connection':s.connection, 'system-status-news':s.news, 'system-status-events':s.events,
            'system-status-podcasts':s.podcasts, 'system-status-generated':s.generated, 'system-status-radio':s.radio,
            'system-status-source-health':s.sourceHealth, 'system-status-podcast-health':s.podcastHealth,
            'system-status-worker':s.worker
        };
        Object.entries(rows).forEach(([id, label]) => {
            const node = document.querySelector(`#${id} .system-status-name`);
            if (node && node.textContent !== label) node.textContent = label;
        });
    }

    function applyReleaseLanguage() {
        document.documentElement.lang = lang();
        const select = document.getElementById('ui-language');
        if (select) {
            [...select.options].forEach(option => {
                const code = option.value;
                const base = nativeNames[code] || option.textContent.replace(/\s*[·(].*$/, '');
                option.textContent = BETA_LANGUAGES.has(code) ? `${base} · Beta` : base;
            });
        }
        setText('mobile-more-summary', text().more);
        setText('btn-open-system-status', `● ${text().status}`);
        setText('btn-open-data-control', `💾 ${text().storage}`);
        const filterButton = document.querySelector('.filter-control-menu');
        if (filterButton) filterButton.setAttribute('aria-label', text().filterMenu);
        ensureBetaNote();
        applyStatusLanguage();
    }

    mergeLocales();
    const originalChangeLanguage = window.changeLanguage;
    if (typeof originalChangeLanguage === 'function') {
        window.changeLanguage = function(...args) {
            const result = originalChangeLanguage.apply(this, args);
            applyReleaseLanguage();
            return result;
        };
    }

    document.addEventListener('DOMContentLoaded', () => {
        createMobileMenu();
        applyReleaseLanguage();
        const statusModal = document.getElementById('system-status-modal');
        if (statusModal) {
            new MutationObserver(applyStatusLanguage).observe(statusModal, { subtree:true, childList:true, characterData:true });
        }
        window.addEventListener('resize', () => {
            if (window.innerWidth > 720) document.getElementById('mobile-more-menu')?.removeAttribute('open');
        });
    });
})();
'''


def read(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        raise FileNotFoundError(f"Missing required repository file: {path}")
    return target.read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"Could not apply {label}: expected one match, found {count}")
    return content.replace(old, new, 1)


def patch_config() -> None:
    content = read("config.js")
    content, count = re.subn(r"version:\s*'[^']+'", "version: '1.4.0'", content, count=1)
    if count != 1:
        raise RuntimeError("Could not update config version")
    if "build:" not in content:
        content = replace_once(content, "    version: '1.4.0',\n", "    version: '1.4.0',\n    build: '2026.07.16-release',\n", "config build")
    content, count = re.subn(r"releasedAt:\s*'[^']+'", "releasedAt: '2026-07-16T18:00:00Z'", content, count=1)
    if count != 1:
        raise RuntimeError("Could not update release timestamp")
    write("config.js", content)


def patch_index() -> None:
    content = read("index.html")
    css_link = '    <link rel="stylesheet" href="release-1.4.css">\n'
    if 'release-1.4.css' not in content:
        content = replace_once(content, '    <link rel="stylesheet" href="styles.css">\n', '    <link rel="stylesheet" href="styles.css">\n' + css_link, "release stylesheet")
    js_line = '    <script src="release-1.4.js"></script>\n'
    if 'release-1.4.js' not in content:
        if '    <script src="audio-hub.js"></script>\n' in content:
            content = replace_once(content, '    <script src="audio-hub.js"></script>\n', '    <script src="audio-hub.js"></script>\n' + js_line, "release script")
        else:
            content = replace_once(content, '</body>', js_line + '</body>', "release script fallback")
    write("index.html", content)


def patch_status_center() -> None:
    content = read("status-center.js")
    content = content.replace("            errors: 'Fehler',", "            errors: 'Fehler',\n            warnings: 'Warnungen',", 1)
    content = content.replace("            errors: 'errors',", "            errors: 'errors',\n            warnings: 'warnings',", 1)
    old = '''        const errors = normalized.filter(item => {
            const value = String(item.status || item.state || item.result || '').toLowerCase();
            return value.includes('error') || value.includes('fail') || item.ok === false || Boolean(item.error);
        }).length;
        return { total: normalized.length, errors };'''
    new = '''        let ok = 0;
        let warnings = 0;
        let errors = 0;
        normalized.forEach(item => {
            const value = String(item.status || item.state || item.result || '').toLowerCase();
            const httpStatus = Number(item.httpStatus || 0);
            if (item.ok === true || value === 'ok' || value === 'success') {
                ok += 1;
            } else if (value.includes('warning') || (httpStatus >= 200 && httpStatus < 400)) {
                warnings += 1;
            } else {
                errors += 1;
            }
        });
        return { total: normalized.length, ok, warnings, errors };'''
    content = replace_once(content, old, new, "health summary classification")
    old2 = '''            if (summary.total) details.push(`${summary.total} ${t().sources}`);
            if (summary.errors) details.push(`${summary.errors} ${t().errors}`);
            if (result.updatedAt) details.push(formatDate(result.updatedAt));
            renderRow(id, label, {
                kind: summary.errors > 0 ? 'warning' : (summary.total > 0 ? 'ok' : 'warning'),
                badge: summary.total > 0 ? `${summary.total - summary.errors}/${summary.total}` : t().notConfigured,
                details: details.join(' · ')
            });'''
    new2 = '''            if (summary.total) details.push(`${summary.total} ${t().sources}`);
            if (summary.warnings) details.push(`${summary.warnings} ${t().warnings || 'warnings'}`);
            if (summary.errors) details.push(`${summary.errors} ${t().errors}`);
            if (result.updatedAt) details.push(formatDate(result.updatedAt));
            renderRow(id, label, {
                kind: (summary.errors > 0 || summary.warnings > 0) ? 'warning' : (summary.total > 0 ? 'ok' : 'warning'),
                badge: summary.total > 0 ? `${summary.ok}/${summary.total}` : t().notConfigured,
                details: details.join(' · ')
            });'''
    content = replace_once(content, old2, new2, "health row rendering")
    write("status-center.js", content)


def patch_podcast_aggregator() -> None:
    content = read("aggregate_podcasts.py")
    old = '''    unique = {}
    for item in all_items:
        unique[item["audioUrl"]] = item
    items = list(unique.values())
    items.sort(key=lambda x: x.get("published") or "", reverse=True)
    OUTPUT_FILE.write_text(json.dumps(items[:MAX_TOTAL], ensure_ascii=False, indent=2), encoding="utf-8")
    HEALTH_FILE.write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[PODCAST] saved {min(len(items), MAX_TOTAL)} episodes")
    return 0'''
    new = '''    unique = {}
    for item in all_items:
        unique[item["audioUrl"]] = item
    items = list(unique.values())
    items.sort(key=lambda x: x.get("published") or "", reverse=True)

    previous_items = []
    if OUTPUT_FILE.exists():
        try:
            loaded = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                previous_items = [item for item in loaded if isinstance(item, dict) and item.get("audioUrl")]
        except Exception as exc:
            print(f"[PODCAST] previous output could not be read: {exc}")

    if items:
        output_items = items[:MAX_TOTAL]
        OUTPUT_FILE.write_text(json.dumps(output_items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[PODCAST] saved {len(output_items)} episodes")
    elif previous_items:
        # A temporary outage of all feeds must not erase a previously working library.
        print(f"[PODCAST] no fresh episodes; preserving {len(previous_items)} existing episodes")
    else:
        OUTPUT_FILE.write_text("[]\\n", encoding="utf-8")
        print("[PODCAST] no playable episodes and no previous library")

    HEALTH_FILE.write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0'''
    content = replace_once(content, old, new, "podcast output preservation")
    write("aggregate_podcasts.py", content)


def patch_podcast_workflow() -> None:
    path = ".github/workflows/update-podcasts.yml"
    content = read(path)
    if "push:\n" not in content.split("permissions:", 1)[0]:
        content = replace_once(
            content,
            "on:\n  workflow_dispatch:\n  schedule:\n",
            "on:\n  workflow_dispatch:\n  push:\n    branches: [main]\n    paths:\n      - 'aggregate_podcasts.py'\n      - 'podcast-sources.json'\n      - '.github/workflows/update-podcasts.yml'\n  schedule:\n",
            "podcast workflow push trigger",
        )
    verify = '''
      - name: Podcast-Daten prüfen
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          items = json.loads(Path('podcasts.json').read_text(encoding='utf-8'))
          health = json.loads(Path('podcast-health.json').read_text(encoding='utf-8'))
          if not isinstance(items, list) or not items:
              raise SystemExit('podcasts.json ist leer; vorhandene Bibliothek wird nicht überschrieben.')
          if not isinstance(health, dict) or not health:
              raise SystemExit('podcast-health.json ist leer.')
          print(f'{len(items)} Podcast-Episoden aus {len(health)} Quellen geprüft.')
          PY
'''
    if "Podcast-Daten prüfen" not in content:
        content = replace_once(content, "      - name: Podcast-Daten speichern\n", verify + "\n      - name: Podcast-Daten speichern\n", "podcast workflow validation")
    write(path, content)


def patch_service_worker() -> None:
    content = read("service-worker.js")
    content, a = re.subn(r"const APP_CACHE = '[^']+';", "const APP_CACHE = 'wrn-app-v1.4.0';", content, count=1)
    content, b = re.subn(r"const DATA_CACHE = '[^']+';", "const DATA_CACHE = 'wrn-data-v1.4.0';", content, count=1)
    if a != 1 or b != 1:
        raise RuntimeError("Could not update service-worker cache names")
    if "'./release-1.4.css'" not in content:
        content = replace_once(content, "  './styles.css',\n", "  './styles.css',\n  './release-1.4.css',\n", "service-worker release CSS")
    if "'./release-1.4.js'" not in content:
        content = replace_once(content, "  './audio-hub.js',\n", "  './audio-hub.js',\n  './release-1.4.js',\n", "service-worker release JS")
    write("service-worker.js", content)


def validate_json() -> None:
    json.loads(read("manifest.json"))
    json.loads(read("podcast-sources.json"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup-bootstrap", action="store_true")
    args = parser.parse_args()

    patch_config()
    patch_index()
    patch_status_center()
    patch_podcast_aggregator()
    patch_podcast_workflow()
    patch_service_worker()
    write("release-1.4.css", RELEASE_CSS)
    write("release-1.4.js", RELEASE_JS)
    validate_json()

    if args.cleanup_bootstrap:
        for relative in ["tools/apply_release_1_4.py", ".github/workflows/apply-release-1.4.yml"]:
            target = ROOT / relative
            if target.exists():
                target.unlink()

    print("World Revolution News 1.4 release fixes applied successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
