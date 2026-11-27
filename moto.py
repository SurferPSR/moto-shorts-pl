"""
================================================================================
 MOTO SHORTS PL  -  jeden plik, ktory robi wszystko
================================================================================

Co to jest:
  Program zamienia scenariusz (tekst) na gotowy film Shorts 9:16 (~1:20):
  polski lektor, wideo ze stocku albo wlasne klipy, duze napisy po 3 slowa,
  opcjonalna muzyka i powiadomienie na Telegram.

Jak uruchomic (Windows, podwojny klik):
  1) Zainstaluj Python z python.org (zaznacz "Add python.exe to PATH").
  2) Zainstaluj ffmpeg:  winget install Gyan.FFmpeg  (potem nowe okno konsoli).
  3) Podwojny klik na ten plik albo:  python moto.py

Menu (wpisujesz numer i Enter):
  1  Instalacja         - biblioteki, klucz API, ikona na pulpicie
  2  Ustaw klucz API    - wklejasz klucz Pixabay w tym oknie
  3  Generuj filmy      - tworzy wszystkie brakujace Shorty z folderu scripts/
  4  Lista scenariuszy  - co jest gotowe, a co nie
  5  Nowy scenariusz    - kreator: pytania -> plik .json
  6  Zrob skrot         - ikona "Moto Shorts" na pulpicie
  7  Pokaz folder       - otwiera folder output
  0  Wyjscie

Klucz API zdobywasz bezplatnie: https://pixabay.com/api/docs/
================================================================================
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

# ============================================================================ #
#  USTAWIENIA - mozna zmienic recznie
# ============================================================================ #
APP_NAME = "MOTO SHORTS PL"
APP_VERSION = "1.0"
WIDTH, HEIGHT = 1080, 1920          # kadr pionowy 9:16
FPS = 30
MAX_SECONDS = 175                   # powyzej 180 s YouTube nie liczy tego jako Short
SUBTITLE_WORDS = 3                  # ile slow na jedna linijke napisow
DEFAULT_VOICE = "pl-PL-MarekNeural"
DEFAULT_RATE = "+8%"
PIXABAY_HINT = "vertical portrait"  # podpowiedz, zeby dostac kadr pionowy
PACKAGES = ["edge-tts", "requests", "python-dotenv"]

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
OUTPUT = ROOT / "output"
WORK = ROOT / "work"
ENV_FILE = ROOT / ".env"
VENV = ROOT / ".venv"
CACHE = WORK / "_cache"

# ============================================================================ #
#  WYGLAD OKNA - kolory ANSI (same wylaczaja sie na starych konsolach)
# ============================================================================ #
class C:
    """Kolory tekstu w konsoli. Puste, gdy kolorow nie da sie wlaczyc."""
    OFF = RESET = ""
    BOLD = DIM = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ""


def _enable_colours() -> None:
    if os.name == "nt":
        try:  # Windows 10+: wlacz przetwarzanie sekwencji ANSI
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            return
    if not sys.stdout.isatty() and os.name != "nt":
        return
    C.OFF = "\033[0m"
    C.RESET = "\033[0m"
    C.BOLD = "\033[1m"
    C.DIM = "\033[2m"
    C.RED = "\033[31m"
    C.GREEN = "\033[32m"
    C.YELLOW = "\033[33m"
    C.BLUE = "\033[34m"
    C.MAGENTA = "\033[35m"
    C.CYAN = "\033[36m"
    C.WHITE = "\033[97m"


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def line(char: str = "-", width: int = 74) -> None:
    print(f"{C.DIM}{char * width}{C.OFF}")


def title(text: str) -> None:
    line("=")
    print(f"{C.BOLD}{C.CYAN}  {text}{C.OFF}")
    line("=")


def head(text: str) -> None:
    print(f"\n{C.BOLD}{C.BLUE}>> {text}{C.OFF}")
    line("-")


def ok(text: str) -> None:
    print(f"  {C.GREEN}v{C.OFF} {text}")


def warn(text: str) -> None:
    print(f"  {C.YELLOW}!{C.OFF} {text}")


def bad(text: str) -> None:
    print(f"  {C.RED}x{C.OFF} {text}")


def info(text: str) -> None:
    print(f"  {C.CYAN}i{C.OFF} {text}")


def bullet(text: str) -> None:
    print(f"    {C.DIM}>{C.OFF} {text}")


def ask(prompt: str, default: str = "") -> str:
    """Pyta i NIE zamyka okna przy pustej odpowiedzi."""
    shown = f" {C.DIM}[{default}]{C.OFF}" if default else ""
    try:
        value = input(f"  {C.WHITE}?{C.OFF} {prompt}{shown}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return value or default


def confirm(prompt: str, default_yes: bool = True) -> bool:
    d = "T/n" if default_yes else "t/N"
    answer = ask(f"{prompt} {C.DIM}({d}){C.OFF}").lower()
    if not answer:
        return default_yes
    return answer.startswith("t") or answer.startswith("y")


def wait(msg: str = "Nacisnij Enter, aby wrocic do menu") -> None:
    try:
        input(f"\n  {C.DIM}{msg}...{C.OFF}")
    except (EOFError, KeyboardInterrupt):
        print()


# ============================================================================ #
#  PLIK .ENV
# ============================================================================ #
ENV_ORDER = ["PIXABAY_API_KEY", "PEXELS_API_KEY", "VOICE", "VOICE_RATE",
             "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
ENV_DEFAULTS = {
    "PIXABAY_API_KEY": "",
    "PEXELS_API_KEY": "",
    "VOICE": DEFAULT_VOICE,
    "VOICE_RATE": DEFAULT_RATE,
    "TELEGRAM_BOT_TOKEN": "",
    "TELEGRAM_CHAT_ID": "",
}


def read_env() -> dict:
    values = dict(ENV_DEFAULTS)
    if ENV_FILE.exists():
        try:
            for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
                raw = raw.strip()
                if "=" in raw and not raw.startswith("#"):
                    key, _, val = raw.partition("=")
                    values[key.strip()] = val.strip().strip('"').strip("'")
        except OSError:
            pass
    for key in ENV_DEFAULTS:          # zmienne srodowiskowe maja pierwszenstwo
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def write_env(values: dict) -> None:
    lines = [
        "# Plik ustawien programu Moto Shorts PL",
        "# Klucz wideo (bezplatny): https://pixabay.com/api/docs/",
        "",
    ]
    for key in ENV_ORDER:
        lines.append(f"{key}={values.get(key, '')}")
    for key in values:
        if key not in ENV_ORDER:
            lines.append(f"{key}={values[key]}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def env_get(key: str, default: str = "") -> str:
    return read_env().get(key) or default


# ============================================================================ #
#  NARZEDZIA ZEWNETRZNE
# ============================================================================ #
def run_quiet(cmd: list, stderr_to_stdout: bool = True) -> int:
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT if stderr_to_stdout
                       else subprocess.PIPE, text=True, errors="replace")
    return r.returncode


def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def duration_of(path: Path) -> float:
    """Dlugosc pliku w sekundach (przez ffprobe)."""
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip())


def venv_python() -> Path:
    exe = (VENV / "Scripts" / "python.exe") if os.name == "nt" \
        else (VENV / "bin" / "python")
    return exe if exe.exists() else Path(sys.executable)


def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def open_path(path: Path) -> None:
    try:
        if os.name == "nt":
            os.startfile(str(path))                     # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError:
        pass


def notify_telegram(text: str) -> None:
    token = env_get("TELEGRAM_BOT_TOKEN")
    chat = env_get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return
    try:
        import requests
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      data={"chat_id": chat, "text": text}, timeout=15)
    except Exception:
        pass


# ============================================================================ #
#  1. INSTALACJA
# ============================================================================ #
def install_ffmpeg() -> bool:
    if have_ffmpeg():
        ok("ffmpeg: juz jest.")
        return True
    warn("ffmpeg: brak. To on sklada wideo.")
    if os.name == "nt" and shutil.which("winget"):
        info("Instaluje ffmpeg przez winget (moze potrwac chwile)...")
        run_quiet(["winget", "install", "-e", "--id", "Gyan.FFmpeg",
                   "--accept-package-agreements", "--accept-source-agreements"])
    if have_ffmpeg():
        ok("ffmpeg: zainstalowany.")
        return True
    bad("ffmpeg: nadal go nie widze.")
    bullet("Zamknij to okno, otworz nowe i uruchom program ponownie.")
    bullet("Albo recznie: winget install Gyan.FFmpeg")
    return False


def install_packages() -> bool:
    py = venv_python()
    if py == Path(sys.executable) and not VENV.exists():
        info("Tworze osobne srodowisko .venv...")
        run_quiet([sys.executable, "-m", "venv", str(VENV)])
        py = venv_python()
    run_quiet([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    info("Instaluje biblioteki: lektor, pobieranie, ustawienia...")
    if run_quiet([str(py), "-m", "pip", "install", *PACKAGES],
                 stderr_to_stdout=False) != 0:
        bad("Nie udalo sie zainstalowac bibliotek. Sprawdz internet.")
        return False
    ok(f"Biblioteki: gotowe ({py}).")
    return True


def install_shortcut() -> Path | None:
    """Ikona na pulpicie. Windows: plik .lnk; Linux/macOS: skrot .desktop."""
    desktop = None
    for candidate in (Path.home() / "Desktop",
                      Path(os.environ.get("OneDrive", "") or ".") / "Desktop"):
        if candidate.is_dir():
            desktop = candidate
            break
    desktop = desktop or Path.home()

    if os.name != "nt":
        link = desktop / "Moto Shorts.desktop"
        link.write_text(
            "[Desktop Entry]\nType=Application\nName=Moto Shorts\n"
            f"Exec=python3 {ROOT / 'moto.py'}\nPath={ROOT}\nTerminal=true\n"
            f"Icon={ROOT / 'icon.png'}\n", encoding="utf-8")
        link.chmod(0o755)
        return link

    link = desktop / "Moto Shorts.lnk"
    icon = ROOT / "icon.ico"
    icon_line = (f"$s.IconLocation = '{icon}'" if icon.exists()
                 else "$s.IconLocation = 'C:\\Windows\\System32\\imageres.dll,101'")
    script = textwrap.dedent(f"""
        $s = (New-Object -ComObject WScript.Shell).CreateShortcut('{link}')
        $s.TargetPath = '{sys.executable}'
        $s.Arguments = '"{ROOT / "moto.py"}"'
        $s.WorkingDirectory = '{ROOT}'
        {icon_line}
        $s.Description = 'Moto Shorts PL - generuj filmy'
        $s.Save()
    """)
    marker = ROOT / ".shortcut_created"
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        script + f"\nNew-Item -ItemType File -Force -Path "
                                 f"'{marker}' | Out-Null"],
                       capture_output=True, text=True)
    if marker.exists():
        marker.unlink()
        ok(f"Ikona na pulpicie: {link.name}")
        if not icon.exists():
            warn("Twoja ikona wskoczy, gdy polozysz plik icon.ico obok moto.py.")
        return link
    bad("Ikony nie udalo sie utworzyc.")
    if r.stderr.strip():
        bullet(r.stderr.strip()[:200])
    return None


def action_install() -> None:
    head("INSTALACJA")
    good_ffmpeg = install_ffmpeg()
    packages_ok = install_packages()
    action_set_key(first_time=True)
    install_shortcut()
    print()
    if good_ffmpeg and packages_ok:
        ok("Gotowe. Wroc do menu i wybierz 3, aby wygenerowac filmy.")
    else:
        warn("Cos wymaga jeszcze uwagi - patrz komunikaty wyzej.")
    wait()


# ============================================================================ #
#  2. KLUCZ API
# ============================================================================ #
def action_set_key(first_time: bool = False) -> str:
    """Klucz wpisuje sie TU, w tym oknie - nic sie samo nie otwiera."""
    head("KLUCZ API (wideo ze stocku)")
    current = env_get("PIXABAY_API_KEY")
    if current:
        info(f"Zapisany klucz konczy sie na ...{current[-4:]} "
             f"(dlugosc {len(current)}).")
        prompt = "Wklej nowy klucz albo Enter, aby zostawic obecny"
    else:
        info("Klucz jest bezplatny. Otworz w przegladarce:")
        bullet("https://pixabay.com/api/docs/")
        bullet("Zaloz konto, skopiuj klucz i wklej go tutaj.")
        bullet("Wklejanie w tym oknie: prawy przycisk myszy.")
        prompt = "Klucz PIXABAY_API_KEY (Enter = pomin)"

    value = ask(prompt)
    if value:
        values = read_env()
        values["PIXABAY_API_KEY"] = value
        write_env(values)
        ok(f"Zapisano w pliku {ENV_FILE.name}.")
        return value
    if current:
        info("Zostawiam obecny klucz.")
        return current
    warn("Bez klucza nie sciagne wideo ze stocku.")
    bullet("Mozesz uzyc wlasnych nagran: w scenariuszu pole \"file\".")
    return ""


# ============================================================================ #
#  3-4. SCENARIUSZE
# ============================================================================ #
def load_scripts() -> list:
    if not SCRIPTS.is_dir():
        return []
    return sorted(SCRIPTS.glob("*.json"))


def script_title(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("title") or path.stem
    except (json.JSONDecodeError, OSError):
        return path.stem


def action_list() -> None:
    head("SCENARIUSZE")
    jobs = load_scripts()
    if not jobs:
        warn(f"Folder {SCRIPTS.name}/ jest pusty.")
        bullet("Wybierz 5 w menu, aby zrobic nowy scenariusz.")
        wait()
        return
    done = 0
    for j in jobs:
        finished = (OUTPUT / f"{j.stem}.mp4").exists()
        done += finished
        mark = f"{C.GREEN}gotowy{C.OFF}" if finished else f"{C.DIM}czeka {C.OFF}"
        print(f"  [{mark}] {script_title(j)}")
    print()
    info(f"Razem: {len(jobs)} | gotowe: {done} | do zrobienia: {len(jobs) - done}")
    wait()


TEMPLATE_TITLE = "Tytul odcinka"
TEMPLATE_QUERIES = [
    "motorcycle speed road", "motorcycle rider helmet", "motorcycle track corner",
    "sport motorcycle sunset", "motorcycle engine detail", "motorcycle garage",
]


def action_new_script() -> None:
    head("NOWY SCENARIUSZ (kreator)")
    info("Odpowiadaj na pytania. Enter = wartosc domyslna.")
    topic = ask("O czym jest odcinek (krotko)", "Isle of Man TT")
    if not topic:
        warn("Bez tematu nie ma scenariusza.")
        wait()
        return
    hook = ask("Pierwsze zdanie, ktore ma zatrzymac widza",
               f"Ponad 300 km/h. {topic}.")
    body = ask("Glowna czesc (2-4 zdania)", "")
    ending = ask("Zakonczenie z prosba o subskrypcje",
                 "Zasubskrybuj, aby zobaczyc wiecej takich historii.")
    voice = ask("Glos lektora (pl-PL-MarekNeural lub pl-PL-ZofiaNeural)",
                env_get("VOICE", DEFAULT_VOICE))
    music = ask("Plik z muzyka (opcjonalnie, Enter = bez muzyki)", "")

    scenes = [{"text": hook, "query": TEMPLATE_QUERIES[0]}]
    if body:
        chunks = [s.strip() for s in body.replace("\n", " ").split(". ") if s.strip()]
        for i, chunk in enumerate(chunks):
            if not chunk.endswith((".", "!", "?")):
                chunk += "."
            scenes.append({"text": chunk,
                           "query": TEMPLATE_QUERIES[(i + 1) % len(TEMPLATE_QUERIES)]})
    scenes.append({"text": ending, "query": TEMPLATE_QUERIES[-1]})

    script = {"title": topic, "voice": voice, "scenes": scenes}
    if music:
        script["music"] = music

    safe = "".join(ch if ch.isalnum() or ch in " -_" else "" for ch in topic)
    name = (safe.strip().replace(" ", "_").lower() or "nowy")[:40]
    path = SCRIPTS / f"{name}.json"
    SCRIPTS.mkdir(exist_ok=True)
    if path.exists() and not confirm(f"Plik {path.name} istnieje. Nadpisac?"):
        wait()
        return
    path.write_text(json.dumps(script, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    ok(f"Zapisano: {path.relative_to(ROOT)} ({len(scenes)} scen).")
    info("Kazda scena ma \"query\" - slowa do wyszukania wideo w Pixabay.")
    info("Chcesz wlasne nagranie? Zamien \"query\" na \"file\": \"sciezka.mp4\".")
    wait()


# ============================================================================ #
#  LEKTOR I WIDEO
# ============================================================================ #
async def _tts(text: str, voice: str, rate: str, mp3: Path) -> list:
    """Mowa (edge-tts) + znaczniki slow, z ktorych robimy napisy."""
    import edge_tts
    words = []
    communicate = edge_tts.Communicate(text, voice, rate=rate,
                                       boundary="WordBoundary")
    with open(mp3, "wb") as handle:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                handle.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append((start, start + chunk["duration"] / 1e7, chunk["text"]))
    return words


def pixabay_clip(query: str, dest: Path) -> None:
    """Szuka i pobiera pionowy klip. Wynik wyszukiwania cache'ujemy na 24 h."""
    import requests
    key = env_get("PIXABAY_API_KEY")
    if not key:
        raise RuntimeError("Brak klucza PIXABAY_API_KEY w .env")
    cache_file = CACHE / f"{abs(hash(query))}.json"
    hits = None
    if cache_file.exists():
        try:
            hits = json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            hits = None
    if hits is None:
        CACHE.mkdir(parents=True, exist_ok=True)
        for q in (f"{query} {PIXABAY_HINT}", query):
            r = requests.get("https://pixabay.com/api/videos/",
                             params={"key": key, "q": q, "per_page": 20,
                                     "safesearch": "true"}, timeout=30)
            r.raise_for_status()
            hits = r.json().get("hits", [])
            if hits:
                break
        cache_file.write_text(json.dumps(hits), encoding="utf-8")
    if not hits:
        raise RuntimeError(f"Pixabay: brak wideo dla '{query}'")
    variants = random.choice(hits[:10])["videos"]
    pick = variants.get("large") or variants.get("medium") or variants.get("small")
    with requests.get(pick["url"], stream=True, timeout=90) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as handle:
            for part in resp.iter_content(1 << 20):
                handle.write(part)


