"""Moto Shorts PL — jeden plik, który robi wszystko.

Uruchomienie (podwójny klik też działa):
    python moto.py            # instalacja przy pierwszym razie + generowanie filmów
    python moto.py install    # tylko instalacja (biblioteki, .env, skrót na pulpicie)
    python moto.py skrot      # tylko skrót na pulpicie
    python moto.py lista      # co jest gotowe, a co nie

Pierwsze uruchomienie:
 1. sprawdza ffmpeg i biblioteki (instaluje, jeśli brak),
 2. tworzy .env i otwiera go — wklej tam darmowy klucz PIXABAY_API_KEY,
 3. zakłada na pulpicie ikonę "Moto Shorts" (skrót do tego pliku),
 4. generuje wszystkie scenariusze z folderu scripts/.
"""
import json
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
OUTPUT = ROOT / "output"
ENV = ROOT / ".env"
VENV = ROOT / ".venv"
PACKAGES = ["edge-tts", "requests", "python-dotenv"]


# --------------------------------------------------------------------------- #
# pomocnicze
# --------------------------------------------------------------------------- #
def pause(msg="\nNaciśnij Enter, aby zamknąć..."):
    try:
        input(msg)
    except EOFError:
        pass


def step(n, text):
    print(f"[{n}] {text}")


def venv_python():
    """Wolimy własne środowisko; gdy się nie uda, zostaje systemowy Python."""
    if os.name == "nt":
        exe = VENV / "Scripts" / "python.exe"
    else:
        exe = VENV / "bin" / "python"
    return exe if exe.exists() else Path(sys.executable)


def install():
    """ffmpeg + biblioteki w .venv."""
    step(1, "Sprawdzam ffmpeg...")
    if shutil.which("ffmpeg") is None:
        if os.name == "nt" and shutil.which("winget"):
            print("   instaluje ffmpeg przez winget...")
            subprocess.run(["winget", "install", "-e", "--id", "Gyan.FFmpeg",
                            "--accept-package-agreements",
                            "--accept-source-agreements"], check=False)
        if shutil.which("ffmpeg") is None:
            print("   UWAGA: nie widzę ffmpeg. Zainstaluj go i uruchom ponownie:")
            print("   winget install Gyan.FFmpeg")
    else:
        print("   OK, ffmpeg jest.")

    step(2, "Przygotowuję biblioteki Pythona...")
    py = venv_python()
    if py == Path(sys.executable) and not VENV.exists():
        if subprocess.run([sys.executable, "-m", "venv", str(VENV)]).returncode == 0:
            py = venv_python()
    subprocess.run([str(py), "-m", "pip", "install", "--upgrade", "pip"],
                   check=False, stdout=subprocess.DEVNULL)
    if subprocess.run([str(py), "-m", "pip", "install", *PACKAGES]).returncode != 0:
        print("   Nie udało się zainstalować bibliotek — sprawdź internet.")
    else:
        print(f"   OK ({py}).")

    step(3, "Sprawdzam plik .env...")
    if not ENV.exists():
        ENV.write_text("PIXABAY_API_KEY=\nVOICE=pl-PL-MarekNeural\n"
                       "VOICE_RATE=+8%\nTELEGRAM_BOT_TOKEN=\n"
                       "TELEGRAM_CHAT_ID=798730878\n", encoding="utf-8")
        print("   Utworzyłem .env — wklej klucz PIXABAY_API_KEY i zapisz.")
        if os.name == "nt":
            subprocess.Popen(["notepad.exe", str(ENV)])
        webbrowser.open("https://pixabay.com/accounts/register/")
    else:
        print("   Plik .env już jest.")
    return py


def desktop():
    for c in (Path.home() / "Desktop",
              Path(os.environ.get("OneDrive", "") or ".") / "Desktop"):
        if c.is_dir():
            return c
    return Path.home()


