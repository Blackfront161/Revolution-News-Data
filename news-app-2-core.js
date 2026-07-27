/* World Revolution News – News App 2 preview core */
'use strict';

(function expose(factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof window !== 'undefined') window.WRNNewsApp2Core = Object.freeze(api);
})(function createCore() {
  const REGION_ALIASES = Object.freeze({
    'Australia & NZ': 'Oceania',
    Australia: 'Oceania',
    'North Am.': 'North America',
    'Latin Am.': 'Latin America'
  });

  function text(value) {
    return String(value ?? '').replace(/\s+/g, ' ').trim();
  }

  function stripHtml(value) {
    return text(String(value ?? '')
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/gi, ' ')
      .replace(/&amp;/gi, '&')
      .replace(/&quot;/gi, '"')
      .replace(/&#39;/gi, "'"))
      .replace(/\s+([,.;:!?])/g, '$1');
  }

  function safeHttpUrl(value) {
    try {
      const url = new URL(String(value || ''));
      return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch {
      return '';
    }
  }

  function dateValue(article) {
    const timestamp = Date.parse(
      article?.pubDate || article?.date || article?.eventStart || ''
    );
    return Number.isFinite(timestamp) ? timestamp : 0;
  }

  function articleId(article) {
    return text(article?.link)
      || `${text(article?.quelleName)}::${text(article?.title)}::${dateValue(article)}`;
  }

  function normalizeRegion(value) {
    const region = text(value);
    return REGION_ALIASES[region] || region || 'Global';
  }

  function normalizeArticle(article) {
    const categories = Array.isArray(article?.categories)
      ? article.categories.map(text).filter(Boolean)
      : [];
    const primaryRegion = normalizeRegion(
      article?.primaryRegion || article?.kontinent || categories[0]
    );
    const primaryTopic = text(
      article?.primaryTopic
      || categories.find(item => normalizeRegion(item) !== primaryRegion)
      || ''
    );
    const content = stripHtml(
      article?.content || article?.description || article?.summary || ''
    );

    return {
      ...article,
      id: articleId(article),
      type: text(article?.type || 'article'),
      title: text(article?.title || 'Untitled'),
      intro: excerpt(content, 230),
      content,
      source: text(article?.quelleName || article?.source || 'Unknown source'),
      author: text(article?.author),
      link: safeHttpUrl(article?.link),
      image: safeHttpUrl(article?.image || article?.imageUrl),
      primaryRegion,
      primaryTopic,
      secondaryTopics: Array.isArray(article?.secondaryTopics)
        ? article.secondaryTopics.map(text).filter(Boolean)
        : [],
      categories,
      timestamp: dateValue(article)
    };
  }

  function normalizeArticles(payload) {
    const source = Array.isArray(payload)
      ? payload
      : Array.isArray(payload?.items)
        ? payload.items
        : Array.isArray(payload?.articles)
          ? payload.articles
          : [];
    const seen = new Set();

    return source
      .filter(item => item && typeof item === 'object' && item.type !== 'event')
      .map(normalizeArticle)
      .filter(item => {
        const key = `${item.link || ''}|${item.title.toLowerCase()}`;
        if (!item.title || seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((a, b) => b.timestamp - a.timestamp);
  }

  function excerpt(value, maxLength = 180) {
    const clean = stripHtml(value);
    if (clean.length <= maxLength) return clean;
    const slice = clean.slice(0, Math.max(1, maxLength - 1));
    const boundary = slice.lastIndexOf(' ');
    return `${slice.slice(0, boundary > maxLength * 0.55 ? boundary : slice.length)}…`;
  }

  function balanceBySource(items, limit = 10, maxPerSource = 2) {
    const source = Array.isArray(items) ? items : [];
    const remaining = source.slice();
    const result = [];
    const counts = new Map();
    let lastSource = '';

    while (remaining.length && result.length < limit) {
      let index = remaining.findIndex(item => {
        const name = text(item?.source || item?.quelleName);
        return name !== lastSource && (counts.get(name) || 0) < maxPerSource;
      });
      if (index < 0) {
        index = remaining.findIndex(item => {
          const name = text(item?.source || item?.quelleName);
          return (counts.get(name) || 0) < maxPerSource;
        });
      }
      if (index < 0) break;

      const [item] = remaining.splice(index, 1);
      const name = text(item?.source || item?.quelleName);
      result.push(item);
      counts.set(name, (counts.get(name) || 0) + 1);
      lastSource = name;
    }

    return result;
  }

  function matchesPreferences(article, preferences = {}) {
    const regions = new Set(preferences.regions || []);
    const topics = new Set(preferences.topics || []);
    const sources = new Set(preferences.sources || []);
    const blockedSources = new Set(preferences.blockedSources || []);

    if (blockedSources.has(article.source)) return false;
    if (!regions.size && !topics.size && !sources.size) return true;

    const articleTopics = new Set([
      article.primaryTopic,
      ...(article.secondaryTopics || []),
      ...(article.categories || [])
    ].filter(Boolean));

    return regions.has(article.primaryRegion)
      || sources.has(article.source)
      || [...topics].some(topic => articleTopics.has(topic));
  }

  function filterArticles(items, filters = {}) {
    const query = text(filters.query).toLocaleLowerCase();
    return (Array.isArray(items) ? items : []).filter(article => {
      if (filters.region && article.primaryRegion !== filters.region) return false;
      if (
        filters.topic
        && article.primaryTopic !== filters.topic
        && !(article.secondaryTopics || []).includes(filters.topic)
        && !(article.categories || []).includes(filters.topic)
      ) return false;
      if (filters.source && article.source !== filters.source) return false;
      if (!query) return true;
      return [
        article.title,
        article.intro,
        article.source,
        article.primaryRegion,
        article.primaryTopic
      ].join(' ').toLocaleLowerCase().includes(query);
    });
  }

  function collectFacets(items) {
    const regions = new Set();
    const topics = new Set();
    const sources = new Set();

    for (const article of Array.isArray(items) ? items : []) {
      if (article.primaryRegion) regions.add(article.primaryRegion);
      if (article.primaryTopic) topics.add(article.primaryTopic);
      for (const topic of article.secondaryTopics || []) topics.add(topic);
      if (article.source) sources.add(article.source);
    }

    return {
      regions: [...regions].sort((a, b) => a.localeCompare(b)),
      topics: [...topics].sort((a, b) => a.localeCompare(b)),
      sources: [...sources].sort((a, b) => a.localeCompare(b))
    };
  }

  function splitTranslatedTeaser(value) {
    const clean = text(value);
    const separators = [/\s+---\s+/, /\n-{3,}\n/, /\n\n+/];
    for (const separator of separators) {
      const parts = String(value || '').trim().split(separator);
      if (parts.length >= 2) {
        return {
          title: text(parts.shift()),
          intro: text(parts.join(' '))
        };
      }
    }
    return { title: clean, intro: '' };
  }

  function hasVideo(article) {
    const haystack = [
      article?.link,
      article?.content,
      article?.description
    ].join(' ').toLowerCase();
    return /youtube\.com|youtu\.be|vimeo\.com|peertube|kolektiva\.media/.test(haystack);
  }

  return {
    articleId,
    balanceBySource,
    collectFacets,
    dateValue,
    excerpt,
    filterArticles,
    hasVideo,
    matchesPreferences,
    normalizeArticle,
    normalizeArticles,
    normalizeRegion,
    safeHttpUrl,
    splitTranslatedTeaser,
    stripHtml,
    text
  };
});
