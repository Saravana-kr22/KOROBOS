"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_alembic(
    command: str,
    message: Optional[str] = None,
    alembic_dir: Optional[Path] = None,
) -> None:
    """
    Helper to run Alembic CLI commands programmatically.

    Args:
        command: Alembic sub-command, e.g. "upgrade", "revision", "downgrade".
        message: Optional revision message (used with "revision --autogenerate").
        alembic_dir: Working directory containing alembic.ini.
    """
    cmd = ["alembic", command]

    if command == "revision":
        cmd.append("--autogenerate")
        if message:
            cmd.extend(["-m", message])

    if command in ("upgrade", "downgrade") and message:
        cmd.append(message)
    elif command == "upgrade":
        cmd.append("head")

    cwd = str(alembic_dir) if alembic_dir else None
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Alembic {command} failed:\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"Alembic {command} failed")

    print(result.stdout)
