# Launcher tests

pytest suite for the `./paranoia` launcher. It copies the script into a
temporary tree with stub clients, so it is offline and never touches the
real client venvs. Needs bash and Python 3.9+ with `venv`.

From the repo root:

```sh
python3 -m venv tests/launcher/.venv
tests/launcher/.venv/bin/pip install -r tests/launcher/requirements.txt
tests/launcher/.venv/bin/pytest tests/launcher
```

Takes about 15 seconds. No display, Tk, container runtime or network is
needed.
