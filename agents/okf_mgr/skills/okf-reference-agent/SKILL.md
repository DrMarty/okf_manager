---
name: okf-reference-agent
description: Run the OKF source-enrichment workflow modeled on GoogleCloudPlatform/knowledge-catalog's reference_instruction.md.
version: 0.1.0
tags: [okf, enrichment, bigquery, catalog]
triggers: [okf enrich concept, OKF BigQuery pass, write concept doc, list concepts]
---
# OKF Reference Agent Workflow

Use this skill when enriching exactly one concept from source metadata into an OKF bundle.

Workflow:
1. Use `okf_read_existing_doc` for the `concept_id`; refine rather than overwrite when present.
2. Use `okf_read_concept_raw` to inspect structured metadata.
3. Optionally use `okf_sample_rows` when sparse metadata needs examples.
4. Use `okf_list_concepts` to discover cross-link targets.
5. Compose one OKF document and call `okf_write_concept_doc` exactly once for that concept.
   - Call it directly from the active `okf_mgr` context; do not dispatch it through generic `parallel` jobs.

Follow the reference conventions: required `type`, `title`, `description`, timestamp auto-fill, optional `resource` and `tags`, body sections for prose, `# Schema`, `# Common query patterns`, and `# Citations` where applicable. Use relative Markdown links only to known concepts.

For multi-concept or repository-style source passes, create a compact JSON concept plan and use deterministic sequential writing rather than dumping long source files into chat. Preserve non-internal raw evidence under `<okf-root>/raw/<meaningful-name>/` and exclude `.git/**`, hidden files, caches, dependency folders, virtualenvs, and generated artifacts from source inventories.

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

