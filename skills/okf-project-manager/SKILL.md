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
5. Delegate OKF catalog decisions and bundle-management work to `call_subordinate` with `profile: "okf_mgr"` whenever the task is nontrivial.
6. In the subordinate prompt, require work inside the resolved workspace owner, require the resolved catalog directory, and require preservation of source provenance.
7. Maintain derived concept Markdown in the resolved catalog directory:
   - Each concept must include YAML frontmatter with `type`, `title`, `description`, and `timestamp`.
   - Prefer `resource` values pointing to a source file or source URL when known.
   - Preserve provenance in `# Citations` sections.
   - Use relative internal links for OKF relationships.
   - Use `index.md` only for directory indexes and `log.md` only for chronological update history.
   - Do not paste generated Markdown or prose directly into `code_execution_tool` shell commands; write concept files with OKF tools, `text_editor`, or carefully quoted here-docs/scripts so headings, backticks, paths, and links are not executed by the shell.
8. After changes, ensure the bundle is validated, indexes are regenerated, `log.md` is updated, and `viz.html` is refreshed when graph-visible content changes.
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
