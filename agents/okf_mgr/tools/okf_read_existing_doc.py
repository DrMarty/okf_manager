from __future__ import annotations

import json
from pathlib import Path
from helpers.tool import Tool, Response

class OkfReadExistingDoc(Tool):
    """Read an existing OKF concept document as frontmatter/body."""
    async def execute(self, **kwargs):
        ctx = self.agent.get_data("okf_context") or {}
        root = Path(self.args.get("bundle_root") or ctx.get("bundle_root") or ".").expanduser()
        if not root.is_absolute(): root = Path.cwd() / root
        concept_id = self.args.get("concept_id")
        if not concept_id:
            return Response(message="concept_id is required", break_loop=False)
        path = root.joinpath(*concept_id.split("/")).with_suffix(".md")
        if not path.exists():
            return Response(message="null", break_loop=False)
        text = path.read_text(encoding="utf-8")
        fm, body = _split(text)
        return Response(message=json.dumps({"frontmatter": fm, "body": body}, indent=2, ensure_ascii=False), break_loop=False)

def _split(text):
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    import yaml
    fm = yaml.safe_load(text[4:end]) or {}
    body = text[end+4:].lstrip("\n")
    return (fm if isinstance(fm, dict) else {}), body
