"""Moto Shorts PL — instalacja i skrót na pulpicie. Uruchom raz: python setup_moto.py

Co robi:
 1. sprawdza ffmpeg,
 2. instaluje biblioteki z requirements.txt,
 3. tworzy .env (jeśli brak) i otwiera go w Notatniku,
 4. tworzy na pulpicie skrót "Moto Shorts.lnk" -> run.bat z ikoną motocykla.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ICON_SOURCES = [
    Path(r"C:\Windows\System32\imageres.dll"),   # zawiera ikony motoryzacyjne
    Path(r"C:\Windows\System32\shell32.dll"),
]


def pause():
    try:
        input("\nNaciśnij Enter, aby zamknąć...")
    except EOFError:
        pass


def install_packages():
    print("[1/4] Instaluje biblioteki...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r",
                    str(ROOT / "requirements.txt")], check=False)


def ensure_env():
    env, example = ROOT / ".env", ROOT / ".env.example"
    if env.exists():
        print("[2/4] Plik .env juz istnieje.")
        return
    if example.exists():
        shutil.copy(example, env)
    else:
        env.write_text("PIXABAY_API_KEY=\nVOICE=pl-PL-MarekNeural\n"
                       "VOICE_RATE=+8%\nTELEGRAM_BOT_TOKEN=\n"
                       "TELEGRAM_CHAT_ID=798730878\n", encoding="utf-8")
    print("[2/4] Utworzono .env - wklej klucz PIXABAY_API_KEY i zapisz plik.")
    try:
        subprocess.Popen(["notepad.exe", str(env)])
    except OSError:
        pass
    import webbrowser
    webbrowser.open("https://pixabay.com/accounts/register/")


def shortcut_path():
    """Pulpit — OneDrive też, jeśli tam jest przeniesiony."""
    candidates = [Path.home() / "Desktop",
                  Path(os.environ.get("OneDrive", "")) / "Desktop"]
    for c in candidates:
        if c.is_dir():
            return c / "Moto Shorts.lnk"
    return Path.home() / "Moto Shorts.lnk"


def make_shortcut():
    target = ROOT / "run.bat"
    if not target.exists():
        print("   Brak run.bat w folderze - skrót nie powstanie.")
        return None
    icon = next((f",{n}" for f, n in
                 ((p, 0) for p in ICON_SOURCES if p.exists())), "")
    ps = f"""
$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{shortcut_path()}')
$s.TargetPath = '{target}'
$s.WorkingDirectory = '{ROOT}'
$s.IconLocation = 'C:\\Windows\\System32\\imageres.dll,101'{icon}
$s.Description = 'Moto Shorts PL - generuj Shorty'
$s.Save()
"""
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("   Nie udało się utworzyć skrótu:", r.stderr.strip()[:300])
        return None
    return shortcut_path()


def main():
    print("=== Moto Shorts PL - instalacja ===\n")
    if os.name != "nt":
        print("Ten instalator jest dla Windows. Na innym systemie uruchom "
              "run.bat odpowiednikiem: python make_short.py scripts/*.json")
        pause()
        return
    if shutil.which("ffmpeg") is None:
        print("[0/4] Brak ffmpeg. Zainstaluj: winget install Gyan.FFmpeg "
              "i uruchom ten plik ponownie.")
        pause()
        return
    print("[0/4] ffmpeg OK.")
    install_packages()
    ensure_env()
    print("[3/4] Tworze skrót na pulpicie...")
    link = make_shortcut()
    print("[4/4] " + (f"Skrót gotowy: {link}" if link
                      else "Skrót nie powstał - uruchamiaj run.bat z folderu."))
    print("\nGotowe. Klikaj ikone 'Moto Shorts' na pulpicie, aby generowac filmy.")
    pause()


if __name__ == "__main__":
    main()
