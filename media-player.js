/* World Revolution News – gemeinsamer Podcast- und Radio-Player */
'use strict';

const mediaUiTexts = {
    en:{play:'Play', pause:'Pause', stop:'Stop', loading:'Connecting…', playing:'Playing', paused:'Paused', failed:'Audio could not be loaded.'},
    de:{play:'Abspielen', pause:'Pause', stop:'Stop', loading:'Verbinde…', playing:'Läuft', paused:'Pausiert', failed:'Audio konnte nicht geladen werden.'},
    es:{play:'Reproducir', pause:'Pausa', stop:'Parar', loading:'Conectando…', playing:'Reproduciendo', paused:'Pausado', failed:'No se pudo cargar el audio.'},
    fr:{play:'Lecture', pause:'Pause', stop:'Arrêter', loading:'Connexion…', playing:'Lecture', paused:'En pause', failed:'Impossible de charger l’audio.'},
    it:{play:'Riproduci', pause:'Pausa', stop:'Stop', loading:'Connessione…', playing:'In riproduzione', paused:'In pausa', failed:'Impossibile caricare l’audio.'},
    pt:{play:'Reproduzir', pause:'Pausa', stop:'Parar', loading:'Conectando…', playing:'Reproduzindo', paused:'Pausado', failed:'Não foi possível carregar o áudio.'},
    ru:{play:'Воспроизвести', pause:'Пауза', stop:'Стоп', loading:'Подключение…', playing:'Воспроизведение', paused:'Пауза', failed:'Не удалось загрузить аудио.'},
    el:{play:'Αναπαραγωγή', pause:'Παύση', stop:'Στοπ', loading:'Σύνδεση…', playing:'Αναπαραγωγή', paused:'Παύση', failed:'Δεν ήταν δυνατή η φόρτωση του ήχου.'},
    tr:{play:'Oynat', pause:'Duraklat', stop:'Durdur', loading:'Bağlanıyor…', playing:'Çalıyor', paused:'Duraklatıldı', failed:'Ses yüklenemedi.'}
};
let globalMediaState = {
    id:'', kind:'', title:'', artist:'', candidates:[], candidateIndex:0,
    statusId:'', progressId:'', timeId:'', artwork:'', initialized:false
};

function getMediaUiText() {
    return mediaUiTexts[currentLang] || mediaUiTexts.en;
}

function normalizePlayableMediaUrl(value) {
    const safe = getSafeHttpUrl(value);
    if (!safe) return '';
    try {
        const url = new URL(safe);
        // Eine HTTPS-App darf keine HTTP-Audiodateien laden. Bei bekannten
        // Podcast-Hosts wird deshalb auf deren HTTPS-Adresse umgestellt.
        const upgradeHosts = new Set(['www.freie-radios.net', 'freie-radios.net']);
        if (url.protocol === 'http:' && upgradeHosts.has(url.hostname.toLowerCase())) {
            url.protocol = 'https:';
            return url.href;
        }
        if (location.protocol === 'https:' && url.protocol === 'http:') return '';
        return url.href;
    } catch { return ''; }
}

function uniquePlayableCandidates(values) {
    return [...new Set((Array.isArray(values) ? values : [values])
        .map(normalizePlayableMediaUrl)
        .filter(Boolean))];
}

function getGlobalMediaPlayer() {
    const audio = document.getElementById('global-media-player');
    if (!audio) return null;
    if (!globalMediaState.initialized) {
        globalMediaState.initialized = true;
        audio.addEventListener('loadstart', () => setGlobalMediaStatus(getMediaUiText().loading));
        audio.addEventListener('waiting', () => setGlobalMediaStatus(getMediaUiText().loading));
        audio.addEventListener('playing', () => {
            setGlobalMediaStatus(getMediaUiText().playing, 'playing');
            if ('mediaSession' in navigator) navigator.mediaSession.playbackState = 'playing';
            updateGlobalMediaButtons();
        });
        audio.addEventListener('pause', () => {
            if (!audio.ended && globalMediaState.id) setGlobalMediaStatus(getMediaUiText().paused);
            if ('mediaSession' in navigator) navigator.mediaSession.playbackState = 'paused';
            updateGlobalMediaButtons();
        });
        audio.addEventListener('ended', () => stopGlobalMedia());
        audio.addEventListener('error', () => tryNextGlobalMediaCandidate());
        ['loadedmetadata', 'durationchange', 'timeupdate', 'progress', 'emptied'].forEach(eventName => {
            audio.addEventListener(eventName, updateGlobalMediaProgress);
        });
        setupMediaSessionHandlers();
    }
    return audio;
}

