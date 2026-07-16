from __future__ import annotations

import json, re
from datetime import datetime, timezone
from pathlib import Path
from helpers.tool import Tool, Response

_REQUIRED = ("type", "title", "description", "timestamp")
_ORDER = ("type", "resource", "title", "description", "tags", "timestamp")
_SEGMENT_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
_FIELD_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*)`")

class OkfWriteConceptDoc(Tool):
    """Write an OKF concept document with reference-agent-compatible validation."""
    async def execute(self, **kwargs):
        ctx = self.agent.get_data("okf_context") or {}
        root = Path(self.args.get("bundle_root") or ctx.get("bundle_root") or ".").expanduser()
        if not root.is_absolute(): root = Path.cwd() / root
        concept_id = self.args.get("concept_id")
        frontmatter = dict(self.args.get("frontmatter") or {})
        body = self.args.get("body") or ""
        if not concept_id or not isinstance(frontmatter, dict):
            return Response(message="concept_id and frontmatter object are required", break_loop=False)
        err = _validate_concept_id(concept_id)
        if err: return Response(message=err, break_loop=False)
        if not frontmatter.get("timestamp"):
            frontmatter["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        missing = [k for k in _REQUIRED if not frontmatter.get(k)]
        if missing:
            return Response(message=f"Refusing to write document with invalid frontmatter. Missing required keys: {', '.join(missing)}", break_loop=False)
        frontmatter = _reorder(frontmatter)
        path = root.joinpath(*concept_id.split("/")).with_suffix(".md")
        web_pass = bool(self.args.get("web_pass"))
        if web_pass and path.exists():
            old_fm, old_body = _split(path.read_text(encoding="utf-8"))
            if old_fm.get("type") == "BigQuery Table":
                old_fields, new_fields = _schema_fields(old_body), _schema_fields(body)
                missing_fields = sorted(old_fields - new_fields)
                if missing_fields:
                    return Response(message=f"Refusing to write: new # Schema is missing {len(missing_fields)} existing field(s): {', '.join('`'+x+'`' for x in missing_fields[:10])}", break_loop=False)
                if _citation_count(body) < _citation_count(old_body):
                    return Response(message="Refusing to write: new # Citations has fewer entries than existing doc.", break_loop=False)
        import yaml
        text = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).rstrip() + "\n---\n\n" + (body if body.endswith("\n") else body + "\n")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return Response(message=json.dumps({"path": str(path.relative_to(root)), "bytes": len(text.encode("utf-8"))}, indent=2), break_loop=False)

def _validate_concept_id(s):
    parts = [p for p in s.split("/") if p]
    if not parts: return "Empty concept_id"
    if parts[-1] in {"index", "log"}: return "Reserved filenames index.md and log.md cannot be concept documents"
    for p in parts:
        if not _SEGMENT_RE.fullmatch(p): return f"Invalid concept id segment: {p!r}"
    return ""

def _reorder(fm):
    out = {k: fm[k] for k in _ORDER if k in fm}
    out.update({k:v for k,v in fm.items() if k not in out})
    return out

def _split(text):
    if not text.startswith("---\n"): return {}, text
    end = text.find("\n---", 4)
    if end < 0: return {}, text
    import yaml
    return yaml.safe_load(text[4:end]) or {}, text[end+4:].lstrip("\n")

def _section_lines(body, heading):
    on=False; out=[]
    for line in body.splitlines():
        st=line.strip()
        if st.startswith("# "):
            on = st == heading
            continue
        if on and st: out.append(line)
    return out

def _schema_fields(body):
    names=set()
    for line in _section_lines(body, "# Schema"):
        names.update(_FIELD_RE.findall(line))
    return names

def _citation_count(body):
    return len(_section_lines(body, "# Citations"))
