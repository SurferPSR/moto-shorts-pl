# Moto Shorts PL

Scenariusz JSON -> Short 9:16 (~1:20): polski lektor (edge-tts), wideo z Pexels lub własne, napisy po 3 słowa, opcjonalna muzyka, powiadomienie na Telegram.

## Instalacja (Windows)
1. Python 3.11+ z python.org (zaznacz "Add to PATH").
2. ffmpeg: `winget install Gyan.FFmpeg` (potem nowe okno terminala, sprawdź `ffmpeg -version`).
3. `pip install -r requirements.txt`
4. Darmowy klucz: https://www.pexels.com/api/ -> wpisz do `.env` (skopiuj z `.env.example`).

## Użycie
```
python make_short.py scripts/01_isle_of_man.json
python make_short.py scripts/*.json
```
Wynik w `output/`.

## Format scenariusza
```json
{"title": "...", "music": "music/track.mp3",
 "scenes": [{"text": "tekst lektora", "query": "motorcycle race"},
            {"text": "...", "file": "moje/klip.mp4"}]}
```
`query` = wyszukiwanie w Pexels (po angielsku), `file` = własne nagranie. Muzyka tylko z Biblioteki audio YouTube.

## Zasady
- Bez nagrań MotoGP/WSBK/TV – Shorts >1 min z zastrzeżonymi treściami są blokowane.
- Fakty i liczby sprawdzaj przed publikacją.
