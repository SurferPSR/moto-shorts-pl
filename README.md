# Moto Shorts PL

Jedna aplikacja: zamienia scenariusz na gotowy film Shorts 9:16 (~1:20) — polski lektor, wideo ze stocku albo własne, duże napisy po 3 słowa, opcjonalna muzyka, powiadomienie na Telegram.

## Uruchomienie
Podwójny klik na `moto.py` (albo `run.bat`, `install.bat` — wszystkie trzy robią to samo: otwierają menu).

Wymagania: Python 3.10+ oraz ffmpeg (`winget install Gyan.FFmpeg`). Program sam sprawdzi, czego brakuje.

## Menu
```
1  Instalacja  (biblioteki + klucz + ikona)
2  Ustaw klucz API
3  Generuj filmy
4  Lista scenariuszy
5  Nowy scenariusz (kreator)
6  Zrob skrot na pulpicie
7  Pokaz folder z filmami
0  Wyjscie
```
Klucz API wpisujesz w oknie programu (bezpłatny: https://pixabay.com/api/docs/).

## Struktura folderu
```
moto.py          caly program (jeden plik)
run.bat          uruchamia menu (Windows)
install.bat      to samo, dla wygody
icon.ico         ikona skrotu
scripts/*.json   scenariusze
output/*.mp4     gotowe filmy
```

## Format scenariusza
```json
{"title": "Isle of Man TT", "voice": "pl-PL-MarekNeural",
 "music": "music/track.mp3",
 "scenes": [{"text": "tekst lektora", "query": "motorcycle race"},
            {"text": "...", "file": "moje/klip.mp4"}]}
```
- `query` — czego szukać w Pixabay (po angielsku),
- `file` — własne nagranie zamiast stocku,
- `music` — tylko z Biblioteki audio YouTube.

## Zasady
- Bez nagrań MotoGP/WSBK/TV: Shorts dłuższe niż minuta z zastrzeżonymi treściami są blokowane.
- W Pixabay nie używaj komercyjnie klipów z widocznym logo lub marką.
- Fakty i liczby sprawdzaj przed publikacją.
