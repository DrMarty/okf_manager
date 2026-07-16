from __future__ import annotations

import re
from pathlib import Path
from helpers.tool import Tool, Response

_SHARD_SUFFIX_RE = re.compile(r"^(?P<prefix>.+?_)(?P<shard>\d{6,8})$")

class OkfListConcepts(Tool):
    """List concepts from an OKF bundle or, when requested, a BigQuery dataset."""

    async def execute(self, **kwargs):
        source = self.args.get("source") or (self.agent.get_data("okf_context") or {}).get("source") or "bundle"
        if source == "bq":
            return await self._list_bq()
        return await self._list_bundle()

    async def _list_bundle(self):
        ctx = self.agent.get_data("okf_context") or {}
        root = Path(self.args.get("bundle_root") or ctx.get("bundle_root") or ".").expanduser()
        if not root.is_absolute():
            root = Path.cwd() / root
        if not root.is_dir():
            return Response(message=f"Bundle directory not found: {root}", break_loop=False)
        out = []
        for path in sorted(root.rglob("*.md")):
            if path.name in {"index.md", "log.md"}:
                continue
            rel = path.relative_to(root).with_suffix("").as_posix()
            fm = _parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
            out.append({"id": rel, "type": fm.get("type", ""), "resource": fm.get("resource"), "title": fm.get("title", ""), "description": fm.get("description", "")})
        return Response(message=_json(out), break_loop=False)

    async def _list_bq(self):
        try:
            from google.cloud import bigquery
        except Exception as e:
            return Response(message=f"BigQuery dependency unavailable: {e}", break_loop=False)
        ctx = self.agent.get_data("okf_context") or {}
        dataset = self.args.get("dataset") or ctx.get("dataset")
        billing_project = self.args.get("billing_project") or ctx.get("billing_project")
        if not dataset or "." not in dataset:
            return Response(message="dataset is required in 'project.dataset' form", break_loop=False)
        project, dataset_id = dataset.split(".", 1)
        client = bigquery.Client(project=billing_project)
        ds_ref = bigquery.DatasetReference(project, dataset_id)
        concepts = [{"id": f"datasets/{dataset_id}", "type": "BigQuery Dataset", "resource": f"https://bigquery.googleapis.com/v2/projects/{project}/datasets/{dataset_id}", "hint": {"dataset_project": project, "dataset_id": dataset_id}}]
        families, singletons = {}, []
        for tbl in client.list_tables(ds_ref):
            m = _SHARD_SUFFIX_RE.match(tbl.table_id)
            if m:
                families.setdefault(m.group("prefix"), []).append(tbl.table_id)
            else:
                singletons.append(tbl.table_id)
        for prefix, shards in sorted(families.items()):
            ss = sorted(shards)
            concepts.append({"id": f"tables/{prefix}", "type": "BigQuery Table", "resource": f"https://bigquery.googleapis.com/v2/projects/{project}/datasets/{dataset_id}/tables/{prefix}*", "hint": {"wildcard": True, "family_prefix": prefix, "shard_count": len(ss), "first_shard": ss[0], "last_shard": ss[-1]}})
        for table_id in sorted(singletons):
            concepts.append({"id": f"tables/{table_id}", "type": "BigQuery Table", "resource": f"https://bigquery.googleapis.com/v2/projects/{project}/datasets/{dataset_id}/tables/{table_id}", "hint": {"wildcard": False, "table_id": table_id}})
        return Response(message=_json(concepts), break_loop=False)

def _parse_frontmatter(text: str):
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    try:
        import yaml
        fm = yaml.safe_load(text[4:end]) or {}
        return fm if isinstance(fm, dict) else {}
    except Exception:
        return {}

def _json(obj):
    import json
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)
