# QuickHerbalist

A quick 2D items-collecting game built with Kivy 3.

## Graphics backend

Kivy 3.0.0 is not on PyPI, so `pyproject.toml` pins an upstream `kivy/kivy`
git commit. On Linux the desktop window runs on Kivy 3's SDL3 backend (the
`sdl3` window provider; the built wheel reports `USE_SDL3 = 1`). Before the
first `uv sync` (which compiles kivy from git), install SDL3 plus the
SDL3_image, SDL3_ttf and SDL3_mixer libraries and their headers, e.g. on
Fedora:

```bash
sudo dnf install gcc gcc-c++ pkgconf-pkg-config mesa-libGL-devel \
    SDL3-devel SDL3_image-devel SDL3_ttf-devel SDL3_mixer-devel
```

The runtime needs the same without `-devel` (e.g. `SDL3_ttf SDL3_image
SDL3_mixer`); a missing one surfaces as `ImportError: libSDL3_*.so.0: cannot
open shared object file` and "Unable to get a Text/Image provider". OpenGL is
a runtime dependency loaded by SDL3 and provided by the desktop GL driver.
Profile saves use Kivy's per-app user data directory (`~/.local/share/quickherbalist`
on Linux); the save format itself is unchanged from the Kivy 2.x builds.

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

## Development

Run tests:
```bash
make test
```

Run linters and formatting checks:
```bash
make check-all
```

Automated spec-kit task runner (implements unchecked tasks in a spec's `tasks.md` in sequence):
```bash
scripts/run_yolo_tasks.sh specs/<spec-dir>
```
