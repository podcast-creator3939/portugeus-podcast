#!/usr/bin/env python3
"""Turn an episode script (Markdown) into a single MP3.

Dialogue lines look like:  **Ana:** Bom dia, gente!
Only the dialogue before the "## Notas de estudo" heading is read aloud.
Ana and Rafa use the same Piper voice; Ana is pitched up so the hosts sound different.

Usage: python3 tools/make_audio.py episodes/2026-11-12/script.md episodes/2026-11-12/episode.mp3
"""
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

REPO = Path(__file__).resolve().parent.parent
VOICE = REPO / "voices" / "pt_BR-faber-medium.onnx"
SPEAKERS = {
    # name: (pitch factor, tempo after pitch shift, Piper length_scale)
    "Ana": (1.22, 1.0, 1.0),
    "Rafa": (1.0, 1.0, 1.05),
}
LINE_RE = re.compile(r"^\s*\*\*(Ana|Rafa)\s*:\*\*\s*(.+)$")
PAUSE_SEC = 0.35


def dialogue(script: str):
    body = re.split(r"^##\s+Notas de estudo", script, flags=re.M | re.I)[0]
    for raw in body.splitlines():
        m = LINE_RE.match(raw)
        if not m:
            continue
        text = m.group(2)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links -> text
        text = re.sub(r"[*_`#>]", "", text).strip()
        if text:
            yield m.group(1), text


def main(src: str, out: str):
    lines = list(dialogue(Path(src).read_text(encoding="utf-8")))
    if not lines:
        sys.exit("No dialogue lines found (expected '**Ana:** ...' / '**Rafa:** ...').")
    voice = PiperVoice.load(str(VOICE))
    rate = voice.config.sample_rate
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts = []
        for i, (who, text) in enumerate(lines):
            pitch, tempo, length = SPEAKERS[who]
            raw = tmp / f"{i:04d}_raw.wav"
            with wave.open(str(raw), "wb") as wf:
                voice.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=length))
            seg = tmp / f"{i:04d}.wav"
            filt = (
                f"asetrate={rate}*{pitch},aresample={rate},atempo={tempo / pitch:.4f},"
                f"apad=pad_dur={PAUSE_SEC}"
            )
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-af", filt,
                            "-ac", "1", "-ar", "24000", str(seg)], check=True)
            parts.append(seg)
        listing = tmp / "list.txt"
        listing.write_text("".join(f"file '{p}'\n" for p in parts))
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(listing), "-af", "loudnorm=I=-16:TP=-1.5",
                        "-c:a", "libmp3lame", "-b:a", "64k", "-ac", "1", out], check=True)
    print(f"Wrote {out} ({len(lines)} lines)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
