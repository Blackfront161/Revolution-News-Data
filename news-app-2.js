/* World Revolution News – parallel News App 2 preview */
'use strict';

(() => {
  const core = window.WRNNewsApp2Core;
  const specialty = window.WRNNewsApp2Specialty;
  const media = window.WRNNewsApp2Media;
  if (!core || !specialty || !media || window.__wrnNewsApp2Loaded) return;
  window.__wrnNewsApp2Loaded = true;

  const PREFS_KEY = 'wrn_next_preferences_v1';
  const TRANSLATIONS_KEY = 'wrn_next_teaser_translations_v1';
  const BOOKMARKS_KEY = 'wrn_bookmarks';
  const READ_KEY = 'wrn_read_list';
  const ZINE_KEY = 'wrn_zine_articles';
  const LANGUAGE_KEY = 'wrn_system_lang';
  const STORY_WATCH_KEY = 'wrn_next_story_watch_v1';
  const UI_SETTINGS_KEY = 'wrn_next_ui_settings_v1';
  const HOME_COUNT = 10;

  const PRODUCT_COPY = {
    de: {
      currentPeriod:'Aktuell', last7Days:'Letzte 7 Tage', last30Days:'Letzte 30 Tage', allArticles:'Alle Artikel',
      archiveBrowse:'Zum Nachrichtenarchiv', showMore:'Mehr Artikel laden',
      groupPolitics:'Politik & Herrschaft', groupRights:'Rechte & Gesellschaft',
      groupAction:'Bewegung & Praxis', groupEcology:'Ökologie & Wissen',
      prisonersShort:'Gefangene', summary:'Zusammenfassen', podcast:'Podcast', markRead:'Als gelesen',
      markUnread:'Als ungelesen', share:'Teilen', shared:'Geteilt.', linkCopied:'Link kopiert.',
      shareFailed:'Teilen ist nicht verfügbar.', translationCompare:'Übersetzungsvergleich',
      originalVersion:'Original', translatedVersion:'Übersetzung', closeTool:'Schließen',
      summaryLocal:'Lokale Zusammenfassung – bitte mit dem Original abgleichen.',
      summaryShort:'Kurz', summaryStandard:'Standard', summaryDetailed:'Ausführlich',
      deviceVoice:'Kostenlose Gerätestimme', voice:'Stimme', speed:'Tempo', play:'Abspielen',
      pause:'Pause', stop:'Stopp', ready:'Bereit – startet erst nach deiner Auswahl.',
      listening:'Wird vorgelesen', finished:'Wiedergabe beendet.'
    },
    en: {
      currentPeriod:'Current', last7Days:'Last 7 days', last30Days:'Last 30 days', allArticles:'All articles',
      archiveBrowse:'Open news archive', showMore:'Load more articles',
      groupPolitics:'Politics & power', groupRights:'Rights & society',
      groupAction:'Movements & action', groupEcology:'Ecology & knowledge',
      prisonersShort:'Prisoners', summary:'Summarize', podcast:'Podcast', markRead:'Mark read',
      markUnread:'Mark unread', share:'Share', shared:'Shared.', linkCopied:'Link copied.',
      shareFailed:'Sharing is unavailable.', translationCompare:'Translation comparison',
      originalVersion:'Original', translatedVersion:'Translation', closeTool:'Close',
      summaryLocal:'Local summary – please compare it with the original.',
      summaryShort:'Short', summaryStandard:'Standard', summaryDetailed:'Detailed',
      deviceVoice:'Free device voice', voice:'Voice', speed:'Speed', play:'Play',
      pause:'Pause', stop:'Stop', ready:'Ready – starts only after you choose play.',
      listening:'Reading aloud', finished:'Playback finished.'
    },
    es: {
      currentPeriod:'Actualidad', last7Days:'Últimos 7 días', last30Days:'Últimos 30 días', allArticles:'Todos los artículos',
      archiveBrowse:'Abrir archivo de noticias', showMore:'Cargar más artículos',
      groupPolitics:'Política y poder', groupRights:'Derechos y sociedad',
      groupAction:'Movimientos y acción', groupEcology:'Ecología y conocimiento',
      prisonersShort:'Presxs', summary:'Resumir', podcast:'Pódcast', markRead:'Marcar como leído',
      markUnread:'Marcar como no leído', share:'Compartir', shared:'Compartido.', linkCopied:'Enlace copiado.',
      shareFailed:'No se puede compartir.', translationCompare:'Comparar traducción',
      originalVersion:'Original', translatedVersion:'Traducción', closeTool:'Cerrar',
      summaryLocal:'Resumen local; compáralo con el original.',
      summaryShort:'Breve', summaryStandard:'Estándar', summaryDetailed:'Detallado',
      deviceVoice:'Voz gratuita del dispositivo', voice:'Voz', speed:'Velocidad', play:'Reproducir',
      pause:'Pausa', stop:'Detener', ready:'Listo; comienza solo cuando lo elijas.',
      listening:'Leyendo', finished:'Reproducción terminada.'
    },
    fr: {
      currentPeriod:'Actualité', last7Days:'7 derniers jours', last30Days:'30 derniers jours', allArticles:'Tous les articles',
      archiveBrowse:'Ouvrir les archives', showMore:'Charger plus d’articles',
      groupPolitics:'Politique et pouvoir', groupRights:'Droits et société',
      groupAction:'Mouvements et action', groupEcology:'Écologie et savoirs',
      prisonersShort:'Prisonnier·ères', summary:'Résumer', podcast:'Podcast', markRead:'Marquer comme lu',
      markUnread:'Marquer non lu', share:'Partager', shared:'Partagé.', linkCopied:'Lien copié.',
      shareFailed:'Le partage est indisponible.', translationCompare:'Comparer la traduction',
      originalVersion:'Original', translatedVersion:'Traduction', closeTool:'Fermer',
      summaryLocal:'Résumé local – à comparer avec l’original.',
      summaryShort:'Court', summaryStandard:'Standard', summaryDetailed:'Détaillé',
      deviceVoice:'Voix gratuite de l’appareil', voice:'Voix', speed:'Vitesse', play:'Lire',
      pause:'Pause', stop:'Arrêter', ready:'Prêt – démarre uniquement après votre choix.',
      listening:'Lecture en cours', finished:'Lecture terminée.'
    },
    it: {
      currentPeriod:'Attualità', last7Days:'Ultimi 7 giorni', last30Days:'Ultimi 30 giorni', allArticles:'Tutti gli articoli',
      archiveBrowse:'Apri archivio notizie', showMore:'Carica altri articoli',
      groupPolitics:'Politica e potere', groupRights:'Diritti e società',
      groupAction:'Movimenti e azione', groupEcology:'Ecologia e sapere',
      prisonersShort:'Prigionieri', summary:'Riassumi', podcast:'Podcast', markRead:'Segna come letto',
      markUnread:'Segna come non letto', share:'Condividi', shared:'Condiviso.', linkCopied:'Link copiato.',
      shareFailed:'Condivisione non disponibile.', translationCompare:'Confronto traduzione',
      originalVersion:'Originale', translatedVersion:'Traduzione', closeTool:'Chiudi',
      summaryLocal:'Riassunto locale – confrontalo con l’originale.',
      summaryShort:'Breve', summaryStandard:'Standard', summaryDetailed:'Dettagliato',
      deviceVoice:'Voce gratuita del dispositivo', voice:'Voce', speed:'Velocità', play:'Riproduci',
      pause:'Pausa', stop:'Stop', ready:'Pronto – parte solo dopo la selezione.',
      listening:'Lettura in corso', finished:'Riproduzione terminata.'
    },
    pt: {
      currentPeriod:'Atualidade', last7Days:'Últimos 7 dias', last30Days:'Últimos 30 dias', allArticles:'Todos os artigos',
      archiveBrowse:'Abrir arquivo de notícias', showMore:'Carregar mais artigos',
      groupPolitics:'Política e poder', groupRights:'Direitos e sociedade',
      groupAction:'Movimentos e ação', groupEcology:'Ecologia e saberes',
      prisonersShort:'Prisioneiros', summary:'Resumir', podcast:'Podcast', markRead:'Marcar como lido',
      markUnread:'Marcar como não lido', share:'Partilhar', shared:'Partilhado.', linkCopied:'Ligação copiada.',
      shareFailed:'Partilha indisponível.', translationCompare:'Comparar tradução',
      originalVersion:'Original', translatedVersion:'Tradução', closeTool:'Fechar',
      summaryLocal:'Resumo local – compara com o original.',
      summaryShort:'Curto', summaryStandard:'Padrão', summaryDetailed:'Detalhado',
      deviceVoice:'Voz gratuita do dispositivo', voice:'Voz', speed:'Velocidade', play:'Reproduzir',
      pause:'Pausa', stop:'Parar', ready:'Pronto – só começa após a tua escolha.',
      listening:'A ler', finished:'Reprodução terminada.'
    },
    ru: {
      currentPeriod:'Актуальное', last7Days:'Последние 7 дней', last30Days:'Последние 30 дней', allArticles:'Все материалы',
      archiveBrowse:'Открыть архив новостей', showMore:'Загрузить ещё',
      groupPolitics:'Политика и власть', groupRights:'Права и общество',
      groupAction:'Движения и действия', groupEcology:'Экология и знания',
      prisonersShort:'Заключённые', summary:'Кратко', podcast:'Подкаст', markRead:'Отметить прочитанным',
      markUnread:'Отметить непрочитанным', share:'Поделиться', shared:'Отправлено.', linkCopied:'Ссылка скопирована.',
      shareFailed:'Поделиться не удалось.', translationCompare:'Сравнение перевода',
      originalVersion:'Оригинал', translatedVersion:'Перевод', closeTool:'Закрыть',
      summaryLocal:'Локальное резюме — сверьте с оригиналом.',
      summaryShort:'Коротко', summaryStandard:'Обычно', summaryDetailed:'Подробно',
      deviceVoice:'Бесплатный голос устройства', voice:'Голос', speed:'Скорость', play:'Воспроизвести',
      pause:'Пауза', stop:'Стоп', ready:'Готово — запуск только после выбора.',
      listening:'Чтение', finished:'Воспроизведение завершено.'
    },
    el: {
      currentPeriod:'Τρέχοντα', last7Days:'Τελευταίες 7 ημέρες', last30Days:'Τελευταίες 30 ημέρες', allArticles:'Όλα τα άρθρα',
      archiveBrowse:'Άνοιγμα αρχείου ειδήσεων', showMore:'Φόρτωση περισσότερων',
      groupPolitics:'Πολιτική και εξουσία', groupRights:'Δικαιώματα και κοινωνία',
      groupAction:'Κινήματα και δράση', groupEcology:'Οικολογία και γνώση',
      prisonersShort:'Κρατούμενοι', summary:'Σύνοψη', podcast:'Podcast', markRead:'Σήμανση ως διαβασμένο',
      markUnread:'Σήμανση ως αδιάβαστο', share:'Κοινοποίηση', shared:'Κοινοποιήθηκε.', linkCopied:'Ο σύνδεσμος αντιγράφηκε.',
      shareFailed:'Η κοινοποίηση δεν είναι διαθέσιμη.', translationCompare:'Σύγκριση μετάφρασης',
      originalVersion:'Πρωτότυπο', translatedVersion:'Μετάφραση', closeTool:'Κλείσιμο',
      summaryLocal:'Τοπική σύνοψη – ελέγξτε την με το πρωτότυπο.',
      summaryShort:'Σύντομη', summaryStandard:'Κανονική', summaryDetailed:'Αναλυτική',
      deviceVoice:'Δωρεάν φωνή συσκευής', voice:'Φωνή', speed:'Ταχύτητα', play:'Αναπαραγωγή',
      pause:'Παύση', stop:'Διακοπή', ready:'Έτοιμο – ξεκινά μόνο μετά την επιλογή σας.',
      listening:'Ανάγνωση', finished:'Η αναπαραγωγή ολοκληρώθηκε.'
    },
    tr: {
      currentPeriod:'Güncel', last7Days:'Son 7 gün', last30Days:'Son 30 gün', allArticles:'Tüm haberler',
      archiveBrowse:'Haber arşivini aç', showMore:'Daha fazla haber yükle',
      groupPolitics:'Siyaset ve iktidar', groupRights:'Haklar ve toplum',
      groupAction:'Hareketler ve eylem', groupEcology:'Ekoloji ve bilgi',
      prisonersShort:'Tutsaklar', summary:'Özetle', podcast:'Podcast', markRead:'Okundu işaretle',
      markUnread:'Okunmadı işaretle', share:'Paylaş', shared:'Paylaşıldı.', linkCopied:'Bağlantı kopyalandı.',
      shareFailed:'Paylaşım kullanılamıyor.', translationCompare:'Çeviri karşılaştırması',
      originalVersion:'Özgün', translatedVersion:'Çeviri', closeTool:'Kapat',
      summaryLocal:'Yerel özet – özgün metinle karşılaştırın.',
      summaryShort:'Kısa', summaryStandard:'Standart', summaryDetailed:'Ayrıntılı',
      deviceVoice:'Ücretsiz cihaz sesi', voice:'Ses', speed:'Hız', play:'Oynat',
      pause:'Duraklat', stop:'Durdur', ready:'Hazır – yalnızca seçiminizden sonra başlar.',
      listening:'Seslendiriliyor', finished:'Oynatma tamamlandı.'
    }
  };

  const COPY = {
    de: {
      preview: 'News App 2 · Vorschau', language: 'Sprache', classic: 'Bisherige App',
      searchLabel: 'Nachrichten durchsuchen', search: 'Suchen', searchPlaceholder: 'Titel, Quelle oder Thema',
      home: 'Start', following: 'Für mich', discover: 'Entdecken', media: 'Medien', saved: 'Gespeichert',
      loading: 'Nachrichten werden geladen …', latest: 'Aktuell', important: 'Das Wichtigste',
      briefing: 'In 5 Minuten', briefingHint: 'Fünf aktuelle Meldungen in Kürze',
      moreNews: 'Weitere Nachrichten', source: 'Quelle', translate: 'Übersetzen',
      translating: 'Übersetzung läuft …', translated: 'Maschinell übersetzt', translationFailed: 'Übersetzung nicht verfügbar.',
      original: 'Original öffnen', save: 'Später lesen', savedLabel: 'Gespeichert', removeSaved: 'Entfernen',
      personalTitle: 'Deine Nachrichten', personalIntro: 'Nach deinen ausgewählten Regionen und Themen zusammengestellt.',
      personalize: 'Deinen Feed einrichten', personalLocal: 'Nur auf diesem Gerät gespeichert',
      editSelection: 'Auswahl bearbeiten', chooseRegions: 'Regionen auswählen', chooseTopics: 'Themen auswählen',
      savePreferences: 'Auswahl speichern', cancel: 'Abbrechen', noPreferences: 'Noch keine Auswahl gespeichert',
      noPreferencesText: 'Wähle Regionen und Themen. Deine Auswahl bleibt ausschließlich auf diesem Gerät.',
      noMatches: 'Keine passenden Nachrichten gefunden', noMatchesText: 'Passe deine Auswahl oder Suche an.',
      discoverIntro: 'Durchsuche Regionen, Themen und Quellen, ohne deinen persönlichen Feed zu verändern.',
      all: 'Alle', regions: 'Regionen', topics: 'Themen', results: 'Ergebnisse',
      mediaIntro: 'Video, Podcasts und Radio an einem ruhigen, datensparsamen Ort.',
      video: 'Video', videoText: 'Videos aus Nachrichten und kuratierten Informationsquellen.',
      podcasts: 'Original-Podcasts', podcastsText: 'Sendungen aus unabhängigen und bewegungsnahen Quellen.',
      generated: 'Erzeugte Podcasts', generatedText: 'Gespeicherte Azure-Podcasts der letzten 30 Tage.',
      radio: 'Live-Radio', radioText: 'Freie und nichtkommerzielle Radiostationen.',
      openClassic: 'Im bisherigen Bereich öffnen', specialty: 'Weitere Bereiche',
      events: 'Termine', eventsText: 'Aktionen, Treffen und Veranstaltungen.',
      lexicon: 'Lexikon', lexiconText: '100 Begriffe, Perspektiven und Quellen.',
      prisoners: 'Gefangenensolidarität', prisonersText: 'Informationen und private Briefwerkstatt.',
      developments: 'Entwicklungen · Beta', developmentsText: 'Zusammengehörige Meldungen und Zeitverläufe.',
      savedIntro: 'Lokal gespeicherte Artikel aus beiden App-Oberflächen.',
      emptySaved: 'Noch keine Artikel gespeichert', emptySavedText: 'Tippe bei einem Artikel auf den Stern.',
      openArticle: 'Artikel öffnen', readOriginal: 'Beim Original lesen', loadError: 'Die Nachrichtendaten konnten nicht geladen werden.',
      retry: 'Erneut versuchen', menuSearch: 'Suche öffnen', close: 'Schließen',
      selectionSaved: 'Deine Auswahl wurde lokal gespeichert.', articleSaved: 'Artikel gespeichert.',
      articleRemoved: 'Artikel entfernt.', translatedTitle: 'Übersetzter Titel und Einleitung',
      previewNotice: 'Parallele Vorschau – die veröffentlichte App bleibt unverändert.'
    },
    en: {
      preview: 'News App 2 · Preview', language: 'Language', classic: 'Current app',
      searchLabel: 'Search news', search: 'Search', searchPlaceholder: 'Title, source or topic',
      home: 'Home', following: 'For you', discover: 'Discover', media: 'Media', saved: 'Saved',
      loading: 'Loading news …', latest: 'Latest', important: 'Top stories',
      briefing: 'In 5 minutes', briefingHint: 'Five current stories at a glance',
      moreNews: 'More news', source: 'Source', translate: 'Translate',
      translating: 'Translating …', translated: 'Machine translated', translationFailed: 'Translation unavailable.',
      original: 'Open original', save: 'Read later', savedLabel: 'Saved', removeSaved: 'Remove',
      personalTitle: 'Your news', personalIntro: 'Built from your selected regions and topics.',
      personalize: 'Set up your feed', personalLocal: 'Stored only on this device',
      editSelection: 'Edit selection', chooseRegions: 'Choose regions', chooseTopics: 'Choose topics',
      savePreferences: 'Save selection', cancel: 'Cancel', noPreferences: 'No selection saved yet',
      noPreferencesText: 'Choose regions and topics. Your selection stays on this device.',
      noMatches: 'No matching news', noMatchesText: 'Adjust your selection or search.',
      discoverIntro: 'Explore regions, topics and sources without changing your personal feed.',
      all: 'All', regions: 'Regions', topics: 'Topics', results: 'Results',
      mediaIntro: 'Video, podcasts and radio in one calm, privacy-conscious place.',
      video: 'Video', videoText: 'Videos from news stories and curated information sources.',
      podcasts: 'Original podcasts', podcastsText: 'Shows from independent and movement sources.',
      generated: 'Generated podcasts', generatedText: 'Stored Azure podcasts from the last 30 days.',
      radio: 'Live radio', radioText: 'Free and non-commercial radio stations.',
      openClassic: 'Open current section', specialty: 'More areas',
      events: 'Events', eventsText: 'Actions, meetings and events.',
      lexicon: 'Glossary', lexiconText: '100 terms, perspectives and sources.',
      prisoners: 'Prisoner solidarity', prisonersText: 'Information and private letter workshop.',
      developments: 'Developments · Beta', developmentsText: 'Related coverage and timelines.',
      savedIntro: 'Articles stored locally from both app interfaces.',
      emptySaved: 'No saved articles yet', emptySavedText: 'Tap the star on an article.',
      openArticle: 'Open article', readOriginal: 'Read original', loadError: 'News data could not be loaded.',
      retry: 'Try again', menuSearch: 'Open search', close: 'Close',
      selectionSaved: 'Your selection was saved locally.', articleSaved: 'Article saved.',
      articleRemoved: 'Article removed.', translatedTitle: 'Translated title and introduction',
      previewNotice: 'Parallel preview – the published app remains unchanged.'
    },
    es: {
      preview:'News App 2 · Vista previa', language:'Idioma', classic:'Aplicación actual', searchLabel:'Buscar noticias', search:'Buscar',
      searchPlaceholder:'Título, fuente o tema', home:'Inicio', following:'Para mí', discover:'Explorar', media:'Medios', saved:'Guardado',
      loading:'Cargando noticias …', latest:'Actualidad', important:'Lo más importante', briefing:'En 5 minutos',
      briefingHint:'Cinco noticias actuales en breve', moreNews:'Más noticias', source:'Fuente', translate:'Traducir',
      translating:'Traduciendo …', translated:'Traducción automática', translationFailed:'Traducción no disponible.',
      original:'Abrir original', save:'Leer después', savedLabel:'Guardado', removeSaved:'Eliminar',
      personalTitle:'Tus noticias', personalIntro:'Según tus regiones y temas seleccionados.', personalize:'Configurar tu feed',
      personalLocal:'Guardado solo en este dispositivo', editSelection:'Editar selección', chooseRegions:'Elegir regiones',
      chooseTopics:'Elegir temas', savePreferences:'Guardar selección', cancel:'Cancelar', noPreferences:'Aún no hay selección',
      noPreferencesText:'Elige regiones y temas. La selección permanece en este dispositivo.', noMatches:'No hay noticias coincidentes',
      noMatchesText:'Ajusta tu selección o búsqueda.', discoverIntro:'Explora regiones, temas y fuentes sin cambiar tu feed.',
      all:'Todo', regions:'Regiones', topics:'Temas', results:'Resultados', mediaIntro:'Vídeo, pódcasts y radio en un solo lugar.',
      video:'Vídeo', videoText:'Vídeos de noticias y fuentes informativas seleccionadas.', podcasts:'Pódcasts originales',
      podcastsText:'Programas de fuentes independientes y de movimientos.', generated:'Pódcasts generados',
      generatedText:'Pódcasts de Azure guardados durante 30 días.', radio:'Radio en directo',
      radioText:'Radios libres y no comerciales.', openClassic:'Abrir área actual', specialty:'Más áreas',
      events:'Eventos', eventsText:'Acciones, reuniones y eventos.', lexicon:'Glosario', lexiconText:'100 términos, perspectivas y fuentes.',
      prisoners:'Solidaridad con presxs', prisonersText:'Información y taller privado de cartas.', developments:'Desarrollos · Beta',
      developmentsText:'Noticias relacionadas y cronologías.', savedIntro:'Artículos guardados localmente.',
      emptySaved:'No hay artículos guardados', emptySavedText:'Pulsa la estrella en un artículo.', openArticle:'Abrir artículo',
      readOriginal:'Leer original', loadError:'No se pudieron cargar las noticias.', retry:'Intentar de nuevo',
      menuSearch:'Abrir búsqueda', close:'Cerrar', selectionSaved:'Selección guardada localmente.',
      articleSaved:'Artículo guardado.', articleRemoved:'Artículo eliminado.', translatedTitle:'Título e introducción traducidos',
      previewNotice:'Vista previa paralela: la aplicación publicada no cambia.'
    },
    fr: {
      preview:'News App 2 · Aperçu', language:'Langue', classic:'Application actuelle', searchLabel:'Rechercher des actualités', search:'Rechercher',
      searchPlaceholder:'Titre, source ou thème', home:'Accueil', following:'Pour moi', discover:'Découvrir', media:'Médias', saved:'Enregistré',
      loading:'Chargement des actualités …', latest:'Actualité', important:'À la une', briefing:'En 5 minutes',
      briefingHint:'Cinq informations actuelles en bref', moreNews:'Plus d’actualités', source:'Source', translate:'Traduire',
      translating:'Traduction …', translated:'Traduit automatiquement', translationFailed:'Traduction indisponible.',
      original:'Ouvrir l’original', save:'Lire plus tard', savedLabel:'Enregistré', removeSaved:'Supprimer',
      personalTitle:'Vos actualités', personalIntro:'Selon vos régions et thèmes choisis.', personalize:'Configurer votre fil',
      personalLocal:'Stocké uniquement sur cet appareil', editSelection:'Modifier la sélection', chooseRegions:'Choisir les régions',
      chooseTopics:'Choisir les thèmes', savePreferences:'Enregistrer', cancel:'Annuler', noPreferences:'Aucune sélection enregistrée',
      noPreferencesText:'Choisissez des régions et thèmes. Le choix reste sur cet appareil.', noMatches:'Aucune actualité correspondante',
      noMatchesText:'Modifiez votre sélection ou recherche.', discoverIntro:'Explorez régions, thèmes et sources sans changer votre fil.',
      all:'Tout', regions:'Régions', topics:'Thèmes', results:'Résultats', mediaIntro:'Vidéos, podcasts et radio au même endroit.',
      video:'Vidéo', videoText:'Vidéos d’actualité et sources informatives sélectionnées.', podcasts:'Podcasts originaux',
      podcastsText:'Émissions de sources indépendantes et militantes.', generated:'Podcasts générés',
      generatedText:'Podcasts Azure enregistrés pendant 30 jours.', radio:'Radio en direct',
      radioText:'Radios libres et non commerciales.', openClassic:'Ouvrir l’espace actuel', specialty:'Autres espaces',
      events:'Événements', eventsText:'Actions, rencontres et événements.', lexicon:'Lexique', lexiconText:'100 termes, perspectives et sources.',
      prisoners:'Solidarité avec les prisonnier·ères', prisonersText:'Informations et atelier privé de lettres.',
      developments:'Évolutions · Bêta', developmentsText:'Articles liés et chronologies.', savedIntro:'Articles enregistrés localement.',
      emptySaved:'Aucun article enregistré', emptySavedText:'Touchez l’étoile d’un article.', openArticle:'Ouvrir l’article',
      readOriginal:'Lire l’original', loadError:'Impossible de charger les actualités.', retry:'Réessayer',
      menuSearch:'Ouvrir la recherche', close:'Fermer', selectionSaved:'Sélection enregistrée localement.',
      articleSaved:'Article enregistré.', articleRemoved:'Article supprimé.', translatedTitle:'Titre et introduction traduits',
      previewNotice:'Aperçu parallèle – l’application publiée reste inchangée.'
    },
    it: {
      preview:'News App 2 · Anteprima', language:'Lingua', classic:'App attuale', searchLabel:'Cerca notizie', search:'Cerca',
      searchPlaceholder:'Titolo, fonte o tema', home:'Inizio', following:'Per me', discover:'Scopri', media:'Media', saved:'Salvati',
      loading:'Caricamento notizie …', latest:'Attualità', important:'In primo piano', briefing:'In 5 minuti',
      briefingHint:'Cinque notizie attuali in breve', moreNews:'Altre notizie', source:'Fonte', translate:'Traduci',
      translating:'Traduzione …', translated:'Traduzione automatica', translationFailed:'Traduzione non disponibile.',
      original:'Apri originale', save:'Leggi dopo', savedLabel:'Salvato', removeSaved:'Rimuovi',
      personalTitle:'Le tue notizie', personalIntro:'In base a regioni e temi scelti.', personalize:'Configura il tuo feed',
      personalLocal:'Salvato solo su questo dispositivo', editSelection:'Modifica selezione', chooseRegions:'Scegli regioni',
      chooseTopics:'Scegli temi', savePreferences:'Salva selezione', cancel:'Annulla', noPreferences:'Nessuna selezione salvata',
      noPreferencesText:'Scegli regioni e temi. La selezione resta sul dispositivo.', noMatches:'Nessuna notizia corrispondente',
      noMatchesText:'Modifica selezione o ricerca.', discoverIntro:'Esplora regioni, temi e fonti senza cambiare il feed.',
      all:'Tutto', regions:'Regioni', topics:'Temi', results:'Risultati', mediaIntro:'Video, podcast e radio in un unico luogo.',
      video:'Video', videoText:'Video da notizie e fonti informative selezionate.', podcasts:'Podcast originali',
      podcastsText:'Programmi da fonti indipendenti e dei movimenti.', generated:'Podcast generati',
      generatedText:'Podcast Azure conservati per 30 giorni.', radio:'Radio in diretta', radioText:'Radio libere e non commerciali.',
      openClassic:'Apri area attuale', specialty:'Altre aree', events:'Eventi', eventsText:'Azioni, incontri ed eventi.',
      lexicon:'Glossario', lexiconText:'100 termini, prospettive e fonti.', prisoners:'Solidarietà ai prigionieri',
      prisonersText:'Informazioni e laboratorio privato di lettere.', developments:'Sviluppi · Beta',
      developmentsText:'Notizie collegate e cronologie.', savedIntro:'Articoli salvati localmente.',
      emptySaved:'Nessun articolo salvato', emptySavedText:'Tocca la stella su un articolo.', openArticle:'Apri articolo',
      readOriginal:'Leggi originale', loadError:'Impossibile caricare le notizie.', retry:'Riprova',
      menuSearch:'Apri ricerca', close:'Chiudi', selectionSaved:'Selezione salvata localmente.',
      articleSaved:'Articolo salvato.', articleRemoved:'Articolo rimosso.', translatedTitle:'Titolo e introduzione tradotti',
      previewNotice:'Anteprima parallela: l’app pubblicata non cambia.'
    },
    pt: {
      preview:'News App 2 · Pré-visualização', language:'Idioma', classic:'Aplicação atual', searchLabel:'Pesquisar notícias', search:'Pesquisar',
      searchPlaceholder:'Título, fonte ou tema', home:'Início', following:'Para mim', discover:'Explorar', media:'Media', saved:'Guardados',
      loading:'A carregar notícias …', latest:'Atualidade', important:'Destaques', briefing:'Em 5 minutos',
      briefingHint:'Cinco notícias atuais em resumo', moreNews:'Mais notícias', source:'Fonte', translate:'Traduzir',
      translating:'A traduzir …', translated:'Tradução automática', translationFailed:'Tradução indisponível.',
      original:'Abrir original', save:'Ler depois', savedLabel:'Guardado', removeSaved:'Remover',
      personalTitle:'As tuas notícias', personalIntro:'Com base nas regiões e temas escolhidos.', personalize:'Configurar o feed',
      personalLocal:'Guardado apenas neste dispositivo', editSelection:'Editar seleção', chooseRegions:'Escolher regiões',
      chooseTopics:'Escolher temas', savePreferences:'Guardar seleção', cancel:'Cancelar', noPreferences:'Nenhuma seleção guardada',
      noPreferencesText:'Escolhe regiões e temas. A seleção fica neste dispositivo.', noMatches:'Nenhuma notícia correspondente',
      noMatchesText:'Altera a seleção ou pesquisa.', discoverIntro:'Explora regiões, temas e fontes sem alterar o teu feed.',
      all:'Tudo', regions:'Regiões', topics:'Temas', results:'Resultados', mediaIntro:'Vídeo, podcasts e rádio num só lugar.',
      video:'Vídeo', videoText:'Vídeos de notícias e fontes informativas selecionadas.', podcasts:'Podcasts originais',
      podcastsText:'Programas de fontes independentes e de movimentos.', generated:'Podcasts gerados',
      generatedText:'Podcasts Azure guardados durante 30 dias.', radio:'Rádio em direto', radioText:'Rádios livres e não comerciais.',
      openClassic:'Abrir área atual', specialty:'Outras áreas', events:'Eventos', eventsText:'Ações, encontros e eventos.',
      lexicon:'Glossário', lexiconText:'100 termos, perspetivas e fontes.', prisoners:'Solidariedade com prisioneiros',
      prisonersText:'Informação e oficina privada de cartas.', developments:'Desenvolvimentos · Beta',
      developmentsText:'Notícias relacionadas e cronologias.', savedIntro:'Artigos guardados localmente.',
      emptySaved:'Nenhum artigo guardado', emptySavedText:'Toca na estrela de um artigo.', openArticle:'Abrir artigo',
      readOriginal:'Ler original', loadError:'Não foi possível carregar as notícias.', retry:'Tentar novamente',
      menuSearch:'Abrir pesquisa', close:'Fechar', selectionSaved:'Seleção guardada localmente.',
      articleSaved:'Artigo guardado.', articleRemoved:'Artigo removido.', translatedTitle:'Título e introdução traduzidos',
      previewNotice:'Pré-visualização paralela: a aplicação publicada não muda.'
    },
    ru: {
      preview:'News App 2 · Предпросмотр', language:'Язык', classic:'Текущее приложение', searchLabel:'Поиск новостей', search:'Поиск',
      searchPlaceholder:'Заголовок, источник или тема', home:'Главная', following:'Для меня', discover:'Обзор', media:'Медиа', saved:'Сохранённое',
      loading:'Загрузка новостей …', latest:'Сейчас', important:'Главное', briefing:'За 5 минут',
      briefingHint:'Пять актуальных новостей кратко', moreNews:'Другие новости', source:'Источник', translate:'Перевести',
      translating:'Перевод …', translated:'Машинный перевод', translationFailed:'Перевод недоступен.',
      original:'Открыть оригинал', save:'Прочитать позже', savedLabel:'Сохранено', removeSaved:'Удалить',
      personalTitle:'Ваши новости', personalIntro:'По выбранным регионам и темам.', personalize:'Настроить ленту',
      personalLocal:'Хранится только на этом устройстве', editSelection:'Изменить выбор', chooseRegions:'Выбрать регионы',
      chooseTopics:'Выбрать темы', savePreferences:'Сохранить', cancel:'Отмена', noPreferences:'Выбор ещё не сохранён',
      noPreferencesText:'Выберите регионы и темы. Данные останутся на устройстве.', noMatches:'Подходящих новостей нет',
      noMatchesText:'Измените выбор или поиск.', discoverIntro:'Изучайте регионы, темы и источники, не меняя личную ленту.',
      all:'Все', regions:'Регионы', topics:'Темы', results:'Результаты', mediaIntro:'Видео, подкасты и радио в одном месте.',
      video:'Видео', videoText:'Видео из новостей и отобранных источников.', podcasts:'Оригинальные подкасты',
      podcastsText:'Передачи независимых и общественных источников.', generated:'Созданные подкасты',
      generatedText:'Подкасты Azure за последние 30 дней.', radio:'Прямое радио', radioText:'Свободные некоммерческие радиостанции.',
      openClassic:'Открыть текущий раздел', specialty:'Другие разделы', events:'События', eventsText:'Акции, встречи и события.',
      lexicon:'Словарь', lexiconText:'100 терминов, точек зрения и источников.', prisoners:'Солидарность с заключёнными',
      prisonersText:'Информация и приватная мастерская писем.', developments:'Развитие · Бета',
      developmentsText:'Связанные материалы и хронологии.', savedIntro:'Локально сохранённые статьи.',
      emptySaved:'Сохранённых статей пока нет', emptySavedText:'Нажмите звезду на статье.', openArticle:'Открыть статью',
      readOriginal:'Читать оригинал', loadError:'Не удалось загрузить новости.', retry:'Повторить',
      menuSearch:'Открыть поиск', close:'Закрыть', selectionSaved:'Выбор сохранён локально.',
      articleSaved:'Статья сохранена.', articleRemoved:'Статья удалена.', translatedTitle:'Переведённые заголовок и введение',
      previewNotice:'Параллельный предпросмотр — опубликованное приложение не меняется.'
    },
    el: {
      preview:'News App 2 · Προεπισκόπηση', language:'Γλώσσα', classic:'Τρέχουσα εφαρμογή', searchLabel:'Αναζήτηση ειδήσεων', search:'Αναζήτηση',
      searchPlaceholder:'Τίτλος, πηγή ή θέμα', home:'Αρχική', following:'Για μένα', discover:'Ανακάλυψη', media:'Μέσα', saved:'Αποθηκευμένα',
      loading:'Φόρτωση ειδήσεων …', latest:'Τώρα', important:'Σημαντικότερα', briefing:'Σε 5 λεπτά',
      briefingHint:'Πέντε τρέχουσες ειδήσεις εν συντομία', moreNews:'Περισσότερες ειδήσεις', source:'Πηγή', translate:'Μετάφραση',
      translating:'Μετάφραση …', translated:'Αυτόματη μετάφραση', translationFailed:'Η μετάφραση δεν είναι διαθέσιμη.',
      original:'Άνοιγμα πρωτοτύπου', save:'Ανάγνωση αργότερα', savedLabel:'Αποθηκεύτηκε', removeSaved:'Αφαίρεση',
      personalTitle:'Οι ειδήσεις σου', personalIntro:'Με βάση τις περιοχές και τα θέματα που επέλεξες.', personalize:'Ρύθμιση ροής',
      personalLocal:'Αποθήκευση μόνο σε αυτή τη συσκευή', editSelection:'Επεξεργασία επιλογής', chooseRegions:'Επιλογή περιοχών',
      chooseTopics:'Επιλογή θεμάτων', savePreferences:'Αποθήκευση', cancel:'Ακύρωση', noPreferences:'Δεν υπάρχει αποθηκευμένη επιλογή',
      noPreferencesText:'Επίλεξε περιοχές και θέματα. Η επιλογή μένει στη συσκευή.', noMatches:'Δεν βρέθηκαν σχετικές ειδήσεις',
      noMatchesText:'Άλλαξε την επιλογή ή την αναζήτηση.', discoverIntro:'Εξερεύνησε περιοχές, θέματα και πηγές χωρίς αλλαγή της ροής.',
      all:'Όλα', regions:'Περιοχές', topics:'Θέματα', results:'Αποτελέσματα', mediaIntro:'Βίντεο, podcast και ραδιόφωνο μαζί.',
      video:'Βίντεο', videoText:'Βίντεο από ειδήσεις και επιλεγμένες ενημερωτικές πηγές.', podcasts:'Πρωτότυπα podcast',
      podcastsText:'Εκπομπές από ανεξάρτητες πηγές και κινήματα.', generated:'Δημιουργημένα podcast',
      generatedText:'Podcast Azure αποθηκευμένα για 30 ημέρες.', radio:'Ζωντανό ραδιόφωνο', radioText:'Ελεύθεροι μη εμπορικοί σταθμοί.',
      openClassic:'Άνοιγμα τρέχουσας ενότητας', specialty:'Περισσότερες ενότητες', events:'Εκδηλώσεις', eventsText:'Δράσεις, συναντήσεις και εκδηλώσεις.',
      lexicon:'Λεξικό', lexiconText:'100 όροι, οπτικές και πηγές.', prisoners:'Αλληλεγγύη κρατουμένων',
      prisonersText:'Πληροφορίες και ιδιωτικό εργαστήριο επιστολών.', developments:'Εξελίξεις · Beta',
      developmentsText:'Σχετικές ειδήσεις και χρονολόγια.', savedIntro:'Άρθρα αποθηκευμένα τοπικά.',
      emptySaved:'Δεν υπάρχουν αποθηκευμένα άρθρα', emptySavedText:'Πάτησε το αστέρι σε ένα άρθρο.', openArticle:'Άνοιγμα άρθρου',
      readOriginal:'Ανάγνωση πρωτοτύπου', loadError:'Δεν ήταν δυνατή η φόρτωση.', retry:'Δοκιμή ξανά',
      menuSearch:'Άνοιγμα αναζήτησης', close:'Κλείσιμο', selectionSaved:'Η επιλογή αποθηκεύτηκε τοπικά.',
      articleSaved:'Το άρθρο αποθηκεύτηκε.', articleRemoved:'Το άρθρο αφαιρέθηκε.', translatedTitle:'Μεταφρασμένος τίτλος και εισαγωγή',
      previewNotice:'Παράλληλη προεπισκόπηση — η δημοσιευμένη εφαρμογή δεν αλλάζει.'
    },
    tr: {
      preview:'News App 2 · Önizleme', language:'Dil', classic:'Mevcut uygulama', searchLabel:'Haberlerde ara', search:'Ara',
      searchPlaceholder:'Başlık, kaynak veya konu', home:'Başlangıç', following:'Benim için', discover:'Keşfet', media:'Medya', saved:'Kaydedilenler',
      loading:'Haberler yükleniyor …', latest:'Güncel', important:'Önemli haberler', briefing:'5 dakikada',
      briefingHint:'Beş güncel haberin kısa özeti', moreNews:'Diğer haberler', source:'Kaynak', translate:'Çevir',
      translating:'Çevriliyor …', translated:'Makine çevirisi', translationFailed:'Çeviri kullanılamıyor.',
      original:'Orijinali aç', save:'Sonra oku', savedLabel:'Kaydedildi', removeSaved:'Kaldır',
      personalTitle:'Haberlerin', personalIntro:'Seçtiğin bölge ve konulara göre.', personalize:'Akışını ayarla',
      personalLocal:'Yalnızca bu cihazda saklanır', editSelection:'Seçimi düzenle', chooseRegions:'Bölgeleri seç',
      chooseTopics:'Konuları seç', savePreferences:'Seçimi kaydet', cancel:'İptal', noPreferences:'Henüz seçim kaydedilmedi',
      noPreferencesText:'Bölge ve konu seç. Seçimin bu cihazda kalır.', noMatches:'Uygun haber bulunamadı',
      noMatchesText:'Seçimini veya aramanı değiştir.', discoverIntro:'Kişisel akışını değiştirmeden bölge, konu ve kaynakları keşfet.',
      all:'Tümü', regions:'Bölgeler', topics:'Konular', results:'Sonuçlar', mediaIntro:'Video, podcast ve radyo tek yerde.',
      video:'Video', videoText:'Haberlerden ve seçilmiş bilgi kaynaklarından videolar.', podcasts:'Orijinal podcastler',
      podcastsText:'Bağımsız ve hareket kaynaklarından programlar.', generated:'Oluşturulan podcastler',
      generatedText:'Son 30 günün Azure podcastleri.', radio:'Canlı radyo', radioText:'Özgür ve ticari olmayan radyolar.',
      openClassic:'Mevcut bölümü aç', specialty:'Diğer alanlar', events:'Etkinlikler', eventsText:'Eylemler, toplantılar ve etkinlikler.',
      lexicon:'Sözlük', lexiconText:'100 kavram, bakış açısı ve kaynak.', prisoners:'Tutsak dayanışması',
      prisonersText:'Bilgi ve özel mektup atölyesi.', developments:'Gelişmeler · Beta',
      developmentsText:'İlgili haberler ve zaman çizelgeleri.', savedIntro:'Yerel olarak kaydedilen haberler.',
      emptySaved:'Henüz kaydedilmiş haber yok', emptySavedText:'Bir haberdeki yıldıza dokun.', openArticle:'Haberi aç',
      readOriginal:'Orijinali oku', loadError:'Haberler yüklenemedi.', retry:'Tekrar dene',
      menuSearch:'Aramayı aç', close:'Kapat', selectionSaved:'Seçimin yerel olarak kaydedildi.',
      articleSaved:'Haber kaydedildi.', articleRemoved:'Haber kaldırıldı.', translatedTitle:'Çevrilmiş başlık ve giriş',
      previewNotice:'Paralel önizleme — yayımlanmış uygulama değişmez.'
    }
  };

  const SPECIAL_COPY = {
    de: {
      backDiscover:'Zurück zu Entdecken', underConstruction:'Im Aufbau', beta:'Beta',
      eventUpcoming:'Kommende Termine', eventArchive:'Archiv', eventSearch:'Termine durchsuchen',
      eventCountry:'Land', eventAllCountries:'Alle Länder', eventRepeat:'zusammengefasste Termine',
      when:'Wann', where:'Wo', internationalUnknown:'International / unklar', noEvents:'Keine passenden Termine gefunden.',
      glossaryIntro:'Kurze Einordnungen zu Begriffen aus anarchistischen, antiautoritären und linksrevolutionären Bewegungen.',
      glossaryNote:'Ohne Anspruch auf Vollständigkeit: Begriffe bewegen sich, werden umkämpft und gemeinsam weiterentwickelt.',
      glossarySearch:'Begriffe durchsuchen', glossarySources:'Quellen', meaning:'Kurz erklärt', practice:'In der Praxis',
      debate:'Unterschiedliche Perspektiven', related:'Verwandte Begriffe', downloadJson:'Lexikon als JSON sichern',
      sourceOpen:'Quelle öffnen', fallbackLanguage:'Dieser Eintrag ist noch nicht vollständig übersetzt; die englische Fassung wird angezeigt.',
      prisonerIntro:'Verifizierte öffentliche Adressen und eine private Briefwerkstatt für solidarische Post.',
      prisonerLimited:'Bewusst kleine, unvollständige und redaktionell geprüfte Liste – keine juristische Bewertung.',
      verified:'Geprüft', reviewBy:'Erneut prüfen bis', address:'Postadresse', writeLetter:'Brief schreiben',
      relatedNews:'Zugehörige Nachrichten', noRelated:'Noch kein passender Artikel im lokalen Archiv.',
      mailRules:'Versandregeln', localOnly:'Entwürfe und persönliche Angaben bleiben auf diesem Gerät.',
      developmentIntro:'Mehrere Berichte über dasselbe Geschehen – streng und lokal gruppiert.',
      developmentGuard:'Nur verschiedene Quellen mit hoher inhaltlicher Übereinstimmung werden verbunden.',
      whyLinked:'Verbunden durch', confidence:'Übereinstimmung', storySources:'Quellen', storyArticles:'Berichte',
      storyTimeline:'Zeitverlauf', noDevelopments:'Aktuell gibt es keine ausreichend sichere Mehrquellen-Entwicklung.',
      watch:'Beobachten', watching:'Beobachtet', showWatched:'Nur beobachtete', showAll:'Alle Entwicklungen'
    },
    en: {
      backDiscover:'Back to Discover', underConstruction:'Under construction', beta:'Beta',
      eventUpcoming:'Upcoming events', eventArchive:'Archive', eventSearch:'Search events', eventCountry:'Country',
      eventAllCountries:'All countries', eventRepeat:'grouped dates', when:'When', where:'Where', internationalUnknown:'International / unclear', noEvents:'No matching events found.',
      glossaryIntro:'Short contextual explanations of terms used in anarchist, anti-authoritarian and revolutionary left movements.',
      glossaryNote:'No claim to completeness: words move, are contested and develop through collective use.',
      glossarySearch:'Search terms', glossarySources:'Sources', meaning:'In brief', practice:'In practice',
      debate:'Different perspectives', related:'Related terms', downloadJson:'Save glossary as JSON',
      sourceOpen:'Open source', fallbackLanguage:'This entry is not fully translated yet; the English version is shown.',
      prisonerIntro:'Verified public addresses and a private workshop for solidarity letters.',
      prisonerLimited:'A deliberately small, incomplete and editorially reviewed list — not a legal assessment.',
      verified:'Verified', reviewBy:'Review again by', address:'Mailing address', writeLetter:'Write a letter',
      relatedNews:'Related news', noRelated:'No matching article in the local archive yet.', mailRules:'Mail rules',
      localOnly:'Drafts and personal details remain on this device.',
      developmentIntro:'Several reports about the same event, grouped strictly and locally.',
      developmentGuard:'Only different sources with strong content overlap are linked.', whyLinked:'Linked by',
      confidence:'Match', storySources:'Sources', storyArticles:'Reports', storyTimeline:'Timeline',
      noDevelopments:'There is currently no sufficiently reliable multi-source development.',
      watch:'Watch', watching:'Watching', showWatched:'Watched only', showAll:'All developments'
    },
    es: {
      backDiscover:'Volver a Explorar', underConstruction:'En desarrollo', beta:'Beta', eventUpcoming:'Próximos eventos', eventArchive:'Archivo',
      eventSearch:'Buscar eventos', eventCountry:'País', eventAllCountries:'Todos los países', eventRepeat:'fechas agrupadas', when:'Cuándo', where:'Dónde', noEvents:'No se encontraron eventos.',
      glossaryIntro:'Explicaciones breves de términos de movimientos anarquistas, antiautoritarios y revolucionarios.', glossaryNote:'Sin pretensión de totalidad: las palabras cambian y se debaten.', glossarySearch:'Buscar términos', glossarySources:'Fuentes', meaning:'En breve', practice:'En la práctica', debate:'Perspectivas diferentes', related:'Términos relacionados', downloadJson:'Guardar glosario como JSON', sourceOpen:'Abrir fuente',
      prisonerIntro:'Direcciones públicas verificadas y taller privado de cartas solidarias.', prisonerLimited:'Lista pequeña e incompleta; no es una valoración jurídica.', verified:'Verificado', reviewBy:'Revisar antes de', address:'Dirección postal', writeLetter:'Escribir una carta', relatedNews:'Noticias relacionadas', noRelated:'Aún no hay noticias relacionadas.', mailRules:'Normas de envío', localOnly:'Los borradores permanecen en este dispositivo.',
      developmentIntro:'Varios informes del mismo hecho, agrupados localmente con criterios estrictos.', developmentGuard:'Solo se conectan fuentes diferentes con gran coincidencia.', whyLinked:'Vinculado por', confidence:'Coincidencia', storySources:'Fuentes', storyArticles:'Informes', storyTimeline:'Cronología', noDevelopments:'No hay desarrollos suficientemente seguros.', watch:'Seguir', watching:'Siguiendo', showWatched:'Solo seguidos', showAll:'Todos'
    },
    fr: {
      backDiscover:'Retour à Découvrir', underConstruction:'En construction', beta:'Bêta', eventUpcoming:'Événements à venir', eventArchive:'Archives', eventSearch:'Rechercher des événements', eventCountry:'Pays', eventAllCountries:'Tous les pays', eventRepeat:'dates regroupées', when:'Quand', where:'Où', noEvents:'Aucun événement trouvé.',
      glossaryIntro:'Explications brèves de termes des mouvements anarchistes, anti-autoritaires et révolutionnaires.', glossaryNote:'Sans prétention d’exhaustivité : les mots évoluent et sont débattus.', glossarySearch:'Rechercher des termes', glossarySources:'Sources', meaning:'En bref', practice:'En pratique', debate:'Perspectives différentes', related:'Termes liés', downloadJson:'Enregistrer en JSON', sourceOpen:'Ouvrir la source',
      prisonerIntro:'Adresses publiques vérifiées et atelier privé de lettres solidaires.', prisonerLimited:'Liste volontairement petite et incomplète ; pas une évaluation juridique.', verified:'Vérifié', reviewBy:'Réviser avant le', address:'Adresse postale', writeLetter:'Écrire une lettre', relatedNews:'Actualités liées', noRelated:'Aucun article lié pour le moment.', mailRules:'Règles postales', localOnly:'Les brouillons restent sur cet appareil.',
      developmentIntro:'Plusieurs rapports sur un même événement, regroupés localement avec prudence.', developmentGuard:'Seules des sources différentes fortement concordantes sont reliées.', whyLinked:'Relié par', confidence:'Correspondance', storySources:'Sources', storyArticles:'Rapports', storyTimeline:'Chronologie', noDevelopments:'Aucune évolution multisource assez fiable.', watch:'Suivre', watching:'Suivi', showWatched:'Suivis seulement', showAll:'Toutes'
    },
    it: {
      backDiscover:'Torna a Scopri', underConstruction:'In costruzione', beta:'Beta', eventUpcoming:'Prossimi eventi', eventArchive:'Archivio', eventSearch:'Cerca eventi', eventCountry:'Paese', eventAllCountries:'Tutti i paesi', eventRepeat:'date raggruppate', when:'Quando', where:'Dove', noEvents:'Nessun evento trovato.',
      glossaryIntro:'Brevi spiegazioni di termini dei movimenti anarchici, antiautoritari e rivoluzionari.', glossaryNote:'Senza pretesa di completezza: le parole cambiano e sono controverse.', glossarySearch:'Cerca termini', glossarySources:'Fonti', meaning:'In breve', practice:'Nella pratica', debate:'Prospettive diverse', related:'Termini collegati', downloadJson:'Salva come JSON', sourceOpen:'Apri fonte',
      prisonerIntro:'Indirizzi pubblici verificati e laboratorio privato per lettere solidali.', prisonerLimited:'Elenco volutamente piccolo e incompleto; non è una valutazione legale.', verified:'Verificato', reviewBy:'Ricontrollare entro', address:'Indirizzo postale', writeLetter:'Scrivi una lettera', relatedNews:'Notizie correlate', noRelated:'Nessuna notizia correlata.', mailRules:'Regole postali', localOnly:'Le bozze restano su questo dispositivo.',
      developmentIntro:'Più resoconti dello stesso evento, raggruppati localmente con criteri rigorosi.', developmentGuard:'Si collegano solo fonti diverse con forte concordanza.', whyLinked:'Collegato da', confidence:'Corrispondenza', storySources:'Fonti', storyArticles:'Resoconti', storyTimeline:'Cronologia', noDevelopments:'Nessuno sviluppo multisorgente abbastanza affidabile.', watch:'Segui', watching:'Seguito', showWatched:'Solo seguiti', showAll:'Tutti'
    },
    pt: {
      backDiscover:'Voltar a Explorar', underConstruction:'Em construção', beta:'Beta', eventUpcoming:'Próximos eventos', eventArchive:'Arquivo', eventSearch:'Pesquisar eventos', eventCountry:'País', eventAllCountries:'Todos os países', eventRepeat:'datas agrupadas', when:'Quando', where:'Onde', noEvents:'Nenhum evento encontrado.',
      glossaryIntro:'Explicações breves de termos de movimentos anarquistas, antiautoritários e revolucionários.', glossaryNote:'Sem pretensão de totalidade: as palavras mudam e são disputadas.', glossarySearch:'Pesquisar termos', glossarySources:'Fontes', meaning:'Em resumo', practice:'Na prática', debate:'Perspetivas diferentes', related:'Termos relacionados', downloadJson:'Guardar como JSON', sourceOpen:'Abrir fonte',
      prisonerIntro:'Endereços públicos verificados e oficina privada de cartas solidárias.', prisonerLimited:'Lista deliberadamente pequena e incompleta; não é avaliação jurídica.', verified:'Verificado', reviewBy:'Rever até', address:'Endereço postal', writeLetter:'Escrever carta', relatedNews:'Notícias relacionadas', noRelated:'Ainda não há notícia relacionada.', mailRules:'Regras postais', localOnly:'Os rascunhos ficam neste dispositivo.',
      developmentIntro:'Vários relatos do mesmo acontecimento, agrupados localmente com rigor.', developmentGuard:'Só fontes diferentes com forte concordância são ligadas.', whyLinked:'Ligado por', confidence:'Correspondência', storySources:'Fontes', storyArticles:'Relatos', storyTimeline:'Cronologia', noDevelopments:'Nenhum desenvolvimento multisource suficientemente fiável.', watch:'Observar', watching:'Observado', showWatched:'Só observados', showAll:'Todos'
    },
    ru: {
      backDiscover:'Назад к обзору', underConstruction:'В разработке', beta:'Бета', eventUpcoming:'Предстоящие события', eventArchive:'Архив', eventSearch:'Поиск событий', eventCountry:'Страна', eventAllCountries:'Все страны', eventRepeat:'объединённых дат', when:'Когда', where:'Где', noEvents:'События не найдены.',
      glossaryIntro:'Краткие объяснения терминов анархистских, антиавторитарных и революционных движений.', glossaryNote:'Без претензии на полноту: слова меняются и оспариваются.', glossarySearch:'Поиск терминов', glossarySources:'Источники', meaning:'Кратко', practice:'На практике', debate:'Разные взгляды', related:'Связанные термины', downloadJson:'Сохранить JSON', sourceOpen:'Открыть источник',
      prisonerIntro:'Проверенные публичные адреса и приватная мастерская писем солидарности.', prisonerLimited:'Намеренно небольшой и неполный список; не юридическая оценка.', verified:'Проверено', reviewBy:'Проверить до', address:'Почтовый адрес', writeLetter:'Написать письмо', relatedNews:'Связанные новости', noRelated:'Связанных материалов пока нет.', mailRules:'Почтовые правила', localOnly:'Черновики остаются на устройстве.',
      developmentIntro:'Несколько сообщений об одном событии, строго сгруппированных локально.', developmentGuard:'Связываются только разные источники с сильным совпадением.', whyLinked:'Связано по', confidence:'Совпадение', storySources:'Источники', storyArticles:'Материалы', storyTimeline:'Хронология', noDevelopments:'Нет достаточно надёжного развития из нескольких источников.', watch:'Отслеживать', watching:'Отслеживается', showWatched:'Только отслеживаемые', showAll:'Все'
    },
    el: {
      backDiscover:'Πίσω στην Ανακάλυψη', underConstruction:'Υπό ανάπτυξη', beta:'Beta', eventUpcoming:'Επερχόμενες εκδηλώσεις', eventArchive:'Αρχείο', eventSearch:'Αναζήτηση εκδηλώσεων', eventCountry:'Χώρα', eventAllCountries:'Όλες οι χώρες', eventRepeat:'ομαδοποιημένες ημερομηνίες', when:'Πότε', where:'Πού', noEvents:'Δεν βρέθηκαν εκδηλώσεις.',
      glossaryIntro:'Σύντομες εξηγήσεις όρων αναρχικών, αντιεξουσιαστικών και επαναστατικών κινημάτων.', glossaryNote:'Χωρίς αξίωση πληρότητας: οι λέξεις αλλάζουν και αμφισβητούνται.', glossarySearch:'Αναζήτηση όρων', glossarySources:'Πηγές', meaning:'Συνοπτικά', practice:'Στην πράξη', debate:'Διαφορετικές οπτικές', related:'Σχετικοί όροι', downloadJson:'Αποθήκευση JSON', sourceOpen:'Άνοιγμα πηγής',
      prisonerIntro:'Επαληθευμένες δημόσιες διευθύνσεις και ιδιωτικό εργαστήριο επιστολών.', prisonerLimited:'Σκόπιμα μικρός και ελλιπής κατάλογος· όχι νομική αξιολόγηση.', verified:'Επαληθεύτηκε', reviewBy:'Επανέλεγχος έως', address:'Ταχυδρομική διεύθυνση', writeLetter:'Γράψτε επιστολή', relatedNews:'Σχετικές ειδήσεις', noRelated:'Δεν υπάρχει σχετικό άρθρο ακόμη.', mailRules:'Κανόνες αλληλογραφίας', localOnly:'Τα προσχέδια μένουν στη συσκευή.',
      developmentIntro:'Πολλαπλές αναφορές για το ίδιο γεγονός, αυστηρά ομαδοποιημένες τοπικά.', developmentGuard:'Συνδέονται μόνο διαφορετικές πηγές με ισχυρή συμφωνία.', whyLinked:'Σύνδεση μέσω', confidence:'Αντιστοίχιση', storySources:'Πηγές', storyArticles:'Αναφορές', storyTimeline:'Χρονολόγιο', noDevelopments:'Δεν υπάρχει αρκετά αξιόπιστη εξέλιξη πολλών πηγών.', watch:'Παρακολούθηση', watching:'Παρακολουθείται', showWatched:'Μόνο παρακολουθούμενα', showAll:'Όλα'
    },
    tr: {
      backDiscover:'Keşfet’e dön', underConstruction:'Yapım aşamasında', beta:'Beta', eventUpcoming:'Yaklaşan etkinlikler', eventArchive:'Arşiv', eventSearch:'Etkinlik ara', eventCountry:'Ülke', eventAllCountries:'Tüm ülkeler', eventRepeat:'birleştirilmiş tarihler', when:'Ne zaman', where:'Nerede', noEvents:'Etkinlik bulunamadı.',
      glossaryIntro:'Anarşist, otorite karşıtı ve devrimci hareket kavramlarının kısa açıklamaları.', glossaryNote:'Eksiksizlik iddiası yoktur: sözcükler değişir ve tartışılır.', glossarySearch:'Kavram ara', glossarySources:'Kaynaklar', meaning:'Kısaca', practice:'Pratikte', debate:'Farklı bakışlar', related:'İlgili kavramlar', downloadJson:'JSON kaydet', sourceOpen:'Kaynağı aç',
      prisonerIntro:'Doğrulanmış kamusal adresler ve özel dayanışma mektubu atölyesi.', prisonerLimited:'Bilinçli olarak küçük ve eksik liste; hukuki değerlendirme değildir.', verified:'Doğrulandı', reviewBy:'Yeniden kontrol', address:'Posta adresi', writeLetter:'Mektup yaz', relatedNews:'İlgili haberler', noRelated:'Henüz ilgili haber yok.', mailRules:'Posta kuralları', localOnly:'Taslaklar bu cihazda kalır.',
      developmentIntro:'Aynı olay hakkındaki birden fazla haber, yerel olarak sıkı biçimde gruplanır.', developmentGuard:'Yalnızca güçlü içerik örtüşmesi olan farklı kaynaklar bağlanır.', whyLinked:'Bağlantı nedeni', confidence:'Eşleşme', storySources:'Kaynaklar', storyArticles:'Haberler', storyTimeline:'Zaman çizelgesi', noDevelopments:'Yeterince güvenilir çok kaynaklı gelişme yok.', watch:'İzle', watching:'İzleniyor', showWatched:'Yalnız izlenenler', showAll:'Tümü'
    }
  };

  const MEDIA_COPY = {
    de: {
      current:'Aktuell', information:'Information', politics:'Politik', society:'Gesellschaft', culture:'Kultur',
      allCategories:'Alle Kategorien', allRegions:'Alle Regionen', mediaSearch:'Medien durchsuchen',
      privacyMedia:'Datenschutz: Nichts startet automatisch. Externe Medien werden erst nach deiner Auswahl geladen.',
      playEpisode:'Folge abspielen', openEpisode:'Original öffnen', openChannel:'Kanal öffnen',
      noMedia:'Keine passenden Medien gefunden.', noGenerated:'Noch keine erzeugten Podcasts gespeichert.',
      generatedNotice:'Erzeugte Podcasts bleiben höchstens 30 Tage gespeichert.', station:'Sender', listenLive:'Live hören',
      streamFallback:'Kein geprüfter Browser-Stream. Öffne die Senderseite.', episodes:'Folgen', stations:'Sender'
    },
    en: {
      current:'Current', information:'Information', politics:'Politics', society:'Society', culture:'Culture',
      allCategories:'All categories', allRegions:'All regions', mediaSearch:'Search media',
      privacyMedia:'Privacy: nothing starts automatically. External media load only after you choose them.',
      playEpisode:'Play episode', openEpisode:'Open original', openChannel:'Open channel',
      noMedia:'No matching media found.', noGenerated:'No generated podcasts are stored yet.',
      generatedNotice:'Generated podcasts are stored for no longer than 30 days.', station:'Station', listenLive:'Listen live',
      streamFallback:'No verified browser stream. Open the station website.', episodes:'Episodes', stations:'Stations'
    },
    es: {
      current:'Actualidad', information:'Información', politics:'Política', society:'Sociedad', culture:'Cultura',
      allCategories:'Todas las categorías', allRegions:'Todas las regiones', mediaSearch:'Buscar medios',
      privacyMedia:'Privacidad: nada se inicia automáticamente. Los medios externos se cargan solo tras elegirlos.',
      playEpisode:'Reproducir episodio', openEpisode:'Abrir original', openChannel:'Abrir canal',
      noMedia:'No se encontraron medios.', noGenerated:'Aún no hay pódcasts generados guardados.',
      generatedNotice:'Los pódcasts generados se guardan como máximo 30 días.', station:'Emisora', listenLive:'Escuchar en directo',
      streamFallback:'No hay un flujo web verificado. Abre la web de la emisora.', episodes:'Episodios', stations:'Emisoras'
    },
    fr: {
      current:'Actualité', information:'Information', politics:'Politique', society:'Société', culture:'Culture',
      allCategories:'Toutes les catégories', allRegions:'Toutes les régions', mediaSearch:'Rechercher des médias',
      privacyMedia:'Confidentialité : rien ne démarre automatiquement. Les médias externes ne chargent qu’après votre choix.',
      playEpisode:'Lire l’épisode', openEpisode:'Ouvrir l’original', openChannel:'Ouvrir la chaîne',
      noMedia:'Aucun média correspondant.', noGenerated:'Aucun podcast généré n’est encore enregistré.',
      generatedNotice:'Les podcasts générés sont conservés au maximum 30 jours.', station:'Station', listenLive:'Écouter en direct',
      streamFallback:'Aucun flux web vérifié. Ouvrez le site de la station.', episodes:'Épisodes', stations:'Stations'
    },
    it: {
      current:'Attualità', information:'Informazione', politics:'Politica', society:'Società', culture:'Cultura',
      allCategories:'Tutte le categorie', allRegions:'Tutte le regioni', mediaSearch:'Cerca media',
      privacyMedia:'Privacy: nulla parte automaticamente. I media esterni si caricano solo dopo la scelta.',
      playEpisode:'Riproduci episodio', openEpisode:'Apri originale', openChannel:'Apri canale',
      noMedia:'Nessun media corrispondente.', noGenerated:'Nessun podcast generato è ancora salvato.',
      generatedNotice:'I podcast generati restano salvati al massimo 30 giorni.', station:'Emittente', listenLive:'Ascolta dal vivo',
      streamFallback:'Nessuno stream web verificato. Apri il sito dell’emittente.', episodes:'Episodi', stations:'Emittenti'
    },
    pt: {
      current:'Atualidade', information:'Informação', politics:'Política', society:'Sociedade', culture:'Cultura',
      allCategories:'Todas as categorias', allRegions:'Todas as regiões', mediaSearch:'Pesquisar media',
      privacyMedia:'Privacidade: nada começa automaticamente. Os media externos só carregam após a escolha.',
      playEpisode:'Reproduzir episódio', openEpisode:'Abrir original', openChannel:'Abrir canal',
      noMedia:'Nenhum media correspondente.', noGenerated:'Ainda não há podcasts gerados guardados.',
      generatedNotice:'Os podcasts gerados ficam guardados no máximo 30 dias.', station:'Estação', listenLive:'Ouvir em direto',
      streamFallback:'Sem transmissão web verificada. Abre o site da estação.', episodes:'Episódios', stations:'Estações'
    },
    ru: {
      current:'Актуальное', information:'Справочные', politics:'Политика', society:'Общество', culture:'Культура',
      allCategories:'Все категории', allRegions:'Все регионы', mediaSearch:'Поиск медиа',
      privacyMedia:'Конфиденциальность: ничего не запускается автоматически. Внешние медиа загружаются только после выбора.',
      playEpisode:'Воспроизвести', openEpisode:'Открыть оригинал', openChannel:'Открыть канал',
      noMedia:'Подходящих медиа нет.', noGenerated:'Созданные подкасты пока не сохранены.',
      generatedNotice:'Созданные подкасты хранятся не более 30 дней.', station:'Станция', listenLive:'Слушать эфир',
      streamFallback:'Нет проверенного веб-потока. Откройте сайт станции.', episodes:'Выпуски', stations:'Станции'
    },
    el: {
      current:'Τρέχοντα', information:'Πληροφορίες', politics:'Πολιτική', society:'Κοινωνία', culture:'Πολιτισμός',
      allCategories:'Όλες οι κατηγορίες', allRegions:'Όλες οι περιοχές', mediaSearch:'Αναζήτηση πολυμέσων',
      privacyMedia:'Απόρρητο: τίποτα δεν ξεκινά αυτόματα. Τα εξωτερικά μέσα φορτώνουν μόνο μετά την επιλογή.',
      playEpisode:'Αναπαραγωγή', openEpisode:'Άνοιγμα πρωτοτύπου', openChannel:'Άνοιγμα καναλιού',
      noMedia:'Δεν βρέθηκαν πολυμέσα.', noGenerated:'Δεν υπάρχουν ακόμη αποθηκευμένα podcast.',
      generatedNotice:'Τα δημιουργημένα podcast διατηρούνται έως 30 ημέρες.', station:'Σταθμός', listenLive:'Ζωντανή ακρόαση',
      streamFallback:'Δεν υπάρχει επαληθευμένη ροή. Ανοίξτε τη σελίδα του σταθμού.', episodes:'Επεισόδια', stations:'Σταθμοί'
    },
    tr: {
      current:'Güncel', information:'Bilgi', politics:'Siyaset', society:'Toplum', culture:'Kültür',
      allCategories:'Tüm kategoriler', allRegions:'Tüm bölgeler', mediaSearch:'Medya ara',
      privacyMedia:'Gizlilik: hiçbir şey otomatik başlamaz. Harici medya yalnızca seçiminizden sonra yüklenir.',
      playEpisode:'Bölümü oynat', openEpisode:'Orijinali aç', openChannel:'Kanalı aç',
      noMedia:'Uygun medya bulunamadı.', noGenerated:'Henüz oluşturulmuş podcast kaydedilmedi.',
      generatedNotice:'Oluşturulan podcastler en fazla 30 gün saklanır.', station:'İstasyon', listenLive:'Canlı dinle',
      streamFallback:'Doğrulanmış web yayını yok. İstasyon sitesini açın.', episodes:'Bölümler', stations:'İstasyonlar'
    }
  };

  const UI_COPY = {
    de: {
      menu:'Menü', menuOpen:'Menü öffnen', aboutProject:'Über das Projekt', privacy:'Datenschutz', diagnostics:'Diagnose',
      sourceCheck:'Quellenprüfung', selfTest:'App-Selbsttest', feedback:'Feedback & neue Quellen', briefingCreate:'Briefing erstellen',
      display:'Darstellung', project:'Projekt', theme:'Farbdarstellung', themeDark:'Dunkel', themeLight:'Hell',
      themeSystem:'Systemeinstellung', themeContrast:'Hoher Kontrast', fontSize:'Schriftgröße', normal:'Normal',
      large:'Groß', xlarge:'Sehr groß', density:'Artikeldarstellung', compact:'Kompakt', standard:'Standard',
      spacious:'Großzügig', settingsLocal:'Diese Einstellungen bleiben auf diesem Gerät.',
      briefingSetup:'Wähle in drei kurzen Schritten, was du hören oder lesen möchtest.', step:'Schritt', of:'von',
      next:'Weiter', back:'Zurück', listen:'Anhören', stop:'Stoppen', done:'Fertig', briefingLocal:'Wird nur auf diesem Gerät zusammengestellt.',
      briefingAmount:'Länge', briefingItems:'Meldungen', noBriefing:'Keine passenden Meldungen gefunden.',
      speechUnavailable:'Vorlesen ist in diesem Browser nicht verfügbar.',
      chooseSources:'Quellen priorisieren oder ausblenden', sourcePreferenceSearch:'Quellen durchsuchen',
      sourceNeutral:'Standard', sourceFollow:'Folgen', sourceHide:'Ausblenden',
      followPrisoners:'Politische Gefangene beobachten', followDevelopments:'Entwicklungen beobachten',
      feedLanguage:'App-Sprache', preferredBriefingLength:'Standardlänge des Briefings',
      shownBecause:'Angezeigt wegen', followedPrisoners:'Beobachtete Gefangene',
      followedDevelopments:'Beobachtete Entwicklungen', noWatchOptions:'Aktuell steht keine Auswahl zur Verfügung.',
      zine:'Zine', zineIntro:'Stelle Artikel zu einer eigenen Ausgabe zusammen und gestalte sie anschließend für Druck oder PDF.',
      zineAdd:'Zum Zine', zineAdded:'Artikel zum Zine hinzugefügt.', zineRemove:'Aus Zine entfernen',
      zineRemoved:'Artikel aus dem Zine entfernt.', zineEmpty:'Das Zine ist noch leer.',
      zineClear:'Zine leeren', zineClearConfirm:'Alle Artikel aus dem Zine entfernen?'
    },
    en: {
      menu:'Menu', menuOpen:'Open menu', aboutProject:'About the project', privacy:'Privacy', diagnostics:'Diagnostics',
      sourceCheck:'Source check', selfTest:'App self-test', feedback:'Feedback & new sources', briefingCreate:'Create briefing',
      display:'Appearance', project:'Project', theme:'Colour theme', themeDark:'Dark', themeLight:'Light',
      themeSystem:'System setting', themeContrast:'High contrast', fontSize:'Text size', normal:'Normal',
      large:'Large', xlarge:'Very large', density:'Article layout', compact:'Compact', standard:'Standard',
      spacious:'Spacious', settingsLocal:'These settings remain on this device.',
      briefingSetup:'Choose what you want to hear or read in three short steps.', step:'Step', of:'of',
      next:'Next', back:'Back', listen:'Listen', stop:'Stop', done:'Done', briefingLocal:'Assembled only on this device.',
      briefingAmount:'Length', briefingItems:'stories', noBriefing:'No matching stories found.',
      speechUnavailable:'Read-aloud is not available in this browser.',
      chooseSources:'Prioritize or hide sources', sourcePreferenceSearch:'Search sources',
      sourceNeutral:'Default', sourceFollow:'Follow', sourceHide:'Hide',
      followPrisoners:'Watch political prisoners', followDevelopments:'Watch developments',
      feedLanguage:'App language', preferredBriefingLength:'Default briefing length',
      shownBecause:'Shown because of', followedPrisoners:'Watched prisoners',
      followedDevelopments:'Watched developments', noWatchOptions:'No options are currently available.',
      zine:'Zine', zineIntro:'Collect articles into your own issue, then design it for print or PDF.',
      zineAdd:'Add to Zine', zineAdded:'Article added to the Zine.', zineRemove:'Remove from Zine',
      zineRemoved:'Article removed from the Zine.', zineEmpty:'The Zine is empty.',
      zineClear:'Clear Zine', zineClearConfirm:'Remove every article from the Zine?'
    },
    es: {
      menu:'Menú', menuOpen:'Abrir menú', aboutProject:'Sobre el proyecto', privacy:'Privacidad', diagnostics:'Diagnóstico',
      sourceCheck:'Comprobar fuentes', selfTest:'Autoprueba', feedback:'Comentarios y nuevas fuentes', briefingCreate:'Crear resumen',
      display:'Apariencia', project:'Proyecto', theme:'Tema de color', themeDark:'Oscuro', themeLight:'Claro',
      themeSystem:'Sistema', themeContrast:'Alto contraste', fontSize:'Tamaño del texto', normal:'Normal',
      large:'Grande', xlarge:'Muy grande', density:'Vista de artículos', compact:'Compacta', standard:'Estándar',
      spacious:'Amplia', settingsLocal:'Estos ajustes permanecen en este dispositivo.',
      briefingSetup:'Elige en tres pasos lo que quieres escuchar o leer.', step:'Paso', of:'de', next:'Siguiente', back:'Atrás',
      listen:'Escuchar', stop:'Detener', done:'Listo', briefingLocal:'Se crea solo en este dispositivo.',
      briefingAmount:'Duración', briefingItems:'noticias', noBriefing:'No se encontraron noticias.', speechUnavailable:'La lectura no está disponible.',
      chooseSources:'Priorizar u ocultar fuentes', sourcePreferenceSearch:'Buscar fuentes', sourceNeutral:'Predeterminado',
      sourceFollow:'Seguir', sourceHide:'Ocultar', followPrisoners:'Seguir a presxs políticxs',
      followDevelopments:'Seguir desarrollos', feedLanguage:'Idioma de la aplicación',
      preferredBriefingLength:'Duración predeterminada del resumen', shownBecause:'Se muestra por',
      followedPrisoners:'Presxs seguidxs', followedDevelopments:'Desarrollos seguidos', noWatchOptions:'No hay opciones disponibles.',
      zine:'Zine', zineIntro:'Reúne artículos en una edición y diseña el resultado para imprimir o guardar en PDF.',
      zineAdd:'Añadir al Zine', zineAdded:'Artículo añadido al Zine.', zineRemove:'Quitar del Zine',
      zineRemoved:'Artículo eliminado del Zine.', zineEmpty:'El Zine está vacío.',
      zineClear:'Vaciar Zine', zineClearConfirm:'¿Quitar todos los artículos del Zine?'
    },
    fr: {
      menu:'Menu', menuOpen:'Ouvrir le menu', aboutProject:'À propos du projet', privacy:'Confidentialité', diagnostics:'Diagnostic',
      sourceCheck:'Vérifier les sources', selfTest:'Autotest', feedback:'Commentaires et nouvelles sources', briefingCreate:'Créer un briefing',
      display:'Affichage', project:'Projet', theme:'Thème de couleur', themeDark:'Sombre', themeLight:'Clair',
      themeSystem:'Système', themeContrast:'Contraste élevé', fontSize:'Taille du texte', normal:'Normale',
      large:'Grande', xlarge:'Très grande', density:'Affichage des articles', compact:'Compact', standard:'Standard',
      spacious:'Aéré', settingsLocal:'Ces réglages restent sur cet appareil.',
      briefingSetup:'Choisissez en trois étapes ce que vous souhaitez écouter ou lire.', step:'Étape', of:'sur', next:'Suivant', back:'Retour',
      listen:'Écouter', stop:'Arrêter', done:'Terminé', briefingLocal:'Assemblé uniquement sur cet appareil.',
      briefingAmount:'Durée', briefingItems:'informations', noBriefing:'Aucune information correspondante.', speechUnavailable:'La lecture vocale est indisponible.',
      chooseSources:'Prioriser ou masquer des sources', sourcePreferenceSearch:'Rechercher des sources', sourceNeutral:'Par défaut',
      sourceFollow:'Suivre', sourceHide:'Masquer', followPrisoners:'Suivre des prisonnier·ères politiques',
      followDevelopments:'Suivre des évolutions', feedLanguage:'Langue de l’application',
      preferredBriefingLength:'Durée par défaut du briefing', shownBecause:'Affiché en raison de',
      followedPrisoners:'Prisonnier·ères suivi·es', followedDevelopments:'Évolutions suivies', noWatchOptions:'Aucune option disponible.',
      zine:'Zine', zineIntro:'Rassemblez des articles dans un numéro, puis préparez-le pour l’impression ou le PDF.',
      zineAdd:'Ajouter au Zine', zineAdded:'Article ajouté au Zine.', zineRemove:'Retirer du Zine',
      zineRemoved:'Article retiré du Zine.', zineEmpty:'Le Zine est vide.',
      zineClear:'Vider le Zine', zineClearConfirm:'Retirer tous les articles du Zine ?'
    },
    it: {
      menu:'Menu', menuOpen:'Apri menu', aboutProject:'Il progetto', privacy:'Privacy', diagnostics:'Diagnostica',
      sourceCheck:'Controllo fonti', selfTest:'Autotest', feedback:'Feedback e nuove fonti', briefingCreate:'Crea briefing',
      display:'Aspetto', project:'Progetto', theme:'Tema colore', themeDark:'Scuro', themeLight:'Chiaro',
      themeSystem:'Sistema', themeContrast:'Contrasto elevato', fontSize:'Dimensione testo', normal:'Normale',
      large:'Grande', xlarge:'Molto grande', density:'Vista articoli', compact:'Compatta', standard:'Standard',
      spacious:'Spaziosa', settingsLocal:'Queste impostazioni restano su questo dispositivo.',
      briefingSetup:'Scegli in tre passaggi cosa ascoltare o leggere.', step:'Passaggio', of:'di', next:'Avanti', back:'Indietro',
      listen:'Ascolta', stop:'Ferma', done:'Fatto', briefingLocal:'Creato solo su questo dispositivo.',
      briefingAmount:'Durata', briefingItems:'notizie', noBriefing:'Nessuna notizia corrispondente.', speechUnavailable:'La lettura vocale non è disponibile.',
      chooseSources:'Dai priorità o nascondi fonti', sourcePreferenceSearch:'Cerca fonti', sourceNeutral:'Predefinito',
      sourceFollow:'Segui', sourceHide:'Nascondi', followPrisoners:'Segui prigionierə politicə',
      followDevelopments:'Segui sviluppi', feedLanguage:'Lingua dell’app',
      preferredBriefingLength:'Durata predefinita del briefing', shownBecause:'Mostrato per',
      followedPrisoners:'Prigionierə seguitə', followedDevelopments:'Sviluppi seguiti', noWatchOptions:'Nessuna opzione disponibile.',
      zine:'Zine', zineIntro:'Raccogli articoli in un numero e preparalo per la stampa o il PDF.',
      zineAdd:'Aggiungi allo Zine', zineAdded:'Articolo aggiunto allo Zine.', zineRemove:'Rimuovi dallo Zine',
      zineRemoved:'Articolo rimosso dallo Zine.', zineEmpty:'Lo Zine è vuoto.',
      zineClear:'Svuota Zine', zineClearConfirm:'Rimuovere tutti gli articoli dallo Zine?'
    },
    pt: {
      menu:'Menu', menuOpen:'Abrir menu', aboutProject:'Sobre o projeto', privacy:'Privacidade', diagnostics:'Diagnóstico',
      sourceCheck:'Verificar fontes', selfTest:'Autoteste', feedback:'Comentários e novas fontes', briefingCreate:'Criar briefing',
      display:'Aparência', project:'Projeto', theme:'Tema de cores', themeDark:'Escuro', themeLight:'Claro',
      themeSystem:'Sistema', themeContrast:'Alto contraste', fontSize:'Tamanho do texto', normal:'Normal',
      large:'Grande', xlarge:'Muito grande', density:'Vista de artigos', compact:'Compacta', standard:'Padrão',
      spacious:'Ampla', settingsLocal:'Estas definições ficam neste dispositivo.',
      briefingSetup:'Escolhe em três passos o que queres ouvir ou ler.', step:'Passo', of:'de', next:'Seguinte', back:'Voltar',
      listen:'Ouvir', stop:'Parar', done:'Concluir', briefingLocal:'Criado apenas neste dispositivo.',
      briefingAmount:'Duração', briefingItems:'notícias', noBriefing:'Nenhuma notícia correspondente.', speechUnavailable:'A leitura em voz alta não está disponível.',
      chooseSources:'Priorizar ou ocultar fontes', sourcePreferenceSearch:'Pesquisar fontes', sourceNeutral:'Padrão',
      sourceFollow:'Seguir', sourceHide:'Ocultar', followPrisoners:'Seguir prisioneiros políticos',
      followDevelopments:'Seguir desenvolvimentos', feedLanguage:'Idioma da aplicação',
      preferredBriefingLength:'Duração predefinida do briefing', shownBecause:'Mostrado por',
      followedPrisoners:'Prisioneiros seguidos', followedDevelopments:'Desenvolvimentos seguidos', noWatchOptions:'Não há opções disponíveis.',
      zine:'Zine', zineIntro:'Reúne artigos numa edição e prepara-a para impressão ou PDF.',
      zineAdd:'Adicionar ao Zine', zineAdded:'Artigo adicionado ao Zine.', zineRemove:'Remover do Zine',
      zineRemoved:'Artigo removido do Zine.', zineEmpty:'O Zine está vazio.',
      zineClear:'Esvaziar Zine', zineClearConfirm:'Remover todos os artigos do Zine?'
    },
    ru: {
      menu:'Меню', menuOpen:'Открыть меню', aboutProject:'О проекте', privacy:'Конфиденциальность', diagnostics:'Диагностика',
      sourceCheck:'Проверка источников', selfTest:'Самопроверка', feedback:'Отзывы и новые источники', briefingCreate:'Создать брифинг',
      display:'Оформление', project:'Проект', theme:'Цветовая тема', themeDark:'Тёмная', themeLight:'Светлая',
      themeSystem:'Системная', themeContrast:'Высокий контраст', fontSize:'Размер текста', normal:'Обычный',
      large:'Большой', xlarge:'Очень большой', density:'Вид статей', compact:'Компактный', standard:'Стандартный',
      spacious:'Свободный', settingsLocal:'Эти настройки остаются на устройстве.',
      briefingSetup:'За три шага выберите, что слушать или читать.', step:'Шаг', of:'из', next:'Далее', back:'Назад',
      listen:'Слушать', stop:'Стоп', done:'Готово', briefingLocal:'Составляется только на этом устройстве.',
      briefingAmount:'Длина', briefingItems:'материалов', noBriefing:'Подходящих материалов нет.', speechUnavailable:'Озвучивание недоступно.',
      chooseSources:'Выбрать приоритетные или скрытые источники', sourcePreferenceSearch:'Поиск источников',
      sourceNeutral:'По умолчанию', sourceFollow:'Следить', sourceHide:'Скрыть',
      followPrisoners:'Следить за политзаключёнными', followDevelopments:'Следить за событиями',
      feedLanguage:'Язык приложения', preferredBriefingLength:'Длина обзора по умолчанию',
      shownBecause:'Показано по причине', followedPrisoners:'Отслеживаемые заключённые',
      followedDevelopments:'Отслеживаемые события', noWatchOptions:'Сейчас вариантов нет.',
      zine:'Zine', zineIntro:'Соберите статьи в выпуск и подготовьте его к печати или сохранению в PDF.',
      zineAdd:'Добавить в Zine', zineAdded:'Статья добавлена в Zine.', zineRemove:'Удалить из Zine',
      zineRemoved:'Статья удалена из Zine.', zineEmpty:'Zine пока пуст.',
      zineClear:'Очистить Zine', zineClearConfirm:'Удалить все статьи из Zine?'
    },
    el: {
      menu:'Μενού', menuOpen:'Άνοιγμα μενού', aboutProject:'Σχετικά με το έργο', privacy:'Απόρρητο', diagnostics:'Διαγνωστικά',
      sourceCheck:'Έλεγχος πηγών', selfTest:'Αυτοέλεγχος', feedback:'Σχόλια και νέες πηγές', briefingCreate:'Δημιουργία ενημέρωσης',
      display:'Εμφάνιση', project:'Έργο', theme:'Χρωματικό θέμα', themeDark:'Σκούρο', themeLight:'Ανοιχτό',
      themeSystem:'Σύστημα', themeContrast:'Υψηλή αντίθεση', fontSize:'Μέγεθος κειμένου', normal:'Κανονικό',
      large:'Μεγάλο', xlarge:'Πολύ μεγάλο', density:'Προβολή άρθρων', compact:'Συμπαγής', standard:'Κανονική',
      spacious:'Άνετη', settingsLocal:'Αυτές οι ρυθμίσεις μένουν στη συσκευή.',
      briefingSetup:'Επιλέξτε σε τρία βήματα τι θέλετε να ακούσετε ή να διαβάσετε.', step:'Βήμα', of:'από', next:'Επόμενο', back:'Πίσω',
      listen:'Ακρόαση', stop:'Διακοπή', done:'Τέλος', briefingLocal:'Δημιουργείται μόνο σε αυτή τη συσκευή.',
      briefingAmount:'Διάρκεια', briefingItems:'ειδήσεις', noBriefing:'Δεν βρέθηκαν ειδήσεις.', speechUnavailable:'Η εκφώνηση δεν είναι διαθέσιμη.',
      chooseSources:'Προτεραιότητα ή απόκρυψη πηγών', sourcePreferenceSearch:'Αναζήτηση πηγών',
      sourceNeutral:'Προεπιλογή', sourceFollow:'Παρακολούθηση', sourceHide:'Απόκρυψη',
      followPrisoners:'Παρακολούθηση πολιτικών κρατουμένων', followDevelopments:'Παρακολούθηση εξελίξεων',
      feedLanguage:'Γλώσσα εφαρμογής', preferredBriefingLength:'Προεπιλεγμένη διάρκεια ενημέρωσης',
      shownBecause:'Εμφανίζεται λόγω', followedPrisoners:'Παρακολουθούμενοι κρατούμενοι',
      followedDevelopments:'Παρακολουθούμενες εξελίξεις', noWatchOptions:'Δεν υπάρχουν διαθέσιμες επιλογές.',
      zine:'Zine', zineIntro:'Συγκεντρώστε άρθρα σε ένα τεύχος και σχεδιάστε το για εκτύπωση ή PDF.',
      zineAdd:'Προσθήκη στο Zine', zineAdded:'Το άρθρο προστέθηκε στο Zine.', zineRemove:'Αφαίρεση από το Zine',
      zineRemoved:'Το άρθρο αφαιρέθηκε από το Zine.', zineEmpty:'Το Zine είναι κενό.',
      zineClear:'Εκκαθάριση Zine', zineClearConfirm:'Να αφαιρεθούν όλα τα άρθρα από το Zine;'
    },
    tr: {
      menu:'Menü', menuOpen:'Menüyü aç', aboutProject:'Proje hakkında', privacy:'Gizlilik', diagnostics:'Tanılama',
      sourceCheck:'Kaynak kontrolü', selfTest:'Uygulama testi', feedback:'Geri bildirim ve yeni kaynaklar', briefingCreate:'Bülten oluştur',
      display:'Görünüm', project:'Proje', theme:'Renk teması', themeDark:'Koyu', themeLight:'Açık',
      themeSystem:'Sistem', themeContrast:'Yüksek kontrast', fontSize:'Metin boyutu', normal:'Normal',
      large:'Büyük', xlarge:'Çok büyük', density:'Haber görünümü', compact:'Kompakt', standard:'Standart',
      spacious:'Geniş', settingsLocal:'Bu ayarlar yalnızca bu cihazda kalır.',
      briefingSetup:'Dinlemek veya okumak istediklerini üç adımda seç.', step:'Adım', of:'/', next:'İleri', back:'Geri',
      listen:'Dinle', stop:'Durdur', done:'Bitti', briefingLocal:'Yalnızca bu cihazda hazırlanır.',
      briefingAmount:'Uzunluk', briefingItems:'haber', noBriefing:'Uygun haber bulunamadı.', speechUnavailable:'Sesli okuma kullanılamıyor.',
      chooseSources:'Kaynaklara öncelik ver veya gizle', sourcePreferenceSearch:'Kaynak ara',
      sourceNeutral:'Varsayılan', sourceFollow:'Takip et', sourceHide:'Gizle',
      followPrisoners:'Siyasi mahpusları takip et', followDevelopments:'Gelişmeleri takip et',
      feedLanguage:'Uygulama dili', preferredBriefingLength:'Varsayılan bülten uzunluğu',
      shownBecause:'Gösterilme nedeni', followedPrisoners:'Takip edilen mahpuslar',
      followedDevelopments:'Takip edilen gelişmeler', noWatchOptions:'Şu anda seçenek yok.',
      zine:'Zine', zineIntro:'Makaleleri bir sayıda topla ve baskı veya PDF için tasarla.',
      zineAdd:'Zine’a ekle', zineAdded:'Makale Zine’a eklendi.', zineRemove:'Zine’dan çıkar',
      zineRemoved:'Makale Zine’dan çıkarıldı.', zineEmpty:'Zine henüz boş.',
      zineClear:'Zine’ı temizle', zineClearConfirm:'Zine’daki tüm makaleler kaldırılsın mı?'
    }
  };

  const state = {
    articles: [],
    facets: { regions: [], topics: [], sources: [] },
    view: 'home',
    language: supportedLanguage(localStorage.getItem(LANGUAGE_KEY) || navigator.language || 'de'),
    ui: readJson(UI_SETTINGS_KEY, { theme: 'dark', fontSize: 'normal', density: 'standard' }),
    preferences: normalizedPreferences(readJson(PREFS_KEY, {})),
    translations: readJson(TRANSLATIONS_KEY, {}),
    discover: { query: '', region: '', topic: '', period: 'current', limit: 24 },
    events: [],
    eventFilter: { query: '', country: '', archived: false },
    prisonerData: { profiles: [], sources: [] },
    lexicon: { section: 'all', query: '' },
    lexiconSnapshot: { terms: [], sources: [] },
    developmentWatch: readJson(STORY_WATCH_KEY, []),
    developmentsWatchedOnly: false,
    podcasts: [],
    generatedPodcasts: [],
    radioStations: [],
    media: { section: 'video', videoMode: 'current', query: '', region: 'all', category: 'all' },
    briefing: { step: 1, regions: [], topics: [], language: '', amount: 5, items: [] },
    cardArticles: [],
    activeArticle: null
  };
  let articlePodcast = {
    chunks: [],
    index: 0,
    utterance: null,
    playing: false,
    paused: false,
    language: 'de'
  };

  const viewRoot = document.getElementById('next-view');
  const loading = document.getElementById('next-loading');
  const articleDialog = document.getElementById('next-article-dialog');
  const preferencesDialog = document.getElementById('next-preferences-dialog');
  const menuDialog = document.getElementById('next-menu-dialog');
  const briefingDialog = document.getElementById('next-briefing-dialog');
  const searchPanel = document.getElementById('next-global-search');
  const searchInput = document.getElementById('next-search-input');
  const languageSelect = document.getElementById('next-language');
  const themeSelect = document.getElementById('next-menu-theme');
  const fontSizeSelect = document.getElementById('next-menu-font-size');
  const densitySelect = document.getElementById('next-menu-density');
  const briefingTranslationsInFlight = new Set();
  const briefingTranslationsAttempted = new Set();
  const systemTheme = window.matchMedia?.('(prefers-color-scheme: light)');

  function supportedLanguage(value) {
    const language = String(value || '').toLowerCase().split('-')[0];
    return Object.prototype.hasOwnProperty.call(COPY, language) ? language : 'en';
  }

  function t(key) {
    return PRODUCT_COPY[state.language]?.[key]
      || PRODUCT_COPY.en[key]
      || UI_COPY[state.language]?.[key]
      || UI_COPY.en[key]
      || MEDIA_COPY[state.language]?.[key]
      || MEDIA_COPY.en[key]
      || SPECIAL_COPY[state.language]?.[key]
      || SPECIAL_COPY.en[key]
      || COPY[state.language]?.[key]
      || COPY.en[key]
      || key;
  }

  function readJson(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key) || 'null');
      return value ?? fallback;
    } catch {
      return fallback;
    }
  }

  function normalizedPreferences(value = {}) {
    const uniqueStrings = key => [...new Set(
      (Array.isArray(value[key]) ? value[key] : []).map(item => String(item || '').trim()).filter(Boolean)
    )];
    const briefingAmount = Number(value.briefingAmount);
    return {
      regions: uniqueStrings('regions'),
      topics: uniqueStrings('topics'),
      sources: uniqueStrings('sources'),
      blockedSources: uniqueStrings('blockedSources'),
      prisonerIds: uniqueStrings('prisonerIds'),
      preferredLanguage: value.preferredLanguage ? supportedLanguage(value.preferredLanguage) : '',
      briefingAmount: [3, 5, 8].includes(briefingAmount) ? briefingAmount : 5
    };
  }

  function writeJson(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.warn('Local storage unavailable', error);
      return false;
    }
  }

  function normalizedUiSettings(value = {}) {
    return {
      theme: ['dark', 'light', 'system', 'contrast'].includes(value.theme) ? value.theme : 'dark',
      fontSize: ['normal', 'large', 'xlarge'].includes(value.fontSize) ? value.fontSize : 'normal',
      density: ['compact', 'standard', 'spacious'].includes(value.density) ? value.density : 'standard'
    };
  }

  function applyUiSettings() {
    state.ui = normalizedUiSettings(state.ui);
    const resolvedTheme = state.ui.theme === 'system'
      ? (systemTheme?.matches ? 'light' : 'dark')
      : state.ui.theme;
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.dataset.fontSize = state.ui.fontSize;
    document.documentElement.dataset.density = state.ui.density;
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      'content',
      resolvedTheme === 'light' ? '#f3eee5' : '#05080b'
    );
    themeSelect.value = state.ui.theme;
    fontSizeSelect.value = state.ui.fontSize;
    densitySelect.value = state.ui.density;
  }

  function saveUiSettings() {
    state.ui = normalizedUiSettings({
      theme: themeSelect.value,
      fontSize: fontSizeSelect.value,
      density: densitySelect.value
    });
    writeJson(UI_SETTINGS_KEY, state.ui);
    applyUiSettings();
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function dateLabel(article) {
    if (!article?.timestamp) return '';
    try {
      return new Intl.DateTimeFormat(state.language, {
        day: '2-digit',
        month: 'short',
        year: new Date(article.timestamp).getFullYear() === new Date().getFullYear()
          ? undefined
          : 'numeric'
      }).format(new Date(article.timestamp));
    } catch {
      return '';
    }
  }

  function applyLanguage() {
    window.currentLang = state.language;
    document.documentElement.lang = state.language;
    languageSelect.value = state.language;
    document.querySelectorAll('[data-i18n]').forEach(element => {
      element.textContent = t(element.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
      element.placeholder = t(element.dataset.i18nPlaceholder);
    });
    searchInput.placeholder = t('searchPlaceholder');
    document.getElementById('next-search-toggle').setAttribute('aria-label', t('menuSearch'));
    document.getElementById('next-menu-toggle').setAttribute('aria-label', t('menuOpen'));
    document.querySelector('[data-dialog-close]').setAttribute('aria-label', t('close'));
    document.querySelector('[data-menu-close]').setAttribute('aria-label', t('close'));
    document.querySelector('[data-briefing-close]').setAttribute('aria-label', t('close'));
    document.getElementById('next-menu-title').textContent = t('menu');
    document.getElementById('next-menu-display-title').textContent = t('display');
    document.getElementById('next-menu-project-title').textContent = t('project');
    document.getElementById('next-menu-theme-label').textContent = t('theme');
    document.getElementById('next-menu-font-label').textContent = t('fontSize');
    document.getElementById('next-menu-density-label').textContent = t('density');
    document.getElementById('next-menu-settings-local').textContent = t('settingsLocal');
    [
      [themeSelect, [['dark', 'themeDark'], ['light', 'themeLight'], ['system', 'themeSystem'], ['contrast', 'themeContrast']]],
      [fontSizeSelect, [['normal', 'normal'], ['large', 'large'], ['xlarge', 'xlarge']]],
      [densitySelect, [['compact', 'compact'], ['standard', 'standard'], ['spacious', 'spacious']]]
    ].forEach(([select, options]) => {
      options.forEach(([value, key]) => {
        const option = select.querySelector(`option[value="${value}"]`);
        if (option) option.textContent = t(key);
      });
    });
    document.getElementById('next-menu-about').textContent = t('aboutProject');
    document.getElementById('next-menu-feedback').textContent = t('feedback');
    document.getElementById('next-menu-privacy').textContent = t('privacy');
    document.getElementById('next-menu-diagnostics-label').textContent = t('diagnostics');
    document.getElementById('next-menu-sources').textContent = t('sourceCheck');
    document.getElementById('next-menu-selftest').textContent = t('selfTest');
  }

  function translationFor(article) {
    return state.translations?.[state.language]?.[article.id] || null;
  }

  function storeTranslation(article, translation, language = state.language) {
    if (!state.translations[language]) state.translations[language] = {};
    const entry = {
      title: core.text(translation.title),
      intro: core.text(translation.intro),
      storedAt: new Date().toISOString()
    };
    if (translation.content) {
      entry.content = core.text(translation.content);
      entry.fullContent = true;
    }
    state.translations[language][article.id] = entry;
    writeJson(TRANSLATIONS_KEY, state.translations);
  }

  function bookmarks() {
    const values = readJson(BOOKMARKS_KEY, []);
    return Array.isArray(values) ? values : [];
  }

  function isSaved(article) {
    return bookmarks().some(item => core.articleId(item) === article.id);
  }

  function toggleSaved(article) {
    const items = bookmarks();
    const index = items.findIndex(item => core.articleId(item) === article.id);
    const saved = index < 0;
    if (saved) items.push(article);
    else items.splice(index, 1);
    writeJson(BOOKMARKS_KEY, items);
    showToast(saved ? t('articleSaved') : t('articleRemoved'));
    return saved;
  }

  function readArticles() {
    const values = readJson(READ_KEY, []);
    return Array.isArray(values) ? values.filter(Boolean) : [];
  }

  function isRead(article) {
    return readArticles().includes(article?.link || article?.id || '');
  }

  function toggleRead(article) {
    const key = article?.link || article?.id || '';
    if (!key) return false;
    const values = readArticles();
    const index = values.indexOf(key);
    const read = index < 0;
    if (read) values.push(key);
    else values.splice(index, 1);
    writeJson(READ_KEY, values);
    return read;
  }

  function zineArticles() {
    const values = readJson(ZINE_KEY, []);
    return Array.isArray(values) ? values.filter(item => item && typeof item === 'object') : [];
  }

  function zineArticleKey(article) {
    return String(
      article?.link
      || `${article?.source || article?.quelleName || ''}::${article?.title || ''}::${article?.pubDate || article?.timestamp || ''}`
    ).trim();
  }

  function isInZine(article) {
    const key = zineArticleKey(article);
    return Boolean(key && zineArticles().some(item => zineArticleKey(item) === key));
  }

  function storeZineArticles(items) {
    writeJson(ZINE_KEY, items);
    window.dispatchEvent(new CustomEvent('wrnzinechange', { detail: { count: items.length } }));
  }

  function toggleZineArticle(article) {
    const items = zineArticles();
    const key = zineArticleKey(article);
    const index = items.findIndex(item => zineArticleKey(item) === key);
    const added = index < 0;
    if (added) {
      items.push({
        ...article,
        quelleName: article.source,
        pubDate: article.pubDate || (article.timestamp ? new Date(article.timestamp).toISOString() : ''),
        summary: article.intro,
        description: article.content || article.intro
      });
    } else {
      items.splice(index, 1);
    }
    storeZineArticles(items);
    showToast(t(added ? 'zineAdded' : 'zineRemoved'));
    return added;
  }

  function removeZineArticle(key) {
    storeZineArticles(zineArticles().filter(article => zineArticleKey(article) !== key));
    if (state.view === 'media' && state.media.section === 'zine') renderMedia();
  }

  function showToast(message) {
    const toast = document.getElementById('next-toast');
    toast.textContent = message;
    toast.hidden = false;
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => { toast.hidden = true; }, 2600);
  }

  function cardMarkup(article) {
    const cardIndex = state.cardArticles.push(article) - 1;
    const translation = translationFor(article);
    const title = translation?.title || article.title;
    const intro = translation?.intro || article.intro;
    const saved = isSaved(article);
    const image = article.image
      ? `<div class="news-card__image"><img src="${escapeHtml(article.image)}" alt="" loading="lazy" referrerpolicy="no-referrer"></div>`
      : '<div class="news-card__image" aria-hidden="true"></div>';
    const preferenceReasons = state.view === 'following'
      ? [
          (state.preferences.regions || []).includes(article.primaryRegion) ? article.primaryRegion : '',
          (state.preferences.topics || []).includes(article.primaryTopic) ? article.primaryTopic : '',
          (state.preferences.sources || []).includes(article.source) ? article.source : ''
        ].filter(Boolean)
      : [];

    return `
      <article class="news-card" data-card-index="${cardIndex}">
        <div class="news-card__body">
          <div class="meta-line">
            <span>${escapeHtml(article.source)}</span>
            <span>${escapeHtml(dateLabel(article))}</span>
          </div>
          <button class="news-card__open" type="button" data-action="open" data-index="${cardIndex}">
            <h3>${escapeHtml(title)}</h3>
            <p>${escapeHtml(intro || '')}</p>
          </button>
          <div class="meta-line article-classification">
            ${article.primaryRegion ? `<span class="tag">${escapeHtml(article.primaryRegion)}</span>` : ''}
            ${article.primaryTopic ? `<span class="tag optional-meta">${escapeHtml(article.primaryTopic)}</span>` : ''}
          </div>
          ${preferenceReasons.length ? `<small class="preference-reason">${escapeHtml(t('shownBecause'))}: ${escapeHtml(preferenceReasons.join(' · '))}</small>` : ''}
          ${translation ? `<small class="translation-note">${escapeHtml(t('translated'))}</small>` : ''}
          <div class="card-actions">
            <button class="translate-card" type="button" data-action="translate" data-index="${cardIndex}">
              <span class="red-black-star" aria-hidden="true">★</span>
              <span>${escapeHtml(t('translate'))}</span>
            </button>
            <button class="save-card" type="button" data-action="save" data-index="${cardIndex}" aria-label="${escapeHtml(saved ? t('removeSaved') : t('save'))}" aria-pressed="${saved}">${saved ? '★' : '☆'}</button>
          </div>
        </div>
        ${image}
      </article>`;
  }

  function cardsMarkup(items) {
    if (!items.length) {
      return `<div class="empty-state"><strong>${escapeHtml(t('noMatches'))}</strong><p>${escapeHtml(t('noMatchesText'))}</p></div>`;
    }
    return `<div class="article-grid">${items.map(cardMarkup).join('')}</div>`;
  }

  function headingMarkup(eyebrow, title, intro, action = '') {
    return `
      <header class="view-heading">
        <div>
          <span class="eyebrow">${escapeHtml(eyebrow)}</span>
          <h1>${escapeHtml(title)}</h1>
          ${intro ? `<p>${escapeHtml(intro)}</p>` : ''}
        </div>
        ${action}
      </header>`;
  }

  function renderHome() {
    state.cardArticles = [];
    const selected = core.balanceBySource(state.articles, HOME_COUNT, 2);
    const hero = selected[0];
    const others = selected.slice(1);
    if (!hero) return renderError();

    const heroIndex = state.cardArticles.push(hero) - 1;
    const heroTranslation = translationFor(hero);
    const heroTitle = heroTranslation?.title || hero.title;
    const heroIntro = heroTranslation?.intro || hero.intro;
    const heroImage = hero.image
      ? `<div class="home-hero__image"><img src="${escapeHtml(hero.image)}" alt="" referrerpolicy="no-referrer"></div>`
      : '<div class="home-hero__image" aria-hidden="true"></div>';

    viewRoot.innerHTML = `
      <div class="meta-line"><span class="tag">${escapeHtml(t('previewNotice'))}</span></div>
      <div class="section-heading"><h2>${escapeHtml(t('latest'))}</h2><small>${selected.length}</small></div>
      <article class="home-hero">
        ${heroImage}
        <div class="home-hero__content">
          <span class="eyebrow">${escapeHtml(hero.source)} · ${escapeHtml(dateLabel(hero))}</span>
          <h1>${escapeHtml(heroTitle)}</h1>
          <p>${escapeHtml(heroIntro)}</p>
          <div class="meta-line article-classification">
            <span class="tag">${escapeHtml(hero.primaryRegion)}</span>
            ${hero.primaryTopic ? `<span class="tag">${escapeHtml(hero.primaryTopic)}</span>` : ''}
          </div>
          <div class="card-actions">
            <button class="small-action" type="button" data-action="open" data-index="${heroIndex}">${escapeHtml(t('openArticle'))}</button>
            <button class="translate-card" type="button" data-action="translate" data-index="${heroIndex}">
              <span class="red-black-star" aria-hidden="true">★</span><span>${escapeHtml(t('translate'))}</span>
            </button>
          </div>
        </div>
      </article>
      <div class="section-heading briefing-heading">
        <div><h2>${escapeHtml(t('briefing'))}</h2><small>${escapeHtml(t('briefingHint'))}</small></div>
        <button class="secondary-button" type="button" data-action="briefing-open">${escapeHtml(t('briefingCreate'))}</button>
      </div>
      <div class="briefing-strip">
        ${selected.slice(0, 5).map((article, index) => {
          const cardIndex = state.cardArticles.push(article) - 1;
          const translation = translationFor(article);
          return `<button class="briefing-item" type="button" data-action="open" data-index="${cardIndex}" data-briefing-id="${escapeHtml(article.id)}"><b>${index + 1}</b><span>${escapeHtml(translation?.title || article.title)}</span></button>`;
        }).join('')}
      </div>
      <div class="section-heading">
        <h2>${escapeHtml(t('moreNews'))}</h2>
        <button class="section-text-action" type="button" data-action="open-archive" data-period="7d">${escapeHtml(t('archiveBrowse'))} →</button>
      </div>
      ${cardsMarkup(others)}
    `;
    void ensureBriefingTranslations(selected.slice(0, 5));
  }

  async function ensureBriefingTranslations(items) {
    if (!window.WRNSharedTranslations?.request || !Array.isArray(items)) return;
    const language = state.language;

    for (const article of items.slice(0, 5)) {
      if (state.language !== language) break;
      if (!article || state.translations?.[language]?.[article.id]) continue;
      const sourceLanguage = String(
        article.language || article.lang || article.sprache || ''
      ).trim().toLowerCase().split('-')[0];
      if (sourceLanguage && sourceLanguage !== 'und' && sourceLanguage === language) continue;

      const requestKey = `${language}::${article.id}`;
      if (briefingTranslationsInFlight.has(requestKey) || briefingTranslationsAttempted.has(requestKey)) continue;
      briefingTranslationsInFlight.add(requestKey);
      briefingTranslationsAttempted.add(requestKey);
      const item = [...viewRoot.querySelectorAll('.briefing-item')]
        .find(element => element.dataset.briefingId === article.id);
      item?.setAttribute('aria-busy', 'true');

      try {
        const result = await window.WRNSharedTranslations.request({
          title: article.title,
          text: article.intro || core.excerpt(article.content, 230),
          targetLanguage: language,
          mode: 'title_and_text'
        });
        if (result?.error || !result?.text) throw new Error(result?.message || 'Translation failed');
        const parsed = core.splitTranslatedTeaser(result.text);
        const translated = {
          title: parsed.title || article.title,
          intro: parsed.intro || article.intro
        };
        storeTranslation(article, translated, language);
        const currentItem = [...viewRoot.querySelectorAll('.briefing-item')]
          .find(element => element.dataset.briefingId === article.id);
        if (currentItem && state.language === language) {
          currentItem.querySelector('span').textContent = translated.title;
          currentItem.removeAttribute('aria-busy');
        }
      } catch (error) {
        console.warn('Automatic briefing translation failed', error);
        const currentItem = [...viewRoot.querySelectorAll('.briefing-item')]
          .find(element => element.dataset.briefingId === article.id);
        currentItem?.removeAttribute('aria-busy');
      } finally {
        briefingTranslationsInFlight.delete(requestKey);
      }
    }
  }

  function hasPreferences() {
    return ['regions', 'topics', 'sources', 'blockedSources', 'prisonerIds']
      .some(key => Array.isArray(state.preferences[key]) && state.preferences[key].length)
      || (Array.isArray(state.developmentWatch) && state.developmentWatch.length);
  }

  function followedContextMarkup() {
    const prisonerIds = new Set(state.preferences.prisonerIds || []);
    const prisoners = (state.prisonerData.profiles || []).filter(profile => prisonerIds.has(profile.id));
    const watched = new Set(Array.isArray(state.developmentWatch) ? state.developmentWatch : []);
    const developments = specialty
      .developmentClusters(state.articles, window.WRNStoriesCore, { days: 30, threshold: 0.5 })
      .filter(story => watched.has(story.id));
    if (!prisoners.length && !developments.length) return '';

    return `<div class="followed-context">
      ${prisoners.length ? `<section>
        <div class="section-heading"><h2>${escapeHtml(t('followedPrisoners'))}</h2><small>${prisoners.length}</small></div>
        <button type="button" class="followed-context__button" data-view-target="prisoners">${prisoners.map(profile => escapeHtml(profile.publicName)).join(' · ')}</button>
      </section>` : ''}
      ${developments.length ? `<section>
        <div class="section-heading"><h2>${escapeHtml(t('followedDevelopments'))}</h2><small>${developments.length}</small></div>
        <button type="button" class="followed-context__button" data-view-target="developments">${developments.map(story => escapeHtml(story.title)).join(' · ')}</button>
      </section>` : ''}
    </div>`;
  }

  function renderFollowing() {
    state.cardArticles = [];
    if (!hasPreferences()) {
      viewRoot.innerHTML = `
        ${headingMarkup(t('following'), t('noPreferences'), t('noPreferencesText'))}
        <div class="empty-state">
          <strong>${escapeHtml(t('personalize'))}</strong>
          <p>${escapeHtml(t('personalLocal'))}</p>
          <button class="primary-button" type="button" data-action="preferences">${escapeHtml(t('personalize'))}</button>
        </div>`;
      return;
    }

    const hasArticlePreferences = ['regions', 'topics', 'sources', 'blockedSources']
      .some(key => Array.isArray(state.preferences[key]) && state.preferences[key].length);
    const chosen = hasArticlePreferences
      ? state.articles.filter(article => core.matchesPreferences(article, state.preferences))
      : [];
    const selected = core.balanceBySource(chosen, HOME_COUNT, 2);
    const summary = [
      ...(state.preferences.regions || []),
      ...(state.preferences.topics || []),
      ...(state.preferences.sources || [])
    ].slice(0, 5).join(' · ');

    viewRoot.innerHTML = `
      ${headingMarkup(t('following'), t('personalTitle'), t('personalIntro'))}
      <div class="personal-summary">
        <div><strong>${escapeHtml(summary || t('personalize'))}</strong><p>${escapeHtml(t('personalLocal'))}</p></div>
        <button class="secondary-button" type="button" data-action="preferences">${escapeHtml(t('editSelection'))}</button>
      </div>
      ${followedContextMarkup()}
      ${cardsMarkup(selected)}
    `;
  }

  function filterChipMarkup(kind, value, active) {
    return `<button type="button" class="filter-chip${active ? ' active' : ''}" data-filter-kind="${escapeHtml(kind)}" data-filter-value="${escapeHtml(value)}">${escapeHtml(value || t('all'))}</button>`;
  }

  const TOPIC_GROUPS = [
    ['groupPolitics', ['Anti-Imperialism', 'Anticapitalism', 'Anticolonialism', 'Antifascism', 'No War', 'Theory & Strategy']],
    ['groupRights', ['Antiracism', 'Antisexism', 'Queer-Feminism', 'No Borders', 'Radical Health & Disability', 'Indigenous Struggles']],
    ['groupAction', ['Movement News', 'Demonstrations', 'Labor Struggles', 'Squatting & Housing', 'Anti-Rep & Prisons', 'Cyberactivism']],
    ['groupEcology', ['Eco-Anarchism', 'Animal Liberation', 'Libraries']]
  ];

  function periodArticles(items) {
    if (!['7d', '30d'].includes(state.discover.period)) return items;
    const newest = Math.max(...state.articles.map(article => Number(article.timestamp) || 0));
    if (!Number.isFinite(newest) || newest <= 0) return items;
    const days = state.discover.period === '7d' ? 7 : 30;
    const threshold = newest - days * 24 * 60 * 60 * 1000;
    return items.filter(article => Number(article.timestamp) >= threshold);
  }

  function allDiscoverResults() {
    return periodArticles(core.filterArticles(state.articles, state.discover));
  }

  function discoverResults() {
    return allDiscoverResults().slice(0, state.discover.limit);
  }

  function periodButton(value, label) {
    const active = state.discover.period === value;
    return `<button type="button" class="${active ? 'active' : ''}" data-action="discover-period" data-value="${value}" aria-pressed="${active}">${escapeHtml(label)}</button>`;
  }

  function topicDirectoryMarkup(topics) {
    const available = new Set(topics);
    const grouped = new Set(TOPIC_GROUPS.flatMap(([, values]) => values));
    const groups = TOPIC_GROUPS.map(([label, values]) => {
      const items = values.filter(value => available.has(value));
      if (!items.length) return '';
      return `<section class="topic-group">
        <h3>${escapeHtml(t(label))}</h3>
        <div class="filter-chips filter-chips--topics">
          ${items.map(value => filterChipMarkup('topic', value, state.discover.topic === value)).join('')}
        </div>
      </section>`;
    }).join('');
    const remaining = topics.filter(value => !grouped.has(value));
    const remainingMarkup = remaining.length
      ? `<section class="topic-group">
          <h3>${escapeHtml(t('topics'))}</h3>
          <div class="filter-chips filter-chips--topics">
            ${remaining.map(value => filterChipMarkup('topic', value, state.discover.topic === value)).join('')}
          </div>
        </section>`
      : '';
    return `<div class="topic-directory">${groups}${remainingMarkup}</div>`;
  }

  function renderDiscover() {
    state.cardArticles = [];
    const results = discoverResults();
    const total = allDiscoverResults().length;
    const regionChips = ['', ...state.facets.regions].map(value =>
      filterChipMarkup('region', value, state.discover.region === value)
    ).join('');
    const topics = [...state.facets.topics].sort((a, b) => a.localeCompare(b, state.language));

    viewRoot.innerHTML = `
      ${headingMarkup(t('discover'), t('discover'), t('discoverIntro'))}
      <section class="feature-grid" aria-label="${escapeHtml(t('specialty'))}">
        ${featureCard('◷', t('events'), t('eventsText'), 'events')}
        ${featureCard('A–Z', t('lexicon'), t('lexiconText'), 'lexicon')}
        ${featureCard('✉', t('prisonersShort'), t('prisonersText'), 'prisoners')}
        ${featureCard('↗', t('developments'), t('developmentsText'), 'developments')}
      </section>
      <nav class="archive-periods" aria-label="${escapeHtml(t('allArticles'))}">
        ${periodButton('current', t('currentPeriod'))}
        ${periodButton('7d', t('last7Days'))}
        ${periodButton('30d', t('last30Days'))}
        ${periodButton('all', t('allArticles'))}
      </nav>
      <div class="discover-controls">
        <input id="next-discover-query" type="search" value="${escapeHtml(state.discover.query)}" placeholder="${escapeHtml(t('searchPlaceholder'))}" aria-label="${escapeHtml(t('searchLabel'))}">
        <section class="filter-directory">
          <span class="eyebrow">${escapeHtml(t('regions'))}</span>
          <div class="filter-chips filter-chips--regions">${regionChips}</div>
        </section>
        <section class="filter-directory">
          <div class="filter-directory__heading">
            <span class="eyebrow">${escapeHtml(t('topics'))}</span>
            ${state.discover.topic ? filterChipMarkup('topic', '', false) : ''}
          </div>
          ${topicDirectoryMarkup(topics)}
        </section>
      </div>
      <div class="section-heading"><h2>${escapeHtml(t('results'))}</h2><small>${results.length} ${escapeHtml(t('of'))} ${total}</small></div>
      ${cardsMarkup(results)}
      ${results.length < total ? `<div class="load-more-row"><button class="secondary-button" type="button" data-action="discover-more">${escapeHtml(t('showMore'))}</button></div>` : ''}
    `;
  }

  function featureCard(icon, title, description, view) {
    return `<button class="feature-card" type="button" data-view-target="${escapeHtml(view)}"><span aria-hidden="true">${escapeHtml(icon)}</span><strong>${escapeHtml(title)}</strong><p>${escapeHtml(description)}</p></button>`;
  }

  function specialtyBack() {
    return `<button class="secondary-button" type="button" data-view-target="discover">← ${escapeHtml(t('backDiscover'))}</button>`;
  }

  function formatTimestamp(value, options = {}) {
    if (!value) return '—';
    try {
      const format = options.dateOnly
        ? { dateStyle: 'medium' }
        : { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' };
      if (options.timeZone) format.timeZone = options.timeZone;
      return new Intl.DateTimeFormat(state.language, format).format(new Date(value));
    } catch {
      return '—';
    }
  }

  function countryLabel(value) {
    return ['XC', 'XE'].includes(value) ? t('internationalUnknown') : value;
  }

  function eventWhenLabel(event) {
    const start = formatTimestamp(event.start, { timeZone: event.timezone });
    const range = event.end > event.start + 12 * 60 * 60 * 1000
      ? ` – ${formatTimestamp(event.end, { timeZone: event.timezone })}`
      : '';
    return `${start}${range}${event.timezone ? ` · ${event.timezone}` : ''}`;
  }

  function renderEvents() {
    state.cardArticles = [];
    const countries = [...new Set(state.events.map(item => item.country).filter(Boolean))].sort();
    const filtered = specialty.filterEvents(state.events, state.eventFilter).slice(0, 40);
    viewRoot.innerHTML = `
      ${headingMarkup(t('events'), t('events'), t('eventsText'), specialtyBack())}
      <div class="special-tabs" role="tablist" aria-label="${escapeHtml(t('events'))}">
        <button type="button" class="filter-chip${state.eventFilter.archived ? '' : ' active'}" data-action="event-period" data-value="upcoming">${escapeHtml(t('eventUpcoming'))}</button>
        <button type="button" class="filter-chip${state.eventFilter.archived ? ' active' : ''}" data-action="event-period" data-value="archive">${escapeHtml(t('eventArchive'))}</button>
      </div>
      <div class="special-filter-row">
        <input id="next-event-query" type="search" value="${escapeHtml(state.eventFilter.query)}" placeholder="${escapeHtml(t('eventSearch'))}" aria-label="${escapeHtml(t('eventSearch'))}">
        <label><span class="sr-only">${escapeHtml(t('eventCountry'))}</span><select id="next-event-country">
          <option value="">${escapeHtml(t('eventAllCountries'))}</option>
          ${countries.map(country => `<option value="${escapeHtml(country)}"${country === state.eventFilter.country ? ' selected' : ''}>${escapeHtml(countryLabel(country))}</option>`).join('')}
        </select></label>
      </div>
      <div class="section-heading"><h2>${escapeHtml(state.eventFilter.archived ? t('eventArchive') : t('eventUpcoming'))}</h2><small>${filtered.length}</small></div>
      ${filtered.length ? `<div class="event-grid">${filtered.map(event => `
        <article class="event-card">
          ${event.image ? `<img src="${escapeHtml(event.image)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : ''}
          <div>
            <span class="eyebrow">${escapeHtml(event.source)}</span>
            <h3>${escapeHtml(event.title)}</h3>
            <dl><div><dt>${escapeHtml(t('when'))}</dt><dd>${escapeHtml(eventWhenLabel(event))}</dd></div>
            <div><dt>${escapeHtml(t('where'))}</dt><dd>${escapeHtml([event.venue, event.city, countryLabel(event.country)].filter(Boolean).join(' · ') || '—')}</dd></div></dl>
            ${event.content ? `<p>${escapeHtml(core.excerpt(event.content, 220))}</p>` : ''}
            <div class="meta-line">${event.categories.slice(0, 3).map(value => `<span class="tag">${escapeHtml(value)}</span>`).join('')}</div>
            ${event.occurrenceCount > 1 ? `<small>${event.occurrenceCount} ${escapeHtml(t('eventRepeat'))}</small>` : ''}
            ${event.link ? `<a class="small-action" href="${escapeHtml(event.link)}" target="_blank" rel="noopener noreferrer">${escapeHtml(t('original'))}</a>` : ''}
          </div>
        </article>`).join('')}</div>` : `<div class="empty-state"><strong>${escapeHtml(t('noEvents'))}</strong></div>`}
    `;
  }

  function sectionLabel(section) {
    return window.WRNLexicon184?.sectionLabel?.(section, state.language) || section;
  }

  function renderLexiconSources() {
    return `<div class="source-grid">${state.lexiconSnapshot.sources.map(source => `
      <article class="source-card">
        <span class="eyebrow">${escapeHtml(source.language || '')}</span>
        <h3>${escapeHtml(source.name)}</h3>
        <p>${escapeHtml(specialty.localized(source.description, state.language))}</p>
        <div class="source-actions">
          ${source.url ? `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(t('sourceOpen'))}</a>` : ''}
          ${(source.downloads || []).map(download => `<a href="${escapeHtml(download.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(download.label)}</a>`).join('')}
        </div>
      </article>`).join('')}</div>`;
  }

  function renderLexicon() {
    state.cardArticles = [];
    const sections = ['all', 'basics', 'organisation', 'justice', 'power', 'tactics', 'ecology', 'struggles', 'sources'];
    const terms = specialty.glossaryEntries(state.lexiconSnapshot, state.language, state.lexicon.section, state.lexicon.query);
    viewRoot.innerHTML = `
      ${headingMarkup(t('lexicon'), t('lexicon'), t('glossaryIntro'), specialtyBack())}
      <div class="notice-card"><strong>${escapeHtml(t('underConstruction'))}</strong><p>${escapeHtml(t('glossaryNote'))}</p></div>
      <div class="special-tabs lexicon-tabs">${sections.map(section => `<button type="button" class="filter-chip${state.lexicon.section === section ? ' active' : ''}" data-action="lexicon-section" data-value="${section}">${escapeHtml(section === 'sources' ? t('glossarySources') : sectionLabel(section))}</button>`).join('')}</div>
      ${state.lexicon.section === 'sources' ? `
        <div class="special-actions"><button type="button" class="secondary-button" data-action="lexicon-download">${escapeHtml(t('downloadJson'))}</button></div>
        ${renderLexiconSources()}` : `
        <div class="special-filter-row"><input id="next-lexicon-query" type="search" value="${escapeHtml(state.lexicon.query)}" placeholder="${escapeHtml(t('glossarySearch'))}" aria-label="${escapeHtml(t('glossarySearch'))}"><span class="result-count">${terms.length}</span></div>
        <div class="lexicon-grid">${terms.map(term => `
          <details class="lexicon-card">
            <summary><span class="eyebrow">${escapeHtml(sectionLabel(term.category))}</span><strong>${escapeHtml(term.displayTitle)}</strong><p>${escapeHtml(term.displaySummary)}</p></summary>
            <div class="lexicon-detail">
              ${term.displayPractice ? `<h4>${escapeHtml(t('practice'))}</h4><p>${escapeHtml(term.displayPractice)}</p>` : ''}
              ${term.displayDebate ? `<h4>${escapeHtml(t('debate'))}</h4><p>${escapeHtml(term.displayDebate)}</p>` : ''}
              ${(term.related || []).length ? `<h4>${escapeHtml(t('related'))}</h4><div class="meta-line">${term.related.map(value => `<span class="tag">${escapeHtml(value)}</span>`).join('')}</div>` : ''}
              ${!['de', 'en'].includes(state.language) ? `<small>${escapeHtml(t('fallbackLanguage'))}</small>` : ''}
            </div>
          </details>`).join('')}</div>`}
    `;
  }

  function prisonerAddress(profile) {
    return (profile?.mailingAddress?.lines || []).join('\n');
  }

  function renderPrisoners() {
    state.cardArticles = [];
    const profiles = state.prisonerData.profiles || [];
    viewRoot.innerHTML = `
      ${headingMarkup(t('prisoners'), t('prisoners'), t('prisonerIntro'), specialtyBack())}
      <div class="notice-card"><strong>${escapeHtml(t('underConstruction'))}</strong><p>${escapeHtml(t('prisonerLimited'))}</p><small>🔒 ${escapeHtml(t('localOnly'))}</small></div>
      <div class="prisoner-grid">${profiles.map(profile => {
        const current = specialty.isCurrentProfile(profile);
        const related = specialty.relatedArticles(profile, state.articles).slice(0, 3);
        const relatedMarkup = related.map(article => {
          const index = state.cardArticles.push(article) - 1;
          return `<button type="button" data-action="open" data-index="${index}"><strong>${escapeHtml(article.title)}</strong><small>${escapeHtml(article.source)}</small></button>`;
        }).join('');
        return `<article class="prisoner-card${current ? '' : ' stale'}">
          <header><div><span class="eyebrow">${escapeHtml(profile.country)} · ${escapeHtml(profile.institution)}</span><h3>${escapeHtml(profile.publicName)}</h3></div><span class="verification-badge">${escapeHtml(current ? t('verified') : t('reviewBy'))}: ${escapeHtml(formatTimestamp(`${profile.verification?.[current ? 'verifiedAt' : 'nextReviewAt']}T12:00:00Z`, { dateOnly: true }))}</span></header>
          <p>${escapeHtml(specialty.localized(profile.context, state.language))}</p>
          <div class="meta-line">${(profile.movementTags || []).map(value => `<span class="tag">${escapeHtml(value)}</span>`).join('')}</div>
          <details><summary>${escapeHtml(t('address'))}</summary><address>${escapeHtml(prisonerAddress(profile))}</address><p>${escapeHtml(specialty.localized(profile.mailRules?.notes, state.language))}</p></details>
          <div class="prisoner-related"><h4>${escapeHtml(t('relatedNews'))}</h4>${relatedMarkup || `<p>${escapeHtml(t('noRelated'))}</p>`}</div>
          <button type="button" class="primary-button" data-action="letter" data-profile-id="${escapeHtml(profile.id)}"${current ? '' : ' disabled'}>✉ ${escapeHtml(t('writeLetter'))}</button>
        </article>`;
      }).join('')}</div>
    `;
  }

  function renderDevelopments() {
    state.cardArticles = [];
    const all = specialty.developmentClusters(state.articles, window.WRNStoriesCore, { days: 30, threshold: 0.5 });
    const watched = new Set(Array.isArray(state.developmentWatch) ? state.developmentWatch : []);
    const clusters = state.developmentsWatchedOnly ? all.filter(story => watched.has(story.id)) : all;
    viewRoot.innerHTML = `
      ${headingMarkup(t('developments'), t('developments'), t('developmentIntro'), specialtyBack())}
      <div class="notice-card"><strong>${escapeHtml(t('beta'))}</strong><p>${escapeHtml(t('developmentGuard'))}</p></div>
      <div class="special-tabs"><button type="button" class="filter-chip${state.developmentsWatchedOnly ? '' : ' active'}" data-action="development-filter" data-value="all">${escapeHtml(t('showAll'))}</button><button type="button" class="filter-chip${state.developmentsWatchedOnly ? ' active' : ''}" data-action="development-filter" data-value="watched">${escapeHtml(t('showWatched'))}</button></div>
      ${clusters.length ? `<div class="development-grid">${clusters.map(story => {
        const isWatching = watched.has(story.id);
        return `<article class="development-card">
          <header><div><span class="eyebrow">${story.itemCount} ${escapeHtml(t('storyArticles'))} · ${story.sourceCount} ${escapeHtml(t('storySources'))}</span><h3>${escapeHtml(story.title)}</h3></div><button type="button" class="watch-button" data-action="watch-development" data-story-id="${escapeHtml(story.id)}" aria-pressed="${isWatching}">${isWatching ? '★' : '☆'} ${escapeHtml(isWatching ? t('watching') : t('watch'))}</button></header>
          <div class="evidence-line"><strong>${escapeHtml(t('whyLinked'))}:</strong> ${(story.matchReasons || []).slice(0, 5).map(value => `<span class="tag">${escapeHtml(value)}</span>`).join('')}<span>${escapeHtml(t('confidence'))}: ${Math.round((story.matchConfidence || 0) * 100)}%</span></div>
          <ol class="timeline-list">${story.items.map(item => {
            const normalized = core.normalizeArticle(item);
            const index = state.cardArticles.push(normalized) - 1;
            return `<li><time>${escapeHtml(dateLabel(normalized))}</time><button type="button" data-action="open" data-index="${index}"><strong>${escapeHtml(normalized.title)}</strong><small>${escapeHtml(normalized.source)}</small></button></li>`;
          }).join('')}</ol>
        </article>`;
      }).join('')}</div>` : `<div class="empty-state"><strong>${escapeHtml(t('noDevelopments'))}</strong></div>`}
    `;
  }

  function renderMedia() {
    state.cardArticles = [];
    const section = state.media.section;
    viewRoot.innerHTML = `
      ${headingMarkup(t('media'), t('media'), t('mediaIntro'))}
      <div class="media-section-tabs" role="tablist" aria-label="${escapeHtml(t('media'))}">
        ${mediaTab('video', '▶', t('video'))}
        ${mediaTab('podcasts', '◉', t('podcasts'))}
        ${mediaTab('generated', '◌', t('generated'))}
        ${mediaTab('radio', '⌁', t('radio'))}
        ${mediaTab('zine', '📄', t('zine'))}
      </div>
      <p class="media-privacy">◉ ${escapeHtml(t('privacyMedia'))}</p>
      ${section === 'zine'
        ? renderZineSection()
        : section === 'podcasts'
        ? renderPodcastSection(state.podcasts, false)
        : section === 'generated'
          ? renderPodcastSection(state.generatedPodcasts, true)
          : section === 'radio'
            ? renderRadioSection()
            : renderVideoSection()}
    `;
    if (section === 'zine') {
      window.setTimeout(() => window.WRNZineDesigner1719?.install?.(), 0);
    }
  }

  function mediaTab(value, icon, label) {
    const active = state.media.section === value;
    return `<button type="button" role="tab" aria-selected="${active}" class="${active ? 'active' : ''}" data-action="media-section" data-value="${escapeHtml(value)}"><span aria-hidden="true">${escapeHtml(icon)}</span><strong>${escapeHtml(label)}</strong></button>`;
  }

  function mediaFilters({ categories = false } = {}) {
    const regions = [...new Set([
      ...state.articles.map(item => item.primaryRegion),
      ...state.podcasts.map(item => item.region),
      ...state.radioStations.map(item => item.region),
      ...media.INFORMATION_VIDEOS.map(item => item.region)
    ].filter(Boolean))].sort((a, b) => a.localeCompare(b));
    return `<div class="media-controls${categories ? '' : ' media-controls--two'}">
      <input id="next-media-query" type="search" value="${escapeHtml(state.media.query)}" placeholder="${escapeHtml(t('mediaSearch'))}" aria-label="${escapeHtml(t('mediaSearch'))}">
      ${categories ? `<select id="next-media-category" aria-label="${escapeHtml(t('allCategories'))}">
        <option value="all"${state.media.category === 'all' ? ' selected' : ''}>${escapeHtml(t('allCategories'))}</option>
        <option value="politics"${state.media.category === 'politics' ? ' selected' : ''}>${escapeHtml(t('politics'))}</option>
        <option value="society"${state.media.category === 'society' ? ' selected' : ''}>${escapeHtml(t('society'))}</option>
        <option value="culture"${state.media.category === 'culture' ? ' selected' : ''}>${escapeHtml(t('culture'))}</option>
      </select>` : ''}
      <select id="next-media-region" aria-label="${escapeHtml(t('allRegions'))}">
        <option value="all"${state.media.region === 'all' ? ' selected' : ''}>${escapeHtml(t('allRegions'))}</option>
        ${regions.map(region => `<option value="${escapeHtml(region)}"${state.media.region === region ? ' selected' : ''}>${escapeHtml(region)}</option>`).join('')}
      </select>
    </div>`;
  }

  function renderVideoSection() {
    const query = state.media.query.toLocaleLowerCase();
    const currentVideos = state.articles.filter(article => {
      if (!core.hasVideo(article)) return false;
      if (state.media.region !== 'all' && article.primaryRegion !== state.media.region) return false;
      return !query || [article.title, article.intro, article.source].join(' ').toLocaleLowerCase().includes(query);
    });
    const current = core.balanceBySource(currentVideos, 24, 2);
    const information = media.INFORMATION_VIDEOS.filter(item => {
      if (state.media.region !== 'all' && item.region !== state.media.region) return false;
      return !query || [item.title, item.source, item.summary].join(' ').toLocaleLowerCase().includes(query);
    });
    const items = state.media.videoMode === 'information' ? information : current;
    return `
      <div class="special-tabs media-mode-tabs">
        <button type="button" class="filter-chip${state.media.videoMode === 'current' ? ' active' : ''}" data-action="media-video-mode" data-value="current">${escapeHtml(t('current'))}</button>
        <button type="button" class="filter-chip${state.media.videoMode === 'information' ? ' active' : ''}" data-action="media-video-mode" data-value="information">${escapeHtml(t('information'))}</button>
      </div>
      ${mediaFilters()}
      <div class="section-heading"><h2>${escapeHtml(state.media.videoMode === 'information' ? t('information') : t('current'))}</h2><small>${items.length}</small></div>
      ${state.media.videoMode === 'information'
        ? informationVideoMarkup(information)
        : cardsMarkup(current)}
    `;
  }

  function informationVideoMarkup(items) {
    if (!items.length) return mediaEmpty(t('noMedia'));
    return `<div class="media-results">${items.map(item => `
      <article class="media-result-card">
        <div class="media-result-card__icon" aria-hidden="true">▶</div>
        <div>
          <div class="meta-line"><span>${escapeHtml(item.source)}</span><span>${escapeHtml(item.language)} · ${escapeHtml(item.region)}</span></div>
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.summary)}</p>
          <div class="media-links">
            <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(t('openEpisode'))}</a>
            <a href="${escapeHtml(item.channelUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(t('openChannel'))}</a>
          </div>
        </div>
      </article>`).join('')}</div>`;
  }

  function mediaDescription(value) {
    const clean = core.text(value);
    const firstSentence = clean.match(/^(.{20,260}?[.!?])(?:\s|$)/)?.[1];
    return firstSentence || core.excerpt(clean, 220);
  }

  function renderPodcastSection(source, generated) {
    const filtered = media.filterItems(
      (source || []).filter(item => generated || media.isRelevantPodcast(item)),
      state.media
    ).slice(0, 40);
    return `
      ${mediaFilters({ categories: true })}
      ${generated ? `<div class="notice-card"><strong>30 Tage</strong><p>${escapeHtml(t('generatedNotice'))}</p></div>` : ''}
      <div class="section-heading"><h2>${escapeHtml(generated ? t('generated') : t('podcasts'))}</h2><small>${filtered.length} ${escapeHtml(t('episodes'))}</small></div>
      ${filtered.length ? `<div class="media-results">${filtered.map(podcast => `
        <article class="media-result-card podcast-card">
          ${podcast.artwork ? `<img src="${escapeHtml(podcast.artwork)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : `<div class="media-result-card__icon" aria-hidden="true">◉</div>`}
          <div>
            <div class="meta-line"><span>${escapeHtml(podcast.source)}</span><span>${escapeHtml(podcast.language.toUpperCase())}${podcast.region ? ` · ${escapeHtml(podcast.region)}` : ''}</span></div>
            <h3>${escapeHtml(podcast.title)}</h3>
            <p>${escapeHtml(mediaDescription(podcast.description))}</p>
            ${podcast.audioUrl ? `<audio controls preload="none" src="${escapeHtml(podcast.audioUrl)}" aria-label="${escapeHtml(`${t('playEpisode')}: ${podcast.title}`)}"></audio>` : ''}
            <div class="media-links">
              ${podcast.episodeUrl ? `<a href="${escapeHtml(podcast.episodeUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(t('openEpisode'))}</a>` : ''}
            </div>
          </div>
        </article>`).join('')}</div>` : mediaEmpty(generated ? t('noGenerated') : t('noMedia'))}
    `;
  }

  function renderRadioSection() {
    const filtered = media.filterItems(state.radioStations, state.media);
    return `
      ${mediaFilters()}
      <div class="section-heading"><h2>${escapeHtml(t('radio'))}</h2><small>${filtered.length} ${escapeHtml(t('stations'))}</small></div>
      ${filtered.length ? `<div class="media-results">${filtered.map(station => `
        <article class="media-result-card radio-card">
          <div class="media-result-card__icon" aria-hidden="true">⌁</div>
          <div>
            <div class="meta-line"><span>${escapeHtml(t('station'))}</span><span>${escapeHtml([station.city, station.country].filter(Boolean).join(', '))}</span></div>
            <h3>${escapeHtml(station.name)}</h3>
            <p>${escapeHtml(station.description)}</p>
            ${station.streamUrl
              ? `<audio controls preload="none" src="${escapeHtml(station.streamUrl)}" aria-label="${escapeHtml(`${t('listenLive')}: ${station.name}`)}"></audio>`
              : `<p class="stream-fallback">${escapeHtml(t('streamFallback'))}</p>`}
            <div class="media-links">${station.website ? `<a href="${escapeHtml(station.website)}" target="_blank" rel="noopener noreferrer">${escapeHtml(t('openEpisode'))}</a>` : ''}</div>
          </div>
        </article>`).join('')}</div>` : mediaEmpty(t('noMedia'))}
    `;
  }

  function mediaEmpty(message) {
    return `<div class="empty-state compact"><strong>${escapeHtml(message)}</strong></div>`;
  }

  function renderZineSection() {
    const items = zineArticles();
    const normalizedItems = core.normalizeArticles(items);
    return `
      <p class="zine-workspace-intro">${escapeHtml(t('zineIntro'))}</p>
      <div class="zine-toolbar">
        <button class="secondary-button" type="button" data-action="zine-clear"${items.length ? '' : ' disabled'}>${escapeHtml(t('zineClear'))}</button>
      </div>
      <section class="wrn-zine" id="zine-container" data-wrn-zine>
        <div class="section-heading"><h2>${escapeHtml(t('zine'))}</h2><small>${items.length}</small></div>
        ${normalizedItems.length ? `<div class="zine-content">${normalizedItems.map((article, index) => `
          <article class="zine-workspace-item">
            <div>
              <span class="eyebrow">${escapeHtml(article.source)}</span>
              <h3>${escapeHtml(translationFor(article)?.title || article.title)}</h3>
              <p>${escapeHtml(mediaDescription(translationFor(article)?.intro || article.intro || article.content))}</p>
            </div>
            <button type="button" data-action="zine-remove" data-zine-key="${escapeHtml(zineArticleKey(items[index]))}">${escapeHtml(t('zineRemove'))}</button>
          </article>`).join('')}</div>` : mediaEmpty(t('zineEmpty'))}
      </section>`;
  }

  function renderSaved() {
    state.cardArticles = [];
    const saved = core.normalizeArticles(bookmarks());
    viewRoot.innerHTML = `
      ${headingMarkup(t('saved'), t('saved'), t('savedIntro'))}
      ${saved.length
        ? cardsMarkup(saved)
        : `<div class="empty-state"><strong>${escapeHtml(t('emptySaved'))}</strong><p>${escapeHtml(t('emptySavedText'))}</p></div>`}
    `;
  }

  function renderError() {
    viewRoot.innerHTML = `
      <div class="empty-state">
        <strong>${escapeHtml(t('loadError'))}</strong>
        <button class="primary-button" type="button" data-action="retry">${escapeHtml(t('retry'))}</button>
      </div>`;
  }

  function render() {
    loading.hidden = true;
    const discoverViews = new Set(['discover', 'events', 'lexicon', 'prisoners', 'developments']);
    document.querySelectorAll('[data-view-target]').forEach(button => {
      const active = button.dataset.viewTarget === state.view
        || (button.dataset.viewTarget === 'discover' && discoverViews.has(state.view));
      button.classList.toggle('active', active);
      if (button.closest('.bottom-nav')) {
        if (active) button.setAttribute('aria-current', 'page');
        else button.removeAttribute('aria-current');
      }
    });

    if (state.view === 'following') renderFollowing();
    else if (state.view === 'discover') renderDiscover();
    else if (state.view === 'events') renderEvents();
    else if (state.view === 'lexicon') renderLexicon();
    else if (state.view === 'prisoners') renderPrisoners();
    else if (state.view === 'developments') renderDevelopments();
    else if (state.view === 'media') renderMedia();
    else if (state.view === 'saved') renderSaved();
    else renderHome();
    applyLanguage();
  }

  async function translateTeaser(article, button, card) {
    if (!window.WRNSharedTranslations?.request || !article) {
      showToast(t('translationFailed'));
      return;
    }
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    const label = button.querySelector('span:last-child');
    if (label) label.textContent = t('translating');

    try {
      const result = await window.WRNSharedTranslations.request({
        title: article.title,
        text: article.intro || core.excerpt(article.content, 230),
        mode: 'title_and_text'
      });
      if (result?.error || !result?.text) throw new Error(result?.message || 'Translation failed');
      const parsed = core.splitTranslatedTeaser(result.text);
      storeTranslation(article, {
        title: parsed.title || article.title,
        intro: parsed.intro || article.intro
      });
      if (card) {
        const title = card.querySelector('h3');
        const intro = card.querySelector('.news-card__open p');
        if (title) title.textContent = parsed.title || article.title;
        if (intro) intro.textContent = parsed.intro || article.intro;
        let note = card.querySelector('.translation-note');
        if (!note) {
          note = document.createElement('small');
          note.className = 'translation-note';
          card.querySelector('.card-actions')?.before(note);
        }
        note.textContent = t('translated');
      }
      showToast(t('translatedTitle'));
    } catch (error) {
      console.warn('Teaser translation failed', error);
      showToast(t('translationFailed'));
    } finally {
      button.disabled = false;
      button.removeAttribute('aria-busy');
      if (label) label.textContent = t('translate');
    }
  }

  function openArticle(article) {
    state.activeArticle = article;
    const translation = translationFor(article);
    const related = state.articles
      .filter(candidate => candidate.id !== article.id && candidate.source === article.source)
      .slice(0, 5);
    const relatedMarkup = related.length
      ? `<section class="publisher-related">
          <h2>${escapeHtml(t('moreNews'))} · ${escapeHtml(article.source)}</h2>
          <div>
            ${related.map(candidate => {
              const index = state.cardArticles.push(candidate) - 1;
              const candidateTranslation = translationFor(candidate);
              return `<button type="button" data-action="open" data-index="${index}">
                <strong>${escapeHtml(candidateTranslation?.title || candidate.title)}</strong>
                <small>${escapeHtml(dateLabel(candidate))}</small>
              </button>`;
            }).join('')}
          </div>
        </section>`
      : '';
    document.getElementById('next-article-source').textContent =
      `${article.source} · ${dateLabel(article)}`;
    document.getElementById('next-article-title').textContent =
      translation?.title || article.title;
    updateDialogSave();
    updateDialogZine();
    updateDialogRead();
    stopArticlePodcast();

    document.getElementById('next-article-content').innerHTML = `
      ${article.image ? `<img class="article-lead-image" src="${escapeHtml(article.image)}" alt="" referrerpolicy="no-referrer">` : ''}
      <h1>${escapeHtml(translation?.title || article.title)}</h1>
      <div class="meta-line">
        <span class="tag">${escapeHtml(article.primaryRegion)}</span>
        ${article.primaryTopic ? `<span class="tag">${escapeHtml(article.primaryTopic)}</span>` : ''}
      </div>
      ${article.link ? `<p class="article-source-link"><a href="${escapeHtml(article.link)}" target="_blank" rel="noopener noreferrer">↗ ${escapeHtml(t('original'))}</a></p>` : ''}
      <section class="article-tool-panel" id="next-article-tool-panel" aria-live="polite" hidden></section>
      <p class="article-intro">${escapeHtml(translation?.intro || article.intro)}</p>
      <div class="article-body">${escapeHtml(translation?.fullContent ? translation.content : (article.content || article.intro))}</div>
      ${relatedMarkup}
    `;
    if (!articleDialog.open) articleDialog.showModal();
    document.getElementById('next-article-content').scrollTop = 0;
  }

  function updateDialogSave() {
    const button = document.getElementById('next-dialog-save');
    const saved = state.activeArticle ? isSaved(state.activeArticle) : false;
    button.setAttribute('aria-pressed', String(saved));
    button.setAttribute('aria-label', saved ? t('removeSaved') : t('save'));
    button.textContent = saved ? '★' : '☆';
  }

  function updateDialogZine() {
    const button = document.getElementById('next-dialog-zine');
    const added = state.activeArticle ? isInZine(state.activeArticle) : false;
    button.setAttribute('aria-pressed', String(added));
    button.querySelector('span:last-child').textContent = t(added ? 'zineRemove' : 'zineAdd');
  }

  function updateDialogRead() {
    const button = document.getElementById('next-dialog-read');
    const read = state.activeArticle ? isRead(state.activeArticle) : false;
    button.setAttribute('aria-pressed', String(read));
    button.querySelector('span:first-child').textContent = read ? '✓' : '○';
    button.querySelector('span:last-child').textContent = t(read ? 'markUnread' : 'markRead');
  }

  function showArticleTool(title, body) {
    const panel = document.getElementById('next-article-tool-panel');
    if (!panel) return null;
    panel.innerHTML = `
      <header>
        <h2>${escapeHtml(title)}</h2>
        <button type="button" data-action="article-tool-close" aria-label="${escapeHtml(t('closeTool'))}">×</button>
      </header>
      <div class="article-tool-panel__body">${body}</div>
    `;
    panel.hidden = false;
    panel.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    return panel;
  }

  function closeArticleTool() {
    stopArticlePodcast();
    const panel = document.getElementById('next-article-tool-panel');
    if (!panel) return;
    panel.hidden = true;
    panel.textContent = '';
  }

  function renderArticleSummary(length = 'standard') {
    const article = state.activeArticle;
    if (!article || !window.WRNSummaryCore?.summarizeText) return;
    const translation = translationFor(article);
    const text = translation?.fullContent ? translation.content : (article.content || article.intro);
    const summary = window.WRNSummaryCore.summarizeText(text, {
      title: translation?.title || article.title,
      length,
      language: translation?.fullContent
        ? state.language
        : String(article.language || article.lang || state.language).toLowerCase().split(/[-_]/)[0]
    });
    const lengthButtons = [
      ['short', 'summaryShort'],
      ['standard', 'summaryStandard'],
      ['detailed', 'summaryDetailed']
    ].map(([value, key]) => `<button type="button" class="${length === value ? 'active' : ''}" data-action="article-summary-length" data-value="${value}" aria-pressed="${length === value}">${escapeHtml(t(key))}</button>`).join('');
    const bullets = summary.bullets.length
      ? `<ul>${summary.bullets.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`
      : '';
    showArticleTool(t('summary'), `
      <div class="article-summary-lengths">${lengthButtons}</div>
      <p class="article-summary-lead">${escapeHtml(summary.lead || article.intro)}</p>
      ${bullets}
      <small>${escapeHtml(t('summaryLocal'))}</small>
    `);
  }

  function renderTranslationComparison() {
    const article = state.activeArticle;
    const translation = article ? translationFor(article) : null;
    if (!article || !translation) return;
    showArticleTool(t('translationCompare'), `
      <div class="translation-comparison">
        <section>
          <h3>${escapeHtml(t('originalVersion'))}</h3>
          <strong>${escapeHtml(article.title)}</strong>
          <p>${escapeHtml(article.content || article.intro)}</p>
        </section>
        <section>
          <h3>${escapeHtml(t('translatedVersion'))}</h3>
          <strong>${escapeHtml(translation.title || article.title)}</strong>
          <p>${escapeHtml(translation.fullContent ? translation.content : translation.intro)}</p>
        </section>
      </div>
    `);
  }

  function splitTextForArticleSpeech(value, maxLength = 280) {
    const text = core.text(value).replace(/https?:\/\/\S+/g, '');
    const sentences = text.match(/[^.!?…]+[.!?…]+|[^.!?…]+$/g) || [text];
    const chunks = [];
    let current = '';
    for (const sentenceValue of sentences) {
      const sentence = sentenceValue.trim();
      if (!sentence) continue;
      const words = sentence.split(/\s+/);
      for (const word of words) {
        if (current && current.length + word.length + 1 > maxLength) {
          chunks.push(current);
          current = word;
        } else {
          current += `${current ? ' ' : ''}${word}`;
        }
      }
    }
    if (current) chunks.push(current);
    return chunks;
  }

  function articleVoiceOptions() {
    const voices = window.speechSynthesis?.getVoices?.() || [];
    const prefix = articlePodcast.language.toLowerCase();
    return voices
      .slice()
      .sort((a, b) => {
        const aMatch = String(a.lang || '').toLowerCase().startsWith(prefix);
        const bMatch = String(b.lang || '').toLowerCase().startsWith(prefix);
        return Number(bMatch) - Number(aMatch) || Number(b.localService) - Number(a.localService) || a.name.localeCompare(b.name);
      })
      .map(voice => `<option value="${escapeHtml(voice.voiceURI || voice.name)}">${escapeHtml(`${voice.name} (${voice.lang})`)}</option>`)
      .join('');
  }

  function renderArticlePodcast() {
    const article = state.activeArticle;
    if (!article || !('speechSynthesis' in window)) {
      showToast(t('speechUnavailable'));
      return;
    }
    stopArticlePodcast();
    const translation = translationFor(article);
    articlePodcast.language = translation?.fullContent
      ? state.language
      : String(article.language || article.lang || state.language).toLowerCase().split(/[-_]/)[0];
    articlePodcast.chunks = splitTextForArticleSpeech(
      `${translation?.title || article.title}. ${translation?.fullContent ? translation.content : (article.content || article.intro)}`
    );
    showArticleTool(t('podcast'), `
      <p>${escapeHtml(t('deviceVoice'))}</p>
      <div class="article-podcast-settings">
        <label><span>${escapeHtml(t('voice'))}</span><select id="next-article-podcast-voice"><option value="">${escapeHtml(t('deviceVoice'))}</option>${articleVoiceOptions()}</select></label>
        <label><span>${escapeHtml(t('speed'))}</span><select id="next-article-podcast-speed"><option value=".85">0.85×</option><option value="1" selected>1×</option><option value="1.15">1.15×</option><option value="1.3">1.3×</option></select></label>
      </div>
      <div class="article-podcast-controls">
        <button type="button" class="primary-button" data-action="article-podcast-play">${escapeHtml(t('play'))}</button>
        <button type="button" class="secondary-button" data-action="article-podcast-stop">${escapeHtml(t('stop'))}</button>
        <span id="next-article-podcast-status">${escapeHtml(t('ready'))}</span>
      </div>
    `);
  }

  function updateArticlePodcastUi(status) {
    const button = document.querySelector('[data-action="article-podcast-play"]');
    const label = document.getElementById('next-article-podcast-status');
    if (button) button.textContent = t(articlePodcast.playing && !articlePodcast.paused ? 'pause' : 'play');
    if (label) {
      const progress = articlePodcast.chunks.length
        ? ` · ${Math.min(articlePodcast.index + 1, articlePodcast.chunks.length)}/${articlePodcast.chunks.length}`
        : '';
      label.textContent = `${status || t('ready')}${progress}`;
    }
  }

  function speakArticlePodcastChunk() {
    if (!articlePodcast.chunks.length || articlePodcast.index >= articlePodcast.chunks.length) {
      articlePodcast.playing = false;
      articlePodcast.paused = false;
      updateArticlePodcastUi(t('finished'));
      return;
    }
    const utterance = new SpeechSynthesisUtterance(articlePodcast.chunks[articlePodcast.index]);
    utterance.lang = articlePodcast.language;
    utterance.rate = Number(document.getElementById('next-article-podcast-speed')?.value || 1);
    const selectedVoice = document.getElementById('next-article-podcast-voice')?.value || '';
    if (selectedVoice) {
      utterance.voice = (window.speechSynthesis.getVoices() || [])
        .find(voice => (voice.voiceURI || voice.name) === selectedVoice) || null;
    }
    articlePodcast.utterance = utterance;
    articlePodcast.playing = true;
    articlePodcast.paused = false;
    utterance.onend = () => {
      if (articlePodcast.utterance !== utterance) return;
      articlePodcast.index += 1;
      articlePodcast.utterance = null;
      speakArticlePodcastChunk();
    };
    utterance.onerror = () => {
      if (articlePodcast.utterance !== utterance) return;
      stopArticlePodcast(false);
      updateArticlePodcastUi(t('speechUnavailable'));
    };
    updateArticlePodcastUi(t('listening'));
    window.speechSynthesis.speak(utterance);
  }

  function toggleArticlePodcast() {
    if (!('speechSynthesis' in window)) return showToast(t('speechUnavailable'));
    if (articlePodcast.playing && !articlePodcast.paused) {
      window.speechSynthesis.pause();
      articlePodcast.paused = true;
      updateArticlePodcastUi(t('pause'));
      return;
    }
    if (articlePodcast.playing && articlePodcast.paused) {
      window.speechSynthesis.resume();
      articlePodcast.paused = false;
      updateArticlePodcastUi(t('listening'));
      return;
    }
    speakArticlePodcastChunk();
  }

  function stopArticlePodcast(reset = true) {
    window.speechSynthesis?.cancel?.();
    articlePodcast.utterance = null;
    articlePodcast.playing = false;
    articlePodcast.paused = false;
    if (reset) articlePodcast.index = 0;
    updateArticlePodcastUi(t('ready'));
  }

  async function shareOpenArticle() {
    const article = state.activeArticle;
    if (!article?.link) return showToast(t('shareFailed'));
    try {
      if (navigator.share) {
        await navigator.share({ title: article.title, url: article.link });
        showToast(t('shared'));
        return;
      }
      await navigator.clipboard.writeText(article.link);
      showToast(t('linkCopied'));
    } catch (error) {
      if (error?.name !== 'AbortError') showToast(t('shareFailed'));
    }
  }

  async function translateOpenArticle() {
    const article = state.activeArticle;
    const button = document.getElementById('next-dialog-translate');
    if (!article || !window.WRNSharedTranslations?.request) return;
    if (translationFor(article)?.fullContent) {
      renderTranslationComparison();
      return;
    }
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');

    try {
      const result = await window.WRNSharedTranslations.request({
        title: article.title,
        text: article.content || article.intro,
        mode: 'title_and_text'
      });
      if (result?.error || !result?.text) throw new Error(result?.message || 'Translation failed');
      const parsed = core.splitTranslatedTeaser(result.text);
      const translated = {
        title: parsed.title || article.title,
        intro: core.excerpt(parsed.intro || article.intro, 230),
        content: parsed.intro || article.content || article.intro
      };
      storeTranslation(article, translated);
      document.getElementById('next-article-title').textContent = translated.title;
      const content = document.getElementById('next-article-content');
      content.querySelector('h1').textContent = translated.title;
      content.querySelector('.article-intro').textContent = translated.intro;
      content.querySelector('.article-body').textContent = translated.content;
      renderTranslationComparison();
      showToast(t('translatedTitle'));
    } catch (error) {
      console.warn('Article translation failed', error);
      showToast(t('translationFailed'));
    } finally {
      button.disabled = false;
      button.removeAttribute('aria-busy');
    }
  }

  function openBriefing() {
    state.briefing = {
      step: 1,
      regions: [...(state.preferences.regions || [])],
      topics: [...(state.preferences.topics || [])],
      language: state.preferences.preferredLanguage || state.language,
      amount: state.preferences.briefingAmount || 5,
      items: []
    };
    renderBriefingStep();
    briefingDialog.showModal();
  }

  function briefingStepLabel() {
    return `${t('step')} ${state.briefing.step} ${t('of')} 3`;
  }

  function briefingLanguageOptions() {
    const labels = {
      de:'Deutsch', en:'English', es:'Español', fr:'Français', it:'Italiano',
      pt:'Português', ru:'Русский', el:'Ελληνικά', tr:'Türkçe'
    };
    return Object.entries(labels).map(([value, label]) =>
      `<option value="${value}"${state.briefing.language === value ? ' selected' : ''}>${escapeHtml(label)}</option>`
    ).join('');
  }

  function collectBriefingStep() {
    if (state.briefing.step === 1) {
      state.briefing.regions = [...briefingDialog.querySelectorAll('input[name="briefing-region"]:checked')].map(input => input.value);
      state.briefing.topics = [...briefingDialog.querySelectorAll('input[name="briefing-topic"]:checked')].map(input => input.value);
    }
    if (state.briefing.step === 2) {
      state.briefing.language = document.getElementById('next-briefing-language')?.value || state.language;
      state.briefing.amount = Number(briefingDialog.querySelector('input[name="briefing-amount"]:checked')?.value || 5);
    }
  }

  function buildBriefingItems() {
    const preferences = {
      regions: state.briefing.regions,
      topics: state.briefing.topics,
      sources: [...(state.preferences.sources || [])],
      blockedSources: [...(state.preferences.blockedSources || [])]
    };
    const candidates = state.briefing.regions.length || state.briefing.topics.length
      ? state.articles.filter(article => core.matchesPreferences(article, preferences))
      : state.articles;
    state.briefing.items = core.balanceBySource(candidates, state.briefing.amount, 2);
  }

  function renderBriefingStep() {
    document.getElementById('next-briefing-step-label').textContent = briefingStepLabel();
    const content = document.getElementById('next-briefing-content');
    const actions = document.getElementById('next-briefing-actions');

    if (state.briefing.step === 1) {
      const regions = new Set(state.briefing.regions);
      const topics = new Set(state.briefing.topics);
      content.innerHTML = `
        <p class="media-privacy">🔒 ${escapeHtml(t('briefingLocal'))}</p>
        <p>${escapeHtml(t('briefingSetup'))}</p>
        <section class="briefing-section">
          <h3>${escapeHtml(t('chooseRegions'))}</h3>
          <div class="choice-grid">${state.facets.regions.map(value => choiceMarkup('briefing-region', value, regions.has(value))).join('')}</div>
        </section>
        <section class="briefing-section">
          <h3>${escapeHtml(t('chooseTopics'))}</h3>
          <div class="choice-grid">${state.facets.topics.slice(0, 28).map(value => choiceMarkup('briefing-topic', value, topics.has(value))).join('')}</div>
        </section>`;
      actions.innerHTML = `<button class="secondary-button" type="button" data-briefing-close>${escapeHtml(t('cancel'))}</button><button class="primary-button" type="button" data-action="briefing-next">${escapeHtml(t('next'))}</button>`;
      return;
    }

    if (state.briefing.step === 2) {
      content.innerHTML = `
        <section class="briefing-section">
          <h3>${escapeHtml(t('language'))}</h3>
          <select class="briefing-language" id="next-briefing-language">${briefingLanguageOptions()}</select>
        </section>
        <section class="briefing-section">
          <h3>${escapeHtml(t('briefingAmount'))}</h3>
          <div class="briefing-lengths">
            ${[3, 5, 8].map(amount => `<label><input type="radio" name="briefing-amount" value="${amount}"${state.briefing.amount === amount ? ' checked' : ''}><strong>${amount}</strong><span>${escapeHtml(t('briefingItems'))}</span></label>`).join('')}
          </div>
        </section>`;
      actions.innerHTML = `<button class="secondary-button" type="button" data-action="briefing-back">${escapeHtml(t('back'))}</button><button class="primary-button" type="button" data-action="briefing-next">${escapeHtml(t('next'))}</button>`;
      return;
    }

    buildBriefingItems();
    content.innerHTML = state.briefing.items.length
      ? `<ol class="briefing-preview">${state.briefing.items.map((article, index) => `<li><b>${index + 1}</b><div><strong>${escapeHtml(translationFor(article)?.title || article.title)}</strong><small>${escapeHtml(article.source)} · ${escapeHtml(mediaDescription(translationFor(article)?.intro || article.intro))}</small></div></li>`).join('')}</ol>`
      : `<div class="empty-state compact"><strong>${escapeHtml(t('noBriefing'))}</strong></div>`;
    actions.innerHTML = `<button class="secondary-button" type="button" data-action="briefing-back">${escapeHtml(t('back'))}</button><button class="secondary-button" type="button" data-action="briefing-stop">${escapeHtml(t('stop'))}</button><button class="primary-button" type="button" data-action="briefing-listen"${state.briefing.items.length ? '' : ' disabled'}>${escapeHtml(t('listen'))}</button><button class="primary-button" type="button" data-briefing-close>${escapeHtml(t('done'))}</button>`;
  }

  function speakBriefing() {
    if (!('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined') {
      showToast(t('speechUnavailable'));
      return;
    }
    window.speechSynthesis.cancel();
    const speech = state.briefing.items.map((article, index) =>
      `${index + 1}. ${translationFor(article)?.title || article.title}. ${translationFor(article)?.intro || article.intro}`
    ).join(' ');
    const utterance = new SpeechSynthesisUtterance(speech);
    const languageCodes = { de:'de-DE', en:'en-US', es:'es-ES', fr:'fr-FR', it:'it-IT', pt:'pt-PT', ru:'ru-RU', el:'el-GR', tr:'tr-TR' };
    utterance.lang = languageCodes[state.briefing.language] || state.briefing.language;
    utterance.rate = 1;
    window.speechSynthesis.speak(utterance);
  }

  function openPreferences() {
    const selectedRegions = new Set(state.preferences.regions || []);
    const selectedTopics = new Set(state.preferences.topics || []);
    const followedSources = new Set(state.preferences.sources || []);
    const blockedSources = new Set(state.preferences.blockedSources || []);
    const selectedPrisoners = new Set(state.preferences.prisonerIds || []);
    const selectedDevelopments = new Set(Array.isArray(state.developmentWatch) ? state.developmentWatch : []);
    const topics = [...state.facets.topics].sort((a, b) => a.localeCompare(b, state.language));
    const sources = [...state.facets.sources].sort((a, b) => a.localeCompare(b, state.language));
    const developments = specialty.developmentClusters(
      state.articles,
      window.WRNStoriesCore,
      { days: 30, threshold: 0.5 }
    );

    document.getElementById('next-region-choices').innerHTML = [...state.facets.regions]
      .sort((a, b) => a.localeCompare(b, state.language)).map(value =>
      choiceMarkup('region', value, selectedRegions.has(value))
    ).join('');
    document.getElementById('next-topic-choices').innerHTML = topics.map(value =>
      choiceMarkup('topic', value, selectedTopics.has(value))
    ).join('');
    document.getElementById('next-source-choices').innerHTML = sources.map(value =>
      sourcePreferenceMarkup(
        value,
        followedSources.has(value) ? 'follow' : blockedSources.has(value) ? 'hide' : 'neutral'
      )
    ).join('');
    document.getElementById('next-prisoner-choices').innerHTML = (state.prisonerData.profiles || [])
      .filter(specialty.isCurrentProfile)
      .map(profile => choiceMarkup('prisoner', profile.id, selectedPrisoners.has(profile.id), profile.publicName))
      .join('') || `<small>${escapeHtml(t('noWatchOptions'))}</small>`;
    document.getElementById('next-development-choices').innerHTML = developments
      .map(story => choiceMarkup('development', story.id, selectedDevelopments.has(story.id), story.title))
      .join('') || `<small>${escapeHtml(t('noWatchOptions'))}</small>`;
    document.getElementById('next-preference-language').value = state.preferences.preferredLanguage || state.language;
    document.getElementById('next-preference-briefing-length').innerHTML = [3, 5, 8].map(amount =>
      `<label><input type="radio" name="preference-briefing-amount" value="${amount}"${state.preferences.briefingAmount === amount ? ' checked' : ''}><strong>${amount}</strong><span>${escapeHtml(t('briefingItems'))}</span></label>`
    ).join('');
    document.getElementById('next-preference-source-search').value = '';
    filterPreferenceSources('');
    preferencesDialog.showModal();
  }

  function choiceMarkup(kind, value, selected, label = value) {
    return `<label class="choice-chip"><input type="checkbox" name="${escapeHtml(kind)}" value="${escapeHtml(value)}"${selected ? ' checked' : ''}><span>${escapeHtml(label)}</span></label>`;
  }

  function sourcePreferenceMarkup(source, value) {
    return `<label class="source-preference-row" data-source-row data-source-search="${escapeHtml(source.toLocaleLowerCase())}">
      <span>${escapeHtml(source)}</span>
      <select data-source-preference="${escapeHtml(source)}" aria-label="${escapeHtml(`${source}: ${t('chooseSources')}`)}">
        <option value="neutral"${value === 'neutral' ? ' selected' : ''}>${escapeHtml(t('sourceNeutral'))}</option>
        <option value="follow"${value === 'follow' ? ' selected' : ''}>${escapeHtml(t('sourceFollow'))}</option>
        <option value="hide"${value === 'hide' ? ' selected' : ''}>${escapeHtml(t('sourceHide'))}</option>
      </select>
    </label>`;
  }

  function filterPreferenceSources(query) {
    const normalized = String(query || '').trim().toLocaleLowerCase();
    preferencesDialog.querySelectorAll('[data-source-row]').forEach(row => {
      row.hidden = Boolean(normalized && !row.dataset.sourceSearch.includes(normalized));
    });
  }

  function savePreferences() {
    const sourcePreferences = [...preferencesDialog.querySelectorAll('[data-source-preference]')];
    const selectedLanguage = supportedLanguage(document.getElementById('next-preference-language').value);
    state.preferences = {
      ...normalizedPreferences(state.preferences),
      regions: [...preferencesDialog.querySelectorAll('input[name="region"]:checked')].map(input => input.value),
      topics: [...preferencesDialog.querySelectorAll('input[name="topic"]:checked')].map(input => input.value),
      sources: sourcePreferences.filter(select => select.value === 'follow').map(select => select.dataset.sourcePreference),
      blockedSources: sourcePreferences.filter(select => select.value === 'hide').map(select => select.dataset.sourcePreference),
      prisonerIds: [...preferencesDialog.querySelectorAll('input[name="prisoner"]:checked')].map(input => input.value),
      preferredLanguage: selectedLanguage,
      briefingAmount: Number(preferencesDialog.querySelector('input[name="preference-briefing-amount"]:checked')?.value || 5)
    };
    state.developmentWatch = [...preferencesDialog.querySelectorAll('input[name="development"]:checked')].map(input => input.value);
    writeJson(PREFS_KEY, state.preferences);
    writeJson(STORY_WATCH_KEY, state.developmentWatch);
    state.language = selectedLanguage;
    localStorage.setItem(LANGUAGE_KEY, state.language);
    applyLanguage();
    window.dispatchEvent(new CustomEvent('wrnlanguagechange', { detail: { language: state.language } }));
    preferencesDialog.close();
    state.view = 'following';
    render();
    showToast(t('selectionSaved'));
  }

  function changeView(view) {
    if (!['home', 'following', 'discover', 'events', 'lexicon', 'prisoners', 'developments', 'media', 'saved'].includes(view)) return;
    state.view = view;
    render();
    document.getElementById('next-main').focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function bindEvents() {
    document.addEventListener('click', event => {
      const target = event.target.closest('[data-view-target], [data-action], [data-filter-kind], [data-menu-close], [data-briefing-close]');
      if (!target) return;

      if (target.hasAttribute('data-menu-close')) {
        menuDialog.close();
        return;
      }

      if (target.hasAttribute('data-briefing-close')) {
        window.speechSynthesis?.cancel?.();
        briefingDialog.close();
        return;
      }

      if (target.dataset.viewTarget) {
        if (menuDialog.open) menuDialog.close();
        changeView(target.dataset.viewTarget);
        return;
      }

      if (target.dataset.filterKind) {
        state.discover[target.dataset.filterKind] = target.dataset.filterValue;
        state.discover.limit = 24;
        renderDiscover();
        return;
      }

      const action = target.dataset.action;
      const article = Number.isInteger(Number(target.dataset.index))
        ? state.cardArticles[Number(target.dataset.index)]
        : null;
      if (action === 'open' && article) openArticle(article);
      if (action === 'translate' && article) {
        translateTeaser(article, target, target.closest('.news-card'));
      }
      if (action === 'save' && article) {
        const saved = toggleSaved(article);
        target.setAttribute('aria-pressed', String(saved));
        target.setAttribute('aria-label', saved ? t('removeSaved') : t('save'));
        target.textContent = saved ? '★' : '☆';
        if (state.view === 'saved' && !saved) renderSaved();
      }
      if (action === 'open-archive') {
        state.discover.period = ['7d', '30d', 'all'].includes(target.dataset.period)
          ? target.dataset.period
          : 'current';
        state.discover.limit = 24;
        changeView('discover');
      }
      if (action === 'discover-period') {
        state.discover.period = ['current', '7d', '30d', 'all'].includes(target.dataset.value)
          ? target.dataset.value
          : 'current';
        state.discover.limit = 24;
        renderDiscover();
      }
      if (action === 'discover-more') {
        state.discover.limit += 24;
        renderDiscover();
      }
      if (action === 'article-summary') renderArticleSummary();
      if (action === 'article-summary-length') renderArticleSummary(target.dataset.value || 'standard');
      if (action === 'article-translate') translateOpenArticle();
      if (action === 'article-podcast') renderArticlePodcast();
      if (action === 'article-podcast-play') toggleArticlePodcast();
      if (action === 'article-podcast-stop') stopArticlePodcast();
      if (action === 'article-zine' && state.activeArticle) {
        toggleZineArticle(state.activeArticle);
        updateDialogZine();
      }
      if (action === 'article-read' && state.activeArticle) {
        toggleRead(state.activeArticle);
        updateDialogRead();
      }
      if (action === 'article-share') shareOpenArticle();
      if (action === 'article-tool-close') closeArticleTool();
      if (action === 'preferences') {
        if (menuDialog.open) menuDialog.close();
        openPreferences();
      }
      if (action === 'retry') loadData();
      if (action === 'event-period') {
        state.eventFilter.archived = target.dataset.value === 'archive';
        renderEvents();
      }
      if (action === 'lexicon-section') {
        state.lexicon.section = target.dataset.value || 'all';
        renderLexicon();
      }
      if (action === 'lexicon-download') window.WRNLexicon184?.exportData?.();
      if (action === 'letter') {
        window.WRNPrisonerSolidarity190?.loadData?.()
          .then(() => window.WRNPrisonerSolidarity190.openWorkshop(target.dataset.profileId))
          .catch(error => {
            console.warn('Letter workshop unavailable', error);
            showToast(t('loadError'));
          });
      }
      if (action === 'development-filter') {
        state.developmentsWatchedOnly = target.dataset.value === 'watched';
        renderDevelopments();
      }
      if (action === 'watch-development') {
        const values = new Set(Array.isArray(state.developmentWatch) ? state.developmentWatch : []);
        if (values.has(target.dataset.storyId)) values.delete(target.dataset.storyId);
        else values.add(target.dataset.storyId);
        state.developmentWatch = [...values];
        writeJson(STORY_WATCH_KEY, state.developmentWatch);
        renderDevelopments();
      }
      if (action === 'media-section') {
        state.media.section = target.dataset.value || 'video';
        state.media.query = '';
        state.media.region = 'all';
        state.media.category = 'all';
        renderMedia();
      }
      if (action === 'media-video-mode') {
        state.media.videoMode = target.dataset.value === 'information' ? 'information' : 'current';
        renderMedia();
      }
      if (action === 'zine-remove') removeZineArticle(target.dataset.zineKey || '');
      if (action === 'zine-clear' && zineArticles().length && window.confirm(t('zineClearConfirm'))) {
        storeZineArticles([]);
        renderMedia();
      }
      if (action === 'briefing-open') {
        if (menuDialog.open) menuDialog.close();
        openBriefing();
      }
      if (action === 'briefing-next') {
        collectBriefingStep();
        state.briefing.step = Math.min(3, state.briefing.step + 1);
        renderBriefingStep();
      }
      if (action === 'briefing-back') {
        collectBriefingStep();
        state.briefing.step = Math.max(1, state.briefing.step - 1);
        renderBriefingStep();
      }
      if (action === 'briefing-listen') speakBriefing();
      if (action === 'briefing-stop') window.speechSynthesis?.cancel?.();
    });

    document.getElementById('next-menu-toggle').addEventListener('click', () => menuDialog.showModal());

    document.getElementById('next-search-toggle').addEventListener('click', event => {
      const open = searchPanel.hidden;
      searchPanel.hidden = !open;
      event.currentTarget.setAttribute('aria-expanded', String(open));
      if (open) searchInput.focus();
    });

    document.getElementById('next-global-search').addEventListener('submit', event => {
      event.preventDefault();
      state.discover.query = searchInput.value.trim();
      state.discover.period = 'all';
      state.discover.limit = 24;
      searchPanel.hidden = true;
      document.getElementById('next-search-toggle').setAttribute('aria-expanded', 'false');
      changeView('discover');
    });

    viewRoot.addEventListener('input', event => {
      const id = event.target.id;
      if (!['next-discover-query', 'next-event-query', 'next-lexicon-query', 'next-media-query'].includes(id)) return;
      if (id === 'next-discover-query') state.discover.query = event.target.value;
      if (id === 'next-event-query') state.eventFilter.query = event.target.value;
      if (id === 'next-lexicon-query') state.lexicon.query = event.target.value;
      if (id === 'next-media-query') state.media.query = event.target.value;
      window.clearTimeout(bindEvents.searchTimer);
      if (id === 'next-discover-query') state.discover.limit = 24;
      bindEvents.searchTimer = window.setTimeout(() => {
        if (id === 'next-event-query') renderEvents();
        else if (id === 'next-lexicon-query') renderLexicon();
        else if (id === 'next-media-query') renderMedia();
        else renderDiscover();
        const replacement = document.getElementById(id);
        replacement?.focus();
        replacement?.setSelectionRange(replacement.value.length, replacement.value.length);
      }, 180);
    });

    viewRoot.addEventListener('change', event => {
      if (event.target.id === 'next-event-country') {
        state.eventFilter.country = event.target.value;
        renderEvents();
      }
      if (event.target.id === 'next-media-region') {
        state.media.region = event.target.value;
        renderMedia();
      }
      if (event.target.id === 'next-media-category') {
        state.media.category = event.target.value;
        renderMedia();
      }
    });

    viewRoot.addEventListener('play', event => {
      if (!(event.target instanceof HTMLMediaElement)) return;
      viewRoot.querySelectorAll('audio, video').forEach(player => {
        if (player !== event.target && !player.paused) player.pause();
      });
    }, true);

    languageSelect.addEventListener('change', () => {
      state.language = supportedLanguage(languageSelect.value);
      window.currentLang = state.language;
      localStorage.setItem(LANGUAGE_KEY, state.language);
      applyLanguage();
      render();
      window.dispatchEvent(new CustomEvent('wrnlanguagechange', { detail: { language: state.language } }));
    });
    [themeSelect, fontSizeSelect, densitySelect].forEach(select => {
      select.addEventListener('change', saveUiSettings);
    });
    systemTheme?.addEventListener?.('change', () => {
      if (state.ui.theme === 'system') applyUiSettings();
    });

    document.querySelector('[data-dialog-close]').addEventListener('click', () => {
      stopArticlePodcast();
      articleDialog.close();
    });
    document.getElementById('next-dialog-save').addEventListener('click', () => {
      if (!state.activeArticle) return;
      toggleSaved(state.activeArticle);
      updateDialogSave();
    });
    document.getElementById('next-save-preferences').addEventListener('click', event => {
      event.preventDefault();
      savePreferences();
    });
    document.getElementById('next-preference-source-search').addEventListener('input', event => {
      filterPreferenceSources(event.target.value);
    });

    articleDialog.addEventListener('click', event => {
      if (event.target === articleDialog) {
        stopArticlePodcast();
        articleDialog.close();
      }
    });
    articleDialog.addEventListener('close', () => stopArticlePodcast());
    preferencesDialog.addEventListener('click', event => {
      if (event.target === preferencesDialog) preferencesDialog.close();
    });
    menuDialog.addEventListener('click', event => {
      if (event.target === menuDialog) menuDialog.close();
    });
    briefingDialog.addEventListener('click', event => {
      if (event.target === briefingDialog) {
        window.speechSynthesis?.cancel?.();
        briefingDialog.close();
      }
    });
  }

  async function fetchJson(url) {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
    return response.json();
  }

  async function loadSpecialtyData() {
    state.lexiconSnapshot = window.WRNLexicon184?.snapshot?.() || { terms: [], sources: [] };
    const [eventsResult, prisonersResult, podcastsResult, generatedResult, radioResult, radioHealthResult] = await Promise.allSettled([
      fetchJson('events-feed.json'),
      fetchJson('prisoner-solidarity.json'),
      fetchJson('podcasts.json'),
      fetchJson('generated-podcasts.json'),
      fetchJson('radio-stations.json'),
      fetchJson('radio-health.json')
    ]);
    if (eventsResult.status === 'fulfilled') {
      state.events = specialty.collapseRecurringEvents(eventsResult.value);
    } else {
      console.warn('Events unavailable in preview', eventsResult.reason);
      state.events = [];
    }
    if (prisonersResult.status === 'fulfilled' && Array.isArray(prisonersResult.value?.profiles)) {
      state.prisonerData = prisonersResult.value;
    } else {
      console.warn('Prisoner solidarity data unavailable in preview', prisonersResult.reason);
      state.prisonerData = { profiles: [], sources: [] };
    }
    state.podcasts = podcastsResult.status === 'fulfilled' && Array.isArray(podcastsResult.value)
      ? podcastsResult.value.map(media.normalizePodcast).sort((a, b) => b.timestamp - a.timestamp)
      : [];
    state.generatedPodcasts = generatedResult.status === 'fulfilled' && Array.isArray(generatedResult.value)
      ? generatedResult.value.map(media.normalizePodcast).sort((a, b) => b.timestamp - a.timestamp)
      : [];
    const radioHealth = radioHealthResult.status === 'fulfilled' && radioHealthResult.value
      ? radioHealthResult.value
      : {};
    state.radioStations = radioResult.status === 'fulfilled' && Array.isArray(radioResult.value)
      ? radioResult.value.map(item => {
        const health = radioHealth[item.id] || {};
        return media.normalizeRadio({
          ...item,
          streamCandidates: health.ok && health.workingStream ? [health.workingStream] : [],
          healthStatus: health.status || item.healthStatus
        });
      })
      : [];
  }

  async function loadData() {
    loading.hidden = false;
    viewRoot.innerHTML = '';
    const candidates = [
      window.WRN_CONFIG?.dataUrls?.newsFeed,
      'news-feed.json',
      window.WRN_CONFIG?.dataUrls?.news,
      'news.json'
    ].filter(Boolean);
    let lastError = null;

    for (const url of [...new Set(candidates)]) {
      try {
        const payload = await fetchJson(url);
        const articles = core.normalizeArticles(payload);
        if (!articles.length) throw new Error(`No articles in ${url}`);
        state.articles = articles;
        state.facets = core.collectFacets(articles);
        await loadSpecialtyData();
        render();
        return;
      } catch (error) {
        lastError = error;
        console.warn('News App 2 data source failed', url, error);
      }
    }

    console.error('News App 2 could not load data', lastError);
    loading.hidden = true;
    renderError();
  }

  applyUiSettings();
  applyLanguage();
  bindEvents();
  loadData();
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('./news-app-2-sw.js', {
        scope: './next.html',
        updateViaCache: 'none'
      }).catch(error => console.warn('Preview offline cache unavailable', error));
    }, { once: true });
  }
})();