function setGlobalMediaStatus(text, className='') {
    const globalStatus = document.getElementById('global-media-status');
    if (globalStatus) globalStatus.textContent = text || '';
    if (globalMediaState.statusId) {
        const localStatus = document.getElementById(globalMediaState.statusId);
        if (localStatus) {
            localStatus.textContent = text || '';
            localStatus.className = `media-card-status ${className}`.trim();
        }
    }
}

function updateGlobalMediaBar() {
    const bar = document.getElementById('global-media-bar');
    const title = document.getElementById('global-media-title');
    const subtitle = document.getElementById('global-media-subtitle');
    const pauseButton = document.getElementById('global-media-pause');
    const progressRow = document.getElementById('global-media-progress-row');
    const isLiveRadio = globalMediaState.kind === 'radio';
    if (bar) bar.hidden = !globalMediaState.id;
    if (title) title.textContent = globalMediaState.title || 'Audio';
    if (subtitle) subtitle.textContent = globalMediaState.artist || '';
    if (pauseButton) pauseButton.hidden = isLiveRadio;
    if (progressRow) progressRow.hidden = isLiveRadio;
    updateGlobalMediaButtons();
    updateGlobalMediaProgress();
}

function formatMediaTime(value) {
    const seconds = Number(value);
    if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
    const total = Math.floor(seconds);
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const rest = total % 60;
    return hours > 0
        ? `${hours}:${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`
        : `${minutes}:${String(rest).padStart(2, '0')}`;
}

function updateGlobalMediaProgress() {
    const audio = document.getElementById('global-media-player');
    if (!audio) return;
    const current = Number.isFinite(audio.currentTime) ? Math.max(0, audio.currentTime) : 0;
    const duration = Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : 0;
    const isLive = globalMediaState.kind === 'radio' || !duration;

    const updateRange = element => {
        if (!element) return;
        element.disabled = isLive || !globalMediaState.id;
        element.max = duration || 1;
        element.value = duration ? Math.min(current, duration) : 0;
    };
    const updateTime = element => {
        if (!element) return;
        element.textContent = isLive
            ? `${formatMediaTime(current)} / LIVE`
            : `${formatMediaTime(current)} / ${formatMediaTime(duration)}`;
    };

    updateRange(document.getElementById('global-media-progress'));
    updateTime(document.getElementById('global-media-time'));
    updateRange(globalMediaState.progressId ? document.getElementById(globalMediaState.progressId) : null);
    updateTime(globalMediaState.timeId ? document.getElementById(globalMediaState.timeId) : null);

    if ('mediaSession' in navigator && typeof navigator.mediaSession.setPositionState === 'function' && duration > 0) {
        try {
            navigator.mediaSession.setPositionState({
                duration,
                playbackRate: audio.playbackRate || 1,
                position: Math.min(current, Math.max(0, duration - 0.001))
            });
        } catch {}
    }
}

function seekGlobalMedia(value) {
    const audio = getGlobalMediaPlayer();
    const target = Number(value);
    if (!audio || !Number.isFinite(audio.duration) || audio.duration <= 0 || !Number.isFinite(target)) return;
    audio.currentTime = Math.max(0, Math.min(audio.duration, target));
    updateGlobalMediaProgress();
}

function updateGlobalMediaButtons() {
    const audio = document.getElementById('global-media-player');
    const t = getMediaUiText();
    document.querySelectorAll('.btn-media-play[data-media-id]').forEach(button => {
        button.textContent = `▶ ${t.play}`;
    });
    document.querySelectorAll('.btn-media-pause[data-media-id]').forEach(button => {
        const active = button.dataset.mediaId === globalMediaState.id;
        button.textContent = `❚❚ ${t.pause}`;
        button.disabled = !active || !audio || audio.paused;
    });
    document.querySelectorAll('.btn-media-stop[data-media-id]').forEach(button => {
        button.textContent = `■ ${t.stop}`;
        button.disabled = button.dataset.mediaId !== globalMediaState.id;
    });
    const globalPlay = document.getElementById('global-media-play');
    const globalPause = document.getElementById('global-media-pause');
    const globalStop = document.getElementById('global-media-stop');
    if (globalPlay) {
        globalPlay.textContent = `▶ ${t.play}`;
        globalPlay.disabled = !globalMediaState.id || Boolean(audio && !audio.paused);
    }
    if (globalPause) {
        globalPause.textContent = `❚❚ ${t.pause}`;
        globalPause.disabled = !globalMediaState.id || !audio || audio.paused;
    }
    if (globalStop) {
        globalStop.textContent = `■ ${t.stop}`;
        globalStop.disabled = !globalMediaState.id;
    }
}

