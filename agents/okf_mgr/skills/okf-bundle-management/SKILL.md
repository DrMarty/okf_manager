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

## Runtime and dependency discipline

Use deterministic OKF scripts and JSON concept plans before generating large ad hoc code in chat. Do not use bare `python` for OKF workflows. Prefer `scripts/okf_run.py`, which bootstraps and reuses the plugin-local worker environment, or explicitly use `/opt/venv-a0/bin/python` for framework/plugin checks.

When generated code is unavoidable, write it to disk, run syntax checks, preflight imports, and only then execute it. If dependencies such as PyYAML are needed for reliability, install or verify them through `scripts/okf_bootstrap_env.py` / `requirements-worker.txt` instead of rewriting fragile fallback code repeatedly.

After document modifications, run code-driven catalog lint, repair/validate relative links to sibling `okf/raw/<meaningful-name>/` evidence, regenerate indexes, refresh visualization, and verify the embedded `bundle-data` graph payload before reporting success.

## Local OKF worker hardening

- Prefer `scripts/okf_run.py` subcommands with explicit named options where available, e.g. `lint --catalog <okf>/catalog`, `verify-graph --catalog <okf>/catalog`, and `pipeline --catalog <okf>/catalog`.
- For unstructured file collections, first run a code-generated source inventory/plan scaffold with `scripts/okf_run.py plan-sources --source-root <path> --out <inventory.json>`. This inventory must make no assumptions about file meaning, concept boundaries, or relationships; use it only as evidence for a separate JSON concept plan.
- Do not execute or import scripts from retained evidence under `<okf>/raw/**`. Raw evidence is audit/reparse input only. Run OKF scripts from the installed plugin path through `scripts/okf_run.py`.
- After copying or retaining raw evidence, clean generated/internal artifacts with `scripts/okf_run.py clean-raw --catalog <okf>/catalog` or the full `pipeline` command. Raw evidence must not retain `.git/**`, `__pycache__/**`, `.pyc`, virtualenvs, dependency folders, logs, or generated caches.
- Final graph verification should report explicit graph mode from the embedded `bundle-data` payload; the expected D3 graph mode is `live-d3-self-graph`.

