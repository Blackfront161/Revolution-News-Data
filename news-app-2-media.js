/* World Revolution News – News App 2 media helpers */
'use strict';

(function expose(factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.WRNNewsApp2Media = Object.freeze(api);
})(function createMediaHelpers() {
  const POLITICS = /anarch|antifasc|anti-fasc|anticapital|anti-capital|libertar|communis|solidarit|strike|union|labou?r|protest|revolution|prison|border|migration|racis|colonial|imperial|feminis|queer|climate|ecolog|indigenous|housing|squat|politi|society|gesellschaft|politik|bewegung/i;
  const CULTURE = /culture|kultur|book|literature|music|film|theatre|theater|art|kunst|history|geschichte/i;

  const INFORMATION_VIDEOS = Object.freeze([
    {
      id: 'lrTzjaXskUU',
      title: 'How Anarchy Works',
      source: 'Andrewism',
      language: 'English',
      region: 'Latin America',
      url: 'https://www.youtube.com/watch?v=lrTzjaXskUU',
      channelUrl: 'https://www.youtube.com/@Andrewism',
      summary: 'A clear introduction to cooperation and organisation without rulers.'
    },
    {
      id: 'o8Btb1sGRK0',
      title: 'How Does Anarchy Handle “Bad People”?',
      source: 'Andrewism',
      language: 'English',
      region: 'Latin America',
      url: 'https://www.youtube.com/watch?v=o8Btb1sGRK0',
      channelUrl: 'https://www.youtube.com/@Andrewism',
      summary: 'Community responses to harm without relying on authoritarian institutions.'
    },
    {
      id: 'nrm4gj_eDGA',
      title: 'David Graeber on Democracy and Debt',
      source: 'David Graeber / OWS Free University',
      language: 'English',
      region: 'North America',
      url: 'https://www.youtube.com/watch?v=nrm4gj_eDGA',
      channelUrl: 'https://davidgraeber.org/videos/',
      summary: 'An open-air lecture connecting democracy, debt and organising.'
    },
    {
      id: 'mOlpZzlh09s',
      title: 'Anarchism: What It Really Stands For',
      source: 'Audible Anarchist / Emma Goldman',
      language: 'English',
      region: 'Europe',
      url: 'https://www.youtube.com/watch?v=mOlpZzlh09s',
      channelUrl: 'https://www.youtube.com/channel/UCaO1QA8QL99_eb0XhJI2Fyw',
      summary: 'A volunteer-read introduction to Emma Goldman’s explanation of anarchism.'
    },
    {
      id: 'mfEYye6TNlk',
      title: 'Ecology and Revolutionary Thought',
      source: 'Audible Anarchist / Murray Bookchin',
      language: 'English',
      region: 'North America',
      url: 'https://www.youtube.com/watch?v=mfEYye6TNlk',
      channelUrl: 'https://www.youtube.com/channel/UCaO1QA8QL99_eb0XhJI2Fyw',
      summary: 'An introduction to the connection between ecological and social domination.'
    },
    {
      id: 'submedia-channel',
      title: 'subMedia',
      source: 'Anarchist video collective',
      language: 'Multilingual',
      region: 'Global',
      url: 'https://kolektiva.media/a/submedia/video-channels',
      channelUrl: 'https://kolektiva.media/a/submedia/video-channels',
      summary: 'Movement reporting, documentaries and analysis from struggles around the world.'
    }
  ]);

  function text(value) {
    return String(value ?? '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function safeUrl(value) {
    try {
      const url = new URL(String(value || ''));
      return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch {
      return '';
    }
  }

  function categoryFor(item) {
    const haystack = [
      item?.title,
      item?.description,
      ...(item?.topics || []),
      ...(item?.categories || [])
    ].join(' ');
    if (POLITICS.test(haystack)) return 'politics';
    if (CULTURE.test(haystack)) return 'culture';
    return 'society';
  }

  function normalizePodcast(item) {
    return {
      id: text(item?.id || `${item?.sourceName || ''}:${item?.title || ''}:${item?.published || ''}`),
      title: text(item?.title || 'Untitled'),
      description: text(item?.description),
      source: text(item?.sourceName || item?.source || 'Unknown source'),
      sourcePriority: Number(item?.sourcePriority || 0),
      published: text(item?.published),
      timestamp: Date.parse(item?.published || '') || 0,
      duration: text(item?.duration),
      language: text(item?.language),
      country: text(item?.country),
      region: text(item?.region || 'Global'),
      audioUrl: safeUrl(item?.audioUrl || item?.url),
      episodeUrl: safeUrl(item?.episodeUrl || item?.link),
      artwork: safeUrl(item?.artwork),
      topics: Array.isArray(item?.topics) ? item.topics.map(text).filter(Boolean) : [],
      categories: Array.isArray(item?.categories) ? item.categories.map(text).filter(Boolean) : [],
      category: categoryFor(item)
    };
  }

  function normalizeRadio(item) {
    const streams = (item?.streamCandidates || []).map(safeUrl).filter(Boolean);
    return {
      id: text(item?.id || item?.name),
      name: text(item?.name || 'Radio'),
      city: text(item?.city),
      country: text(item?.country),
      region: text(item?.region || 'Global'),
      languages: Array.isArray(item?.languages) ? item.languages.map(text).filter(Boolean) : [],
      topics: Array.isArray(item?.topics) ? item.topics.map(text).filter(Boolean) : [],
      description: text(item?.description),
      website: safeUrl(item?.website),
      streams,
      streamUrl: streams[0] || '',
      healthStatus: text(item?.healthStatus || 'unknown')
    };
  }

  function isRelevantPodcast(item) {
    if (!item) return false;
    const normalized = item.category ? item : normalizePodcast(item);
    const haystack = [
      normalized.title,
      normalized.description,
      normalized.source,
      ...normalized.topics,
      ...normalized.categories
    ].join(' ');
    return POLITICS.test(haystack)
      || normalized.topics.length > 0
      || normalized.sourcePriority >= 70;
  }

  function filterItems(items, filters = {}) {
    const query = text(filters.query).toLocaleLowerCase();
    return (Array.isArray(items) ? items : []).filter(item => {
      if (filters.region && filters.region !== 'all' && item.region !== filters.region) return false;
      if (filters.category && filters.category !== 'all' && item.category !== filters.category) return false;
      if (!query) return true;
      return [
        item.title,
        item.name,
        item.source,
        item.description,
        item.region,
        item.country,
        ...(item.topics || [])
      ].join(' ').toLocaleLowerCase().includes(query);
    });
  }

  return {
    INFORMATION_VIDEOS,
    categoryFor,
    filterItems,
    isRelevantPodcast,
    normalizePodcast,
    normalizeRadio,
    safeUrl,
    text
  };
});