def fit_clip(source: Path, dest: Path, seconds: float) -> None:
    """Kadruje do 9:16, przycina do dlugosci sceny i zapetla, gdy klip za krotki."""
    filters = (f"scale={WIDTH * 2}:{HEIGHT * 2}:force_original_aspect_ratio=increase,"
               f"crop={WIDTH * 2}:{HEIGHT * 2},scale={WIDTH}:{HEIGHT},"
               f"fps={FPS},setsar=1")
    cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(source),
           "-t", f"{seconds:.3f}", "-vf", filters, "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(dest)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.PIPE)


def write_srt(words: list, path: Path) -> None:
    """Napisy po SUBTITLE_WORDS slowa - w Shorts czytaja sie najlepiej."""
    with open(path, "w", encoding="utf-8") as handle:
        n = 0
        for i in range(0, len(words), SUBTITLE_WORDS):
            group = words[i:i + SUBTITLE_WORDS]
            n += 1
            handle.write(f"{n}\n{srt_time(group[0][0])} --> "
                         f"{srt_time(group[-1][1])}\n"
                         f"{' '.join(w[2] for w in group).upper()}\n\n")


def build_one(script_path: Path, verbose: bool = True) -> Path | None:
    """Scenariusz JSON -> output/<nazwa>.mp4"""
    try:
        script = json.loads(script_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        bad(f"Nie moge czytac {script_path.name}: {exc}")
        return None
    if not script.get("scenes"):
        bad(f"{script_path.name}: brak listy \"scenes\".")
        return None

    voice = script.get("voice") or env_get("VOICE", DEFAULT_VOICE)
    rate = script.get("rate") or env_get("VOICE_RATE", DEFAULT_RATE)
    name = script_path.stem
    scene_dir = WORK / name
    scene_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)

    words_all, clips, audios, offset = [], [], [], 0.0
    scenes = script["scenes"]
    for index, scene in enumerate(scenes):
        text = (scene.get("text") or "").strip()
        if not text:
            continue
        mp3 = scene_dir / f"voice{index}.mp3"
        words = asyncio.run(_tts(text, voice, rate, mp3))
        seconds = duration_of(mp3) + 0.18
        words_all += [(a + offset, b + offset, w) for a, b, w in words]

        raw, fitted = scene_dir / f"raw{index}.mp4", scene_dir / f"clip{index}.mp4"
        if scene.get("file"):
            source = Path(scene["file"])
            if not source.is_absolute():
                source = ROOT / source
            if not source.exists():
                bad(f"scena {index + 1}: brak pliku {source}")
                return None
        else:
            source = raw
            if not raw.exists():
                pixabay_clip(scene.get("query") or "motorcycle", raw)
        fit_clip(source, fitted, seconds)
        clips.append(fitted)
        audios.append((mp3, seconds))
        offset += seconds
        if verbose:
            print(f"    {C.DIM}scena {index + 1}/{len(scenes)}: "
                  f"{seconds:4.1f}s{C.OFF}")

    # sklejenie obrazu
    concat = scene_dir / "clips.txt"
    concat.write_text("".join(f"file '{c.resolve()}'\n" for c in clips),
                      encoding="utf-8")
    video = scene_dir / "video.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-c", "copy", str(video)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    # lektor: kazda scena dociagnieta cisza do swojej dlugosci
    inputs, filters = [], []
    for i, (mp3, seconds) in enumerate(audios):
        inputs += ["-i", str(mp3)]
        filters.append(f"[{i}:a]apad,atrim=0:{seconds:.3f}[a{i}]")
    filters.append("".join(f"[a{i}]" for i in range(len(audios)))
                   + f"concat=n={len(audios)}:v=0:a=1[voice]")
    narration = scene_dir / "narration.m4a"
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "[voice]", str(narration)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    # napisy
    srt = scene_dir / "subs.srt"
    write_srt(words_all, srt)
    style = ("FontName=Arial,FontSize=15,Bold=1,PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,"
             "Alignment=2,MarginV=120")
    srt_arg = str(srt).replace("\\", "/").replace(":", "\\:")

    final = OUTPUT / f"{name}.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", str(narration)]
    music = script.get("music")
    music_path = (ROOT / music) if music and not Path(music).is_absolute() \
        else Path(music) if music else None
    if music_path and music_path.exists():
        cmd += ["-stream_loop", "-1", "-i", str(music_path), "-filter_complex",
                "[2:a]volume=0.12[bg];[1:a][bg]amix=inputs=2:duration=first[aout]",
                "-map", "0:v", "-map", "[aout]"]
    else:
        if music:
            warn(f"muzyka: nie znalazlem {music} - pomijam")
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-vf", f"subtitles='{srt_arg}':force_style='{style}'",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
            "-shortest", str(final)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    total = duration_of(final)
    if verbose:
        ok(f"{final.name}  ({total:.1f}s)")
    if total > MAX_SECONDS:
        warn(f"{total:.0f}s - powyzej 3 minut YouTube nie uzna tego za Short.")
    return final


