import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture
def scripts_dir():
    return SCRIPTS


@pytest.fixture
def run_script():
    def _run(name, *args, stdin=None, cwd=None):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / name), *map(str, args)],
            input=stdin,
            cwd=cwd,
            capture_output=True,
            text=True,
        )

    return _run
