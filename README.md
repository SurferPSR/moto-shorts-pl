# Moto Shorts PL

Scenariusz JSON -> Short 9:16 (~1:20): polski lektor (edge-tts), wideo ze stocku lub własne, napisy po 3 słowa, opcjonalna muzyka, powiadomienie na Telegram.

## Instalacja (Windows)
1. Pobierz repo (Code -> Download ZIP) i rozpakuj.
2. Skopiuj `install.bat` i `run.bat` do tego folderu.
3. Uruchom `install.bat` (instaluje Python, ffmpeg, biblioteki).
4. Darmowy klucz wideo: https://pixabay.com/accounts/register/ , potem https://pixabay.com/api/docs/ -> wklej do `.env` jako `PIXABAY_API_KEY`.
   (Pexels wstrzymał wydawanie nowych kluczy — nie jest potrzebny.)
5. Uruchom `run.bat`.

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
`query` = wyszukiwanie w Pixabay (po angielsku), `file` = własne nagranie. Muzyka tylko z Biblioteki audio YouTube.

## Zasady
- Bez nagrań MotoGP/WSBK/TV – Shorts >1 min z zastrzeżonymi treściami są blokowane.
- W Pixabay nie używaj komercyjnie klipów z widocznym logo/brandem.
- Fakty i liczby sprawdzaj przed publikacją.
