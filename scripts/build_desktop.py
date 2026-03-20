from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    spec_path = project_root / "gravity_studio.spec"
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_path)]
    subprocess.run(command, cwd=project_root, check=True)


if __name__ == "__main__":
    main()
