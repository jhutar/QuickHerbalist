# QuickHerbalist

A quick 2D items-collecting game built with Kivy 3.

## Play in your browser

[Play the web (WASM) build](https://jhutar.github.io/QuickHerbalist/).
First load takes some time — the browser downloads the Python runtime and
the whole game (~17 MB); later loads use the browser cache.

## Running

The project uses `uv` for dependency and package management.

Run the game:
```bash
uv run quick-herbalist
```

Run the standalone Sprite Manager GUI:
```bash
uv run manage-sprites
```

Profile saves use Kivy's per-app user data directory (`~/.local/share/quickherbalist`
on Linux); the save format itself is unchanged from the Kivy 2.x builds.

## Development

Run tests:
```bash
make test
```

Run linters and formatting checks:
```bash
make check-all
```

Kivy 3.0.0.dev0 is installed from the [Kivy nightly wheels](https://kivy.org/downloads/simple/)
(daily snapshot of Kivy master). To pick up a newer snapshot:
```bash
make deps-upgrade
```
(which also bumps pre-commit hooks and npm dev deps; run occasionally, e.g.
monthly). Other dependencies are kept current by Dependabot
(`.github/dependabot.yml`), which auto-merges its PRs once CI passes.
Once Kivy 3.0.0 reaches PyPI, switch the dependency in `pyproject.toml` to
`"kivy>=3.0.0"` and remove the `kivy-nightly` index and `tool.uv.sources` entries.

### Web build (browser)

Build the static web bundle locally (Kivy 3 WASM + pyodide). Needs `uv` and
network access, no docker. The same script runs in CI on `v*` tags and
publishes the result to GitHub Pages:

```bash
sh web/build.sh
python3 -m http.server 8080 -d web/dist
# open http://127.0.0.1:8080
```

Profile saves persist per browser (localStorage). Headless smoke tests:
`web/probe.mjs` (boot + input) and `web/probe_persist.mjs` (save survives
reload) — run with the static server from above.

The WASM pins in `web/build.sh` (pyodide version, Kivy WASM wheel commit)
are updated manually — there is no registry Dependabot can track. When
bumping one: change the pin, re-download the artifacts, recompute the
sha256 checksums at the bottom of the script, run `sh web/build.sh` and
the probe tests.
