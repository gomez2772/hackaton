"""Claude Code PreToolUse hook: blocks Edit/Write/NotebookEdit outside the agent's role (owner: D).

Reads the hook JSON from stdin. Exit 0 = allow; exit 2 = block (stderr is shown to Claude).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ownership import current_role, rel, verdict  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        return 0
    path = rel(target)
    if path is None:  # outside the repo (scratch files, etc.)
        return 0

    role = current_role()
    if role is None:
        print("ACTA_ROL no está definido en .env. Pregunta al usuario su rol (A, B, C o D) y "
              "pídele que añada ACTA_ROL=<rol> a .env antes de editar.", file=sys.stderr)
        return 2

    allowed, reason = verdict(role, path)
    if not allowed:
        print(f"Bloqueado para el rol {role}: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
