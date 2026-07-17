from __future__ import annotations

import json, re
from pathlib import Path
from urllib.parse import urlparse
from helpers.tool import Tool, Response

_LINK_RE = re.compile(r"\]\(([^)\s#]+)(?:#[A-Za-z0-9_-]*)?\)")


def _is_raw_evidence(rel) -> bool:
    parts = rel.parts if hasattr(rel, "parts") else Path(str(rel)).parts
    return len(parts) >= 2 and parts[0] == "sources" and parts[1] == "raw"


def _is_allowed_raw_link(root: Path, dest: Path) -> bool:
    try:
        rel = dest.resolve().relative_to(root.parent.resolve())
    except Exception:
        return False
    return len(rel.parts) >= 2 and rel.parts[0] == "raw"

class OkfValidateBundle(Tool):
    """Validate an OKF bundle for frontmatter and internal links."""
    async def execute(self, **kwargs):
        ctx = self.agent.get_data("okf_context") or {}
        root = Path(self.args.get("bundle_root") or ctx.get("bundle_root") or ".").expanduser()
        if not root.is_absolute(): root = Path.cwd() / root
        strict = bool(self.args.get("strict_reference", True))
        issues=[]; count=0
        if not root.is_dir(): return Response(message=f"Bundle directory not found: {root}", break_loop=False)
        for path in sorted(root.rglob("*.md")):
            rel_path=path.relative_to(root)
            rel=rel_path.as_posix()
            if path.name in {"index.md","log.md"} or _is_raw_evidence(rel_path):
                continue
            text=path.read_text(encoding="utf-8", errors="replace")
            count += 1
            fm, body, err = _split(text)
            if err: issues.append({"path": rel, "issue": err}); continue
            required=["type"] + (["title","description","timestamp"] if strict else [])
            for k in required:
                if not fm.get(k): issues.append({"path": rel, "issue": f"missing frontmatter {k}"})
            if "tags" in fm and not isinstance(fm["tags"], list): issues.append({"path": rel, "issue": "tags must be a YAML list"})
            for m in _LINK_RE.finditer(body):
                target=m.group(1)
                if "://" in target or target.startswith("#") or target.startswith("mailto:"): continue
                if target.startswith("/"): issues.append({"path": rel, "issue": f"root-relative internal link discouraged: {target}"}); continue
                dest=(path.parent/target).resolve()
                try:
                    dest.relative_to(root.resolve()); allowed=True
                except Exception:
                    allowed=_is_allowed_raw_link(root, dest)
                if not allowed: issues.append({"path": rel, "issue": f"link escapes catalog and is not under sibling raw/: {target}"}); continue
                if not dest.exists(): issues.append({"path": rel, "issue": f"broken link: {target}"})
        return Response(message=json.dumps({"concept_count": count, "issue_count": len(issues), "issues": issues}, indent=2, ensure_ascii=False), break_loop=False)

def _split(text):
    if not text.startswith("---\n"): return {}, text, "missing YAML frontmatter at line 1"
    end=text.find("\n---",4)
    if end<0: return {}, text, "unterminated YAML frontmatter"
    try:
        import yaml
        fm=yaml.safe_load(text[4:end]) or {}
        if not isinstance(fm, dict): return {}, text, "frontmatter must be mapping"
        return fm, text[end+4:].lstrip("\n"), ""
    except Exception as e: return {}, text, f"invalid YAML frontmatter: {e}"
