### okf_write_concept_doc:
Write an OKF concept document. Mirrors the reference agent's `write_concept_doc` capability with stricter reference-compatible validation.

Args: `concept_id`, `frontmatter` object, `body` markdown string, optional `bundle_root`, optional `web_pass` boolean to enable augmentation guards.
Frontmatter must include `type`, `title`, `description`; `timestamp` is filled if omitted. `index.md` and `log.md` are reserved and cannot be concept IDs.

Execution rule: call this profile-local tool sequentially from the active `okf_mgr` context. Do **not** call `okf_write_concept_doc` inside generic `parallel` jobs; parallel worker contexts may not expose `okf_mgr` profile-local tools or agent-scoped `okf_context`, producing `Tool okf_write_concept_doc not found` before this tool is reached. For bulk writes, use sequential calls or a deterministic script/file-writing workflow followed by validation.
