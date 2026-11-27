"""Moto Shorts PL — scenariusz JSON -> gotowy Short 9:16 (MP4).

Wideo: Pixabay (domyślnie) albo Pexels, jeśli masz klucz.
Użycie:  python make_short.py scripts/01_isle_of_man.json
Wynik:   output/<nazwa>.mp4

Uwaga: Pixabay wymaga cache 24h i nie pozwala na masowe pobierania.
Pobrane klipy trzymamy w work/_cache, więc drugi przebieg nie pyta API drugi raz.
"""
import asyncio
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import edge_tts
import requests
from dotenv import load_dotenv

load_dotenv()
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "")
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "")
VOICE = os.getenv("VOICE", "pl-PL-MarekNeural")
RATE = os.getenv("VOICE_RATE", "+8%")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")
W, H = 1080, 1920
CACHE = Path("work") / "_cache"

# Pixabay nie ma filtra orientacji — te słowa pomagają dostać kadr pionowy.
VERTICAL_HINTS = "vertical portrait"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip())


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


async def tts(text, mp3):
    """Mowa + znaczniki słów (do napisów)."""
    words = []
    comm = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append((start, start + chunk["duration"] / 1e7, chunk["text"]))
    return words


def download(url, dest):
    with requests.get(url, stream=True, timeout=90) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for part in resp.iter_content(1 << 20):
                f.write(part)


def pexels_clip(query, dest):
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": query, "orientation": "portrait", "per_page": 15},
        timeout=30)
    r.raise_for_status()
    videos = r.json().get("videos", [])
    if not videos:
        raise SystemExit(f"Pexels: brak wideo dla '{query}'")
    files = sorted(random.choice(videos[:8])["video_files"],
                   key=lambda f: abs((f.get("height") or 0) - H))
    download(files[0]["link"], dest)


def pixabay_clip(query, dest):
    """Pixabay zwraca 'videos' z kilkoma rozdzielczościami na wynik."""
    cache = CACHE / f"{hashlib.md5(query.encode()).hexdigest()}.json"
    if cache.exists():
        hits = json.loads(cache.read_text(encoding="utf-8"))
    else:
        r = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": PIXABAY_KEY, "q": f"{query} {VERTICAL_HINTS}",
                    "per_page": 20, "safesearch": "true"},
            timeout=30)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(hits), encoding="utf-8")  # cache 24h+
        if not hits:  # druga próba bez podpowiedzi o kadrze
            r = requests.get(
                "https://pixabay.com/api/videos/",
                params={"key": PIXABAY_KEY, "q": query, "per_page": 20,
                        "safesearch": "true"},
                timeout=30)
            r.raise_for_status()
            hits = r.json().get("hits", [])
    if not hits:
        raise SystemExit(f"Pixabay: brak wideo dla '{query}'")
    hit = random.choice(hits[:10])
    variants = hit["videos"]
    pick = variants.get("large") or variants.get("medium") or variants.get("small")
    download(pick["url"], dest)


def get_clip(query, dest):
    """Pixabay, a gdy brak klucza — Pexels."""
    if PIXABAY_KEY:
        pixabay_clip(query, dest)
    elif PEXELS_KEY:
        pexels_clip(query, dest)
    else:
        raise SystemExit("Brak klucza: wpisz PIXABAY_API_KEY (albo PEXELS_API_KEY) w .env")


def scene_clip(src, dst, dur):
    """Przytnij, wykadruj do 9:16 i zapętl, jeśli klip za krótki."""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},fps=30,setsar=1")
    run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-t", f"{dur:.3f}",
         "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(dst)])


def write_srt(words, path, per_line=3):
    """Napisy po 3 słowa — dobrze trzymają uwagę w Shorts."""
    lines = []
    for i in range(0, len(words), per_line):
        grp = words[i:i + per_line]
        lines.append((grp[0][0], grp[-1][1], " ".join(w[2] for w in grp).upper()))
    with open(path, "w", encoding="utf-8") as f:
        for n, (a, b, t) in enumerate(lines, 1):
            f.write(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n\n")


def notify(text):
    if TG_TOKEN and TG_CHAT:
        try:
            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                          data={"chat_id": TG_CHAT, "text": text}, timeout=15)
        except requests.RequestException:
            pass


def build(script_path):
    script = json.loads(Path(script_path).read_text(encoding="utf-8"))
    name = Path(script_path).stem
    work = Path("work") / name
    work.mkdir(parents=True, exist_ok=True)
    Path("output").mkdir(exist_ok=True)

    all_words, clips, audios, t0 = [], [], [], 0.0
    for i, sc in enumerate(script["scenes"]):
        mp3 = work / f"a{i}.mp3"
        words = asyncio.run(tts(sc["text"], mp3))
        d = duration(mp3) + 0.15
        all_words += [(a + t0, b + t0, w) for a, b, w in words]
        raw, clip = work / f"raw{i}.mp4", work / f"v{i}.mp4"
        if sc.get("file"):  # własny plik zamiast stocku
            raw = Path(sc["file"])
        elif not raw.exists():
            get_clip(sc["query"], raw)
        scene_clip(raw, clip, d)
        clips.append(clip)
        audios.append((mp3, d))
        t0 += d
        print(f"  scena {i + 1}/{len(script['scenes'])}: {d:.1f}s")

    (work / "v.txt").write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "v.txt"),
         "-c", "copy", str(work / "video.mp4")])

    # audio: każda scena dopełniona ciszą do swojej długości
    inputs, filt = [], []
    for i, (mp3, d) in enumerate(audios):
        inputs += ["-i", str(mp3)]
        filt.append(f"[{i}:a]apad,atrim=0:{d:.3f}[a{i}]")
    filt.append("".join(f"[a{i}]" for i in range(len(audios)))
                + f"concat=n={len(audios)}:v=0:a=1[out]")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filt),
         "-map", "[out]", str(work / "voice.m4a")])

    srt = work / "subs.srt"
    write_srt(all_words, srt)
    style = ("FontName=Arial,FontSize=16,Bold=1,PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H00000000,Outline=3,Shadow=0,Alignment=2,MarginV=90")
    srt_arg = str(srt).replace("\\", "/").replace(":", "\\:")
    out = Path("output") / f"{name}.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(work / "video.mp4"), "-i", str(work / "voice.m4a")]
    music = script.get("music")
    if music and Path(music).exists():
        cmd += ["-stream_loop", "-1", "-i", music, "-filter_complex",
                "[2:a]volume=0.12[m];[1:a][m]amix=inputs=2:duration=first[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-vf", f"subtitles='{srt_arg}':force_style='{style}'",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)]
    run(cmd)

    total = duration(out)
    print(f"Gotowe: {out} ({total:.1f}s)")
    if total > 180:
        print("UWAGA: ponad 3 min — YouTube nie uzna tego za Short.")
    notify(f"Short gotowy: {script.get('title', name)} ({total:.0f}s)")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Użycie: python make_short.py scripts/plik.json")
    for p in sys.argv[1:]:
        print(f"== {p}")
        try:
            build(p)
        except subprocess.CalledProcessError as e:
            print(e.stderr.decode(errors="ignore")[-1500:])
            raise
