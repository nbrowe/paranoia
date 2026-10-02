"""Tests for the launcher's python and tkinter prerequisite checks.

Purpose: check the error paths for a missing, too-old or tk-less python.
Scope:   interpreter checks only; the display check is in test_display.py.
Limitations: the interpreters are simulated with a wrapper script, so a
  real broken python is not exercised.
"""


def test_missing_python_fails(sandbox):
    """A nonexistent PARANOIA_PYTHON gives a clear error."""
    proc = sandbox.run("tui", PARANOIA_PYTHON="/nonexistent/python")
    assert proc.returncode == 1
    assert "not found" in proc.stderr
    assert "PARANOIA_PYTHON" in proc.stderr


def test_old_python_fails(sandbox):
    """A python reporting a version below 3.9 is rejected."""
    proc = sandbox.run("tui", PARANOIA_PYTHON=str(sandbox.fake_py),
                       FAKE_MODE="old")
    assert proc.returncode == 1
    assert "older than 3.9" in proc.stderr
    assert not sandbox.venv("tui").exists()


def test_missing_tkinter_fails_for_desktop(sandbox):
    """Desktop needs tkinter; the error says what to install."""
    proc = sandbox.run("desktop", PARANOIA_PYTHON=str(sandbox.fake_py),
                       FAKE_MODE="no-tk", DISPLAY="placeholder")
    assert proc.returncode == 1
    assert "tkinter is missing" in proc.stderr
    assert not sandbox.venv("desktop").exists()


def test_missing_tkinter_ignored_for_tui(sandbox):
    """The terminal client does not need tkinter."""
    proc = sandbox.run("tui", PARANOIA_PYTHON=str(sandbox.fake_py),
                       FAKE_MODE="no-tk")
    assert proc.returncode == 0
