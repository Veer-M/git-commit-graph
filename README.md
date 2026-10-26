# Git commit graph

This plots the real commit ancestry of a Git repository. Branches get separate lanes, merges connect to both parents, and the graph can be saved as an image without opening a window.

## Run it

Use Python 3.11 or newer. Run these commands from this repository's folder.

```sh
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
```

```sh
python commit_graph.py .
python commit_graph.py ../some-repository --all --output history.png --no-show
```

## How it works and current limits

Requires Git on PATH. Reads real commits and does not create synthetic activity. --all includes every local ref; the default follows HEAD. The lane placement is a small deterministic heuristic, not Git branch-name reconstruction. Parents outside the chosen history limit are omitted from the picture. Disconnected tips can reuse a lane. This is a static plot, not an interactive history browser.

## Tests

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests create a temporary Git history, check a merge layout, and render a PNG with a noninteractive plotting backend.