function setMediaSessionMetadata(config) {
    if (!('mediaSession' in navigator) || typeof MediaMetadata === 'undefined') return;
    const artwork = normalizePlayableMediaUrl(config.artwork) || new URL('icon.svg', location.href).href;
    try {
        navigator.mediaSession.metadata = new MediaMetadata({
            title: config.title || 'World Revolution News',
            artist: config.artist || (config.kind === 'radio' ? 'Live-Radio' : 'Podcast'),
            album: 'World Revolution News',
            artwork: [{ src: artwork }]
        });
    } catch (error) { console.warn('Media-Session-Metadaten:', error); }
}

function setupMediaSessionHandlers() {
    if (!('mediaSession' in navigator)) return;
    const safeSet = (action, handler) => { try { navigator.mediaSession.setActionHandler(action, handler); } catch {} };
    safeSet('play', () => resumeGlobalMedia());
    safeSet('pause', () => pauseGlobalMedia());
    safeSet('stop', () => stopGlobalMedia());
    safeSet('seekbackward', details => {
        const audio = getGlobalMediaPlayer(); if (!audio || !Number.isFinite(audio.duration)) return;
        audio.currentTime = Math.max(0, audio.currentTime - (details.seekOffset || 10));
    });
    safeSet('seekforward', details => {
        const audio = getGlobalMediaPlayer(); if (!audio || !Number.isFinite(audio.duration)) return;
        audio.currentTime = Math.min(audio.duration, audio.currentTime + (details.seekOffset || 10));
    });
    safeSet('seekto', details => {
        const audio = getGlobalMediaPlayer(); if (!audio || !Number.isFinite(details.seekTime)) return;
        audio.currentTime = Math.max(0, Math.min(audio.duration || details.seekTime, details.seekTime));
    });
}

async function playGlobalMedia(config) {
    const audio = getGlobalMediaPlayer();
    if (!audio) return;
    const candidates = uniquePlayableCandidates(config.candidates || config.url || []);
    if (!candidates.length) {
        globalMediaState = { ...globalMediaState, id:config.id || '', statusId:config.statusId || '' };
        setGlobalMediaStatus(getMediaUiText().failed, 'error');
        return;
    }

    if (globalMediaState.id === config.id && audio.src) {
        if (audio.paused) {
            try { await audio.play(); } catch (error) { setGlobalMediaStatus(`${getMediaUiText().failed} ${error.message || ''}`, 'error'); }
        }
        updateGlobalMediaButtons();
        updateGlobalMediaProgress();
        return;
    }

    audio.pause();
    audio.removeAttribute('src');
    audio.load();
    globalMediaState = {
        id:String(config.id || ''), kind:String(config.kind || ''), title:String(config.title || 'Audio'),
        artist:String(config.artist || ''), candidates, candidateIndex:0,
        statusId:String(config.statusId || ''), progressId:String(config.progressId || ''),
        timeId:String(config.timeId || ''), artwork:String(config.artwork || ''), initialized:true
    };
    audio.src = candidates[0];
    audio.preload = 'none';
    updateGlobalMediaBar();
    setMediaSessionMetadata(globalMediaState);
    setGlobalMediaStatus(getMediaUiText().loading);
    try { await audio.play(); }
    catch (error) {
        // Ein echter Medienfehler löst zusätzlich das error-Ereignis aus. Eine
        // Browser-Autoplay-Sperre wird hier verständlich angezeigt.
        if (error?.name === 'NotAllowedError') setGlobalMediaStatus(`${getMediaUiText().failed} Bitte erneut auf Play drücken.`, 'error');
        else if (!audio.error) setGlobalMediaStatus(`${getMediaUiText().failed} ${error?.message || ''}`, 'error');
    }
}

function tryNextGlobalMediaCandidate() {
    const audio = getGlobalMediaPlayer();
    if (!audio || !globalMediaState.id) return;
    if (globalMediaState.candidateIndex + 1 < globalMediaState.candidates.length) {
        globalMediaState.candidateIndex += 1;
        audio.src = globalMediaState.candidates[globalMediaState.candidateIndex];
        setGlobalMediaStatus(getMediaUiText().loading);
        audio.load();
        audio.play().catch(() => {});
        return;
    }
    setGlobalMediaStatus(getMediaUiText().failed, 'error');
    updateGlobalMediaButtons();
}

