# okf_mgr Agent Profile DOX

## Purpose

- Own the `okf_mgr` user agent profile for Open Knowledge Format (OKF) catalog management.
- Keep profile behavior, profile-local tools, profile-local skills, and documentation aligned with the OKF specification and the GoogleCloudPlatform/knowledge-catalog reference implementation.

## Ownership

- `agent.yaml` owns the profile metadata shown in Agent Zero profile lists.
- `prompts/agent.system.main.specifics.md` owns the core okf_mgr role, workflow, and OKF operating guidance.
- `prompts/agent.system.tool.*.md` owns agent-facing contracts for profile-local OKF tools.
- `tools/` owns Agent Zero-compatible profile-local tools mirroring the reference agent capabilities.
- `skills/` owns profile-local skills that load reference-agent workflows for enrichment, web ingestion, validation, indexing, and visualization.

## Local Contracts

- Preserve the standard Agent Zero JSON tool-call contract; do not override core communication prompts unless explicitly requested.
- Keep OKF semantics spec-first and reference-aware: the draft spec requires `type`, while durable output should prefer the reference implementation's stricter `type`, `title`, `description`, and `timestamp` frontmatter.
- Tool implementations must remain portable and avoid hard-coded project-specific bundle paths.
- BigQuery tools may require `google-cloud-bigquery` credentials and should fail with clear messages when dependencies or credentials are unavailable.
- Web ingestion tools must preserve crawl guards for allowed hosts, path filters, max pages, and max depth.
- Ingest workflows must preserve non-internal source evidence under the target OKF root at `raw/<meaningful-name>/` for auditing and future re-parsing; exclude `.git/**`, hidden files, caches, virtualenvs, dependency folders, and generated artifacts.
- Runtime tools and scripts must treat sibling `okf/raw/<meaningful-name>/` as evidence space, not concept space; raw Markdown there must not be counted as concepts, indexed as concepts, or shown as graph nodes.
- Write tools must preserve unknown frontmatter keys and avoid reserved concept filenames `index.md` and `log.md`.
- Profile-local OKF tools must not be dispatched inside generic `parallel` jobs; run them sequentially in the active `okf_mgr` context, or use deterministic scripts for bulk writes followed by validation.
- When users ask to see, show, graph, visualize, or visually inspect a knowledge catalog, the profile must generate/refresh `viz.html` and open or activate it as a live `file://` page in the Agent Zero Browser when possible; because the Browser side panel cannot be reliably forced open or detected from code, the final response must tell the user to open the Browser tab/panel manually if they do not see the loaded live self-view. Do not substitute screenshots, static images, or screenshot-only previews for the live self-view.

## Work Guidance

- Before editing profile files, re-read this DOX file and `/a0/AGENTS.md`.
- When adding or changing a profile-local tool, update its matching `prompts/agent.system.tool.<tool_name>.md` fragment in the same change.
- When changing durable workflows, update the relevant profile-local `skills/*/SKILL.md` file.
- Prefer focused Agent Zero-compatible adapters over copying the reference implementation wholesale.
- Keep skills concise; move long examples to references only if this profile grows substantially.

## Verification

- Validate `agent.yaml` parses as YAML and contains only profile metadata keys.
- Import every `tools/*.py` file with the framework runtime and ensure it defines a `helpers.tool.Tool` subclass.
- Run smoke checks for non-credentialed tools on a temporary OKF bundle: context, write/read/list, validate, index, visualize, and guarded write behavior.
- Use a fresh `call_subordinate(profile="okf_mgr")` smoke test after behavior or tool prompt changes.

## Child DOX Index

No child DOX files.

- Keep concept catalogs clean: write concepts only under `okf/catalog/`; preserve raw ingested evidence under sibling `okf/raw/<meaningful-name>/`; lint catalog links to raw evidence in code after document modifications.
