"""Moto Shorts PL — instalacja, klucz API i skrót na pulpicie.

Uruchomienie:
    python moto.py install   # biblioteki + klucz + ikona na pulpicie
    python moto.py key       # tylko wpisanie / zmiana klucza
    python moto.py skrot     # tylko ikona na pulpicie
    python moto.py           # generowanie filmow (bez pytan)

Klucz wpisujesz TU, w tym oknie — nic nie otwiera sie samo i nic nie zamyka.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
OUTPUT = ROOT / "output"
ENV = ROOT / ".env"
VENV = ROOT / ".venv"
PACKAGES = ["edge-tts", "requests", "python-dotenv"]

DEFAULTS = {
    "PIXABAY_API_KEY": "",
    "PEXELS_API_KEY": "",
    "VOICE": "pl-PL-MarekNeural",
    "VOICE_RATE": "+8%",
    "TELEGRAM_BOT_TOKEN": "",
    "TELEGRAM_CHAT_ID": "798730878",
}


# --------------------------------------------------------------------------- #
# pomocnicze
# --------------------------------------------------------------------------- #
def ask(text, default=""):
    """Pyta i NIE zamyka okna, gdy odpowiedz jest pusta."""
    try:
        value = input(text).strip()
    except EOFError:
        return default
    return value or default


def pause(msg="\nNacisnij Enter, aby zamknac to okno..."):
    try:
        input(msg)
    except EOFError:
        pass


def step(n, text):
    print(f"[{n}] {text}")


def read_env():
    vals = dict(DEFAULTS)
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                vals[k.strip()] = v.strip()
    return vals


def write_env(vals):
    order = ["PIXABAY_API_KEY", "PEXELS_API_KEY", "VOICE", "VOICE_RATE",
             "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    lines = ["# Plik utworzony automatycznie przez moto.py",
             "# Klucz wideo: https://pixabay.com/api/docs/", ""]
    for k in order:
        lines.append(f"{k}={vals.get(k, '')}")
    for k in vals:
        if k not in order:
            lines.append(f"{k}={vals[k]}")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def venv_python():
    exe = (VENV / "Scripts" / "python.exe") if os.name == "nt" \
        else (VENV / "bin" / "python")
    return exe if exe.exists() else Path(sys.executable)


# --------------------------------------------------------------------------- #
# instalacja
# --------------------------------------------------------------------------- #
def install_packages():
    step(1, "Sprawdzam ffmpeg...")
    if shutil.which("ffmpeg") is None:
        if os.name == "nt" and shutil.which("winget"):
            print("   Probuje zainstalowac ffmpeg przez winget...")
            subprocess.run(["winget", "install", "-e", "--id", "Gyan.FFmpeg",
                            "--accept-package-agreements",
                            "--accept-source-agreements"], check=False)
    print("   ffmpeg: " + ("OK" if shutil.which("ffmpeg") else
                           "brak — zainstaluj: winget install Gyan.FFmpeg"))

    step(2, "Biblioteki Pythona...")
    py = venv_python()
    if py == Path(sys.executable) and not VENV.exists():
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=False)
        py = venv_python()
    subprocess.run([str(py), "-m", "pip", "install", "--upgrade", "pip"],
                   check=False, stdout=subprocess.DEVNULL)
    r = subprocess.run([str(py), "-m", "pip", "install", *PACKAGES])
    print("   " + ("OK" if r.returncode == 0 else "BLAD — sprawdz internet"))
    return py


def ask_key(py=None):
    """Wpisanie klucza w tym oknie. Zapisujemy od razu do .env."""
    step(3, "Klucz do wideo (Pixabay)")
    vals = read_env()
    current = vals.get("PIXABAY_API_KEY", "")
    if current:
        print(f"   Klucz juz jest zapisany (konczy sie na ...{current[-4:]}).")
        new = ask("   Enter = zostaw, albo wklej nowy klucz: ")
    else:
        print("   Otworz w przegladarce: https://pixabay.com/api/docs/")
        print("   Zaloguj sie, skopiuj klucz i wklej go tutaj.")
        print("   (W tym oknie: prawy przycisk myszy = wklej)")
        new = ask("   Klucz PIXABAY_API_KEY: ")
    if new:
        vals["PIXABAY_API_KEY"] = new
        write_env(vals)
        print(f"   Zapisano do {ENV.name}.")
    else:
        if not current:
            print("   Pusto — bez klucza nie sciagnie wideo ze stocku.")
            print("   Uruchom pozniej: python moto.py key")
        else:
            print("   Zostawiam stary klucz.")
    return vals.get("PIXABAY_API_KEY", "")


def desktop():
    for c in (Path.home() / "Desktop",
              Path(os.environ.get("OneDrive", "") or ".") / "Desktop"):
        if c.is_dir():
            return c
    return Path.home()


def make_shortcut():
    link = desktop() / "Moto Shorts.lnk"
    if os.name != "nt":
        link = desktop() / "Moto Shorts.desktop"
        link.write_text(
            "[Desktop Entry]\nType=Application\nName=Moto Shorts\n"
            f"Name[pl]=Moto Shorts\nExec=python3 {ROOT / 'moto.py'}\n"
            f"Path={ROOT}\nTerminal=true\n", encoding="utf-8")
        link.chmod(0o755)
        return link

    icon = ROOT / "icon.ico"
    icon_line = (f"$s.IconLocation = '{icon}'" if icon.exists()
                 else "$s.IconLocation = 'C:\\Windows\\System32\\imageres.dll,101'")
    ps = f"""
