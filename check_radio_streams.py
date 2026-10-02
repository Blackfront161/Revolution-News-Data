"""Bounded live stream checks; no audio files are retained."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlparse
import check_audio_sources as audio

ROOT = Path(__file__).resolve().parent


def probe_station(station, probe=None):
    checked = datetime.now(timezone.utc).isoformat()
    candidates = [u for u in audio.radio_urls(station) if urlparse(u).scheme == 'https']
    checks = []
    if probe is None:
        session = audio.client()
        try:
            for candidate in candidates[:4]:
                result = audio.test_url(session, candidate)
                checks.append(result)
                if result['status'] == 'playable':
                    break
        finally:
            session.close()
    else:
        for candidate in candidates[:4]:
            checks.append(probe(candidate))
            if checks[-1]['status'] == 'playable':
                break
    selected = next((c for c in checks if c['status'] == 'playable'), checks[0] if checks else {})
    status = selected.get('status', 'unknown')
    return station['id'], {
        'name': station['name'], 'status': {'playable': 'ok', 'limited': 'warning', 'broken': 'error'}.get(status, 'unknown'),
        'ok': status == 'playable', 'workingStream': selected.get('url', '') if status == 'playable' else '',
        'checkedAt': checked, 'lastChecked': checked, 'audioStatus': status,
        'message': selected.get('detail', 'No verified HTTPS stream in catalog; use original station page.'),
        'audioDetail': selected.get('detail', 'No verified HTTPS stream in catalog.'),
        'candidateChecks': checks,
    }


def main():
    audio.MAX_BYTES = 8192
    audio.TIMEOUT = (4, 6)
    stations = json.loads((ROOT / 'radio-stations.json').read_text(encoding='utf-8'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        health = dict(pool.map(probe_station, stations))
    (ROOT / 'radio-health.json').write_text(json.dumps(health, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    counts = {s: sum(v['audioStatus'] == s for v in health.values()) for s in ['playable', 'limited', 'broken', 'unknown']}
    print(json.dumps({'stations': len(stations), **counts}))


if __name__ == '__main__':
    main()
