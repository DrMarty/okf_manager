from __future__ import annotations

import json
import re
from pathlib import Path
from helpers.tool import Tool, Response

_SHARD_SUFFIX_RE = re.compile(r"^(?P<prefix>.+?_)(?P<shard>\d{6,8})$")

class OkfReadConceptRaw(Tool):
    """Read raw metadata for a bundle concept or BigQuery concept."""

    async def execute(self, **kwargs):
        source = self.args.get("source") or (self.agent.get_data("okf_context") or {}).get("source") or "bundle"
        concept_id = self.args.get("concept_id")
        if not concept_id:
            return Response(message="concept_id is required", break_loop=False)
        if source == "bq":
            return await self._read_bq(concept_id)
        ctx = self.agent.get_data("okf_context") or {}
        root = Path(self.args.get("bundle_root") or ctx.get("bundle_root") or ".").expanduser()
        if not root.is_absolute(): root = Path.cwd() / root
        path = root.joinpath(*concept_id.split("/")).with_suffix(".md")
        if not path.exists():
            return Response(message=f"Concept file not found: {path}", break_loop=False)
        return Response(message=path.read_text(encoding="utf-8"), break_loop=False)

    async def _read_bq(self, concept_id: str):
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
        kind, _, name = concept_id.partition("/")
        if kind == "datasets":
            ds = client.get_dataset(ds_ref)
            data = {"dataset_project": project, "dataset_id": dataset_id, "friendly_name": ds.friendly_name, "description": ds.description, "location": ds.location, "labels": dict(ds.labels or {}), "created": ds.created.isoformat() if ds.created else None, "modified": ds.modified.isoformat() if ds.modified else None, "default_partition_expiration_ms": ds.default_partition_expiration_ms}
            return Response(message=json.dumps(data, indent=2, default=str), break_loop=False)
        if kind != "tables":
            return Response(message=f"Unsupported BigQuery concept kind: {kind}", break_loop=False)
        table_id = name
        if name.endswith("_"):
            shards = sorted(t.table_id for t in client.list_tables(ds_ref) if t.table_id.startswith(name) and _SHARD_SUFFIX_RE.match(t.table_id))
            if shards: table_id = shards[-1]
        tbl = client.get_table(ds_ref.table(table_id))
        data = {"dataset_project": project, "dataset_id": dataset_id, "representative_table_id": table_id, "friendly_name": tbl.friendly_name, "description": tbl.description, "labels": dict(tbl.labels or {}), "num_rows": tbl.num_rows, "num_bytes": tbl.num_bytes, "created": tbl.created.isoformat() if tbl.created else None, "modified": tbl.modified.isoformat() if tbl.modified else None, "schema": [_field(f) for f in list(tbl.schema or [])]}
        if tbl.time_partitioning:
            data["time_partitioning"] = {"type": tbl.time_partitioning.type_, "field": tbl.time_partitioning.field, "expiration_ms": tbl.time_partitioning.expiration_ms}
        if tbl.range_partitioning:
            rp = tbl.range_partitioning
            data["range_partitioning"] = {"field": rp.field, "range": {"start": rp.range_.start, "end": rp.range_.end, "interval": rp.range_.interval}}
        if tbl.clustering_fields:
            data["clustering_fields"] = list(tbl.clustering_fields)
        return Response(message=json.dumps(data, indent=2, default=str), break_loop=False)

def _field(f):
    d = {"name": f.name, "type": f.field_type, "mode": f.mode}
    if f.description: d["description"] = f.description
    if f.fields: d["fields"] = [_field(x) for x in list(f.fields)]
    return d
