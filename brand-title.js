/* World Revolution News 1.7.13 – kompakte Titelgrafik */
'use strict';

(() => {
  if (window.__wrnBrandTitle1713) return;
  window.__wrnBrandTitle1713 = true;

  function install() {
    const header = document.querySelector('header');
    const heading = header?.querySelector('h1');
    if (!header || !heading) return false;

    /*
     * Alte oder mehrfach eingefügte Titelbilder entfernen.
     * Der Text im H1 bleibt für Screenreader und als Fehler-Fallback erhalten.
     */
    header.querySelectorAll(
      '.wrn-brand-title-image, .wrn-title-script, '
      + 'img[src*="wrn-title-script"]'
    ).forEach(node => node.remove());

    const image = document.createElement('img');
    image.className = 'wrn-brand-title-image';
    image.src = './wrn-title-script.webp?v=1713';
    image.alt = '';
    image.setAttribute('aria-hidden', 'true');
    image.decoding = 'async';
    image.fetchPriority = 'high';
    image.draggable = false;

    image.addEventListener('load', () => {
      header.classList.add('wrn-brand-title-ready');
    }, { once: true });

    image.addEventListener('error', () => {
      image.remove();
      header.classList.remove('wrn-brand-title-ready');
    }, { once: true });

    heading.insertAdjacentElement('afterend', image);
    return true;
  }

  function start() {
    if (install()) return;

    let attempts = 0;
    const timer = window.setInterval(() => {
      attempts += 1;
      if (install() || attempts >= 20) {
        window.clearInterval(timer);
      }
    }, 150);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }

  window.addEventListener('pageshow', install);
})();