$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{link}')
$s.TargetPath = '{sys.executable}'
$s.Arguments = '"{ROOT / "moto.py"}"'
$s.WorkingDirectory = '{ROOT}'
{icon_line}
$s.Description = 'Moto Shorts PL - generuj filmy'
$s.Save()
New-Item -ItemType File -Force -Path "{ROOT / 'shortcut_ok.txt'}" | Out-Null
"""
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True)
    ok = (ROOT / "shortcut_ok.txt").exists()
    if ok:
        (ROOT / "shortcut_ok.txt").unlink()
    if r.returncode != 0 or not ok:
        print("   Skrotu nie udalo sie utworzyc:", (r.stderr or "").strip()[:200])
        return None
    return link


# --------------------------------------------------------------------------- #
# generowanie
# --------------------------------------------------------------------------- #
def env_values():
    return read_env()


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


def build_all(py):
    maker = ROOT / "make_short.py"
    if not maker.exists():
        print("Brak make_short.py w tym folderze.")
        return 1
    jobs = sorted(SCRIPTS.glob("*.json")) if SCRIPTS.is_dir() else []
    if not jobs:
        print("Folder scripts/ jest pusty — dodaj scenariusze .json.")
        return 1
    if not env_values().get("PIXABAY_API_KEY") and not env_values().get("PEXELS_API_KEY"):
        print("Brak klucza API. Wpisz go: python moto.py key")
        return 1

    OUTPUT.mkdir(exist_ok=True)
    todo = [j for j in jobs if not (OUTPUT / f"{j.stem}.mp4").exists()]
    if not todo:
        print(f"Wszystkie {len(jobs)} filmow jest juz w output/.")
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
            print("BLAD:")
            print((r.stderr or "")[-1500:])

    print("\n=== Podsumowanie ===")
    print(f"Gotowe:   {len(ok)}" + (f" -> {', '.join(ok)}" if ok else ""))
    print(f"Nieudane: {len(bad)}" + (f" -> {', '.join(bad)}" if bad else ""))
    if ok:
        notify(f"Shorty gotowe: {len(ok)} ({', '.join(ok[:5])})")
        open_folder()
    return 0 if not bad else 1


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
        py = install_packages()
    if cmd == "key":
        ask_key()
        pause()
        return 0
    if cmd in ("install", "skrot"):
        ask_key()
        step(4, "Ikona na pulpicie...")
        link = make_shortcut()
        print("   " + (f"Gotowe: {link}" if link else "Nie udalo sie."))
        if cmd == "install":
            print("\nKlikaj ikone „Moto Shorts” na pulpicie, aby generowac filmy.")
            pause()
            return 0

    code = build_all(py)
    pause()
    return code


if __name__ == "__main__":
    sys.exit(main())
