from __future__ import annotations

import json
from helpers.tool import Tool, Response

class OkfSampleRows(Tool):
    """Sample rows from a BigQuery table concept."""
    async def execute(self, **kwargs):
        try:
            from google.cloud import bigquery
        except Exception as e:
            return Response(message=f"BigQuery dependency unavailable: {e}", break_loop=False)
        ctx = self.agent.get_data("okf_context") or {}
        dataset = self.args.get("dataset") or ctx.get("dataset")
        concept_id = self.args.get("concept_id")
        n = int(self.args.get("n", 5))
        if not dataset or "." not in dataset or not concept_id:
            return Response(message="dataset ('project.dataset') and concept_id are required", break_loop=False)
        project, dataset_id = dataset.split(".", 1)
        kind, _, table_id = concept_id.partition("/")
        if kind != "tables" or not table_id:
            return Response(message="sample_rows supports table concepts like tables/users", break_loop=False)
        client = bigquery.Client(project=self.args.get("billing_project") or ctx.get("billing_project"))
        table_ref = f"{project}.{dataset_id}.{table_id}"
        try:
            table = client.get_table(table_ref)
            if getattr(table, "table_type", "TABLE") == "VIEW":
                rows = client.query(f"SELECT * FROM `{table_ref}` LIMIT {n}").result()
            else:
                rows = client.list_rows(table, max_results=n)
            out = [{k: str(v) for k, v in dict(r.items()).items()} for r in rows]
            return Response(message=json.dumps({"rows": out, "note": ""}, indent=2), break_loop=False)
        except Exception as e:
            return Response(message=json.dumps({"rows": [], "note": f"Sampling failed: {e}"}, indent=2), break_loop=False)
