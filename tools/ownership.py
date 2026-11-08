"""Ownership rules shared by the edit hook and the CI check (owner: D)."""

from __future__ import annotations

import json
import os
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = json.loads((ROOT / "tools" / "ownership.json").read_text(encoding="utf-8"))
ROLES = tuple(RULES["roles"])


def current_role() -> str | None:
    """Role from the ACTA_ROL env var or from the repo's .env file."""
    role = os.getenv("ACTA_ROL", "").strip().upper()
    if not role:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("ACTA_ROL="):
                    role = line.split("=", 1)[1].strip().strip('"').strip("'").upper()
    return role if role in ROLES else None


def rel(path: str | Path) -> str | None:
    """Repo-relative POSIX path, or None if the path is outside the repo."""
    p = Path(path)
    if not p.is_absolute():
        p = (Path.cwd() / p)
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def contract_mode() -> bool:
    """D may edit frozen files while ACTA_CONTRACT_EDIT=1 (for a PR labelled 'contrato')."""
    return os.getenv("ACTA_CONTRACT_EDIT", "") == "1"


def verdict(role: str, path: str) -> tuple[bool, str]:
    """(allowed, reason) for `role` touching repo-relative `path`."""
    if any(fnmatch(path, pat) for pat in RULES["frozen"]):
        if role == "D" and contract_mode():
            return True, "congelado, editado por D en modo contrato"
        return False, f"{path} está CONGELADO: solo por PR con etiqueta 'contrato' aprobado por D (CLAUDE.md §2)."
    if any(fnmatch(path, pat) for pat in RULES["shared"]):
        return True, "compartido: respeta las reglas de CLAUDE.md §3"
    if any(fnmatch(path, pat) for pat in RULES["roles"].get(role, [])):
        return True, "propio"
    owner = next((r for r, pats in RULES["roles"].items() if any(fnmatch(path, p) for p in pats)), None)
    if owner:
        return False, (f"{path} pertenece al rol {owner}. No lo edites: añade una petición en la sección "
                       f"'Peticiones' de {owner} en docs/TASKS.md.")
    return False, f"{path} no tiene dueño en tools/ownership.json. Pídele a D que lo asigne antes de crearlo."


if __name__ == "__main__":  # python tools/ownership.py  -> prints the current role (or None)
    print(current_role())
