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

Follow the reference conventions: required `type`, `title`, `description`, timestamp auto-fill, optional `resource` and `tags`, body sections for prose, `# Schema`, `# Common query patterns`, and `# Citations` where applicable. Use relative Markdown links only to known concepts.
