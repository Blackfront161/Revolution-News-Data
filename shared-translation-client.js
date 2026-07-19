/* World Revolution News 1.7.5 – gemeinsamer Übersetzungs-Cache */
'use strict';

(() => {
  if (window.WRNSharedTranslations) return;

  const originalRequest = window.fetchTranslationRequest;

  function targetLanguage() {
    try {
      return typeof currentLang !== 'undefined' ? currentLang : (document.documentElement.lang || 'en');
    } catch {
      return document.documentElement.lang || 'en';
    }
  }

  async function sha256(value) {
    const bytes = new TextEncoder().encode(String(value || ''));
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('');
  }

  function extractText(data) {
    if (typeof window.extractTranslationText === 'function') {
      return window.extractTranslationText(data);
    }
    if (typeof data === 'string') return data.trim();
    return String(
      data?.text
      || data?.translation
      || data?.translatedText
      || data?.result?.text
      || ''
    ).trim();
  }

  async function request(args = {}) {
    const endpoint = String(window.WRN_CONFIG?.sharedTranslationUrl || '').trim();
    if (!endpoint) {
      return typeof originalRequest === 'function'
        ? originalRequest(args)
        : { error: true, message: 'Translation function unavailable.' };
    }

    const title = String(args.title || '').slice(0, 500);
    const text = String(args.text || '').slice(0, 6000);
    const mode = String(args.mode || 'title_and_text');
    const language = targetLanguage();
    const cacheKey = await sha256(JSON.stringify({
      version: 1,
      language,
      mode,
      title,
      text
    }));

    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 45000);

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Id': typeof getClientId === 'function' ? getClientId() : 'wrn-web',
          'X-WRN-Cache-Key': cacheKey
        },
        body: JSON.stringify({
          action: 'translate',
          targetLanguage: language,
          mode,
          title,
          text,
          sharedCacheKey: cacheKey,
          cacheVersion: 1
        }),
        signal: controller.signal
      });

      const raw = await response.text();
      let data = raw;
      try { data = raw ? JSON.parse(raw) : {}; } catch {}

      const translatedText = typeof cleanTranslationOutput === 'function'
        ? cleanTranslationOutput(extractText(data))
        : extractText(data);
      const cacheState = response.headers.get('X-WRN-Shared-Cache') || data?.sharedCache || '';
      const storage = response.headers.get('X-WRN-Storage') || data?.storage || '';
      const providerBase = String(data?.provider || '');
      const provider = [providerBase, cacheState ? `shared:${cacheState.toLowerCase()}` : '']
        .filter(Boolean)
        .join(' · ');

      if (response.ok && translatedText) {
        dispatchState({ type: 'translation', ok: true, cacheState, storage, language, mode });
        return {
          error: false,
          text: translatedText,
          status: response.status,
          provider,
          sharedCache: cacheState,
          cached: cacheState.toUpperCase() === 'HIT',
          storage
        };
      }

      return {
        error: true,
        status: response.status,
        message: data?.message || data?.error?.message || 'Shared translation request failed.',
        data
      };
    } catch (error) {
      dispatchState({ type: 'translation', ok: false, fallback: true, error: String(error?.message || error) });
      if (typeof originalRequest === 'function') return originalRequest(args);
      return {
        error: true,
        status: 0,
        message: error?.name === 'AbortError'
          ? 'The shared translation request timed out.'
          : String(error?.message || error)
      };
    } finally {
      window.clearTimeout(timer);
    }
  }

  window.fetchTranslationRequest = request;
  try { fetchTranslationRequest = request; } catch {}

  function dispatchState(detail) {
    window.dispatchEvent(new CustomEvent('wrnsharedtranslationstate', { detail }));
  }

  async function health() {
    const endpoint = String(window.WRN_CONFIG?.sharedTranslationUrl || '').trim().replace(/\/$/, '');
    if (!endpoint) return { ok: false, disabled: true };
    try {
      const response = await fetch(`${endpoint}/health`, { cache: 'no-store' });
      const data = await response.json();
      const result = { ok: response.ok && data?.ok === true, status: response.status, ...data };
      dispatchState({ type: 'health', ...result });
      return result;
    } catch (error) {
      const result = { ok: false, error: String(error?.message || error) };
      dispatchState({ type: 'health', ...result });
      return result;
    }
  }

  window.WRNSharedTranslations = Object.freeze({
    enabled: () => Boolean(String(window.WRN_CONFIG?.sharedTranslationUrl || '').trim()),
    request,
    health,
    sha256
  });
})();
