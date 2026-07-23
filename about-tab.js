/* World Revolution News 1.8.4 – purpose and feedback */
'use strict';

(() => {
  if (window.WRNAbout184) return;

  const COPY = {
    de: {
      nav: 'Über die App', title: 'Warum es World Revolution News gibt',
      lead: 'World Revolution News macht unabhängige, anarchistische, links-libertäre und antiautoritäre Berichte aus vielen Regionen leichter auffindbar.',
      why: 'Warum wir die App machen',
      whyText: 'Wichtige Stimmen sind über viele kleine Seiten, Sprachen und Formate verteilt. Die App führt sie an einem Ort zusammen, ohne die Originalquellen zu ersetzen.',
      found: 'Was du hier findest',
      items: ['Nachrichten nach Regionen und Themen', 'Termine aus Radar.squat und weiteren Kalendern', 'Podcasts, erzeugte Audiofassungen, Radio und Videos', 'Werkzeuge zum Übersetzen, Zusammenfassen, Speichern und Gestalten eines eigenen Zines'],
      principles: 'Wie wir arbeiten',
      principlesText: 'Quellen bleiben sichtbar und verlinkt. Automatische Übersetzungen und Zusammenfassungen können Fehler enthalten. Auswahl und Einordnung sind offen für Kritik und Veränderung.',
      feedback: 'Hilf mit', feedbackText: 'Kennst du eine fehlende Quelle, entdeckst du einen Fehler oder hast du eine Idee? Schreib uns. Besonders freuen wir uns über Hinweise aus Regionen und Sprachen, die noch wenig vertreten sind.',
      button: 'Feedback senden',
      note: 'Die Sammlung erhebt keinen Anspruch auf Vollständigkeit. Begriffe, Perspektiven und Bewegungen verändern sich – diese App soll gemeinsam mit ihren Nutzer*innen wachsen.'
    },
    en: {
      nav: 'About', title: 'Why World Revolution News exists',
      lead: 'World Revolution News makes independent, anarchist, left-libertarian and anti-authoritarian reporting from many regions easier to find.',
      why: 'Why we build it', whyText: 'Important voices are spread across many small sites, languages and formats. The app brings them together without replacing the original sources.',
      found: 'What you can find', items: ['News by region and topic', 'Events from Radar.squat and other calendars', 'Podcasts, generated audio, radio and videos', 'Tools to translate, summarize, save and design your own zine'],
      principles: 'How we work', principlesText: 'Sources remain visible and linked. Automated translations and summaries can contain errors. Selection and framing remain open to criticism and change.',
      feedback: 'Take part', feedbackText: 'Know a missing source, found a mistake or have an idea? Write to us. We especially welcome suggestions from underrepresented regions and languages.',
      button: 'Send feedback', note: 'This collection is not complete. Words, perspectives and movements change – the app should grow together with its users.'
    },
    es: {
      nav: 'Sobre la app', title: 'Por qué existe World Revolution News',
      lead: 'World Revolution News facilita encontrar información independiente, anarquista, libertaria de izquierda y antiautoritaria de muchas regiones.',
      why: 'Por qué hacemos la app', whyText: 'Voces importantes están repartidas entre sitios pequeños, idiomas y formatos. La app las reúne sin sustituir las fuentes originales.',
      found: 'Qué encontrarás', items: ['Noticias por región y tema', 'Eventos de Radar.squat y otros calendarios', 'Podcasts, audio generado, radio y vídeos', 'Herramientas para traducir, resumir, guardar y diseñar tu propio zine'],
      principles: 'Cómo trabajamos', principlesText: 'Las fuentes siguen visibles y enlazadas. Las traducciones y los resúmenes automáticos pueden contener errores. La selección está abierta a críticas y cambios.',
      feedback: 'Participa', feedbackText: '¿Conoces una fuente que falta, un error o tienes una idea? Escríbenos. Agradecemos especialmente propuestas de regiones e idiomas poco representados.',
      button: 'Enviar comentarios', note: 'La colección no pretende ser completa. Las palabras, perspectivas y movimientos cambian; la app debe crecer con sus usuarias y usuarios.'
    },
    fr: {
      nav: 'À propos', title: 'Pourquoi World Revolution News existe',
      lead: 'World Revolution News facilite l’accès à des informations indépendantes, anarchistes, libertaires de gauche et antiautoritaires de nombreuses régions.',
      why: 'Pourquoi nous créons cette app', whyText: 'Des voix importantes sont dispersées entre de petits sites, langues et formats. L’app les réunit sans remplacer les sources originales.',
      found: 'Ce que vous trouverez', items: ['Actualités par région et thème', 'Événements de Radar.squat et d’autres agendas', 'Podcasts, audio généré, radios et vidéos', 'Outils pour traduire, résumer, sauvegarder et créer votre propre zine'],
      principles: 'Notre méthode', principlesText: 'Les sources restent visibles et liées. Les traductions et résumés automatiques peuvent comporter des erreurs. La sélection reste ouverte à la critique et au changement.',
      feedback: 'Participer', feedbackText: 'Vous connaissez une source manquante, une erreur ou avez une idée ? Écrivez-nous. Les propositions de régions et langues peu représentées sont particulièrement bienvenues.',
      button: 'Envoyer un retour', note: 'Cette collection ne prétend pas être complète. Les mots, perspectives et mouvements évoluent ; l’app doit grandir avec ses utilisatrices et utilisateurs.'
    },
    it: {
      nav: 'Informazioni', title: 'Perché esiste World Revolution News',
      lead: 'World Revolution News rende più facili da trovare notizie indipendenti, anarchiche, libertarie di sinistra e antiautoritarie da molte regioni.',
      why: 'Perché creiamo l’app', whyText: 'Voci importanti sono sparse tra piccoli siti, lingue e formati. L’app le riunisce senza sostituire le fonti originali.',
      found: 'Cosa trovi', items: ['Notizie per regione e tema', 'Eventi da Radar.squat e altri calendari', 'Podcast, audio generato, radio e video', 'Strumenti per tradurre, riassumere, salvare e creare il tuo zine'],
      principles: 'Come lavoriamo', principlesText: 'Le fonti restano visibili e collegate. Traduzioni e riassunti automatici possono contenere errori. Selezione e contesto restano aperti a critica e cambiamento.',
      feedback: 'Partecipa', feedbackText: 'Conosci una fonte mancante, hai trovato un errore o hai un’idea? Scrivici. Apprezziamo in particolare suggerimenti da regioni e lingue poco rappresentate.',
      button: 'Invia feedback', note: 'La raccolta non pretende di essere completa. Parole, prospettive e movimenti cambiano: l’app dovrebbe crescere insieme a chi la usa.'
    },
    pt: {
      nav: 'Sobre', title: 'Por que existe a World Revolution News',
      lead: 'A World Revolution News facilita encontrar informação independente, anarquista, libertária de esquerda e antiautoritária de muitas regiões.',
      why: 'Por que fazemos a app', whyText: 'Vozes importantes estão espalhadas por pequenos sites, idiomas e formatos. A app reúne-as sem substituir as fontes originais.',
      found: 'O que encontras', items: ['Notícias por região e tema', 'Eventos do Radar.squat e outros calendários', 'Podcasts, áudio gerado, rádio e vídeos', 'Ferramentas para traduzir, resumir, guardar e criar o teu zine'],
      principles: 'Como trabalhamos', principlesText: 'As fontes permanecem visíveis e ligadas. Traduções e resumos automáticos podem conter erros. A seleção continua aberta a crítica e mudança.',
      feedback: 'Participa', feedbackText: 'Conheces uma fonte em falta, encontraste um erro ou tens uma ideia? Escreve-nos. Agradecemos especialmente sugestões de regiões e idiomas pouco representados.',
      button: 'Enviar feedback', note: 'A coleção não pretende ser completa. Palavras, perspetivas e movimentos mudam — a app deve crescer com quem a utiliza.'
    },
    ru: {
      nav: 'О приложении', title: 'Зачем существует World Revolution News',
      lead: 'World Revolution News помогает находить независимые, анархистские, лево-либертарианские и антиавторитарные материалы из разных регионов.',
      why: 'Зачем мы создаём приложение', whyText: 'Важные голоса распределены по небольшим сайтам, языкам и форматам. Приложение собирает их вместе, не заменяя оригинальные источники.',
      found: 'Что здесь есть', items: ['Новости по регионам и темам', 'События Radar.squat и других календарей', 'Подкасты, созданное аудио, радио и видео', 'Инструменты перевода, резюмирования, сохранения и создания собственного зина'],
      principles: 'Как мы работаем', principlesText: 'Источники остаются видимыми и доступны по ссылкам. Автоматические переводы и резюме могут содержать ошибки. Выбор материалов открыт критике и изменениям.',
      feedback: 'Участвовать', feedbackText: 'Знаете отсутствующий источник, нашли ошибку или есть идея? Напишите нам. Особенно важны предложения из слабо представленных регионов и языков.',
      button: 'Отправить отзыв', note: 'Коллекция не претендует на полноту. Слова, взгляды и движения меняются — приложение должно развиваться вместе с пользователями.'
    },
    el: {
      nav: 'Σχετικά', title: 'Γιατί υπάρχει το World Revolution News',
      lead: 'Το World Revolution News διευκολύνει την εύρεση ανεξάρτητης, αναρχικής, αριστερής ελευθεριακής και αντιεξουσιαστικής ενημέρωσης από πολλές περιοχές.',
      why: 'Γιατί φτιάχνουμε την εφαρμογή', whyText: 'Σημαντικές φωνές είναι διασκορπισμένες σε μικρούς ιστότοπους, γλώσσες και μορφές. Η εφαρμογή τις συγκεντρώνει χωρίς να αντικαθιστά τις αρχικές πηγές.',
      found: 'Τι θα βρείτε', items: ['Ειδήσεις ανά περιοχή και θέμα', 'Εκδηλώσεις από το Radar.squat και άλλα ημερολόγια', 'Podcast, παραγόμενο ήχο, ραδιόφωνο και βίντεο', 'Εργαλεία μετάφρασης, σύνοψης, αποθήκευσης και δημιουργίας zine'],
      principles: 'Πώς εργαζόμαστε', principlesText: 'Οι πηγές παραμένουν ορατές και συνδεδεμένες. Οι αυτόματες μεταφράσεις και συνόψεις μπορεί να έχουν λάθη. Η επιλογή παραμένει ανοιχτή σε κριτική και αλλαγή.',
      feedback: 'Συμμετοχή', feedbackText: 'Γνωρίζετε πηγή που λείπει, βρήκατε λάθος ή έχετε ιδέα; Γράψτε μας. Ιδιαίτερα ευπρόσδεκτες είναι προτάσεις από περιοχές και γλώσσες με μικρή εκπροσώπηση.',
      button: 'Αποστολή σχολίου', note: 'Η συλλογή δεν ισχυρίζεται ότι είναι πλήρης. Λέξεις, οπτικές και κινήματα αλλάζουν — η εφαρμογή πρέπει να εξελίσσεται μαζί με τους χρήστες της.'
    },
    tr: {
      nav: 'Uygulama hakkında', title: 'World Revolution News neden var',
      lead: 'World Revolution News, birçok bölgeden bağımsız, anarşist, sol-liberter ve otorite karşıtı haberlere ulaşmayı kolaylaştırır.',
      why: 'Uygulamayı neden yapıyoruz', whyText: 'Önemli sesler küçük sitelere, dillere ve formatlara dağılmış durumda. Uygulama özgün kaynakların yerini almadan onları bir araya getirir.',
      found: 'Burada ne var', items: ['Bölge ve konuya göre haberler', 'Radar.squat ve diğer takvimlerden etkinlikler', 'Podcastler, üretilen sesler, radyo ve videolar', 'Çeviri, özetleme, kaydetme ve kendi zine’ını oluşturma araçları'],
      principles: 'Nasıl çalışıyoruz', principlesText: 'Kaynaklar görünür ve bağlantılı kalır. Otomatik çeviri ve özetler hata içerebilir. Seçim ve çerçeveleme eleştiri ve değişime açıktır.',
      feedback: 'Katılın', feedbackText: 'Eksik bir kaynak, hata veya fikriniz mi var? Bize yazın. Özellikle az temsil edilen bölge ve dillerden önerileri bekliyoruz.',
      button: 'Geri bildirim gönder', note: 'Bu koleksiyon eksiksiz olma iddiasında değildir. Sözcükler, bakış açıları ve hareketler değişir; uygulama kullanıcılarıyla birlikte büyümelidir.'
    }
  };

  const hiddenNodes = new Map();
  const lang = value => String(value || document.getElementById('ui-language')?.value || document.documentElement.lang || 'en').toLowerCase().split(/[-_]/)[0];
  const copy = code => COPY[lang(code)] || COPY.en;

  function ensureRoot() {
    let root = document.getElementById('wrn-about-184');
    if (root) return root;
    root = document.createElement('section');
    root.id = 'wrn-about-184';
    root.className = 'wrn-about-184';
    root.hidden = true;
    const anchor = document.getElementById('feed-container');
    anchor?.parentNode?.insertBefore(root, anchor);
    return root;
  }

  function render() {
    const root = ensureRoot();
    const t = copy();
    root.textContent = '';
    const header = document.createElement('header');
    header.innerHTML = `<span>WORLD REVOLUTION NEWS</span><h2></h2><p></p>`;
    header.querySelector('h2').textContent = t.title;
    header.querySelector('p').textContent = t.lead;
    root.appendChild(header);

    const grid = document.createElement('div');
    grid.className = 'wrn-about-grid-184';
    [[t.why, t.whyText], [t.principles, t.principlesText]].forEach(([title, body]) => {
      const section = document.createElement('section');
      const heading = document.createElement('h3');
      const paragraph = document.createElement('p');
      heading.textContent = title;
      paragraph.textContent = body;
      section.append(heading, paragraph);
      grid.appendChild(section);
    });
    const found = document.createElement('section');
    const foundTitle = document.createElement('h3');
    const list = document.createElement('ul');
    foundTitle.textContent = t.found;
    t.items.forEach(value => {
      const item = document.createElement('li');
      item.textContent = value;
      list.appendChild(item);
    });
    found.append(foundTitle, list);
    grid.insertBefore(found, grid.children[1]);
    root.appendChild(grid);

    const feedback = document.createElement('section');
    feedback.className = 'wrn-about-feedback-184';
    const feedbackTitle = document.createElement('h3');
    const feedbackText = document.createElement('p');
    const button = document.createElement('button');
    feedbackTitle.textContent = t.feedback;
    feedbackText.textContent = t.feedbackText;
    button.type = 'button';
    button.textContent = t.button;
    button.addEventListener('click', () => window.openFeedback?.());
    feedback.append(feedbackTitle, feedbackText, button);
    root.appendChild(feedback);

    const note = document.createElement('p');
    note.className = 'wrn-about-note-184';
    note.textContent = t.note;
    root.appendChild(note);
  }

  function hideStandard() {
    ['feed-container', 'archive-container', 'event-filter-panel', 'status-container', 'txt-archive-title', 'wrn-video-hub', 'wrn-stories-view', 'wrn-audio-tab-183', 'wrn-briefing-2'].forEach(id => {
      const node = document.getElementById(id);
      if (!node || node.id === 'wrn-about-184') return;
      if (!hiddenNodes.has(node)) hiddenNodes.set(node, { hidden: node.hidden, display: node.style.display });
      node.hidden = true;
      node.style.display = 'none';
    });
  }

  function show() {
    hideStandard();
    const root = ensureRoot();
    render();
    root.hidden = false;
    root.style.display = 'block';
    document.body.dataset.wrnTab = 'about';
  }

  function hide() {
    const root = document.getElementById('wrn-about-184');
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

  window.WRNAbout184 = Object.freeze({
    show, hide, render,
    label: code => copy(code).nav
  });
})();
