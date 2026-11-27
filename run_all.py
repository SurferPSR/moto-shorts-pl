"""Moto Shorts PL — uruchamiany skrótem z pulpitu. Odpala make_short.py na
wszystkich scenariuszach z folderu scripts, pokazuje postęp i otwiera wynik.
"""
import subprocess
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
OUTPUT = ROOT / "output"


def pause(msg="\nGotowe. Naciśnij Enter, aby zamknąć..."):
    try:
        input(msg)
    except EOFError:
        pass


def main():
    print("=== Moto Shorts PL ===")
    if not (ROOT / ".env").exists():
        print("Brak pliku .env. Uruchom najpierw: python setup_moto.py")
        pause()
        return 1
    if not (ROOT / "make_short.py").exists():
        print("Brak make_short.py w tym folderze.")
        pause()
        return 1

    jobs = sorted(SCRIPTS.glob("*.json")) if SCRIPTS.is_dir() else []
    if not jobs:
        print("Folder scripts jest pusty - nie ma czego generować.")
        pause()
        return 1

    OUTPUT.mkdir(exist_ok=True)
    todo = [j for j in jobs if not (OUTPUT / f"{j.stem}.mp4").exists()]
    if not todo:
        print("Wszystkie Shorty już są w folderze output.")
        subprocess.Popen(["explorer", str(OUTPUT)])
        pause()
        return 0

    print(f"Do wygenerowania: {len(todo)} z {len(jobs)}")
    ok, failed = [], []
    for i, job in enumerate(todo, 1):
        print(f"\n--- [{i}/{len(todo)}] {job.name} ---")
        start = perf_counter()
        r = subprocess.run([sys.executable, str(ROOT / "make_short.py"), str(job)],
                           cwd=ROOT, capture_output=True, text=True, errors="replace")
        print(r.stdout[-4000:] if r.stdout else "")
        if r.returncode == 0 and (OUTPUT / f"{job.stem}.mp4").exists():
            ok.append(job.stem)
            print(f"OK ({perf_counter() - start:.0f}s)")
        else:
            failed.append(job.stem)
            print("BŁĄD:")
            print((r.stderr or "")[-2000:])

    print("\n=== Podsumowanie ===")
    print(f"Gotowe:   {len(ok)}" + (f" -> {', '.join(ok)}" if ok else ""))
    print(f"Nieudane: {len(failed)}" + (f" -> {', '.join(failed)}" if failed else ""))
    if ok:
        subprocess.Popen(["explorer", str(OUTPUT)])
    pause()
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
