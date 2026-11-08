"""Fails if the current branch touches files outside its role (owner: D).

Role comes from the branch prefix (a/, b/, c/, d/) or --role / ACTA_ROL.
Usage:  python tools/check_ownership.py [--base origin/main] [--role B] [--allow-frozen]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership import ROLES, current_role, verdict  # noqa: E402


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--role")
    ap.add_argument("--branch")
    ap.add_argument("--allow-frozen", action="store_true", help="PR con etiqueta 'contrato'")
    args = ap.parse_args()

    branch = args.branch or git("rev-parse", "--abbrev-ref", "HEAD")
    role = (args.role or (branch.split("/", 1)[0] if "/" in branch else "") or current_role() or "").upper()
    if role not in ROLES:
        print(f"No sé qué rol tiene la rama '{branch}'. Usa el prefijo a/, b/, c/ o d/.")
        return 1

    changed = [f for f in git("diff", "--name-only", f"{args.base}...HEAD").splitlines() if f]
    bad = []
    for f in changed:
        ok, reason = verdict(role, f)
        if not ok and not (args.allow_frozen and "CONGELADO" in reason):
            bad.append(reason)
    if bad:
        print(f"Rol {role}: {len(bad)} archivo(s) fuera de tu propiedad:")
        for r in bad:
            print(f"  - {r}")
        return 1
    print(f"Rol {role}: {len(changed)} archivo(s) cambiados, todos dentro de tu propiedad.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
