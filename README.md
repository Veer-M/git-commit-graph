# Git commit graph

Plot a repository's real commit ancestry, including branches and merges. The chart shows short hashes, commit subjects, and branch or tag labels. A JSON export includes the metadata and graph layout for further analysis.

![Example Git history with a feature merge and parallel branch](examples/history.png)

## Run it

Use Python 3.11 or newer and Git on PATH. From this folder:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python commit_graph.py . --output history.png --json history.json --no-show
```

To try a more interesting graph without changing any existing repository:

```sh
python demo.py --output demo-output
```

The demo builds a disposable repository with two feature branches, a merge, and a tag. It saves PNG, SVG, and JSON files, then removes that temporary repository. The pictured history is explicitly sample data, not a claim about this project's development history.

## Choose a history

```sh
python commit_graph.py ../another-repository --all --limit 80 --output graph.svg --no-show
python commit_graph.py ../another-repository --ref main --output main.png --json main.json --no-show
python commit_graph.py ../another-repository --ref v1.0 --limit 40
python commit_graph.py . --no-subjects --output compact.pdf --no-show
```

The default follows HEAD. `--all` includes locally available refs, and `--ref` follows one branch, tag, or commit. They cannot be combined. The program reads local history only; it does not fetch, check out branches, or write commits. Limits range from 1 to 2,000. Large graphs can be very tall, so a smaller limit or SVG output is usually more readable.

`--no-show` uses a noninteractive plotting backend for servers and scripts. Without it, the chart opens in a Matplotlib window. Output can be PNG, SVG, or PDF. `--no-subjects` hides subjects on the chart, but the JSON still contains them.

## What the graph means

Commit rows follow a topological order: every displayed child appears before its displayed parents. Git supplies the initial order, and a stable Kahn topological sort verifies it. The layout also works when a Python caller supplies the commit dictionary in a different order. Cycles are rejected.

Each active ancestry path reserves a lane. The first parent normally continues the current lane; extra parents reserve another free lane. Colors identify drawing lanes rather than permanent branch names. A commit can belong to several branches, and deleted branch names cannot be recovered from parent hashes alone.

Solid lines connect parents inside the displayed history. Dashed arrows indicate parents outside the current view, such as when `--limit` cuts off the graph. Branch and tag labels come from Git decorations. Long labels and subjects are shortened on the chart; JSON retains the full values.

## JSON and statistics

The CLI prints counts for commits, merges, roots, tips, branch points, visible edges, and parent edges outside the view. These describe the selected subgraph, not necessarily the entire repository. Shallow clones only expose ancestry that Git has available locally.

The JSON has a `statistics` object and a `commits` list. Each commit includes its full SHA, parents, author, author date, subject, refs, lane, row, and parents outside the view. Commit text may contain personal information from the repository; review an export before sharing it.

`history.py` handles Git access, metadata, sorting, and statistics. `commit_graph.py` handles lane placement and rendering. `demo.py` generates the disposable example.

## Tests

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests build real temporary repositories and check merge ancestry, branch/tag labels, ref selection, truncated history, metadata, unordered input, cycle rejection, disconnected tips, and image export. GitHub Actions runs the same suite.
