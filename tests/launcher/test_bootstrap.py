"""Tests for the launcher's venv bootstrap and requirements stamp.

Purpose: check first-run setup, no-op reruns and reinstall triggers.
Scope:   the tui client only (the logic is shared with desktop).
Limitations: requirements files are empty or comment-only, so pip does no
  real installs; each test builds a real venv and takes a few seconds.
"""
import os

from conftest import argv_of

SETUP = "paranoia: setting up tui"


def test_first_run_creates_venv_and_announces_once(sandbox):
    """First run builds the venv and prints the setup line once."""
    first = sandbox.run("tui")
    assert first.returncode == 0
    assert (sandbox.venv("tui") / "bin" / "python").exists()
    assert first.stderr.count(SETUP) == 1
    assert argv_of(first) == []
    second = sandbox.run("tui")
    assert SETUP not in second.stderr


def test_unchanged_requirements_do_not_reinstall(sandbox):
    """A second run leaves the stamp alone and prints no setup line."""
    sandbox.run("tui")
    stamp = sandbox.venv("tui") / ".requirements.stamp"
    before = stamp.stat().st_mtime_ns
    proc = sandbox.run("tui")
    assert SETUP not in proc.stderr
    assert stamp.stat().st_mtime_ns == before


def test_changed_requirements_trigger_reinstall(sandbox):
    """New requirements content re-runs setup and updates the stamp."""
    sandbox.run("tui")
    stamp = sandbox.venv("tui") / ".requirements.stamp"
    old = stamp.read_text()
    sandbox.requirements("tui").write_text("# changed\n")
    proc = sandbox.run("tui")
    assert proc.returncode == 0
    assert SETUP in proc.stderr
    assert stamp.read_text() != old


def test_touching_requirements_does_not_reinstall(sandbox):
    """Only content matters: a newer mtime alone is not a change."""
    sandbox.run("tui")
    os.utime(sandbox.requirements("tui"), (1, 2_000_000_000))
    proc = sandbox.run("tui")
    assert SETUP not in proc.stderr
