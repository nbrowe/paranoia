"""Tests for the desktop client's display pre-check.

Purpose: check that the check only looks for a non-empty DISPLAY on Linux
  and never depends on its value.
Scope:   the pre-check in check_desktop; no real display or Tk is used
  (the fake interpreter claims tkinter imports).
Limitations: other OSes are simulated by a stub `uname` on PATH.
"""
import os
import sys

import pytest

from conftest import argv_of

pytestmark = pytest.mark.skipif(
    sys.platform != "linux", reason="display pre-check is Linux-specific"
)


def desktop(warm, **env):
    """Run `desktop` in the warm sandbox with the fake interpreter."""
    return warm.run("desktop", PARANOIA_PYTHON=str(warm.fake_py), **env)


def test_no_display_fails_early(warm):
    """With DISPLAY removed the launcher fails with guidance."""
    proc = desktop(warm, DISPLAY=None)
    assert proc.returncode == 1
    assert "no display available" in proc.stderr
    assert "X forwarding" in proc.stderr


def test_empty_display_fails_early(warm):
    """An empty DISPLAY counts as no display."""
    assert desktop(warm, DISPLAY="").returncode == 1


def test_error_message_names_no_value(warm):
    """The message must not hint at a particular DISPLAY value."""
    proc = desktop(warm, DISPLAY=None)
    assert ":0" not in proc.stderr and "localhost:" not in proc.stderr


@pytest.mark.parametrize("value", ["placeholder", "host.invalid:99.3"])
def test_any_nonempty_display_passes(warm, value):
    """The check is not value-specific; any non-empty value proceeds."""
    proc = desktop(warm, DISPLAY=value)
    assert proc.returncode == 0
    assert argv_of(proc) == []


def test_wayland_display_alone_is_not_enough(warm):
    """Tk needs X11, so WAYLAND_DISPLAY without DISPLAY still fails."""
    proc = desktop(warm, DISPLAY=None, WAYLAND_DISPLAY="wayland-placeholder")
    assert proc.returncode == 1


def test_skipped_on_non_linux(warm, tmp_path):
    """Where uname is not Linux, a missing DISPLAY is not an error."""
    stub = tmp_path / "bin"
    stub.mkdir()
    uname = stub / "uname"
    uname.write_text("#!/bin/sh\necho Darwin\n")
    uname.chmod(0o755)
    path = f"{stub}{os.pathsep}{os.environ['PATH']}"
    proc = desktop(warm, DISPLAY=None, PATH=path)
    assert proc.returncode == 0
