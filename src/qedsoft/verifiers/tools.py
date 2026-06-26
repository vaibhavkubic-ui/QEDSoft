from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class ExternalToolRunner:
    """Thin wrapper around optional EDA/formal tools."""

    def available(self, executable: str) -> bool:
        return shutil.which(executable) is not None

    def run(
        self,
        args: list[str],
        cwd: Path,
        timeout_seconds: int = 30,
    ) -> tuple[int, str]:
        try:
            completed = subprocess.run(
                args,
                cwd=str(cwd),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout_seconds,
                check=False,
            )
            return completed.returncode, completed.stdout
        except FileNotFoundError:
            return 127, f"Tool not found: {args[0]}"
        except subprocess.TimeoutExpired as exc:
            return 124, exc.stdout or f"Timed out after {timeout_seconds}s"
