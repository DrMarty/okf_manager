# OKF Manager Plugin DOX

## Purpose

- Own repository-wide maintenance rules for the `okf_manager` Agent Zero plugin.
- Keep plugin packaging, bundled skills, bundled `okf_mgr` profile, helper scripts, public documentation, and Plugin Index artifacts aligned.
- Provide DOX self-documentation for future edits without becoming a runtime prompt, skill, or OKF behavior specification.

## Ownership

- `plugin.yaml` owns runtime plugin metadata used by Agent Zero plugin discovery.
- `README.md` owns public installation, usage, disclosures, and community-facing documentation.
- `default_config.yaml` owns portable default settings for project-local and global OKF catalog behavior.
- `skills/okf-project-manager/SKILL.md` owns the user-facing orchestration workflow for invoking OKF management from Agent Zero.
- `agents/okf_mgr/` owns the bundled specialist OKF agent profile and has its own child DOX contract.
- `scripts/` owns standalone validation, index-generation, and visualization helper scripts.
- `docs/community/` owns Plugin Index submission artifacts such as `index.yaml` and `thumbnail.png`.
- `webui/` owns runtime WebUI assets exposed through Agent Zero's `/plugins/<name>/webui/...` static route, including the plugin-dialog thumbnail.

## DOX / Runtime Separation Contract

- `AGENTS.md` files in this repository are path-scoped editing contracts, not prompt fragments, skills, user-facing documentation, or executable runtime behavior.
- Do not move primary runtime instructions from prompts, skills, tools, scripts, or config into `AGENTS.md`.
- Do not duplicate long runtime workflows in `AGENTS.md`; reference the owning runtime file instead.
- If an `AGENTS.md` mentions runtime behavior, it must do so only as an ownership rule, invariant, side-effect note, or verification requirement.
- If an edit changes runtime behavior, update the runtime owner first, then update the nearest applicable `AGENTS.md` only when ownership, contracts, workflows, side effects, or verification changed.
- If a child `AGENTS.md` is created because a folder receives functionality changes, that child file documents maintainership of the subtree; it must not instruct `okf_mgr` or the main agent how to act at runtime.

## Runtime Ownership Map

- Main plugin orchestration skill behavior is owned by `skills/okf-project-manager/SKILL.md`.
- Specialist `okf_mgr` role and operating behavior are owned by `agents/okf_mgr/prompts/agent.system.main.specifics.md`.
- Profile-local tool contracts are owned by `agents/okf_mgr/prompts/agent.system.tool.*.md`.
- Profile-local reusable workflows are owned by `agents/okf_mgr/skills/*/SKILL.md`.
- Profile-local OKF tools are active-agent tools; runtime prompts/skills must warn not to dispatch them through generic `parallel` jobs unless the worker is explicitly a fresh `okf_mgr` subordinate.
- Deterministic OKF operations are owned by `agents/okf_mgr/tools/*.py` and `scripts/*.py`.
- Graph verification is owned by `scripts/okf_verify_graph.py`; bulk concept-plan writing is owned by `scripts/okf_bulk_write.py`.
- Public install/use, web-ingestion disclosure, and Plugin Index-facing explanation are owned by `README.md`.
- Runtime defaults are owned by `default_config.yaml`.
- Plugin Index metadata is owned by `docs/community/index.yaml`.
- Plugin Index thumbnail is owned by `docs/community/thumbnail.png`.
- Agent Zero plugins-dialog thumbnail is owned by `webui/thumbnail.png`; Agent Zero discovers it as `/plugins/okf_manager/webui/thumbnail.png`.

## Local Contracts

- Keep the plugin portable; do not hard-code project-specific OKF catalog paths.
- When an active Agent Zero project exists, project-derived OKF catalogs must stay inside that project.
- When no active project exists, OKF catalogs must use the global user workspace under `/a0/usr/okf/`.
- Always require explicit user confirmation before creating a new OKF bundle; the owning runtime rule lives in `skills/okf-project-manager/SKILL.md` and the default setting lives in `default_config.yaml`.
- Preserve the README web-ingestion/network disclosure whenever changing URL-fetch or crawl behavior.
- Do not store generated project OKF catalog data, raw ingested sources, chat transcripts, secrets, tokens, or local user data in the plugin repository.
- Ingested project source evidence belongs in a meaningfully named sibling folder under `<okf-root>/raw/`, not in the plugin repository; internal files such as `.git/**`, hidden files, caches, virtualenvs, and generated artifacts must be excluded from source inventories and raw evidence copies.
- Keep Plugin Index artifacts small and valid: `docs/community/index.yaml` must follow the Plugin Index schema, and `docs/community/thumbnail.png` must remain square and no larger than 20 KB.
- Keep generated `viz.html` graph views stable in Agent Zero's constrained Browser side tab: avoid hover/mousemove handlers, tooltips, or resize logic that can change document layout or trigger aspect-ratio oscillation.
- Keep the runtime plugin-dialog thumbnail at `webui/thumbnail.png`; it should be a valid square image and may mirror `docs/community/thumbnail.png` when the same artwork is appropriate.
- Keep the root plugin DOX focused on repository maintenance; put profile-specific contracts in `agents/okf_mgr/AGENTS.md`.