function pauseGlobalMedia() {
    const audio = getGlobalMediaPlayer();
    if (audio && !audio.paused) audio.pause();
}

async function resumeGlobalMedia() {
    const audio = getGlobalMediaPlayer();
    if (!audio || !globalMediaState.id || !audio.paused) return;
    try { await audio.play(); } catch (error) { setGlobalMediaStatus(`${getMediaUiText().failed} ${error?.message || ''}`, 'error'); }
}

function stopGlobalMedia() {
    const audio = getGlobalMediaPlayer();
    if (audio) {
        audio.pause();
        audio.removeAttribute('src');
        audio.load();
    }
    const oldStatusId = globalMediaState.statusId;
    const oldProgressId = globalMediaState.progressId;
    const oldTimeId = globalMediaState.timeId;
    globalMediaState = {
        id:'', kind:'', title:'', artist:'', candidates:[], candidateIndex:0,
        statusId:'', progressId:'', timeId:'', artwork:'', initialized:true
    };
    if (oldStatusId) { const status = document.getElementById(oldStatusId); if (status) status.textContent = ''; }
    if (oldProgressId) { const progress = document.getElementById(oldProgressId); if (progress) { progress.value = 0; progress.disabled = true; } }
    if (oldTimeId) { const time = document.getElementById(oldTimeId); if (time) time.textContent = '0:00 / 0:00'; }
    if ('mediaSession' in navigator) {
        navigator.mediaSession.playbackState = 'none';
        try { navigator.mediaSession.metadata = null; } catch {}
    }
    updateGlobalMediaBar();
}


function safeDomId(value) { return String(value || '').replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 140); }
function appendSimpleMediaControls(card, config) {
    const mediaConfig = { ...config };
    const row = document.createElement('div');
    row.className = 'media-button-row';

    const play = document.createElement('button');
    play.type = 'button';
    play.className = 'btn-media-play';
    play.dataset.mediaId = mediaConfig.id;
    play.textContent = `▶ ${getMediaUiText().play}`;
    play.addEventListener('click', () => playGlobalMedia(mediaConfig));
    row.append(play);

    if (mediaConfig.showPause) {
        const pause = document.createElement('button');
        pause.type = 'button';
        pause.className = 'btn-media-pause';
        pause.dataset.mediaId = mediaConfig.id;
        pause.textContent = `❚❚ ${getMediaUiText().pause}`;
        pause.disabled = true;
        pause.addEventListener('click', () => {
            if (globalMediaState.id === mediaConfig.id) pauseGlobalMedia();
        });
        row.append(pause);
    }

    const stop = document.createElement('button');
    stop.type = 'button';
    stop.className = 'btn-media-stop';
    stop.dataset.mediaId = mediaConfig.id;
    stop.textContent = `■ ${getMediaUiText().stop}`;
    stop.disabled = mediaConfig.id !== globalMediaState.id;
    stop.addEventListener('click', () => {
        if (globalMediaState.id === mediaConfig.id) stopGlobalMedia();
    });
    row.append(stop);
    card.append(row);

    if (mediaConfig.showProgress) {
        const safeId = safeDomId(mediaConfig.id);
        mediaConfig.progressId = `media-progress-${safeId}`;
        mediaConfig.timeId = `media-time-${safeId}`;
        const progressRow = document.createElement('div');
        progressRow.className = 'media-progress-row';
        const progress = document.createElement('input');
        progress.type = 'range';
        progress.min = '0';
        progress.max = '1';
        progress.step = '0.1';
        progress.value = '0';
        progress.disabled = true;
        progress.id = mediaConfig.progressId;
        progress.setAttribute('aria-label', 'Audio position');
        progress.addEventListener('input', () => {
            if (globalMediaState.id === mediaConfig.id) seekGlobalMedia(progress.value);
        });
        const time = document.createElement('span');
        time.id = mediaConfig.timeId;
        time.className = 'media-time-label';
        time.textContent = '0:00 / 0:00';
        progressRow.append(progress, time);
        card.append(progressRow);
    }

    const status = document.createElement('div');
    status.className = 'media-card-status';
    status.id = mediaConfig.statusId;
    card.append(status);
    if (globalMediaState.id === mediaConfig.id) {
        const audio = getGlobalMediaPlayer();
        globalMediaState.progressId = mediaConfig.progressId || '';
        globalMediaState.timeId = mediaConfig.timeId || '';
        status.textContent = audio && !audio.paused ? getMediaUiText().playing : getMediaUiText().paused;
    }
    updateGlobalMediaButtons();
    updateGlobalMediaProgress();
}
