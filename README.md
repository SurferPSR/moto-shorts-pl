# Moto Shorts PL

Scenariusz JSON -> Short 9:16 (~1:20): polski lektor (edge-tts), wideo ze stocku lub własne, napisy po 3 słowa, opcjonalna muzyka, powiadomienie na Telegram.

## Szybki start (Windows)
1. Pobierz repo (Code -> Download ZIP) i rozpakuj.
2. `python moto.py install` — instaluje biblioteki, tworzy `.env`, zakłada ikonę na pulpicie.
3. Wklej darmowy klucz z https://pixabay.com/api/docs/ do `.env` (`PIXABAY_API_KEY`).
4. Kliknij ikonę **Moto Shorts** na pulpicie (albo `python moto.py`).

Bez Pythona? Uruchom `install.bat`, a potem `run.bat`.

## Użycie
```
python moto.py            # generuj wszystkie brakujące Shorty
python moto.py install    # tylko instalacja + skrót
python moto.py skrot      # tylko skrót na pulpicie
python moto.py lista      # co gotowe, a co nie
python make_short.py scripts/01_isle_of_man.json   # pojedynczy film
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
