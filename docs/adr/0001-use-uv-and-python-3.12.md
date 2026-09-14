# ADR 0001: Use uv and Python 3.12

## Status
Accepted

## Context
We are building NEXUS AI, a complex supply chain control tower with multiple subsystems (API, data pipelines, ML). We need a fast, reproducible way to manage Python environments and dependencies across different machines and eventually in Docker containers. 

## Decision
We will use `uv` as our exclusive Python package and environment manager, and we will target Python 3.12.

## Consequences
- **Pros:** `uv` is written in Rust and is significantly faster than `pip`. It unifies environment creation, dependency resolution, and locking into a single tool. Python 3.12 gives us access to the latest performance improvements and type hinting features. The `uv.lock` file guarantees 100% reproducible builds.
- **Cons:** The team must learn a new tool (`uv`) instead of using standard `pip`/`venv`. 