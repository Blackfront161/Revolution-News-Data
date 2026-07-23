/* World Revolution News 1.7.19 – Flyer-Designer für Zine */
'use strict';

(() => {
    if (window.WRNZineDesigner1719) return;

    const STORAGE_KEY = 'wrn-zine-design-1719';

    const defaults = {
        format: 'a4',
        style: 'cyber',
        columns: '2',
        images: 'normal',
        density: 'comfortable',
        headline: 'WORLD REVOLUTION NEWS',
        intro: '',
        footer: 'worldrevnews'
    };

    let settings = { ...defaults };

    try {
        settings = {
            ...defaults,
            ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
        };
    } catch {
        settings = { ...defaults };
    }

    const text = () => {
        const de = String(
            document.getElementById('ui-language')?.value
            || document.documentElement.lang
            || ''
        ).toLowerCase().startsWith('de');

        return de
            ? {
                title: '3. Ausgabe gestalten und exportieren',
                workflow: '1. Artikel auswählen  ·  2. Texte bearbeiten  ·  3. Gestaltung wählen und als PDF speichern',
                headline: 'Titel der Ausgabe',
                intro: 'Kurze Einleitung (optional)',
                footer: 'Fußzeile / Kontakt (optional)',
                format: 'Format',
                style: 'Stil',
                columns: 'Spalten',
                images: 'Bilder',
                density: 'Abstand',
                print: 'Drucken / als PDF',
                reset: 'Zurücksetzen',
                a4: 'A4 Hochformat',
                a5: 'A5 Hochformat',
                square: 'Quadratisch',
                story: 'Story 9:16',
                cyber: 'Cyberpunk',
                newspaper: 'Zeitung',
                minimal: 'Minimal',
                contrast: 'Hoher Kontrast',
                normal: 'Normal',
                gray: 'Graustufen',
                none: 'Ohne Bilder',
                compact: 'Kompakt',
                comfortable: 'Luftig'
            }
            : {
                title: '3. Design and export',
                workflow: '1. Select articles  ·  2. Edit the text  ·  3. Choose a design and save as PDF',
                headline: 'Issue title',
                intro: 'Short introduction (optional)',
                footer: 'Footer / contact (optional)',
                format: 'Format',
                style: 'Style',
                columns: 'Columns',
                images: 'Images',
                density: 'Spacing',
                print: 'Print / save PDF',
                reset: 'Reset',
                a4: 'A4 portrait',
                a5: 'A5 portrait',
                square: 'Square',
                story: 'Story 9:16',
                cyber: 'Cyberpunk',
                newspaper: 'Newspaper',
                minimal: 'Minimal',
                contrast: 'High contrast',
                normal: 'Normal',
                gray: 'Grayscale',
                none: 'No images',
                compact: 'Compact',
                comfortable: 'Comfortable'
            };
    };

    const findTarget = () => document.querySelector(
        '#zine-container, .zine-container, .wrn-zine, '
        + '[data-wrn-zine], .zine-preview, #zine-preview'
    );

    const apply = target => {
        if (!target) return;

        target.classList.add('wrn-zine-design-target-1719');
        target.dataset.zineFormat = settings.format;
        target.dataset.zineStyle = settings.style;
        target.dataset.zineColumns = settings.columns;
        target.dataset.zineImages = settings.images;
        target.dataset.zineDensity = settings.density;

        try {
            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(settings)
            );
        } catch {
            // Local storage is optional.
        }
    };

    const control = (label, name, options) => `
        <label>
            <span>${label}</span>
            <select data-zine-setting="${name}">
                ${options.map(([value, text]) => `
                    <option value="${value}">
                        ${text}
                    </option>
                `).join('')}
            </select>
        </label>
    `;

    const textControl = (label, name) => `
        <label class="wrn-zine-designer-text-1719">
            <span>${label}</span>
            <input type="text" data-zine-text="${name}">
        </label>
    `;

    const install = () => {
        const target = findTarget();

        if (!target) return false;

        if (document.getElementById('wrn-zine-designer-1719')) {
            apply(target);
            return true;
        }

        const t = text();
        const panel = document.createElement('section');
        panel.id = 'wrn-zine-designer-1719';
        panel.className = 'wrn-zine-designer-1719';
        panel.innerHTML = `
            <header>
                <h2>${t.title}</h2>
                <p>${t.workflow}</p>
            </header>

            <div class="wrn-zine-designer-copy-1719">
                ${textControl(t.headline, 'headline')}
                ${textControl(t.intro, 'intro')}
                ${textControl(t.footer, 'footer')}
            </div>
            <div class="wrn-zine-designer-grid-1719">
                ${control(t.format, 'format', [
                    ['a4', t.a4],
                    ['a5', t.a5],
                    ['square', t.square],
                    ['story', t.story]
                ])}

                ${control(t.style, 'style', [
                    ['cyber', t.cyber],
                    ['newspaper', t.newspaper],
                    ['minimal', t.minimal],
                    ['contrast', t.contrast]
                ])}

                ${control(t.columns, 'columns', [
                    ['1', '1'],
                    ['2', '2'],
                    ['3', '3']
                ])}

                ${control(t.images, 'images', [
                    ['normal', t.normal],
                    ['gray', t.gray],
                    ['none', t.none]
                ])}

                ${control(t.density, 'density', [
                    ['comfortable', t.comfortable],
                    ['compact', t.compact]
                ])}
            </div>

            <div class="wrn-zine-designer-actions-1719">
                <button type="button" data-zine-action="print">
                    ${t.print}
                </button>
                <button type="button" data-zine-action="reset">
                    ${t.reset}
                </button>
            </div>
        `;

        target.parentElement?.insertBefore(panel, target);

        panel.querySelectorAll('[data-zine-setting]')
            .forEach(select => {
                const name = select.dataset.zineSetting;
                select.value = settings[name];

                select.addEventListener('change', () => {
                    settings[name] = select.value;
                    apply(target);
                });
            });

        panel.querySelectorAll('[data-zine-text]').forEach(input => {
            const name = input.dataset.zineText;
            input.value = settings[name] || '';
            input.addEventListener('input', () => {
                settings[name] = input.value.slice(0, 180);
                apply(target);
            });
        });

        panel.addEventListener('click', event => {
            const action = event.target.closest(
                '[data-zine-action]'
            )?.dataset.zineAction;

            if (action === 'print') {
                target.classList.add('wrn-zine-printing-1719');
                window.print();
                window.setTimeout(() => {
                    target.classList.remove('wrn-zine-printing-1719');
                }, 500);
            }

            if (action === 'reset') {
                settings = { ...defaults };

                panel.querySelectorAll('[data-zine-setting]')
                    .forEach(select => {
                        const name = select.dataset.zineSetting;
                        select.value = settings[name];
                    });
                panel.querySelectorAll('[data-zine-text]').forEach(input => {
                    input.value = settings[input.dataset.zineText] || '';
                });

                apply(target);
            }
        });

        apply(target);
        return true;
    };

    const queueInstall = () => {
        window.setTimeout(install, 80);
        window.setTimeout(install, 500);
        window.setTimeout(install, 1400);
    };

    document.addEventListener('click', event => {
        if (
            event.target.closest?.(
                '.wrn-top-tab[data-key="zine"]'
            )
        ) {
            queueInstall();
        }
    });

    new MutationObserver(records => {
        if (records.some(record => record.addedNodes.length)) {
            install();
        }
    }).observe(document.documentElement, {
        childList: true,
        subtree: true
    });

    window.WRNZineDesigner1719 = Object.freeze({
        install,
        settings: () => ({ ...settings })
    });
})();
