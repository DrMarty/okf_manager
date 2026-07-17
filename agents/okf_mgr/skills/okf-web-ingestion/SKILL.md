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