def make_shortcut():
    """Skrót na pulpicie -> ten plik (okno konsoli zostaje otwarte)."""
    link = desktop() / "Moto Shorts.lnk"
    if os.name != "nt":
        target = ROOT / ("moto.sh" if (ROOT / "moto.sh").exists() else "moto.py")
        link = desktop() / "Moto Shorts.desktop"
        link.write_text(
            "[Desktop Entry]\nType=Application\n"
            f"Name=Moto Shorts\nExec=python3 {target}\n"
            f"Path={ROOT}\nTerminal=true\nIcon={ROOT}/icon.ico\n",
            encoding="utf-8")
        link.chmod(0o755)
        return link

    icon = ROOT / "icon.ico"
    icon_arg = f"$s.IconLocation = '{icon}'" if icon.exists() else \
        "$s.IconLocation = 'C:\\Windows\\System32\\imageres.dll,101'"
    ps = f"""
$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{link}')
$s.TargetPath = '{sys.executable}'
$s.Arguments = '"{ROOT / "moto.py"}"'
$s.WorkingDirectory = '{ROOT}'
{icon_arg}
$s.Description = 'Moto Shorts PL - generuj filmy'
$s.Save()
"""
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("   Skrótu nie udało się utworzyć:", (r.stderr or "").strip()[:200])
        return None
    return link


# --------------------------------------------------------------------------- #
# generowanie
# --------------------------------------------------------------------------- #
def env_values():
    vals = {}
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                vals[k.strip()] = v.strip()
    return vals


def notify(text):
    v = env_values()
    token, chat = v.get("TELEGRAM_BOT_TOKEN"), v.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return
    try:
        import requests
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      data={"chat_id": chat, "text": text}, timeout=15)
    except Exception:
        pass


def build_all(py):
    """Odpala make_short.py na każdym scenariuszu, który nie ma jeszcze wyniku."""
    maker = ROOT / "make_short.py"
    jobs = sorted(SCRIPTS.glob("*.json")) if SCRIPTS.is_dir() else []
    if not jobs:
        print("Folder scripts/ jest pusty — dodaj scenariusze .json.")
        return 1
    OUTPUT.mkdir(exist_ok=True)
    todo = [j for j in jobs if not (OUTPUT / f"{j.stem}.mp4").exists()]
    if not todo:
        print(f"Wszystkie {len(jobs)} filmów już jest w output/.")
        open_folder()
        return 0

    print(f"Do wygenerowania: {len(todo)} z {len(jobs)}\n")
    ok, bad = [], []
    for i, job in enumerate(todo, 1):
        print(f"--- [{i}/{len(todo)}] {job.name} ---")
        r = subprocess.run([str(py), str(maker), str(job)], cwd=ROOT,
                           capture_output=True, text=True, errors="replace")
        print((r.stdout or "")[-4000:])
        if r.returncode == 0 and (OUTPUT / f"{job.stem}.mp4").exists():
            ok.append(job.stem)
        else:
            bad.append(job.stem)
            print("BŁĄD:")
            print((r.stderr or "")[-1500:])

    print("\n=== Podsumowanie ===")
    print(f"Gotowe:   {len(ok)}" + (f" -> {', '.join(ok)}" if ok else ""))
    print(f"Nieudane: {len(bad)}" + (f" -> {', '.join(bad)}" if bad else ""))
    if ok:
        notify(f"Shorty gotowe: {len(ok)} ({', '.join(ok[:5])})")
        open_folder()
    return 0 if not bad else 1


def open_folder():
    try:
        if os.name == "nt":
            subprocess.Popen(["explorer", str(OUTPUT)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(OUTPUT)])
        else:
            subprocess.Popen(["xdg-open", str(OUTPUT)])
    except OSError:
        pass


def show_list():
    jobs = sorted(SCRIPTS.glob("*.json")) if SCRIPTS.is_dir() else []
    print(f"Scenariusze: {len(jobs)}")
    for j in jobs:
        got = (OUTPUT / f"{j.stem}.mp4").exists()
        try:
            title = json.loads(j.read_text(encoding="utf-8")).get("title", j.stem)
        except (json.JSONDecodeError, OSError):
            title = j.stem
        print(f"  [{'x' if got else ' '}] {title}")
    return 0


# --------------------------------------------------------------------------- #
def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "run").lower()
    print("=== Moto Shorts PL ===\n")

    if cmd == "lista":
        return show_list()

    py = venv_python()
    if cmd in ("run", "install"):
        py = install()
    if cmd in ("install", "skrot"):
        step(4, "Skrót na pulpicie...")
        link = make_shortcut()
        print(f"   {'Ikona gotowa: ' + str(link) if link else 'Nie udało się.'}")
        if cmd == "install":
            print("\nKlikaj teraz ikonę „Moto Shorts” na pulpicie.")
            pause()
            return 0

    code = build_all(py)
    pause()
    if os.name == "nt" and sys.stdout.isatty():
        pass  # okno zostaje otwarte, żeby dało się przeczytać podsumowanie
    return code


if __name__ == "__main__":
    sys.exit(main())
