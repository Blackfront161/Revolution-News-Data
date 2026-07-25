/* World Revolution News 1.8.4 – movement glossary */
'use strict';

(() => {
  if (window.WRNLexicon184) return;

  const UI = {
    de: {
      nav: 'Lexikon',
      building: 'Im Aufbau',
      title: 'Begriffe in Bewegung',
      lead: 'Kurze, einordnende Erklärungen zu Begriffen aus anarchistischen, antiautoritären und linksrevolutionären Bewegungen.',
      note: 'Dieses Lexikon erhebt keinen Anspruch auf Vollständigkeit. Begriffe entstehen in politischen Kämpfen, verändern sich und werden in unterschiedlichen Strömungen verschieden verwendet. Die Texte sind Einladungen zur gemeinsamen Klärung – keine endgültigen Festlegungen.',
      search: 'Begriffe, alternative Namen oder Inhalte durchsuchen …',
      noResults: 'Für diese Suche wurde kein Begriff gefunden.',
      terms: 'Begriffe',
      meaning: 'Kurz erklärt',
      practice: 'In der Praxis',
      debate: 'Unterschiedliche Perspektiven',
      related: 'Verwandte Begriffe',
      sources: 'Quellen und Weiterlesen',
      sourceOpen: 'Quelle öffnen',
      pdfOpen: 'PDF öffnen / herunterladen',
      downloadLexicon: 'WRN-Lexikon als JSON sichern',
      downloadHint: 'Die WRN-Kurztexte sind eigene redaktionelle Zusammenfassungen. Externe Texte werden nicht kopiert. Offizielle Downloads öffnen direkt beim jeweiligen Projekt.',
      editorialState: 'Redaktioneller Entwurf · Rückmeldungen willkommen',
      feedback: 'Ergänzung oder Korrektur vorschlagen',
      fallback: 'Die redaktionellen Definitionen sind zunächst auf Deutsch und Englisch verfügbar. Angezeigt wird die englische Fassung.',
      sections: {
        basics: 'Grundlagen',
        organisation: 'Organisierung',
        justice: 'Gerechtigkeit & Fürsorge',
        struggles: 'Kämpfe & Kritik',
        all: 'Alle Begriffe',
        sources: 'Quellen'
      }
    },
    en: {
      nav: 'Glossary',
      building: 'Under construction',
      title: 'Words in motion',
      lead: 'Short, contextual explanations of terms used in anarchist, anti-authoritarian and revolutionary left movements.',
      note: 'This glossary does not claim to be complete. Terms emerge through political struggle, change over time and are used differently across tendencies. These texts invite shared clarification; they are not final rulings.',
      search: 'Search terms, alternative names or descriptions …',
      noResults: 'No term matches this search.',
      terms: 'Terms',
      meaning: 'In brief',
      practice: 'In practice',
      debate: 'Different perspectives',
      related: 'Related terms',
      sources: 'Sources and further reading',
      sourceOpen: 'Open source',
      pdfOpen: 'Open / download PDF',
      downloadLexicon: 'Save WRN glossary as JSON',
      downloadHint: 'WRN entries are original editorial summaries. External texts are not copied. Official downloads open directly at the respective project.',
      editorialState: 'Editorial draft · feedback welcome',
      feedback: 'Suggest an addition or correction',
      fallback: '',
      sections: {
        basics: 'Foundations',
        organisation: 'Organising',
        justice: 'Justice & care',
        struggles: 'Struggles & critique',
        all: 'All terms',
        sources: 'Sources'
      }
    },
    es: {
      nav: 'Glosario', building: 'En desarrollo', title: 'Palabras en movimiento',
      lead: 'Explicaciones breves y contextualizadas de términos de movimientos anarquistas, antiautoritarios y de la izquierda revolucionaria.',
      note: 'Este glosario no pretende ser completo. Los términos surgen en las luchas políticas, cambian y se usan de forma diferente según las corrientes.',
      search: 'Buscar términos, nombres alternativos o contenidos …', noResults: 'No se encontró ningún término.',
      terms: 'Términos', meaning: 'En breve', practice: 'En la práctica', debate: 'Perspectivas diferentes',
      related: 'Términos relacionados', sources: 'Fuentes y lecturas', sourceOpen: 'Abrir fuente',
      pdfOpen: 'Abrir / descargar PDF', downloadLexicon: 'Guardar glosario WRN como JSON',
      downloadHint: 'Los textos breves de WRN son resúmenes editoriales propios. Los textos externos no se copian.',
      editorialState: 'Borrador editorial · comentarios bienvenidos', feedback: 'Proponer una adición o corrección',
      fallback: 'Las definiciones editoriales están disponibles inicialmente en alemán e inglés. Se muestra la versión inglesa.',
      sections: { basics:'Fundamentos', organisation:'Organización', justice:'Justicia y cuidados', struggles:'Luchas y crítica', all:'Todos', sources:'Fuentes' }
    },
    fr: {
      nav: 'Lexique', building: 'En construction', title: 'Des mots en mouvement',
      lead: 'Des explications courtes et contextualisées de termes issus des mouvements anarchistes, antiautoritaires et de la gauche révolutionnaire.',
      note: 'Ce lexique ne prétend pas être complet. Les termes naissent dans les luttes politiques, évoluent et sont employés différemment selon les courants.',
      search: 'Rechercher des termes, variantes ou contenus …', noResults: 'Aucun terme trouvé.',
      terms: 'Termes', meaning: 'En bref', practice: 'Dans la pratique', debate: 'Perspectives différentes',
      related: 'Termes liés', sources: 'Sources et lectures', sourceOpen: 'Ouvrir la source',
      pdfOpen: 'Ouvrir / télécharger le PDF', downloadLexicon: 'Enregistrer le lexique WRN en JSON',
      downloadHint: 'Les textes courts de WRN sont des synthèses éditoriales originales. Les textes externes ne sont pas copiés.',
      editorialState: 'Projet éditorial · retours bienvenus', feedback: 'Proposer un ajout ou une correction',
      fallback: 'Les définitions éditoriales sont d’abord disponibles en allemand et en anglais. La version anglaise est affichée.',
      sections: { basics:'Fondements', organisation:'Organisation', justice:'Justice et soin', struggles:'Luttes et critique', all:'Tous les termes', sources:'Sources' }
    },
    it: {
      nav: 'Glossario', building: 'In costruzione', title: 'Parole in movimento',
      lead: 'Spiegazioni brevi e contestualizzate di termini dei movimenti anarchici, antiautoritari e della sinistra rivoluzionaria.',
      note: 'Questo glossario non pretende di essere completo. I termini nascono nelle lotte politiche, cambiano e sono usati diversamente nelle varie correnti.',
      search: 'Cerca termini, nomi alternativi o contenuti …', noResults: 'Nessun termine trovato.',
      terms: 'Termini', meaning: 'In breve', practice: 'Nella pratica', debate: 'Prospettive diverse',
      related: 'Termini collegati', sources: 'Fonti e letture', sourceOpen: 'Apri fonte',
      pdfOpen: 'Apri / scarica PDF', downloadLexicon: 'Salva il glossario WRN come JSON',
      downloadHint: 'I testi brevi WRN sono sintesi editoriali originali. I testi esterni non vengono copiati.',
      editorialState: 'Bozza editoriale · commenti benvenuti', feedback: 'Proponi un’aggiunta o una correzione',
      fallback: 'Le definizioni editoriali sono inizialmente disponibili in tedesco e inglese. Viene mostrata la versione inglese.',
      sections: { basics:'Fondamenti', organisation:'Organizzazione', justice:'Giustizia e cura', struggles:'Lotte e critica', all:'Tutti i termini', sources:'Fonti' }
    },
    pt: {
      nav: 'Glossário', building: 'Em construção', title: 'Palavras em movimento',
      lead: 'Explicações breves e contextualizadas de termos de movimentos anarquistas, antiautoritários e da esquerda revolucionária.',
      note: 'Este glossário não pretende ser completo. Os termos nascem nas lutas políticas, mudam e são usados de forma diferente entre correntes.',
      search: 'Pesquisar termos, nomes alternativos ou conteúdos …', noResults: 'Nenhum termo encontrado.',
      terms: 'Termos', meaning: 'Em resumo', practice: 'Na prática', debate: 'Perspetivas diferentes',
      related: 'Termos relacionados', sources: 'Fontes e leituras', sourceOpen: 'Abrir fonte',
      pdfOpen: 'Abrir / descarregar PDF', downloadLexicon: 'Guardar glossário WRN em JSON',
      downloadHint: 'Os textos breves da WRN são resumos editoriais próprios. Textos externos não são copiados.',
      editorialState: 'Rascunho editorial · comentários bem-vindos', feedback: 'Sugerir adição ou correção',
      fallback: 'As definições editoriais estão inicialmente disponíveis em alemão e inglês. É apresentada a versão inglesa.',
      sections: { basics:'Fundamentos', organisation:'Organização', justice:'Justiça e cuidado', struggles:'Lutas e crítica', all:'Todos os termos', sources:'Fontes' }
    },
    ru: {
      nav: 'Словарь', building: 'В разработке', title: 'Слова в движении',
      lead: 'Краткие контекстные объяснения терминов анархистских, антиавторитарных и левореволюционных движений.',
      note: 'Этот словарь не претендует на полноту. Термины рождаются в политической борьбе, меняются и по-разному используются различными течениями.',
      search: 'Поиск терминов, вариантов названий или описаний …', noResults: 'Термин не найден.',
      terms: 'Термины', meaning: 'Кратко', practice: 'На практике', debate: 'Разные точки зрения',
      related: 'Связанные термины', sources: 'Источники и материалы', sourceOpen: 'Открыть источник',
      pdfOpen: 'Открыть / скачать PDF', downloadLexicon: 'Сохранить словарь WRN в JSON',
      downloadHint: 'Краткие тексты WRN — собственные редакционные резюме. Внешние тексты не копируются.',
      editorialState: 'Редакционный черновик · отзывы приветствуются', feedback: 'Предложить дополнение или исправление',
      fallback: 'Редакционные определения пока доступны на немецком и английском. Показана английская версия.',
      sections: { basics:'Основы', organisation:'Организация', justice:'Справедливость и забота', struggles:'Борьба и критика', all:'Все термины', sources:'Источники' }
    },
    el: {
      nav: 'Γλωσσάρι', building: 'Υπό ανάπτυξη', title: 'Λέξεις σε κίνηση',
      lead: 'Σύντομες, πλαισιωμένες εξηγήσεις όρων από αναρχικά, αντιεξουσιαστικά και επαναστατικά αριστερά κινήματα.',
      note: 'Το γλωσσάρι δεν ισχυρίζεται ότι είναι πλήρες. Οι όροι γεννιούνται σε πολιτικούς αγώνες, αλλάζουν και χρησιμοποιούνται διαφορετικά.',
      search: 'Αναζήτηση όρων, εναλλακτικών ονομάτων ή περιεχομένου …', noResults: 'Δεν βρέθηκε όρος.',
      terms: 'Όροι', meaning: 'Συνοπτικά', practice: 'Στην πράξη', debate: 'Διαφορετικές οπτικές',
      related: 'Σχετικοί όροι', sources: 'Πηγές και ανάγνωση', sourceOpen: 'Άνοιγμα πηγής',
      pdfOpen: 'Άνοιγμα / λήψη PDF', downloadLexicon: 'Αποθήκευση γλωσσαρίου WRN ως JSON',
      downloadHint: 'Τα σύντομα κείμενα του WRN είναι πρωτότυπες συντακτικές περιλήψεις. Τα εξωτερικά κείμενα δεν αντιγράφονται.',
      editorialState: 'Συντακτικό προσχέδιο · τα σχόλια είναι ευπρόσδεκτα', feedback: 'Πρόταση προσθήκης ή διόρθωσης',
      fallback: 'Οι συντακτικοί ορισμοί είναι αρχικά διαθέσιμοι στα γερμανικά και αγγλικά. Εμφανίζεται η αγγλική έκδοση.',
      sections: { basics:'Βάσεις', organisation:'Οργάνωση', justice:'Δικαιοσύνη και φροντίδα', struggles:'Αγώνες και κριτική', all:'Όλοι οι όροι', sources:'Πηγές' }
    },
    tr: {
      nav: 'Sözlük', building: 'Yapım aşamasında', title: 'Hareket hâlindeki sözcükler',
      lead: 'Anarşist, otorite karşıtı ve devrimci sol hareketlerde kullanılan terimlere ilişkin kısa ve bağlamsal açıklamalar.',
      note: 'Bu sözlük eksiksiz olma iddiasında değildir. Kavramlar siyasi mücadelelerde doğar, değişir ve farklı akımlarda farklı kullanılır.',
      search: 'Terim, alternatif ad veya açıklama ara …', noResults: 'Aramayla eşleşen terim bulunamadı.',
      terms: 'Terimler', meaning: 'Kısaca', practice: 'Pratikte', debate: 'Farklı bakışlar',
      related: 'İlgili terimler', sources: 'Kaynaklar ve ileri okuma', sourceOpen: 'Kaynağı aç',
      pdfOpen: 'PDF aç / indir', downloadLexicon: 'WRN sözlüğünü JSON olarak kaydet',
      downloadHint: 'WRN kısa metinleri özgün editoryal özetlerdir. Dış metinler kopyalanmaz.',
      editorialState: 'Editoryal taslak · geri bildirim bekliyoruz', feedback: 'Ekleme veya düzeltme öner',
      fallback: 'Editoryal tanımlar başlangıçta Almanca ve İngilizce sunulmaktadır. İngilizce sürüm gösteriliyor.',
      sections: { basics:'Temeller', organisation:'Örgütlenme', justice:'Adalet ve bakım', struggles:'Mücadele ve eleştiri', all:'Tüm terimler', sources:'Kaynaklar' }
    }
  };

  const SOURCES = [
    {
      id: 'afaq',
      name: 'An Anarchist FAQ',
      language: 'English',
      description: {
        de: 'Umfangreiche Einführung in anarchistische Grundideen, Strömungen, Geschichte, Organisation und Gesellschaftsentwürfe.',
        en: 'A broad introduction to anarchist principles, tendencies, history, organisation and visions of society.'
      },
      url: 'https://www.anarchistfaq.org/afaq/',
      downloads: [
        { label: 'Section A · PDF · English', url: 'https://www.anarchistfaq.org/afaq/pdf/sectionA.pdf' },
        { label: 'Section B · PDF · English', url: 'https://www.anarchistfaq.org/afaq/pdf/sectionB.pdf' }
      ]
    },
    {
      id: 'libcom',
      name: 'Libcom · Anarchism reading guide',
      language: 'English',
      description: {
        de: 'Thematisch geordneter Leseführer mit Einführungen, historischen Texten und verschiedenen anarchistischen Traditionen.',
        en: 'A thematic reading guide with introductions, historical texts and different anarchist traditions.'
      },
      url: 'https://libcom.org/article/anarchism-reading-guide',
      downloads: []
    },
    {
      id: 'transformharm',
      name: 'TransformHarm',
      language: 'English',
      description: {
        de: 'Kuratierte Artikel, Medien und Bildungsmaterialien zu transformativer und restaurativer Gerechtigkeit, Community Accountability, Abolition und Healing Justice.',
        en: 'Curated articles, media and curricula on transformative and restorative justice, community accountability, abolition and healing justice.'
      },
      url: 'https://transformharm.org/',
      downloads: []
    },
    {
      id: 'creative-interventions',
      name: 'Creative Interventions Toolkit',
      language: 'English · Español · Français',
      description: {
        de: 'Ein ausführlicher Praxisleitfaden für gemeinschaftsbasierte Reaktionen auf zwischenmenschliche Gewalt, transformative Gerechtigkeit und Verantwortungsübernahme.',
        en: 'A detailed practical guide to community-based responses to interpersonal violence, transformative justice and accountability.'
      },
      url: 'https://www.creative-interventions.org/toolkit/',
      downloads: [
        { label: 'Toolkit · PDF · English', url: 'https://www.creative-interventions.org/wp-content/uploads/2020/10/CI-Toolkit-Final-ENTIRE-Aug-2020-new-cover.pdf' },
        { label: 'Toolkit · PDF · Español', url: 'https://www.creative-interventions.org/wp-content/uploads/2020/10/toolkit-completo.pdf' }
      ]
    }
  ];

  const TERMS = [
    {
      id: 'anarchism', category: 'basics', sources: ['afaq', 'libcom'],
      title: { de: 'Anarchismus', en: 'Anarchism' },
      aliases: { de: ['antiautoritärer Sozialismus'], en: ['anti-authoritarian socialism'] },
      summary: {
        de: 'Eine vielfältige politische Tradition, die Herrschaft und aufgezwungene Hierarchien kritisiert und eine freie, solidarische Selbstorganisation von unten anstrebt.',
        en: 'A diverse political tradition that challenges domination and imposed hierarchy and seeks free, solidaristic self-organisation from below.'
      },
      practice: {
        de: 'Entscheidungen werden möglichst von den Betroffenen selbst getroffen. Kooperation, gegenseitige Hilfe und freiwillige Föderationen ersetzen zentrale Herrschaft.',
        en: 'Decisions should be made by the people affected. Cooperation, mutual aid and voluntary federations replace centralised rule.'
      },
      debate: {
        de: 'Anarchistische Strömungen unterscheiden sich unter anderem bei Ökonomie, Organisation, Gewaltfragen, Technologie und dem Verhältnis zu anderen Bewegungen.',
        en: 'Anarchist tendencies differ on economics, organisation, violence, technology and relations with other movements.'
      },
      related: ['libertarian-communism', 'mutual-aid', 'federation']
    },
    {
      id: 'libertarian-communism', category: 'basics', sources: ['afaq', 'libcom'],
      title: { de: 'Libertärer Kommunismus', en: 'Libertarian communism' },
      aliases: { de: ['Anarchokommunismus'], en: ['anarchist communism', 'anarcho-communism'] },
      summary: {
        de: 'Eine kommunistische und antiautoritäre Vorstellung einer klassenlosen Gesellschaft ohne Staat, Lohnarbeit und Privateigentum an Produktionsmitteln.',
        en: 'A communist and anti-authoritarian vision of a classless society without a state, wage labour or private ownership of productive resources.'
      },
      practice: {
        de: 'Produktion und Verteilung werden gemeinschaftlich und selbstverwaltet organisiert; Bedürfnisse und freie Vereinbarungen treten an die Stelle von Profit und Befehl.',
        en: 'Production and distribution are organised collectively and through self-management; needs and free agreement replace profit and command.'
      },
      debate: {
        de: 'Diskutiert werden etwa Übergänge, Verteilung, Koordination im großen Maßstab und das Verhältnis von individueller Freiheit und kollektiven Absprachen.',
        en: 'Debates concern transition, distribution, large-scale coordination and the relation between individual freedom and collective agreements.'
      },
      related: ['anarchism', 'mutual-aid', 'federation']
    },
    {
      id: 'mutual-aid', category: 'basics', sources: ['afaq', 'libcom'],
      title: { de: 'Gegenseitige Hilfe', en: 'Mutual aid' },
      aliases: { de: ['solidarische Selbsthilfe'], en: ['solidarity-based support'] },
      summary: {
        de: 'Eine Form solidarischer Zusammenarbeit, bei der Menschen Bedürfnisse gemeinsam erfüllen, statt Hilfe als Wohltätigkeit von oben zu organisieren.',
        en: 'Solidaristic cooperation through which people meet needs together rather than organising help as charity from above.'
      },
      practice: {
        de: 'Beispiele sind selbstorganisierte Essensverteilungen, Streikkassen, Nachbarschaftshilfe, Gesundheitskollektive und solidarische Katastrophenhilfe.',
        en: 'Examples include self-organised food distribution, strike funds, neighbourhood support, health collectives and solidarity disaster relief.'
      },
      debate: {
        de: 'Gegenseitige Hilfe ersetzt nicht automatisch politische Organisierung; sie kann bestehende Verhältnisse lindern oder Teil ihrer Veränderung werden.',
        en: 'Mutual aid does not automatically replace political organising; it can merely soften existing conditions or become part of changing them.'
      },
      related: ['collective-care', 'self-organisation', 'direct-action']
    },
    {
      id: 'direct-action', category: 'basics', sources: ['afaq', 'libcom'],
      title: { de: 'Direkte Aktion', en: 'Direct action' },
      aliases: { de: ['unmittelbares Handeln'], en: ['acting directly'] },
      summary: {
        de: 'Handeln, mit dem Betroffene selbst unmittelbar auf ein Problem oder Machtverhältnis einwirken, statt die Lösung ausschließlich an Stellvertretungen zu delegieren.',
        en: 'Action through which affected people intervene directly in a problem or power relation rather than delegating the solution entirely to representatives.'
      },
      practice: {
        de: 'Dazu können Streiks, Blockaden, Besetzungen, Boykotte, kollektive Verweigerung und der direkte Aufbau von Alternativen gehören.',
        en: 'It can include strikes, blockades, occupations, boycotts, collective refusal and directly building alternatives.'
      },
      debate: {
        de: 'Der Begriff beschreibt eine Handlungsweise, nicht automatisch eine bestimmte Taktik. Über Ziele, Risiken und Beteiligung muss jeweils gemeinsam entschieden werden.',
        en: 'The term describes a mode of action, not one fixed tactic. Goals, risks and participation need collective decisions in each situation.'
      },
      related: ['self-organisation', 'class-struggle', 'prefiguration']
    },
    {
      id: 'prefiguration', category: 'basics', sources: ['afaq', 'libcom'],
      title: { de: 'Präfiguration', en: 'Prefiguration' },
      aliases: { de: ['vorwegnehmende Politik'], en: ['prefigurative politics'] },
      summary: {
        de: 'Der Versuch, gewünschte gesellschaftliche Beziehungen schon in heutigen Organisationsformen, Entscheidungen und alltäglichen Praktiken anzulegen.',
        en: 'The attempt to embody desired social relations in present-day organising, decision-making and everyday practice.'
      },
      practice: {
        de: 'Eine herrschaftsfreie Zukunft soll nicht durch dauerhaft autoritäre Mittel entstehen; Strukturen werden deshalb möglichst horizontal, solidarisch und veränderbar gestaltet.',
        en: 'A non-dominating future should not be built through permanently authoritarian means, so structures aim to be horizontal, solidaristic and open to change.'
      },
      debate: {
        de: 'Spannungen entstehen zwischen dem Anspruch, Alternativen vorzuleben, und der Notwendigkeit, unter bestehenden Machtverhältnissen wirksam zu kämpfen.',
        en: 'Tensions arise between living alternatives now and fighting effectively within existing power relations.'
      },
      related: ['horizontal-organisation', 'direct-action', 'collective-care']
    },
    {
      id: 'federation', category: 'organisation', sources: ['afaq', 'libcom'],
      title: { de: 'Föderalismus', en: 'Federalism' },
      aliases: { de: ['anarchistischer Föderalismus'], en: ['anarchist federalism'] },
      summary: {
        de: 'Eine Organisationsweise, in der autonome Gruppen sich freiwillig verbinden, gemeinsame Aufgaben koordinieren und Macht möglichst nicht in einer Zentrale konzentrieren.',
        en: 'A form of organisation in which autonomous groups associate voluntarily, coordinate shared tasks and avoid concentrating power in a centre.'
      },
      practice: {
        de: 'Delegierte erhalten begrenzte Aufträge, bleiben rechenschaftspflichtig und können abberufen werden. Entscheidungen fließen von unten nach oben.',
        en: 'Delegates receive limited mandates, remain accountable and can be recalled. Decisions flow from the bottom upwards.'
      },
      debate: {
        de: 'Die konkrete Balance zwischen lokaler Autonomie, verbindlichen Absprachen und überregionaler Handlungsfähigkeit bleibt umstritten.',
        en: 'The balance between local autonomy, binding agreements and wider coordination remains contested.'
      },
      related: ['autonomy', 'consensus', 'self-organisation']
    },
    {
      id: 'self-organisation', category: 'organisation', sources: ['afaq', 'libcom'],
      title: { de: 'Selbstorganisation', en: 'Self-organisation' },
      aliases: { de: ['Selbstverwaltung'], en: ['self-management'] },
      summary: {
        de: 'Menschen organisieren ihre gemeinsamen Angelegenheiten selbst, ohne dass eine übergeordnete Instanz dauerhaft für sie entscheidet.',
        en: 'People organise their shared affairs themselves without a superior institution permanently deciding for them.'
      },
      practice: {
        de: 'Aufgaben, Wissen und Verantwortung werden geteilt; Regeln und Rollen bleiben überprüfbar und können von den Beteiligten verändert werden.',
        en: 'Tasks, knowledge and responsibility are shared; rules and roles remain reviewable and can be changed by participants.'
      },
      debate: {
        de: 'Formale Hierarchien abzuschaffen verhindert informelle Macht nicht automatisch. Zugang, Zeit, Wissen und Konfliktfähigkeit müssen mitbedacht werden.',
        en: 'Removing formal hierarchy does not automatically prevent informal power. Access, time, knowledge and capacity for conflict must also be addressed.'
      },
      related: ['horizontal-organisation', 'autonomy', 'federation']
    },
    {
      id: 'horizontal-organisation', category: 'organisation', sources: ['afaq', 'libcom'],
      title: { de: 'Horizontale Organisierung', en: 'Horizontal organising' },
      aliases: { de: ['Hierarchiearmut'], en: ['non-hierarchical organising'] },
      summary: {
        de: 'Eine Organisationsweise, die Entscheidungsmacht verteilt, gleiche Beteiligung ermöglicht und feste Befehlsketten vermeidet.',
        en: 'An approach that distributes decision-making power, enables equal participation and avoids fixed chains of command.'
      },
      practice: {
        de: 'Moderation, rotierende Aufgaben, offene Protokolle, zugängliche Informationen und transparente Mandate können horizontale Strukturen unterstützen.',
        en: 'Facilitation, rotating tasks, open minutes, accessible information and transparent mandates can support horizontal structures.'
      },
      debate: {
        de: 'Horizontalität ist kein Zustand ohne Macht. Unsichtbare Hierarchien müssen benannt und aktiv bearbeitet werden.',
        en: 'Horizontality does not mean power disappears. Invisible hierarchies need to be named and actively addressed.'
      },
      related: ['self-organisation', 'consensus', 'prefiguration']
    },
    {
      id: 'consensus', category: 'organisation', sources: ['afaq', 'creative-interventions'],
      title: { de: 'Konsens', en: 'Consensus' },
      aliases: { de: ['konsensorientierte Entscheidung'], en: ['consensus decision-making'] },
      summary: {
        de: 'Ein Entscheidungsverfahren, das eine gemeinsam tragbare Lösung sucht und Einwände ernst nimmt, statt nur Mehrheiten zu zählen.',
        en: 'A decision process seeking an outcome people can live with and taking objections seriously rather than merely counting majorities.'
      },
      practice: {
        de: 'Gute Verfahren unterscheiden Zustimmung, Bedenken, Beiseitestehen und Blockaden und legen fest, wann andere Verfahren nötig sind.',
        en: 'Good processes distinguish consent, concerns, standing aside and blocks, and define when another decision method is needed.'
      },
      debate: {
        de: 'Konsens kann Minderheiten schützen, aber ohne gute Moderation auch Druck, endlose Sitzungen oder versteckte Vetomacht erzeugen.',
        en: 'Consensus can protect minorities but without good facilitation can create pressure, endless meetings or hidden veto power.'
      },
      related: ['horizontal-organisation', 'federation', 'community-accountability']
    },
    {
      id: 'autonomy', category: 'organisation', sources: ['afaq', 'libcom'],
      title: { de: 'Autonomie', en: 'Autonomy' },
      aliases: { de: ['Selbstbestimmung'], en: ['self-determination'] },
      summary: {
        de: 'Die Fähigkeit von Menschen und Gruppen, ihre Angelegenheiten selbstbestimmt zu gestalten – nicht isoliert, sondern in Beziehungen gegenseitiger Verantwortung.',
        en: 'The capacity of people and groups to shape their affairs through self-determination—not in isolation but within relations of mutual responsibility.'
      },
      practice: {
        de: 'Autonome Gruppen können eigene Entscheidungen treffen und zugleich verbindliche föderale Absprachen mit anderen eingehen.',
        en: 'Autonomous groups can make their own decisions while entering binding federal agreements with others.'
      },
      debate: {
        de: 'Individuelle, kollektive und regionale Autonomie können miteinander in Spannung geraten; Abhängigkeiten verschwinden nicht durch ihre bloße Erklärung.',
        en: 'Individual, collective and regional autonomy can conflict, and dependencies do not disappear merely by declaring autonomy.'
      },
      related: ['federation', 'self-organisation', 'collective-care']
    },
    {
      id: 'syndicalism', category: 'organisation', sources: ['afaq', 'libcom'],
      title: { de: 'Anarchosyndikalismus', en: 'Anarcho-syndicalism' },
      aliases: { de: ['revolutionärer Syndikalismus'], en: ['revolutionary syndicalism'] },
      summary: {
        de: 'Eine anarchistische Strömung, die selbstorganisierte Gewerkschaften und direkte Aktionen der Arbeiter*innen als zentrale Mittel gesellschaftlicher Veränderung versteht.',
        en: 'An anarchist current that sees self-organised unions and workers’ direct action as central means of social transformation.'
      },
      practice: {
        de: 'Arbeitskämpfe sollen unmittelbare Verbesserungen erkämpfen und zugleich Fähigkeiten und Strukturen für eine selbstverwaltete Gesellschaft entwickeln.',
        en: 'Workplace struggles aim to win immediate improvements while developing capacities and structures for a self-managed society.'
      },
      debate: {
        de: 'Diskutiert werden das Verhältnis zu anderen Unterdrückungsverhältnissen, zu nichtbetrieblichen Kämpfen und zu spezifisch anarchistischen Organisationen.',
        en: 'Debates concern other forms of oppression, struggles beyond workplaces and relations with specifically anarchist organisations.'
      },
      related: ['class-struggle', 'direct-action', 'federation']
    },
    {
      id: 'transformative-justice', category: 'justice', sources: ['transformharm', 'creative-interventions'],
      title: { de: 'Transformative Gerechtigkeit', en: 'Transformative justice' },
      aliases: { de: ['Transformative Justice', 'TJ'], en: ['TJ'] },
      summary: {
        de: 'Ein Ansatz, der auf Gewalt reagiert, Sicherheit und Heilung unterstützt, Verantwortungsübernahme ermöglicht und zugleich die gesellschaftlichen Bedingungen verändern will, die Gewalt begünstigen.',
        en: 'An approach that responds to harm, supports safety and healing, enables accountability and seeks to change the social conditions that make violence more likely.'
      },
      practice: {
        de: 'Betroffene Bedürfnisse, Sicherheit, Veränderung schädigenden Verhaltens, Unterstützung durch das Umfeld und langfristige Prävention werden gemeinsam betrachtet.',
        en: 'Survivor needs, safety, change in harmful behaviour, community support and long-term prevention are considered together.'
      },
      debate: {
        de: 'Es gibt kein universelles Verfahren. Prozesse können riskant sein und benötigen Zustimmung, Ressourcen, Schutz vor Machtmissbrauch und ehrliche Grenzen.',
        en: 'There is no universal procedure. Processes can carry risks and require consent, resources, safeguards against abuse of power and honest limits.'
      },
      related: ['community-accountability', 'abolition', 'restorative-justice']
    },
    {
      id: 'restorative-justice', category: 'justice', sources: ['transformharm'],
      title: { de: 'Restaurative Gerechtigkeit', en: 'Restorative justice' },
      aliases: { de: ['wiederherstellende Gerechtigkeit'], en: ['restorative practices'] },
      summary: {
        de: 'Ein Ansatz, der entstandenen Schaden, Bedürfnisse, Verantwortung und mögliche Wiedergutmachung ins Zentrum stellt, statt hauptsächlich Regelbruch und Bestrafung zu betrachten.',
        en: 'An approach centring harm, needs, responsibility and possible repair rather than focusing primarily on rule-breaking and punishment.'
      },
      practice: {
        de: 'Mögliche Formen reichen von moderierten Gesprächen bis zu gemeinschaftlichen Vereinbarungen; Teilnahme und Sicherheit müssen sorgfältig geklärt werden.',
        en: 'Forms range from facilitated dialogue to community agreements; participation and safety require careful consideration.'
      },
      debate: {
        de: 'Restaurative Verfahren können innerhalb staatlicher Institutionen stattfinden. Transformative Ansätze kritisieren, dass dadurch strukturelle Ursachen unberührt bleiben können.',
        en: 'Restorative practices can operate inside state institutions. Transformative approaches argue that this may leave structural causes untouched.'
      },
      related: ['transformative-justice', 'community-accountability', 'abolition']
    },
    {
      id: 'community-accountability', category: 'justice', sources: ['transformharm', 'creative-interventions'],
      title: { de: 'Community Accountability', en: 'Community accountability' },
      aliases: { de: ['gemeinschaftliche Verantwortungsübernahme'], en: ['community-based accountability'] },
      summary: {
        de: 'Gemeinschaftsbasierte Prozesse, mit denen Gewalt benannt, Betroffene unterstützt, schädigendes Verhalten verändert und das soziale Umfeld in Verantwortung genommen werden soll.',
        en: 'Community-based processes intended to name harm, support survivors, change harmful behaviour and make the wider social environment accountable.'
      },
      practice: {
        de: 'Mögliche Schritte sind Sicherheitsplanung, Unterstützungsnetzwerke, klare Forderungen, überprüfbare Vereinbarungen und langfristige Begleitung.',
        en: 'Possible steps include safety planning, support networks, clear demands, reviewable agreements and long-term accompaniment.'
      },
      debate: {
        de: 'Eine „Community“ ist nicht automatisch sicher oder gerecht. Freundschaften, Status, Rassismus, Sexismus und materielle Abhängigkeiten beeinflussen solche Prozesse.',
        en: 'A “community” is not automatically safe or just. Friendships, status, racism, sexism and material dependency shape these processes.'
      },
      related: ['transformative-justice', 'collective-care', 'consensus']
    },
    {
      id: 'abolition', category: 'justice', sources: ['transformharm', 'creative-interventions'],
      title: { de: 'Abolitionismus', en: 'Abolition' },
      aliases: { de: ['Gefängnisabolition', 'Gefängnisabschaffung'], en: ['prison abolition'] },
      summary: {
        de: 'Eine Bewegung gegen Gefängnisse, Polizei und andere strafende Institutionen, die zugleich materielle Bedingungen und gemeinschaftliche Fähigkeiten für Sicherheit ohne Einsperrung aufbauen will.',
        en: 'A movement against prisons, policing and other punitive institutions that also builds material conditions and community capacities for safety without confinement.'
      },
      practice: {
        de: 'Dazu gehören der Abbau strafender Systeme und der Ausbau von Wohnen, Versorgung, Konfliktbearbeitung, Prävention, Unterstützung und demokratischer Kontrolle.',
        en: 'It includes dismantling punitive systems while expanding housing, care, conflict work, prevention, support and democratic control.'
      },
      debate: {
        de: 'Abolition wird oft fälschlich als bloßes Schließen von Gefängnissen verstanden. Zentral ist ebenso die Frage, wodurch Sicherheit und Gerechtigkeit stattdessen getragen werden.',
        en: 'Abolition is often mistaken for simply closing prisons. Equally central is what institutions and relationships should support safety and justice instead.'
      },
      related: ['transformative-justice', 'community-accountability', 'collective-care']
    },
    {
      id: 'collective-care', category: 'justice', sources: ['transformharm', 'creative-interventions'],
      title: { de: 'Kollektive Fürsorge', en: 'Collective care' },
      aliases: { de: ['Care', 'radikale Fürsorge'], en: ['radical care'] },
      summary: {
        de: 'Die gemeinsame Verantwortung für körperliches, emotionales und materielles Wohlergehen – besonders unter Bedingungen von Ausbeutung, Repression und Ausschluss.',
        en: 'Shared responsibility for physical, emotional and material wellbeing, especially under conditions of exploitation, repression and exclusion.'
      },
      practice: {
        de: 'Fürsorge kann Barriereabbau, Kinderbetreuung, Essen, Geld, emotionale Unterstützung, Ruhe, Gesundheitsversorgung und nachhaltige Aufgabenverteilung umfassen.',
        en: 'Care can include accessibility, childcare, food, money, emotional support, rest, healthcare and sustainable distribution of work.'
      },
      debate: {
        de: 'Fürsorge darf nicht unsichtbar einzelnen Personen zugeschoben werden. Sie braucht Ressourcen, Grenzen und eine gerechte Verteilung reproduktiver Arbeit.',
        en: 'Care should not be invisibly assigned to a few people. It requires resources, boundaries and fair distribution of reproductive labour.'
      },
      related: ['mutual-aid', 'community-accountability', 'self-organisation']
    },
    {
      id: 'anti-capitalism', category: 'struggles', sources: ['afaq', 'libcom'],
      title: { de: 'Antikapitalismus', en: 'Anti-capitalism' },
      aliases: { de: ['Kapitalismuskritik'], en: ['critique of capitalism'] },
      summary: {
        de: 'Kritik und Widerstand gegen eine Gesellschaft, in der Produktion und Lebensgrundlagen durch Privateigentum, Profit, Marktzwang und Klassenmacht bestimmt werden.',
        en: 'Critique and resistance to a society in which production and the means of life are shaped by private ownership, profit, market compulsion and class power.'
      },
      practice: {
        de: 'Antikapitalistische Praxis reicht von Arbeitskämpfen und Enteignungsforderungen bis zum Aufbau gemeinschaftlicher, selbstverwalteter Alternativen.',
        en: 'Anti-capitalist practice ranges from workplace struggles and expropriation demands to building communal, self-managed alternatives.'
      },
      debate: {
        de: 'Antikapitalistische Strömungen unterscheiden sich stark bei Staat, Parteien, Übergängen, Eigentumsformen und dem Verhältnis anderer Herrschaftsformen zur Klasse.',
        en: 'Anti-capitalist currents differ sharply on the state, parties, transition, ownership and how other forms of domination relate to class.'
      },
      related: ['class-struggle', 'libertarian-communism', 'anti-imperialism']
    },
    {
      id: 'anti-colonialism', category: 'struggles', sources: ['libcom'],
      title: { de: 'Antikolonialismus', en: 'Anti-colonialism' },
      aliases: { de: ['Dekolonisierung'], en: ['decolonisation'] },
      summary: {
        de: 'Widerstand gegen koloniale Herrschaft und ihre fortwirkenden politischen, wirtschaftlichen, kulturellen und epistemischen Machtverhältnisse.',
        en: 'Resistance to colonial rule and its continuing political, economic, cultural and epistemic power relations.'
      },
      practice: {
        de: 'Dazu gehören Kämpfe um Land, Selbstbestimmung, Sprache, Rückgabe geraubter Güter, Reparationen und die Veränderung kolonial geprägter Institutionen.',
        en: 'It includes struggles over land, self-determination, language, return of stolen objects, reparations and transformation of colonial institutions.'
      },
      debate: {
        de: 'Nationale Befreiung kann Kolonialherrschaft brechen, garantiert aber keine herrschaftsfreie Gesellschaft. Staat, Klasse, Patriarchat und indigene Autonomie bleiben umkämpft.',
        en: 'National liberation can break colonial rule but does not guarantee a society without domination. State, class, patriarchy and Indigenous autonomy remain contested.'
      },
      related: ['anti-imperialism', 'autonomy', 'anti-capitalism']
    },
    {
      id: 'anti-imperialism', category: 'struggles', sources: ['afaq', 'libcom'],
      title: { de: 'Antiimperialismus', en: 'Anti-imperialism' },
      aliases: { de: ['Anti-Imperialismus'], en: ['anti-imperialist struggle'] },
      summary: {
        de: 'Widerstand gegen politische, militärische und wirtschaftliche Dominanz mächtiger Staaten und Kapitalinteressen über andere Regionen und Bevölkerungen.',
        en: 'Resistance to political, military and economic domination of regions and peoples by powerful states and capital interests.'
      },
      practice: {
        de: 'Dazu können Kämpfe gegen Besatzung, Krieg, Schuldenregime, Ressourcenraub, Sanktionen und ungleiche Handelsbeziehungen gehören.',
        en: 'It can include struggles against occupation, war, debt regimes, resource extraction, sanctions and unequal trade relations.'
      },
      debate: {
        de: 'Ein emanzipatorischer Antiimperialismus rechtfertigt nicht automatisch autoritäre Regierungen, nur weil sie mit westlichen Mächten im Konflikt stehen.',
        en: 'Emancipatory anti-imperialism does not automatically justify authoritarian governments merely because they oppose Western powers.'
      },
      related: ['anti-colonialism', 'anti-capitalism', 'internationalism']
    },
    {
      id: 'anti-fascism', category: 'struggles', sources: ['libcom'],
      title: { de: 'Antifaschismus', en: 'Anti-fascism' },
      aliases: { de: ['Antifa'], en: ['antifa'] },
      summary: {
        de: 'Politischer und gesellschaftlicher Widerstand gegen faschistische Ideologien, Organisationen, Gewalt und die Bedingungen, unter denen sie wachsen.',
        en: 'Political and social resistance to fascist ideologies, organisations, violence and the conditions in which they grow.'
      },
      practice: {
        de: 'Antifaschismus umfasst Recherche, Aufklärung, Schutz Betroffener, Gegenmobilisierung, direkte Aktion und den Aufbau solidarischer Gegenmacht.',
        en: 'Anti-fascism includes research, education, protecting targeted people, counter-mobilisation, direct action and building solidaristic counter-power.'
      },
      debate: {
        de: 'Strategien unterscheiden sich bei Bündnissen, Öffentlichkeit, Militanz und dem Verhältnis zwischen Abwehr konkreter Gruppen und gesellschaftlicher Ursachenanalyse.',
        en: 'Strategies differ on alliances, publicity, militancy and the balance between confronting groups and addressing social causes.'
      },
      related: ['direct-action', 'anti-capitalism', 'collective-care']
    },
    {
      id: 'class-struggle', category: 'struggles', sources: ['afaq', 'libcom'],
      title: { de: 'Klassenkampf', en: 'Class struggle' },
      aliases: { de: ['Klassenkonflikt'], en: ['class conflict'] },
      summary: {
        de: 'Konflikte zwischen gesellschaftlichen Klassen, deren Interessen und Handlungsmöglichkeiten durch Besitz, Arbeit, Kontrolle über Produktion und Zugang zu Ressourcen geprägt sind.',
        en: 'Conflict between social classes whose interests and capacities are shaped by ownership, labour, control of production and access to resources.'
      },
      practice: {
        de: 'Klassenkampf findet in Betrieben, bei Mieten, Sozialleistungen, Versorgung, Land, Schulden und der Verteilung unbezahlter Arbeit statt.',
        en: 'Class struggle occurs in workplaces and around rent, welfare, care, land, debt and the distribution of unpaid labour.'
      },
      debate: {
        de: 'Klasse wird nicht überall gleich verstanden. Eine emanzipatorische Analyse muss ihre Verbindungen mit Rassismus, Patriarchat, Kolonialismus und Behinderung berücksichtigen.',
        en: 'Class is understood in different ways. Emancipatory analysis must address its relations with racism, patriarchy, colonialism and disability.'
      },
      related: ['anti-capitalism', 'syndicalism', 'direct-action']
    },
    {
      id: 'internationalism', category: 'struggles', sources: ['afaq', 'libcom'],
      title: { de: 'Internationalismus', en: 'Internationalism' },
      aliases: { de: ['grenzüberschreitende Solidarität'], en: ['cross-border solidarity'] },
      summary: {
        de: 'Solidarität und gemeinsame Organisierung über Staatsgrenzen hinweg, ausgehend davon, dass Herrschafts- und Ausbeutungsverhältnisse international miteinander verbunden sind.',
        en: 'Solidarity and shared organising across state borders, recognising that systems of domination and exploitation are internationally connected.'
      },
      practice: {
        de: 'Dazu gehören gegenseitige Unterstützung, Übersetzung, gemeinsame Kampagnen, Streiksolidarität und das Lernen zwischen Bewegungen.',
        en: 'It includes mutual support, translation, shared campaigns, strike solidarity and learning across movements.'
      },
      debate: {
        de: 'Internationalismus muss lokale Unterschiede und ungleiche Macht beachten, damit Solidarität nicht zu Bevormundung oder politischer Projektion wird.',
        en: 'Internationalism must account for local differences and unequal power so that solidarity does not become paternalism or political projection.'
      },
      related: ['anti-imperialism', 'anti-colonialism', 'mutual-aid']
    }
  ];

  const hiddenNodes = new Map();
  const state = { section: 'basics', query: '' };

  const lang = value => String(
    value
    || document.getElementById('ui-language')?.value
    || document.documentElement.lang
    || 'en'
  ).toLowerCase().split(/[-_]/)[0];

  const ui = code => UI[lang(code)] || UI.en;
  const editorialLanguage = () => lang() === 'de' ? 'de' : 'en';
  const textFor = value => value?.[editorialLanguage()] || value?.en || value?.de || '';
  const sourceById = id => SOURCES.find(source => source.id === id);

  function safeExternalLink(url, label, className = '') {
    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.referrerPolicy = 'no-referrer';
    link.className = className;
    link.textContent = label;
    return link;
  }

  function ensureRoot() {
    let root = document.getElementById('wrn-lexicon-184');
    if (root) return root;
    root = document.createElement('section');
    root.id = 'wrn-lexicon-184';
    root.className = 'wrn-lexicon-184';
    root.hidden = true;
    const anchor = document.getElementById('feed-container');
    anchor?.parentNode?.insertBefore(root, anchor);
    return root;
  }

  function relatedLabels(term) {
    return (term.related || [])
      .map(id => TERMS.find(item => item.id === id))
      .filter(Boolean)
      .map(item => textFor(item.title));
  }

  function sourceLabels(term) {
    return (term.sources || []).map(sourceById).filter(Boolean);
  }

  function matchesQuery(term, query) {
    if (!query) return true;
    const searchable = [
      textFor(term.title),
      ...(term.aliases?.[editorialLanguage()] || term.aliases?.en || []),
      textFor(term.summary),
      textFor(term.practice),
      textFor(term.debate)
    ].join(' ').toLocaleLowerCase();
    return searchable.includes(query.toLocaleLowerCase());
  }

  function termCard(term) {
    const t = ui();
    const card = document.createElement('details');
    card.className = 'wrn-lexicon-card-184';
    card.dataset.term = term.id;

    const summary = document.createElement('summary');
    const heading = document.createElement('span');
    const title = document.createElement('strong');
    const aliases = document.createElement('small');
    const teaser = document.createElement('p');
    title.textContent = textFor(term.title);
    aliases.textContent = (term.aliases?.[editorialLanguage()] || term.aliases?.en || []).join(' · ');
    teaser.textContent = textFor(term.summary);
    heading.append(title, aliases);
    summary.append(heading, teaser);

    const body = document.createElement('div');
    body.className = 'wrn-lexicon-card-body-184';
    [
      [t.practice, textFor(term.practice)],
      [t.debate, textFor(term.debate)]
    ].forEach(([label, value]) => {
      const section = document.createElement('section');
      const h = document.createElement('h4');
      const p = document.createElement('p');
      h.textContent = label;
      p.textContent = value;
      section.append(h, p);
      body.appendChild(section);
    });

    const related = relatedLabels(term);
    if (related.length) {
      const section = document.createElement('section');
      const h = document.createElement('h4');
      const values = document.createElement('div');
      values.className = 'wrn-lexicon-tags-184';
      h.textContent = t.related;
      related.forEach(value => {
        const tag = document.createElement('span');
        tag.textContent = value;
        values.appendChild(tag);
      });
      section.append(h, values);
      body.appendChild(section);
    }

    const sources = sourceLabels(term);
    if (sources.length) {
      const section = document.createElement('section');
      const h = document.createElement('h4');
      const links = document.createElement('div');
      links.className = 'wrn-lexicon-source-links-184';
      h.textContent = t.sources;
      sources.forEach(source => links.appendChild(
        safeExternalLink(source.url, source.name)
      ));
      section.append(h, links);
      body.appendChild(section);
    }

    const feedback = document.createElement('button');
    feedback.type = 'button';
    feedback.className = 'wrn-lexicon-feedback-184';
    feedback.textContent = t.feedback;
    feedback.addEventListener('click', () => window.openFeedback?.());
    body.appendChild(feedback);

    card.append(summary, body);
    return card;
  }

  function downloadLexicon() {
    const data = {
      title: 'World Revolution News – Begriffslexikon',
      version: '1.0-editorial-draft',
      exportedAt: new Date().toISOString(),
      notice: UI.de.note,
      sources: SOURCES.map(source => ({
        name: source.name,
        url: source.url,
        downloads: source.downloads
      })),
      terms: TERMS
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'wrn-begriffslexikon.json';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function renderSources(host) {
    const t = ui();
    const header = document.createElement('div');
    header.className = 'wrn-lexicon-sources-head-184';
    const heading = document.createElement('h3');
    const hint = document.createElement('p');
    const download = document.createElement('button');
    heading.textContent = t.sources;
    hint.textContent = t.downloadHint;
    download.type = 'button';
    download.textContent = t.downloadLexicon;
    download.addEventListener('click', downloadLexicon);
    header.append(heading, hint, download);
    host.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'wrn-lexicon-sources-grid-184';
    SOURCES.forEach(source => {
      const card = document.createElement('article');
      const h = document.createElement('h3');
      const meta = document.createElement('small');
      const description = document.createElement('p');
      const actions = document.createElement('div');
      h.textContent = source.name;
      meta.textContent = source.language;
      description.textContent = textFor(source.description);
      actions.className = 'wrn-lexicon-source-actions-184';
      actions.appendChild(safeExternalLink(source.url, t.sourceOpen, 'primary'));
      source.downloads.forEach(downloadItem => {
        actions.appendChild(safeExternalLink(
          downloadItem.url,
          `${t.pdfOpen}: ${downloadItem.label}`
        ));
      });
      card.append(h, meta, description, actions);
      grid.appendChild(card);
    });
    host.appendChild(grid);
  }

  function render() {
    const root = ensureRoot();
    const t = ui();
    root.textContent = '';

    const header = document.createElement('header');
    const kicker = document.createElement('span');
    const building = document.createElement('span');
    const title = document.createElement('h2');
    const lead = document.createElement('p');
    const note = document.createElement('p');
    const stateLabel = document.createElement('small');
    kicker.className = 'wrn-lexicon-kicker-184';
    kicker.textContent = 'WORLD REVOLUTION NEWS · MOVEMENT GLOSSARY';
    building.className = 'wrn-lexicon-building-184';
    building.textContent = t.building;
    title.textContent = t.title;
    lead.textContent = t.lead;
    note.className = 'wrn-lexicon-note-184';
    note.textContent = t.note;
    stateLabel.textContent = t.editorialState;
    header.append(kicker, building, title, lead, note, stateLabel);
    root.appendChild(header);

    if (lang() !== 'de' && lang() !== 'en' && t.fallback) {
      const fallback = document.createElement('p');
      fallback.className = 'wrn-lexicon-fallback-184';
      fallback.textContent = t.fallback;
      root.appendChild(fallback);
    }

    const content = document.createElement('div');
    content.className = 'wrn-lexicon-content-184';
    root.appendChild(content);

    if (state.section === 'sources') {
      renderSources(content);
      return;
    }

    const controls = document.createElement('div');
    controls.className = 'wrn-lexicon-controls-184';
    const search = document.createElement('input');
    const count = document.createElement('span');
    search.type = 'search';
    search.value = state.query;
    search.placeholder = t.search;
    search.setAttribute('aria-label', t.search);
    controls.append(search, count);
    content.appendChild(controls);

    const list = document.createElement('div');
    list.className = 'wrn-lexicon-list-184';
    const filtered = TERMS
      .filter(term => state.section === 'all' || term.category === state.section)
      .filter(term => matchesQuery(term, state.query))
      .sort((left, right) => textFor(left.title).localeCompare(textFor(right.title), editorialLanguage()));
    count.textContent = `${filtered.length} ${t.terms}`;
    filtered.forEach(term => list.appendChild(termCard(term)));
    if (!filtered.length) {
      const empty = document.createElement('p');
      empty.className = 'wrn-lexicon-empty-184';
      empty.textContent = t.noResults;
      list.appendChild(empty);
    }
    content.appendChild(list);

    search.addEventListener('input', () => {
      state.query = search.value.trim();
      render();
      const next = ensureRoot().querySelector('.wrn-lexicon-controls-184 input');
      next?.focus();
      next?.setSelectionRange(state.query.length, state.query.length);
    });
  }

  function hideStandard() {
    [
      'feed-container', 'archive-container', 'event-filter-panel',
      'status-container', 'txt-archive-title', 'wrn-video-hub',
      'wrn-stories-view', 'wrn-audio-tab-183', 'wrn-briefing-2',
      'wrn-about-184'
    ].forEach(id => {
      const node = document.getElementById(id);
      if (!node || node.id === 'wrn-lexicon-184') return;
      if (!hiddenNodes.has(node)) hiddenNodes.set(node, {
        hidden: node.hidden,
        display: node.style.display
      });
      node.hidden = true;
      node.style.display = 'none';
    });
  }

  function show(section = state.section) {
    state.section = UI.en.sections[section] ? section : 'basics';
    hideStandard();
    const root = ensureRoot();
    render();
    root.hidden = false;
    root.style.display = 'block';
    document.body.dataset.wrnTab = 'lexicon';
  }

  function hide() {
    const root = document.getElementById('wrn-lexicon-184');
    if (root) {
      root.hidden = true;
      root.style.display = 'none';
    }
    hiddenNodes.forEach((value, node) => {
      if (!node.isConnected) return;
      node.hidden = value.hidden;
      node.style.display = value.display;
    });
    hiddenNodes.clear();
  }

  window.WRNLexicon184 = Object.freeze({
    show,
    hide,
    render,
    label: code => ui(code).nav,
    sectionLabel: (section, code) => ui(code).sections[section] || section,
    exportData: downloadLexicon,
    termCount: TERMS.length,
    sourceCount: SOURCES.length
  });
})();
