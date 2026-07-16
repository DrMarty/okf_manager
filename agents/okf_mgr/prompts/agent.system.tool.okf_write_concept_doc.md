### okf_write_concept_doc:
Write an OKF concept document. Mirrors the reference agent's `write_concept_doc` capability with stricter reference-compatible validation.

Args: `concept_id`, `frontmatter` object, `body` markdown string, optional `bundle_root`, optional `web_pass` boolean to enable augmentation guards.
Frontmatter must include `type`, `title`, `description`; `timestamp` is filled if omitted. `index.md` and `log.md` are reserved and cannot be concept IDs.
