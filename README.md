# QuickHerbalist

A quick 2D items-collecting game built with Kivy.

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