def action_generate() -> None:
    head("GENEROWANIE FILMOW")
    if not have_ffmpeg():
        bad("Brak ffmpeg - wybierz 1 w menu, aby go zainstalowac.")
        wait()
        return
    if not env_get("PIXABAY_API_KEY") and not env_get("PEXELS_API_KEY"):
        bad("Brak klucza API - wybierz 2 w menu, aby go wpisac.")
        wait()
        return
    jobs = load_scripts()
    if not jobs:
        warn(f"Folder {SCRIPTS.name}/ jest pusty - wybierz 5 w menu.")
        wait()
        return

    todo = [j for j in jobs if not (OUTPUT / f"{j.stem}.mp4").exists()]
    info(f"Scenariuszy: {len(jobs)} | do wygenerowania: {len(todo)}")
    if not todo:
        ok("Wszystko juz gotowe.")
        open_path(OUTPUT)
        wait()
        return
    if not confirm("Start?", True):
        wait()
        return

    made, failed = [], []
    for i, job in enumerate(todo, 1):
        print(f"\n  {C.BOLD}[{i}/{len(todo)}]{C.OFF} {script_title(job)}")
        try:
            result = build_one(job)
        except subprocess.CalledProcessError as exc:
            result = None
            if exc.stderr:
                bullet(exc.stderr.decode(errors="replace").strip()[-400:])
        except Exception as exc:                                # noqa: BLE001
            result = None
            bad(str(exc)[:300])
        (made if result else failed).append(job.stem)

    head("PODSUMOWANIE")
    ok(f"Gotowe: {len(made)}" + (f"  ->  {', '.join(made)}" if made else ""))
    if failed:
        bad(f"Nieudane: {len(failed)}  ->  {', '.join(failed)}")
    if made:
        notify_telegram(f"Shorty gotowe: {len(made)} ({', '.join(made[:5])})")
        open_path(OUTPUT)
    wait()


