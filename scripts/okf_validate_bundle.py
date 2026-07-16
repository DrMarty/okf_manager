#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_LINK_RE = re.compile(r"\]\(([^)\s]+\.md)(?:#[A-Za-z0-9_-]*)?\)")


def split_frontmatter(text: str):
    if not text.startswith("---\n"):
        return {}, text, "missing YAML frontmatter at line 1"
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text, "unterminated YAML frontmatter"
    try:
        import yaml
        fm = yaml.safe_load(text[4:end]) or {}
    except Exception as exc:
        return {}, text, f"invalid YAML frontmatter: {exc}"
    if not isinstance(fm, dict):
        return {}, text, "frontmatter must be mapping"
    return fm, text[end + 4 :].lstrip("\n"), ""


def validate(root: Path, strict: bool = True) -> dict:
    root = root.expanduser().resolve()
    issues = []
    count = 0
    if not root.is_dir():
        return {"concept_count": 0, "issue_count": 1, "issues": [{"path": str(root), "issue": "bundle directory not found"}]}
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        if path.name in {"index.md", "log.md"}:
            continue
        count += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        fm, body, err = split_frontmatter(text)
        if err:
            issues.append({"path": rel, "issue": err})
            continue
        required = ["type"] + (["title", "description", "timestamp"] if strict else [])
        for key in required:
            if not fm.get(key):
                issues.append({"path": rel, "issue": f"missing frontmatter {key}"})
        if "tags" in fm and not isinstance(fm["tags"], list):
            issues.append({"path": rel, "issue": "tags must be a YAML list"})
        for match in _LINK_RE.finditer(body):
            target = match.group(1)
            if "://" in target:
                continue
            if target.startswith("/"):
                issues.append({"path": rel, "issue": f"root-relative internal link discouraged: {target}"})
                continue
            dest = (path.parent / target).resolve()
            try:
                dest.relative_to(root)
            except Exception:
                issues.append({"path": rel, "issue": f"link escapes bundle: {target}"})
                continue
            if not dest.exists():
                issues.append({"path": rel, "issue": f"broken link: {target}"})
    return {"concept_count": count, "issue_count": len(issues), "issues": issues}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print("Usage: okf_validate_bundle.py <bundle_root> [--non-strict]")
        return 2
    strict = "--non-strict" not in argv[2:]
    result = validate(Path(argv[1]), strict=strict)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["issue_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
