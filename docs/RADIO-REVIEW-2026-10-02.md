# Radio review, 2 October 2026

27 existing directory entries were checked. Eight contained stream addresses; all eight returned nonempty audio samples. Nineteen contain no stream address: directory-only does not mean the broadcaster has stopped transmitting.

3CR Community Radio (Melbourne) was added as the 28th station. Its own [statement of purpose](https://www.3cr.org.au/whoweare) describes a platform for progressive communities. Its [streaming page](https://www.3cr.org.au/streaming) explicitly supplies a direct MP3 URL for external players. The declared HTTPS URL returned a nonempty audio sample. This fits WRN's community-radio scope; it does not imply every broadcast is anarchist or that audio redistribution is licensed. Only the original live-stream link is used; no audio or artwork is copied or stored.

Result: 28 entries, nine audio responses, nineteen directory-only/unknown. Exact candidate results and UTC timestamps are in radio-health.json. This is a bounded HTTP audio-format check, not a guarantee of continuous availability or playback on every device.

The checker rejects empty responses and HTML even when labelled audio, closes responses, retains fallback candidates and dates each result. A serialized six-hour workflow maintains the health file without touching podcast content. Four offline unit tests cover directory-only status, fallback, empty/HTML responses and connection closure.

Further intake: Freies Radio fuer Stuttgart is a candidate; its official pages currently return HTTP403 in this review, so no guessed stream was admitted. Radio Blau explicitly lists an HTTP stream on its official reception page; a browser-compatible HTTPS endpoint still needs verified admission. LoRa Zurich remains distinct from LORA Munich, with audio-directory intake already tracked. Other existing directory stations take priority over claiming more working radios.