# ============================================================================ #
#  MENU
# ============================================================================ #
MENU = [
    ("1", "Instalacja  (biblioteki + klucz + ikona)"),
    ("2", "Ustaw klucz API"),
    ("3", "Generuj filmy"),
    ("4", "Lista scenariuszy"),
    ("5", "Nowy scenariusz (kreator)"),
    ("6", "Zrob skrot na pulpicie"),
    ("7", "Pokaz folder z filmami"),
    ("0", "Wyjscie"),
]


def draw_menu() -> None:
    clear()
    title(f"{APP_NAME}   v{APP_VERSION}")
    print(f"  {C.DIM}Folder: {ROOT}{C.OFF}")
    key = env_get("PIXABAY_API_KEY")
    state = f"{C.GREEN}ustawiony{C.OFF}" if key else f"{C.YELLOW}brak{C.OFF}"
    print(f"  {C.DIM}Klucz API: {state}{C.OFF}")
    print()
    for number, label in MENU:
        print(f"   {C.BOLD}{C.CYAN}{number}{C.OFF}  {label}")
    line()


def main() -> int:
    _enable_colours()
    while True:
        draw_menu()
        choice = ask("Wybierz numer", "0").lower()
        if choice in ("0", "q", "wyjscie", "exit"):
            print(f"\n  {C.CYAN}Do zobaczenia.{C.OFF}\n")
            return 0
        if choice == "1":
            action_install()
        elif choice == "2":
            action_set_key()
            wait()
        elif choice == "3":
            action_generate()
        elif choice == "4":
            action_list()
        elif choice == "5":
            action_new_script()
        elif choice == "6":
            head("SKROT NA PULPICIE")
            install_shortcut()
            wait()
        elif choice == "7":
            OUTPUT.mkdir(exist_ok=True)
            open_path(OUTPUT)
        else:
            warn("Nie ma takiej opcji.")
            wait("Nacisnij Enter, aby wrocic do menu")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n  {C.CYAN}Przerwano.{C.OFF}\n")
        sys.exit(130)
