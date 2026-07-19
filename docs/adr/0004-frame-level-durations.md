# Architecture Decision Record

## Title
Frame-Level Animation Durations

## Status
Accepted

## Context
We need to determine the granularity of animation timing within the custom YAML configuration. Some systems enforce a uniform frame rate per animation, while others allow variable durations per frame.

## Decision
We will support **Frame-Level Durations**. The custom YAML configuration will store a distinct duration value (defaulting to 250ms) for every individual frame in an animation sequence.

## Consequences
- **Positive:** Supports complex, irregular animations (e.g., long wind-ups, quick strikes).
- **Positive:** Aligns with the GUI requirement to "finetune duration of each frame".
- **Negative:** Slightly increases the verbosity of the YAML configuration and the complexity of the Kivy animation loop.