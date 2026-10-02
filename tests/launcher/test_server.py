"""Tests for the launcher's `server` subcommand.

Purpose: check the error path when no compose tool is installed.
Scope:   only the missing-tool failure; no containers are ever started.
Limitations: success paths (real podman-compose/docker) are not tested.
"""
import shutil
import subprocess


def test_server_needs_compose_tool(sandbox, tmp_path):
    """With neither podman-compose nor docker on PATH, it explains."""
    tools = tmp_path / "tools"
    tools.mkdir()
    # Only what the script itself needs before reaching the check.
    for name in ("dirname", "readlink"):
        (tools / name).symlink_to(shutil.which(name))
    proc = subprocess.run(
        [shutil.which("bash"), str(sandbox.script), "server"],
        env={"PATH": str(tools)}, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 1
    assert "need podman-compose or docker" in proc.stderr
