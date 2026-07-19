---
name: okf-web-ingestion
description: Run the OKF web-ingestion workflow modeled on GoogleCloudPlatform/knowledge-catalog's web_ingestion_instruction.md.
version: 0.1.0
tags: [okf, web-ingestion, citations, enrichment]
triggers: [okf web ingest, crawl documentation for OKF, augment concept docs, mint reference concept]
---
# OKF Web Ingestion Workflow

Use this skill when augmenting an existing OKF bundle from web documentation.

Workflow:
1. Use `okf_list_concepts` once at the start.
2. Use `okf_fetch_url` on seed URLs and selected authoritative outbound links; respect max pages, allowed hosts, path filters, denied paths, and max depth.
3. For each fetched page, either augment existing concept docs, mint a reusable `references/<slug>` concept, or skip.
4. Before augmenting, use `okf_read_existing_doc`; preserve complete frontmatter and every existing top-level heading.
5. Use `okf_write_concept_doc` with `web_pass: true` for guarded augmentation.
   - Call it directly from the active `okf_mgr` context; do not dispatch it through generic `parallel` jobs.
6. Preserve fetched source evidence or URL manifests under `<okf-root>/raw/<meaningful-name>/` for auditing and future re-parsing, respecting crawl guards and excluding generated/transient files.
6. Cite only URLs actually fetched or already present.

Create metric references under `references/metrics/`, join references under `references/joins/`, and use relative links from primary docs.

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

