"""Double-click launcher for Verbatim (standard library only).

Steps: create `.venv` and install requirements (only when they change), make sure
`.env` has both API keys, seed the demo transcript cache and start Streamlit in
REAL mode (`ACTA_FAKE_STAGES` empty), opening the browser when the port answers.

Usage: python launcher/launch.py [--check] [--no-browser]
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import venv
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
REQ_HASH = VENV / ".req-hash"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
DATA_DIR = ROOT / "app" / "data"
DEMO_AUDIO_ID = "dfdf840d54fbc7fb"
APP = ROOT / "app" / "ui" / "streamlit_app.py"
PORT = 8501
URL = f"http://localhost:{PORT}"
HEALTH_URL = f"{URL}/_stcore/health"
REQUIRED_KEYS = ("ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY")
KEY_LABELS = {"ANTHROPIC_API_KEY": "Anthropic (Claude)", "ELEVENLABS_API_KEY": "ElevenLabs"}
MIN_PYTHON = (3, 11)
STARTUP_TIMEOUT_S = 120


def say(msg: str) -> None:
    """Print a progress line for the user."""
    print(f"[Verbatim] {msg}", flush=True)


def venv_python() -> Path:
    """Path of the interpreter inside `.venv` for this OS."""
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def requirements_hash() -> str:
    """sha256 of requirements.txt."""
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()


def needs_install() -> bool:
    """True if `.venv` is missing or requirements.txt changed since the last install."""
    if not venv_python().exists():
        return True
    try:
        return REQ_HASH.read_text(encoding="utf-8").strip() != requirements_hash()
    except OSError:
        return True


def ensure_venv() -> None:
    """Create `.venv` if missing and (re)install requirements when their hash changes."""
    if not venv_python().exists():
        say("Primera ejecución: creando el entorno .venv (tarda unos minutos)...")
        venv.EnvBuilder(with_pip=True).create(VENV)
    if not needs_install():
        say("Dependencias al día.")
        return
    say("Instalando dependencias de requirements.txt...")
    py = str(venv_python())
    subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"], check=False)
    subprocess.run([py, "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)
    REQ_HASH.write_text(requirements_hash(), encoding="utf-8")
    say("Dependencias instaladas.")


def read_env(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines of a .env file (no expansion, quotes stripped)."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def set_env_value(path: Path, key: str, value: str) -> None:
    """Set `key=value` in a .env file, replacing the existing line or appending it."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    for i, line in enumerate(lines):
        if line.strip().partition("=")[0].strip() == key and not line.lstrip().startswith("#"):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def missing_keys() -> list[str]:
    """API keys that are empty or absent in `.env`."""
    env = read_env(ENV_FILE)
    return [k for k in REQUIRED_KEYS if not env.get(k)]


def ensure_env() -> None:
    """Create `.env` from `.env.example` and ask for the API keys that are empty."""
    if not ENV_FILE.exists():
        shutil.copyfile(ENV_EXAMPLE, ENV_FILE)
        say("Creado .env a partir de .env.example.")
    missing = missing_keys()
    if not missing:
        say("Claves de API presentes en .env.")
        return
    say("Faltan claves de API. Se guardarán solo en el .env de este ordenador.")
    for key in missing:
        value = ""
        while not value:
            value = getpass.getpass(f"  Pega la clave de {KEY_LABELS[key]} (no se verá al escribir): ").strip()
        set_env_value(ENV_FILE, key, value)
    say("Claves guardadas en .env.")


def cache_dir() -> Path:
    """Transcript cache dir, honouring ACTA_CACHE_DIR in `.env` like app/config.py."""
    return ROOT / read_env(ENV_FILE).get("ACTA_CACHE_DIR", ".cache")


def seed_demo_cache() -> None:
    """Copy every versioned transcript (demo clip + meetings) into the STT cache: 0 ElevenLabs credits."""
    copied = 0
    for src in sorted(DATA_DIR.rglob("*.transcript.json")):
        try:
            aid = json.loads(src.read_text(encoding="utf-8"))["audio_id"]
        except (OSError, ValueError, KeyError):
            continue
        target = cache_dir() / "stt" / f"{aid}.json"
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        copied += 1
    if copied:
        say(f"{copied} transcripciones de la demo copiadas a la caché (0 créditos de ElevenLabs).")


