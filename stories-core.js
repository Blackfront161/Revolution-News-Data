/* World Revolution News 1.8.0 – pure story and briefing analysis */
'use strict';

((root, factory) => {
  const api = factory();

  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  }

  if (root) {
    root.WRNStoriesCore = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, () => {
  const STOPWORDS = new Set([
    'the','and','for','with','from','that','this','into','over','after','against','about','their','they','are','was','were','will','has','have',
    'der','die','das','den','dem','des','und','mit','für','von','aus','auf','gegen','über','eine','einer','einem','einen','ist','sind','wird','werden',
    'les','des','une','pour','avec','dans','sur','contre','est','sont','aux','par',
    'del','los','las','una','para','con','por','contra','sobre','desde',
    'sono','della','delle','degli','una','con','per','contro',
    'que','dos','das','uma','com','sem','sobre','contra',
    'это','для','как','что','или','при','был','будет',
    'και','των','για','από','στο','στη','είναι',
    'ile','bir','bu','için','karşı','olan'
  ]);

  function cleanText(value) {
    return String(value ?? '')
      .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;|&#160;/gi, ' ')
      .replace(/&amp;/gi, '&')
      .replace(/&quot;|&#34;/gi, '"')
      .replace(/&#39;|&apos;/gi, "'")
      .replace(/\s+/g, ' ')
      .trim();
  }

  function normalizeToken(value) {
    return String(value || '')
      .normalize('NFKD')
      .replace(/\p{M}/gu, '')
      .toLocaleLowerCase();
  }

  function tokens(value, limit = 16) {
    return normalizeToken(cleanText(value))
      .replace(/[^\p{L}\p{N}\s-]/gu, ' ')
      .split(/\s+/)
      .map(token => token.replace(/^-+|-+$/g, ''))
      .filter(token =>
        token.length > 2
        && !STOPWORDS.has(token)
        && !/^\d+$/.test(token)
      )
      .slice(0, limit);
  }

  function unique(values) {
    return [...new Set(values.filter(Boolean))];
  }

  function jaccard(first, second) {
    const a = new Set(first);
    const b = new Set(second);

    if (!a.size || !b.size) return 0;

    let intersection = 0;

    for (const token of a) {
      if (b.has(token)) intersection += 1;
    }

    return intersection / (a.size + b.size - intersection);
  }

  function sharedCount(first, second) {
    const other = new Set(second);
    return unique(first).filter(token => other.has(token)).length;
  }

  function dateMs(item) {
    const raw = item?.eventStart
      || item?.pubDate
      || item?.published
      || item?.date
      || item?.createdAt;

    const value = raw ? new Date(raw).getTime() : 0;
    return Number.isFinite(value) ? value : 0;
  }

  function sourceName(item) {
    return cleanText(
      item?.quelleName
      || item?.sourceName
      || item?.source
      || item?.author
      || ''
    );
  }

  function itemKey(item) {
    return cleanText(
      item?.link
      || item?.id
      || `${sourceName(item)}::${item?.title || ''}::${dateMs(item)}`
    );
  }

  function isEvent(item) {
    return Boolean(
      item?.type === 'event'
      || item?.kategorie === 'Radar'
      || item?.eventStart
    );
  }

  function itemTokens(item) {
    return tokens(
      `${item?.title || ''} ${item?.summary || ''}`,
      18
    );
  }

  function clusterLabel(items, fallback = 'Story') {
    const counts = new Map();

    for (const item of items) {
      for (const token of unique(itemTokens(item))) {
        counts.set(token, (counts.get(token) || 0) + 1);
      }
    }

    const keywords = [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || b[0].length - a[0].length)
      .filter(([, count]) => count >= Math.min(2, items.length))
      .slice(0, 4)
      .map(([token]) => token);

    if (keywords.length >= 2) {
      return keywords
        .map(token => token.charAt(0).toLocaleUpperCase() + token.slice(1))
        .join(' · ');
    }

    return cleanText(items[0]?.title || fallback);
  }

  function clusterStories(items, options = {}) {
    const now = Number(options.now || Date.now());
    const days = Math.max(1, Number(options.days || 30));
    const minSources = Math.max(1, Number(options.minSources || 2));
    const minItems = Math.max(2, Number(options.minItems || 2));
    const threshold = Number(options.threshold || 0.27);
    const cutoff = now - days * 86400000;

    const rows = (Array.isArray(items) ? items : [])
      .filter(item => item && cleanText(item.title))
      .map(item => ({
        item,
        date: dateMs(item),
        source: sourceName(item),
        tokens: itemTokens(item)
      }))
      .filter(row => row.date >= cutoff && row.tokens.length >= 2)
      .sort((a, b) => b.date - a.date);

    const clusters = [];

    for (const row of rows) {
      let best = null;
      let bestScore = 0;

      for (const cluster of clusters) {
        const representative = cluster.tokens;
        const similarity = jaccard(row.tokens, representative);
        const shared = sharedCount(row.tokens, representative);
        const score = similarity + Math.min(shared, 4) * 0.04;

        if (
          score > bestScore
          && (
            similarity >= threshold
            || shared >= 3
          )
        ) {
          best = cluster;
          bestScore = score;
        }
      }

      if (!best) {
        clusters.push({
          rows: [row],
          tokens: [...row.tokens],
          newest: row.date,
          oldest: row.date
        });
        continue;
      }

      best.rows.push(row);
      best.newest = Math.max(best.newest, row.date);
      best.oldest = Math.min(best.oldest, row.date);

      const tokenCounts = new Map();

      for (const entry of best.rows) {
        for (const token of unique(entry.tokens)) {
          tokenCounts.set(token, (tokenCounts.get(token) || 0) + 1);
        }
      }

      best.tokens = [...tokenCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 16)
        .map(([token]) => token);
    }

    return clusters
      .map(cluster => {
        const ordered = cluster.rows
          .sort((a, b) => a.date - b.date)
          .map(row => row.item);

        const sources = unique(
          cluster.rows.map(row => row.source)
        );

        const story = {
          id: hashlibId(
            ordered
              .map(itemKey)
              .sort()
              .join('|')
          ),
          title: cleanText(
            ordered[ordered.length - 1]?.title
            || clusterLabel(ordered)
          ),
          items: ordered,
          sources,
          sourceCount: sources.length,
          itemCount: ordered.length,
          oldest: cluster.oldest,
          newest: cluster.newest,
          keywords: cluster.tokens.slice(0, 6),
          eventCount: ordered.filter(isEvent).length
        };

        const recency = Math.max(
          0,
          1 - (now - story.newest) / (days * 86400000)
        );

        story.score = (
          story.sourceCount * 3
          + story.itemCount * 1.5
          + recency * 4
        );

        return story;
      })
      .filter(story =>
        story.itemCount >= minItems
        && story.sourceCount >= minSources
      )
      .sort((a, b) =>
        b.score - a.score
        || b.newest - a.newest
      );
  }

  function hashlibId(value) {
    let hash = 2166136261;

    for (const character of String(value || '')) {
      hash ^= character.codePointAt(0);
      hash = Math.imul(hash, 16777619);
    }

    return `wrn-story-${(hash >>> 0).toString(36)}`;
  }

  function summarizeText(value, maximum = 360) {
    const text = cleanText(value);

    if (!text) return '';

    const sentences = text.match(
      /[^.!?…]+[.!?…]+|[^.!?…]+$/g
    ) || [text];

    const summary = sentences
      .slice(0, 2)
      .join(' ')
      .trim();

    if (summary.length <= maximum) return summary;

    return `${summary
      .slice(0, maximum)
      .replace(/\s+\S*$/, '')
      .trim()}…`;
  }

  function perspectiveRows(story, maximum = 4) {
    const seen = new Set();
    const rows = [];

    for (const item of [...(story?.items || [])].reverse()) {
      const source = sourceName(item) || 'Source';

      if (seen.has(source)) continue;
      seen.add(source);

      rows.push({
        source,
        title: cleanText(item.title),
        summary: summarizeText(
          item.summary
          || item.description
          || item.content
          || item.title
        ),
        link: cleanText(item.link),
        date: dateMs(item)
      });

      if (rows.length >= maximum) break;
    }

    return rows;
  }

  function flattenBriefingHistory(history, days = 7, now = Date.now()) {
    const cutoff = now - days * 86400000;
    const rows = [];

    for (const briefing of Array.isArray(history) ? history : []) {
      const briefingDate = new Date(
        `${briefing?.date || ''}T12:00:00`
      ).getTime();

      if (!Number.isFinite(briefingDate) || briefingDate < cutoff) {
        continue;
      }

      for (const section of briefing?.sections || []) {
        for (const item of section?.items || []) {
          if (item?.isConnection) continue;

          rows.push({
            ...item,
            briefingDate,
            sectionId: section.id || ''
          });
        }
      }
    }

    return rows;
  }

  function weeklyInsights(history, options = {}) {
    const now = Number(options.now || Date.now());
    const days = Math.max(1, Number(options.days || 7));
    const rows = flattenBriefingHistory(history, days, now);

    const stories = clusterStories(rows, {
      now,
      days,
      minSources: 1,
      minItems: 2,
      threshold: 0.22
    }).slice(0, 6);

    const sources = new Map();
    const dates = new Set();

    for (const row of rows) {
      const source = sourceName(row);

      if (source) {
        sources.set(source, (sources.get(source) || 0) + 1);
      }

      if (row.briefingDate) {
        dates.add(new Date(row.briefingDate)
          .toISOString()
          .slice(0, 10));
      }
    }

    return {
      daysCovered: dates.size,
      itemCount: rows.length,
      sourceCount: sources.size,
      newCount: rows.filter(item => item.isNew).length,
      updatedCount: rows.filter(item => item.isUpdated).length,
      storyCount: stories.length,
      stories,
      topSources: [...sources.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([source, count]) => ({ source, count }))
    };
  }

  function normalizeWatchTerms(values) {
    const source = Array.isArray(values) ? values : [values];

    return unique(
      source
        .flatMap(value => String(value || '').split(/[,;\n]+/))
        .map(value => cleanText(value).slice(0, 80))
        .filter(value => value.length >= 2)
    ).slice(0, 30);
  }

  function matchesWatchlist(item, terms) {
    const normalizedTerms = normalizeWatchTerms(terms)
      .map(normalizeToken);

    if (!normalizedTerms.length) return false;

    const haystack = normalizeToken(
      `${item?.title || ''} `
      + `${item?.summary || ''} `
      + `${item?.description || ''} `
      + `${item?.content || ''} `
      + `${sourceName(item)}`
    );

    return normalizedTerms.some(term => haystack.includes(term));
  }

  return Object.freeze({
    cleanText,
    normalizeToken,
    tokens,
    jaccard,
    sharedCount,
    dateMs,
    sourceName,
    itemKey,
    isEvent,
    clusterStories,
    perspectiveRows,
    summarizeText,
    weeklyInsights,
    normalizeWatchTerms,
    matchesWatchlist
  });
});
