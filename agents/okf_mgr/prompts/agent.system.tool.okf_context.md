### okf_context:
Set, show, or clear shared OKF tool context for this agent session. Use it before repeated OKF bundle or BigQuery operations.

Usage:
~~~json
{"tool_name":"okf_context","tool_args":{"action":"set","bundle_root":"/path/to/bundle","source":"bundle"}}
~~~
For BigQuery context, use `source: "bq"`, `dataset: "project.dataset"`, and optional `billing_project`.
