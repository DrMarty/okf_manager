---
name: okf-project-manager
description: Use for Open Knowledge Format catalog work in the currently active Agent Zero project, delegated to the okf_mgr agent profile, including ingesting source evidence, maintaining OKF concept Markdown, validating bundles, regenerating indexes, updating logs, and refreshing graph visualizations.
triggers:
  - "manage the OKF catalog"
  - "ingest into OKF"
  - "update the knowledge graph"
  - "validate the OKF bundle"
  - "wrap okf_mgr workflow"
---

# OKF Project Manager

Use this skill when the user asks to ingest, update, validate, index, visualize, or otherwise manage an OKF catalog for the currently active Agent Zero project.

## Scope

- Project root: use the currently active project root from Agent Zero project context.
- Source evidence: use project-local source files declared by the user, project instructions, `AGENTS.md`, `.a0proj/instructions/`, or files under project-local evidence folders such as `raw/`, `source/`, `sources/`, `inputs/`, or `docs/`.
- Derived OKF catalog: store inside the active project, preferably under `<project-root>/okf/<catalog-slug>/`.
- Default catalog path when no project instruction names one: `<project-root>/okf/catalog/`.
- Required agent profile for OKF work: `okf_mgr`.

## Workflow

1. Resolve the active project root and read project-local instructions before changing derived files:
   - `AGENTS.md` files on the path to the target catalog.
   - `.a0proj/project.json` when present.
   - `.a0proj/instructions/*.md` when present.
   - Any user-named source evidence files or project-local evidence manifests.
2. Determine the OKF catalog directory:
   - Prefer an explicit path from the user or project instructions.
   - Otherwise use an existing project-local `okf/*/` bundle if exactly one exists.
   - Otherwise create/use `<project-root>/okf/catalog/`.
3. Determine source evidence policy:
   - Treat user- or project-marked source folders as immutable.
   - Do not edit raw/source evidence unless the user explicitly asks.
   - Preserve citations to source files, source URLs, manifests, checksums, or notes where available.
4. Delegate OKF catalog decisions and bundle-management work to `call_subordinate` with `profile: "okf_mgr"` whenever the task is nontrivial.
5. In the subordinate prompt, require work inside the active project root, require the resolved catalog directory, and require preservation of source provenance.
6. Maintain derived concept Markdown in the resolved catalog directory:
   - Each concept must include YAML frontmatter with `type`, `title`, `description`, and `timestamp`.
   - Prefer `resource` values pointing to a source file or source URL when known.
   - Preserve provenance in `# Citations` sections.
   - Use relative internal links for OKF relationships.
   - Use `index.md` only for directory indexes and `log.md` only for chronological update history.
7. After changes, ensure the bundle is validated, indexes are regenerated, `log.md` is updated, and `viz.html` is refreshed when graph-visible content changes.
8. Report changed paths and verification results to the user.

## Delegation Prompt Pattern

Use this structure for the subordinate:

```text
You are the okf_mgr specialist for the active Agent Zero project.
Project root: <resolved project root>.
OKF catalog directory: <resolved project-root-relative or absolute catalog path>.
Task: <specific user request>.
Follow project instructions and AGENTS.md. Treat project-designated source evidence as immutable; maintain derived OKF files only in the resolved catalog directory; preserve citations and source provenance; validate the bundle; regenerate indexes; update log.md; refresh viz.html if graph-visible content changes.
Return: changed paths, validation/index/visualization results, and any unresolved questions.
```

## Failure Handling

- If no active project root is available, ask the user which project directory should own the OKF catalog before writing files.
- If source provenance is missing or ambiguous, ask for clarification or create an explicit `Source Note` concept instead of inventing provenance.
- If multiple existing `okf/*/` catalogs are present and no target is specified, ask which catalog to use.
- If validation fails, fix deterministic issues before reporting; only stop when blocked by missing source evidence or user choices.
- If graph display is requested, open the resolved `<catalog-directory>/viz.html` with the Browser tool after regeneration.
