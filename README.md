# Moto Shorts PL

Scenariusz JSON -> Short 9:16 (~1:20): polski lektor (edge-tts), wideo ze stocku lub własne, napisy po 3 słowa, opcjonalna muzyka, powiadomienie na Telegram.

## Szybki start (Windows)
1. Pobierz repo (Code -> Download ZIP) i rozpakuj.
2. Uruchom `install.bat` (albo `python moto.py install`).
3. Klucz Pixabay wklejasz **w tym samym oknie** — nic nie otwiera się samo.
   Klucz: https://pixabay.com/api/docs/
4. Na pulpicie pojawi się ikona **Moto Shorts** — klikaj ją, aby generować filmy.

## Komendy
```
python moto.py install    # biblioteki + klucz + ikona
python moto.py key        # wpisanie / zmiana klucza API
python moto.py skrot      # sama ikona na pulpicie
python moto.py            # generuj wszystkie brakujące Shorty
python moto.py lista      # co gotowe, a co nie
python make_short.py scripts/01_isle_of_man.json   # pojedynczy film
```
Wynik w `output/`. Bez klucza w `.env` program powie, żeby go wpisać.

## Własna ikona
Wrzuć plik `icon.ico` do folderu projektu i uruchom `python moto.py skrot`.
Bez niego skrót używa systemowej ikony motocykla z Windows.

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
