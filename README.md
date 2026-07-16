# OKF Manager

OKF Manager delivers portable Open Knowledge Format ([OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)) management to Agent Zero projects.

It provides:

- `okf-project-manager` skill: an active-project wrapper that resolves where a project's OKF catalog should live, then delegates nontrivial catalog work to `okf_mgr`.
- `okf_mgr` agent profile: a specialist profile for creating, validating, enriching, indexing, and visualizing OKF catalogs.
- Standalone helper scripts for validation, index generation, and visualization.

## What this plugin is for

Use OKF Manager to maintain global / project-specific knowledge catalogs with Markdown concept documents, YAML frontmatter, citations, indexes, update logs, and an interactive `viz.html` graph.

Typical requests:

- "Manage the OKF catalog for this project."
- "Ingest these source documents into OKF."
- "Validate the OKF bundle."
- "Update the knowledge graph."
- "Generate indexes and refresh viz.html."

## Install

Copy or install this plugin into Agent Zero under:

```text
/a0/usr/plugins/okf_manager/
```

Then enable it from the Agent Zero Plugins UI if it is not already enabled.

## Repository layout

```text
okf_manager/
├── plugin.yaml
├── README.md
├── LICENSE
├── default_config.yaml
├── skills/
│   └── okf-project-manager/
│       └── SKILL.md
├── agents/
│   └── okf_mgr/
│       ├── agent.yaml
│       ├── prompts/
│       ├── tools/
│       └── skills/
└── scripts/
    ├── okf_validate_bundle.py
    ├── okf_regenerate_indexes.py
    └── okf_visualize_bundle.py
```

## How catalog paths are resolved

The skill stores derived catalogs in the active Agent Zero project when one is available. If OKF Manager is called outside an active project, it uses a global user OKF workspace instead.

Resolution order:

1. Use an explicit catalog path from the user or project instructions.
2. If an active project exists, use an existing project-local `okf/*/` bundle if exactly one exists.
3. If no active project exists, use an existing global `/a0/usr/okf/*/` bundle if exactly one exists.
4. Otherwise propose the default project-local or global catalog path:

```text
<project-root>/okf/catalog/
```

or, outside a project:

```text
/a0/usr/okf/catalog/
```

The plugin intentionally keeps project data in the project. Global OKF data is kept under `/a0/usr/okf/`, not in the plugin directory.

### Bundle creation confirmation

OKF Manager must always ask the user for explicit confirmation before creating a new OKF bundle directory.

Before creating a bundle, the agent should report:

- whether the bundle is project-local or global,
- the exact target catalog directory,
- the source/evidence locations that will be used, if known,
- the first intended operation.

Existing bundle maintenance does not require this creation confirmation, but ambiguous catalog selection still requires clarification.

## Project conventions

OKF concept Markdown should include YAML frontmatter with:

- `type`
- `title`
- `description`
- `timestamp`

Concept documents should preserve provenance in `# Citations` sections and prefer `resource` values pointing to source files or source URLs when known.

Recommended bundle files:

- `index.md` for generated directory indexes.
- `log.md` for chronological update history.
- `viz.html` for the generated interactive graph.

## Web-ingestion and network disclosure

This plugin includes an `okf_mgr` web-ingestion tool:

```text
agents/okf_mgr/tools/okf_fetch_url.py
```

That tool can fetch user-directed web pages with Python `urllib.request.urlopen` so the agent can ingest or cite web-based source evidence.

The web-ingestion tool is designed to be guarded. It supports constraints such as:

- allowed hosts,
- allowed path prefixes,
- denied path substrings,
- maximum page count,
- maximum crawl depth,
- session-local visited URL tracking.

It is not intended to crawl the open web indiscriminately. Users should provide or approve source URLs and crawl constraints for web ingestion tasks.

## Helper scripts

The scripts can be run manually from the plugin root or copied into automation:

```bash
python scripts/okf_validate_bundle.py /path/to/project/okf/catalog
python scripts/okf_regenerate_indexes.py /path/to/project/okf/catalog
python scripts/okf_visualize_bundle.py /path/to/project/okf/catalog
```

### Validate bundle

```bash
python scripts/okf_validate_bundle.py /path/to/project/okf/catalog
```

Checks concept frontmatter and relative Markdown links.

### Regenerate indexes

```bash
python scripts/okf_regenerate_indexes.py /path/to/project/okf/catalog
```

Writes `index.md` files for bundle directories.

### Generate graph

```bash
python scripts/okf_visualize_bundle.py /path/to/project/okf/catalog
```

Writes `viz.html` in the bundle directory.

## Community Plugin Index

Runtime manifest:

```text
plugin.yaml
```

Suggested Plugin Index entry:

```yaml
title: OKF Manager
description: Portable Open Knowledge Format catalog management for Agent Zero projects, with a specialist okf_mgr profile, project skill, and validation/index/visualization helpers.
github: https://github.com/DrMarty/okf_manager
tags:
  - agents
  - automation
  - development
  - workflow
  - llm
```

The Plugin Index uses a separate `index.yaml` file in the `agent0ai/a0-plugins` repository. Do not confuse it with this plugin's runtime `plugin.yaml`.

A square, Plugin Index-compliant thumbnail is prepared at:

```text
docs/community/thumbnail.png
```

## License

MIT. See `LICENSE`.
