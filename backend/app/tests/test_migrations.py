"""Migration-chain validation without requiring a live PostgreSQL instance."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_alembic_offline_upgrade_and_downgrade_cover_full_chain() -> None:
    """Compile every migration in both directions so broken DDL is caught in CI."""
    backend_root = Path(__file__).resolve().parents[2]
    for command in (
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        [sys.executable, "-m", "alembic", "downgrade", "head:base", "--sql"],
    ):
        result = subprocess.run(
            command, cwd=backend_root, capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stderr