def server_up(timeout: float = 1.0) -> bool:
    """True if Streamlit's health endpoint answers ok."""
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=timeout) as resp:  # noqa: S310 (fixed localhost URL)
            return resp.status == 200
    except OSError:
        return False


def real_mode_env() -> dict[str, str]:
    """Process environment forcing REAL mode (empty ACTA_FAKE_STAGES beats .env)."""
    env = dict(os.environ)
    env["ACTA_FAKE_STAGES"] = ""
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def run_streamlit(open_browser: bool) -> int:
    """Start Streamlit in real mode, open the browser when ready and wait until it exits."""
    if server_up():
        say(f"Verbatim ya está abierto en {URL}.")
        if open_browser:
            webbrowser.open(URL)
        return 0
    cmd = [
        str(venv_python()), "-m", "streamlit", "run", str(APP),
        "--server.port", str(PORT), "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    say("Arrancando Verbatim en modo real...")
    proc = subprocess.Popen(cmd, cwd=ROOT, env=real_mode_env())
    try:
        deadline = time.monotonic() + STARTUP_TIMEOUT_S
        while proc.poll() is None and not server_up():
            if time.monotonic() > deadline:
                say("Streamlit tarda demasiado en responder; revisa los mensajes de arriba.")
                break
            time.sleep(0.5)
        if proc.poll() is None and server_up():
            say(f"Verbatim abierto en {URL}. Para cerrarlo, cierra esta ventana (o pulsa Ctrl+C).")
            if open_browser:
                webbrowser.open(URL)
        return proc.wait()
    except KeyboardInterrupt:
        say("Cerrando Verbatim...")
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        return 0


def check() -> int:
    """Report the launcher state without installing, writing or starting anything."""
    ok = sys.version_info >= MIN_PYTHON
    say(f"Python {sys.version.split()[0]}: {'ok' if ok else 'se necesita 3.11 o superior'}")
    say(f".venv: {'existe' if venv_python().exists() else 'no existe (se creará)'}")
    say(f"Dependencias: {'hay que instalarlas' if needs_install() else 'al día'}")
    if ENV_FILE.exists():
        missing = missing_keys()
        say(f".env: existe; claves {'completas' if not missing else 'faltan: ' + ', '.join(missing)}")
    else:
        say(".env: no existe (se creará desde .env.example y se pedirán las claves)")
    cached = (cache_dir() / "stt" / f"{DEMO_AUDIO_ID}.json").exists()
    say(f"Caché del clip de la demo: {'presente' if cached else 'se copiará'}")
    say(f"App: {'ok' if APP.exists() else 'NO ENCONTRADA'} ({APP.relative_to(ROOT)})")
    say(f"Puerto {PORT}: {'Verbatim ya responde' if server_up() else 'libre'}")
    return 0 if ok and APP.exists() else 1


def main(argv: list[str] | None = None) -> int:
    """Entry point: prepare the environment and launch Verbatim in real mode."""
    parser = argparse.ArgumentParser(description="Lanzador de Verbatim")
    parser.add_argument("--check", action="store_true", help="solo comprueba, no instala ni arranca")
    parser.add_argument("--no-browser", action="store_true", help="no abre el navegador")
    args = parser.parse_args(argv)
    os.chdir(ROOT)
    if args.check:
        return check()
    if sys.version_info < MIN_PYTHON:
        say('Instala Python 3.11 o superior desde python.org (marca "Add Python to PATH")')
        return 1
    try:
        ensure_venv()
        ensure_env()
        seed_demo_cache()
        return run_streamlit(open_browser=not args.no_browser)
    except subprocess.CalledProcessError as exc:
        say(f"Error instalando dependencias (código {exc.returncode}). Revisa la conexión a internet.")
        return 1
    except KeyboardInterrupt:
        say("Cancelado.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
