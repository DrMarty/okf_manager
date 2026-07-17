---
name: okf-bundle-management
description: Manage, validate, index, and visualize Open Knowledge Format bundles.
version: 0.1.0
tags: [okf, validation, index, visualization]
triggers: [validate OKF bundle, regenerate OKF indexes, visualize OKF bundle, manage knowledge catalog]
---

### Profile-local tool execution

Run `okf_context`, `okf_validate_bundle`, `okf_regenerate_indexes`, and `okf_visualize_bundle` directly from the active `okf_mgr` context. Do **not** place these profile-local OKF tools inside generic `parallel` jobs, because those workers may not inherit the `okf_mgr` profile-local tool registry or scoped OKF context.

# OKF Bundle Management

Use this skill for bundle-level maintenance.

Core operations:
- Set bundle context with `okf_context`.
- Validate frontmatter, reserved filenames, tags, timestamps, and links with `okf_validate_bundle`.
- Regenerate progressive-disclosure `index.md` files with `okf_regenerate_indexes`.
- Generate a lightweight graph artifact with `okf_visualize_bundle` when useful.
- Keep `log.md` concise and chronological when the bundle uses one.

Prefer deterministic, git-friendly output and report exact changed paths and validation results.

Graph verification must parse the generated `viz.html` `bundle-data` payload and report concept, edge, and type counts. For batch operations, prefer a JSON concept plan plus deterministic sequential writing over large inline shell/Markdown generation.
