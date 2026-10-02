"""Shared fixtures for the launcher tests.

Purpose: build a throwaway copy of the repo layout (the real `paranoia`
  script plus stub clients) and run the script against it with a scrubbed,
  offline environment.
Scope:   fixtures and helpers only; the tests live in test_*.py.
Limitations: needs bash and a python3 with venv/ensurepip on PATH. Never
  touches the real client directories or their virtualenvs.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REAL_SCRIPT = Path(__file__).resolve().parents[2] / "paranoia"
STUB_MAIN = (
    "import json, sys\n"
    "print('ARGV ' + json.dumps(sys.argv[1:]))\n"
)
# Fake interpreter: FAKE_MODE picks what to break ("old" or "no-tk").
FAKE_PY = """#!/usr/bin/env bash
case "$*" in
  *version_info*) [ "${FAKE_MODE:-}" = old ] && exit 1 ;;
  *"import tkinter"*) [ "${FAKE_MODE:-}" = no-tk ] && exit 1; exit 0 ;;
esac
exec "$REAL_PY" "$@"
"""


class Sandbox:
    """A temp repo tree holding a copy of the launcher and stub clients."""

    def __init__(self, root: Path):
        """Create the tree under `root` and copy the launcher into it."""
        self.root = root
        root.mkdir(parents=True)
        self.script = root / "paranoia"
        shutil.copy(REAL_SCRIPT, self.script)
        for name in ("tui", "desktop"):
            client = root / "client" / name
            pkg = client / f"paranoia_{name}"
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").write_text("")
            (pkg / "__main__.py").write_text(STUB_MAIN)
            (client / "requirements.txt").write_text("")
        self.fake_py = self.make_script("fake-python", FAKE_PY)

    def make_script(self, name: str, body: str) -> Path:
        """Write an executable helper script in the sandbox root."""
        path = self.root / name
        path.write_text(body)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def requirements(self, client: str) -> Path:
        """Return the path of a stub client's requirements.txt."""
        return self.root / "client" / client / "requirements.txt"

    def venv(self, client: str) -> Path:
        """Return the path where the launcher builds a client's venv."""
        return self.root / "client" / client / ".venv"

    def env(self, **extra) -> dict:
        """Build a scrubbed offline environment; None values are dropped."""
        env = {
            "PATH": os.environ["PATH"],
            "HOME": str(self.root),
            "PIP_NO_INDEX": "1",  # hermetic: pip must never reach a network
            "REAL_PY": sys.executable,
        }
        env.update(extra)
        return {k: v for k, v in env.items() if v is not None}

    def run(self, *args, cwd=None, script=None, **env):
        """Run the launcher and return the CompletedProcess (text mode)."""
        return subprocess.run(
            [str(script or self.script), *args],
            cwd=cwd or self.root,
            env=self.env(**env),
            capture_output=True,
            text=True,
            timeout=120,
        )


def argv_of(proc) -> list:
    """Extract the argv the stub client printed on stdout."""
    for line in proc.stdout.splitlines():
        if line.startswith("ARGV "):
            return json.loads(line[5:])
    raise AssertionError(f"no ARGV line; stdout={proc.stdout!r} "
                         f"stderr={proc.stderr!r}")


@pytest.fixture
def sandbox(tmp_path):
    """A fresh, un-bootstrapped sandbox for each test."""
    return Sandbox(tmp_path / "repo")


@pytest.fixture(scope="session")
def warm(tmp_path_factory):
    """A sandbox with both venvs already built; tests must not mutate it.

    Bootstrapped through the fake interpreter so the desktop client passes
    its tkinter check without a real Tk install.
    """
    box = Sandbox(tmp_path_factory.mktemp("warm") / "repo")
    for cmd in ("tui", "desktop"):
        proc = box.run(cmd, PARANOIA_PYTHON=str(box.fake_py),
                       DISPLAY="placeholder")
        assert proc.returncode == 0, proc.stderr
    return box
