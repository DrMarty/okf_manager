---
name: okf-project-manager
description: Use for Open Knowledge Format catalog work in an Agent Zero project or the global user OKF bundle, delegated to the okf_mgr agent profile, including ingesting source evidence, maintaining OKF concept Markdown, validating bundles, regenerating indexes, updating logs, and refreshing graph visualizations.
triggers:
  - "manage the OKF catalog"
  - "ingest into OKF"
  - "update the knowledge graph"
  - "validate the OKF bundle"
  - "wrap okf_mgr workflow"
---

### Tool execution safety

When a project uses the bundled `okf_mgr` profile, profile-local OKF tools must be invoked from the active `okf_mgr` context. Do **not** fan out `okf_write_concept_doc` or other OKF profile-local tools through generic `parallel` jobs; use sequential tool calls or deterministic scripts for bulk writes, then validate the bundle.

For repository or source-folder ingests, only non-internal files are meaningful catalog evidence. Exclude `.git/**`, hidden files, caches, virtualenvs, dependency folders, logs, and generated artifacts unless the user explicitly identifies one as source evidence. Preserve ingested evidence under the target OKF root at `raw/<meaningful-name>/` for future auditing or re-parsing.

`<catalog-directory>/../raw/<meaningful-name>/` is retained evidence space, not OKF concept space. Validation, index generation, visualization, and concept counts must ignore raw Markdown files there.


# OKF Project Manager

Use this skill when the user asks to ingest, update, validate, index, visualize, or otherwise manage an OKF catalog.

## Scope

- Project context: when an active Agent Zero project root is available, use it as the workspace owner.
- Global context: when no active project root is available, use the global user OKF workspace under `/a0/usr/okf/`.
- Source evidence: use source files declared by the user, project instructions, `AGENTS.md`, `.a0proj/instructions/`, or files under evidence folders such as `raw/`, `source/`, `sources/`, `inputs/`, or `docs/`.
- Project-derived OKF catalog: store inside the active project, preferably under `<project-root>/okf/<catalog-slug>/`.
- Global OKF catalog: store outside projects under `/a0/usr/okf/<catalog-slug>/`.
- Default project catalog path when no project instruction names one: `<project-root>/okf/catalog/`.
- Default global catalog path when no project is active and no path is named: `/a0/usr/okf/catalog/`.
- Required agent profile for OKF work: `okf_mgr`.

## Creation Confirmation Rule

Always ask the user for explicit confirmation before creating a new OKF bundle directory.

Before creating any new bundle, report:

- whether the bundle is project-local or global,
- the exact target catalog directory,
- the source/evidence locations that will be used, if known,
- the first intended operation.

Do not create the bundle until the user confirms. Existing bundle maintenance does not require this creation confirmation, but still ask when the target catalog is ambiguous.

## Workflow

1. Resolve the workspace owner:
   - If an active project root exists, use that project root and read project-local instructions before changing derived files:
     - `AGENTS.md` files on the path to the target catalog.
     - `.a0proj/project.json` when present.
     - `.a0proj/instructions/*.md` when present.
     - Any user-named source evidence files or project-local evidence manifests.
   - If no active project root exists, use the global OKF workspace `/a0/usr/okf/` and user-named source evidence.
2. Determine the OKF catalog directory:
   - Prefer an explicit path from the user or project instructions.
   - Otherwise, in a project, use an existing project-local `okf/*/` bundle if exactly one exists.
   - Otherwise, outside a project, use an existing global `/a0/usr/okf/*/` bundle if exactly one exists.
   - Otherwise propose the default project catalog path `<project-root>/okf/catalog/` or the default global catalog path `/a0/usr/okf/catalog/`.
3. If the resolved catalog directory does not already contain an OKF bundle, stop and ask for confirmation before creating it.
4. Determine source evidence policy:
   - Treat user- or project-marked source folders as immutable.
   - Do not edit raw/source evidence unless the user explicitly asks.
   - Preserve citations to source files, source URLs, manifests, checksums, or notes where available.
   - Copy or record ingested non-internal evidence under `<catalog-directory>/../raw/<meaningful-name>/` before final reporting.
5. Delegate OKF catalog decisions and bundle-management work to `call_subordinate` with `profile: "okf_mgr"` whenever the task is nontrivial.
6. In the subordinate prompt, require work inside the resolved workspace owner, require the resolved catalog directory, and require preservation of source provenance.
7. Maintain derived concept Markdown in the resolved catalog directory:
   - Each concept must include YAML frontmatter with `type`, `title`, `description`, and `timestamp`.
   - Prefer `resource` values pointing to a source file or source URL when known.
   - Preserve provenance in `# Citations` sections.
   - Use relative internal links for OKF relationships.
   - Use `index.md` only for directory indexes and `log.md` only for chronological update history.
   - Do not paste generated Markdown or prose directly into `code_execution_tool` shell commands; write concept files with OKF tools, `text_editor`, or carefully quoted here-docs/scripts so headings, backticks, paths, and links are not executed by the shell.
8. After changes, ensure the bundle is validated, indexes are regenerated, `log.md` is updated, and `viz.html` is refreshed when graph-visible content changes. Verify the graph by parsing the embedded `bundle-data` payload and reporting concept, edge, and type counts.
9. Report changed paths and verification results to the user.

## Delegation Prompt Pattern

Use this structure for the subordinate:

```text
You are the okf_mgr specialist for OKF catalog management.
Workspace owner: <active project root or /a0/usr/okf global workspace>.
Workspace mode: <project-local or global>.
OKF catalog directory: <resolved catalog path>.
Task: <specific user request>.
Follow applicable project instructions and AGENTS.md when a project is active. If no project is active, keep derived OKF files in the global OKF workspace. Treat designated source evidence as immutable; maintain derived OKF files only in the resolved catalog directory; preserve citations and source provenance; validate the bundle; regenerate indexes; update log.md; refresh viz.html if graph-visible content changes.
Return: changed paths, validation/index/visualization results, and any unresolved questions.
```

## Failure Handling

- If no active project root is available, use the global OKF workspace `/a0/usr/okf/` rather than asking for a project directory.
- If creating a new OKF bundle would be required, ask the user for explicit confirmation before creating directories or files.
- If source provenance is missing or ambiguous, ask for clarification or create an explicit `Source Note` concept instead of inventing provenance.
- If multiple existing project-local or global `okf/*/` catalogs are present and no target is specified, ask which catalog to use.
- If validation fails, fix deterministic issues before reporting; only stop when blocked by missing source evidence or user choices.
- If graph display is requested, open the resolved `<catalog-directory>/viz.html` with the Browser tool after regeneration.
- If a generated code/script workflow is used, write the code to a file, syntax-check it before execution, then verify exact output paths and counts.

Catalog linting after modifications must be code-driven with minimal LLM judgment: validate concept frontmatter, check all relative Markdown links, allow sibling `../raw/<meaningful-name>/...` evidence links, flag broken links, and repair deterministic path mistakes when possible before final reporting.

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

