"""Build dist/Verbatim.zip for the jury, with a demo `.env` inside (standard library only).

Files come from `git ls-files` (never `.env`, `.venv`, `.cache`, `dist/` or untracked
files). Keys are asked with getpass or read from VERBATIM_ZIP_ANTHROPIC_KEY and
VERBATIM_ZIP_ELEVENLABS_KEY, never from the personal `.env`.

Usage: python launcher/make_zip.py [--include-untracked]
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OUT = DIST / "Verbatim.zip"
TOP = "Verbatim"
EXCLUDED_PREFIXES = ("tests/eval/results/", ".github/", ".claude/", "tools/")
EXECUTABLE = {"Verbatim.command"}
LAUNCHER_FILES = ("Verbatim.bat", "Verbatim.command", "launcher", ".streamlit")
TRANSCRIPT_SUFFIX = ".transcript.json"  # versioned Scribe transcripts next to each audio (demo clip + m01…m05)
README_JURY = ROOT / "launcher" / "LEEME_JURADO.txt"
KEYS = (
    ("ANTHROPIC_API_KEY", "VERBATIM_ZIP_ANTHROPIC_KEY", "Anthropic (Claude)"),
    ("ELEVENLABS_API_KEY", "VERBATIM_ZIP_ELEVENLABS_KEY", "ElevenLabs"),
)
ZIP_ENV_VALUES = {
    "ACTA_FAKE_STAGES": "",
    "ACTA_LLM_CACHE": "1",
    "ACTA_ADVISOR_NAME": "Asesor de demostración",
}


def git(*args: str) -> str:
    """Run a git command in the repo root and return stdout."""
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def list_files(include_untracked: bool) -> list[str]:
    """Versioned files (optionally plus untracked, non-ignored ones) minus what the jury does not need."""
    args = ["ls-files", "-z", "--cached"]
    if include_untracked:
        args += ["--others", "--exclude-standard"]
    names = {n for n in git(*args).split("\0") if n}
    keep = [n for n in names if not n.startswith(EXCLUDED_PREFIXES) and (ROOT / n).is_file()]
    return sorted(keep)


def warn_dirty_tree(include_untracked: bool) -> None:
    """Warn about uncommitted changes: the zip takes files from disk, untracked ones are left out."""
    dirty = git("status", "--porcelain", "--untracked-files=no").rstrip()
    if dirty:
        print("AVISO: hay cambios sin commit; entra la versión del disco de estos archivos:")
        print(dirty)
    untracked = git("status", "--porcelain", "--", *LAUNCHER_FILES).rstrip()
    if not include_untracked and any(line.startswith("??") for line in untracked.splitlines()):
        print("AVISO: archivos del lanzador sin versionar; NO entran en el zip (haz commit o usa --include-untracked):")
        print(untracked)


def ask_keys() -> dict[str, str]:
    """Jury keys from VERBATIM_ZIP_* env vars or getpass; never from the personal .env."""
    keys: dict[str, str] = {}
    for env_key, var, label in KEYS:
        value = os.environ.get(var, "").strip()
        while not value:
            value = getpass.getpass(f"Clave de {label} SOLO para el jurado (con límite de gasto): ").strip()
        keys[env_key] = value
    return keys


def build_env(keys: dict[str, str]) -> str:
    """Content of the zip's .env: .env.example with the jury keys and real-mode settings."""
    values = {**keys, **ZIP_ENV_VALUES}
    lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    pending = dict(values)
    for i, line in enumerate(lines):
        key = line.partition("=")[0].strip()
        if not line.lstrip().startswith("#") and key in pending:
            lines[i] = f"{key}={pending.pop(key)}"
    lines += [f"{k}={v}" for k, v in pending.items()]
    return "\n".join(lines) + "\n"


def fixed_line_endings(name: str, data: bytes) -> bytes:
    """LF for the Mac launcher (bash breaks on CRLF) and CRLF for the .bat, whatever git checked out."""
    if name.endswith(".command"):
        return data.replace(b"\r\n", b"\n")
    if name.endswith(".bat"):
        return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return data


def zip_info(arcname: str, mode: int = 0o100644) -> zipfile.ZipInfo:
    """ZipInfo with Unix permissions so macOS keeps the executable bit."""
    info = zipfile.ZipInfo(arcname, date_time=time.localtime()[:6])
    info.create_system = 3  # Unix: external_attr carries the permissions
    info.external_attr = mode << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def stt_cache_entries(files: list[str]) -> dict[str, bytes]:
    """`.cache/stt/<audio_id>.json` for every versioned transcript, so uploading those audios costs 0 credits."""
    entries: dict[str, bytes] = {}
    for name in files:
        if name.startswith("app/data/") and name.endswith(TRANSCRIPT_SUFFIX):
            data = (ROOT / name).read_bytes()
            entries[f".cache/stt/{json.loads(data)['audio_id']}.json"] = data
    return entries


def build_zip(files: list[str], env_text: str) -> None:
    """Write dist/Verbatim.zip with everything under Verbatim/ plus LEEME_JURADO.txt at the root."""
    DIST.mkdir(exist_ok=True)
    tmp = OUT.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(zip_info("LEEME_JURADO.txt"), README_JURY.read_bytes())
        for name in files:
            mode = 0o100755 if name in EXECUTABLE else 0o100644
            zf.writestr(zip_info(f"{TOP}/{name}", mode), fixed_line_endings(name, (ROOT / name).read_bytes()))
        zf.writestr(zip_info(f"{TOP}/.env", 0o100600), env_text.encode("utf-8"))
        for cache_name, data in stt_cache_entries(files).items():
            zf.writestr(zip_info(f"{TOP}/{cache_name}"), data)
    tmp.replace(OUT)


def main(argv: list[str] | None = None) -> int:
    """Entry point: build the jury zip."""
    parser = argparse.ArgumentParser(description="Genera dist/Verbatim.zip para el jurado (con claves)")
    parser.add_argument(
        "--include-untracked", action="store_true",
        help="incluye también archivos sin versionar no ignorados (útil antes del commit)",
    )
    args = parser.parse_args(argv)
    warn_dirty_tree(args.include_untracked)
    files = list_files(args.include_untracked)
    keys = ask_keys()
    build_zip(files, build_env(keys))
    size_mb = OUT.stat().st_size / 1_000_000
    n_extra = 2 + len(stt_cache_entries(files))  # LEEME_JURADO.txt + .env + STT cache
    print(f"Generado {OUT.relative_to(ROOT)} ({size_mb:.1f} MB, {len(files) + n_extra} archivos).")
    print("Este zip contiene claves: envíalo solo al jurado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
