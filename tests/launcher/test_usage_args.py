"""Tests for launcher usage output, exit codes and argument handling.

Purpose: check help/error behaviour and how arguments and PARANOIA_URL
  reach the client.
Scope:   no-args, help, unknown subcommand, pass-through, --url handling,
  cwd and symlink independence.
Limitations: uses the stub clients; real client behaviour is not tested.
"""
import pytest

from conftest import argv_of


def test_no_args_prints_usage_and_fails(sandbox):
    """No arguments: usage on stdout, exit status 1."""
    proc = sandbox.run()
    assert proc.returncode == 1
    assert "Usage: ./paranoia" in proc.stdout


@pytest.mark.parametrize("flag", ["help", "-h", "--help"])
def test_help_succeeds(sandbox, flag):
    """help and its aliases print usage and exit 0."""
    proc = sandbox.run(flag)
    assert proc.returncode == 0
    assert "Usage: ./paranoia" in proc.stdout


def test_unknown_command_fails_on_stderr(sandbox):
    """Unknown subcommand: named error plus usage on stderr, exit 1."""
    proc = sandbox.run("bogus")
    assert proc.returncode == 1
    assert "unknown command: bogus" in proc.stderr
    assert "Usage: ./paranoia" in proc.stderr
    assert proc.stdout == ""


def test_args_pass_through(warm):
    """Arguments after the subcommand reach the client unchanged."""
    proc = warm.run("tui", "--room", "lobby", "extra one")
    assert proc.returncode == 0
    assert argv_of(proc) == ["--room", "lobby", "extra one"]


def test_url_env_becomes_flag(warm):
    """PARANOIA_URL is passed as --url before other arguments."""
    proc = warm.run("tui", "--room", "r", PARANOIA_URL="ws://example.test/ws")
    assert argv_of(proc) == ["--url", "ws://example.test/ws", "--room", "r"]


def test_no_url_env_adds_nothing(warm):
    """Without PARANOIA_URL no --url is injected."""
    assert argv_of(warm.run("tui")) == []


def test_explicit_url_wins(warm):
    """An explicit --url comes last so it overrides PARANOIA_URL."""
    proc = warm.run("tui", "--url", "ws://explicit.test/ws",
                    PARANOIA_URL="ws://env.test/ws")
    assert argv_of(proc)[-2:] == ["--url", "ws://explicit.test/ws"]


def test_works_from_other_cwd(warm, tmp_path):
    """The repo root is found regardless of the caller's cwd."""
    proc = warm.run("tui", cwd=tmp_path)
    assert proc.returncode == 0
    assert argv_of(proc) == []


def test_works_via_symlink(warm, tmp_path):
    """Invoking through a symlink resolves the real repo root."""
    link = tmp_path / "elsewhere" / "pn"
    link.parent.mkdir()
    link.symlink_to(warm.script)
    proc = warm.run("tui", "--room", "x", cwd=link.parent, script=link)
    assert proc.returncode == 0
    assert argv_of(proc) == ["--room", "x"]
