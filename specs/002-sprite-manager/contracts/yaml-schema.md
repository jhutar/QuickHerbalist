# Contract: sprites.yaml

**Format**: YAML

This file acts as the skinny relational configuration for sprite animation sequences. It is consumed by both the game runtime (`SpriteManager`) and the standalone GUI editor.

## Schema

```yaml
sprites:
  <sprite_name>:
    frames:
      - atlas_id: <string>
        duration_ms: <integer> # Optional, defaults to 250
      # ... more frames ...
```

## Example

```yaml
sprites:
  hero_run:
    frames:
      - atlas_id: "hero_run_0"
        duration_ms: 250
      - atlas_id: "hero_run_1"
        duration_ms: 250
  flower_idle:
    frames:
      - atlas_id: "flower_static_0"
        # duration_ms can be omitted for a single-frame static sprite
```