## Work Guidance

- Before editing, read this root `AGENTS.md` and every child `AGENTS.md` on the direct path to the target file.
- For behavior changes, update the owning runtime artifact first:
  - orchestration changes -> `skills/okf-project-manager/SKILL.md`
  - `okf_mgr` profile behavior changes -> `agents/okf_mgr/prompts/agent.system.main.specifics.md`
  - tool behavior changes -> matching `agents/okf_mgr/tools/*.py` and `agents/okf_mgr/prompts/agent.system.tool.*.md`
  - profile-local workflow changes -> `agents/okf_mgr/skills/*/SKILL.md`
  - profile-local OKF tool execution rules -> `agents/okf_mgr/prompts/agent.system.main.specifics.md` and matching `agent.system.tool.*.md` prompts
  - public usage or disclosure changes -> `README.md`
  - default behavior changes -> `default_config.yaml`
  - Plugin Index metadata changes -> `docs/community/index.yaml`
- After meaningful changes, update the closest owning `AGENTS.md` only for changed ownership, contracts, side effects, workflows, verification, or child DOX indexes.
- When adding a new durable folder boundary with distinct ownership or workflow, create a child `AGENTS.md` there and add it to the nearest parent Child DOX Index.
- Keep DOX concise, current, and operational. Document stable contracts, not diary entries or one-off implementation history.
- Remove stale or contradictory DOX immediately instead of explaining why it is stale.

## Child AGENTS.md Rules

Child `AGENTS.md` files must use this standard shape unless there is a strong reason not to:

1. `Purpose`
2. `Ownership`
3. `Local Contracts`
4. `Work Guidance`
5. `Verification`
6. `Child DOX Index`

Child DOX files must follow these boundaries:

- They may say which runtime file owns a behavior.
- They may state invariants that must remain true after edits.
- They may list verification required after edits.
- They must not become prompt fragments or skill bodies.
- They must not duplicate complete runtime workflows from prompts or skills.

Good DOX wording:

```markdown
- `SKILL.md` owns the runtime workflow for resolving project-local versus global OKF bundle paths.
- When changing bundle creation behavior, update `SKILL.md`, `default_config.yaml`, and README together.
- Verify that the skill still requires user confirmation before creating a new OKF bundle.
```

Avoid runtime-instruction wording in DOX:

```markdown
- When the user asks to create a bundle, ask for confirmation and then create `/a0/usr/okf/catalog/`.
```

Put that kind of runtime instruction in the owning skill or prompt instead.

## Verification

Run relevant checks after edits:

- Parse `plugin.yaml` as YAML.
- Parse `default_config.yaml` as YAML.
- Parse `skills/okf-project-manager/SKILL.md` frontmatter as YAML.
- If profile files changed, follow `agents/okf_mgr/AGENTS.md` verification.
- If tool files changed, import every `agents/okf_mgr/tools/*.py` file with `/opt/venv-a0/bin/python` and verify each defines a `helpers.tool.Tool` subclass.
- If helper scripts changed, run smoke checks for validation, index generation, and visualization on a temporary OKF bundle.
- If graph verification or bulk-write scripts changed, run them on a temporary or test OKF bundle and confirm exact JSON counts.
- If Plugin Index files changed, verify:
  - `docs/community/index.yaml` is valid YAML,
  - `docs/community/index.yaml` is no larger than 2000 characters,
  - `docs/community/thumbnail.png` is square and no larger than 20 KB,
  - `webui/thumbnail.png` exists, is a valid square image, and is discoverable by Agent Zero as `/plugins/okf_manager/webui/thumbnail.png`.
- Before committing, confirm no `__pycache__`, `.pyc`, generated project OKF catalogs, secrets, tokens, or local runtime artifacts are staged.

## Child DOX Index

| Child | Scope |
| --- | --- |
| `agents/okf_mgr/AGENTS.md` | Bundled `okf_mgr` specialist profile, prompts, profile-local tools, and profile-local skills. |

- Keep `okf/catalog/` clean for concept content only; raw evidence must be retained in sibling `okf/raw/<meaningful-name>/` folders and referenced from concepts with code-checked relative links.
