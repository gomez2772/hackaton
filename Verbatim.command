#!/bin/bash
# Verbatim: double-click launcher for macOS. Logic lives in launcher/launch.py.
# Needs the executable bit (git update-index --chmod=+x Verbatim.command, or chmod +x).
cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1 \
    && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
    python3 launcher/launch.py "$@"
    status=$?
else
    echo
    echo 'Instala Python 3.11 o superior desde python.org (marca "Add Python to PATH")'
    echo
    status=1
fi

if [ "$status" -ne 0 ]; then
    echo
    echo "Verbatim se ha detenido con un error. Lee los mensajes de arriba."
    read -r -p "Pulsa Intro para cerrar..." _
fi
exit "$status"
