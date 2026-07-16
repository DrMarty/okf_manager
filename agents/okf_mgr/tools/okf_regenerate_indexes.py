from __future__ import annotations

from pathlib import Path
from collections import defaultdict
from helpers.tool import Tool, Response

class OkfRegenerateIndexes(Tool):
    """Generate reference-agent-style index.md files for an OKF bundle."""
    async def execute(self, **kwargs):
        ctx = self.agent.get_data("okf_context") or {}
        root = Path(self.args.get("bundle_root") or ctx.get("bundle_root") or ".").expanduser()
        if not root.is_absolute(): root = Path.cwd() / root
        if not root.is_dir(): return Response(message=f"Bundle directory not found: {root}", break_loop=False)
        dirs=set()
        for md in root.rglob("*.md"):
            cur=md.parent
            while True:
                dirs.add(cur)
                if cur == root: break
                cur = cur.parent
        written=[]; descriptions={}
        for directory in sorted(dirs, key=lambda p:(-len(p.relative_to(root).parts), str(p))):
            entries=[]
            for child in sorted(directory.iterdir()):
                if child.name == "index.md": continue
                if child.is_file() and child.suffix == ".md" and child.name != "log.md":
                    fm=_fm(child)
                    entries.append((str(fm.get("type") or "Other"), str(fm.get("title") or child.stem), child.name, str(fm.get("description") or "")))
                elif child.is_dir():
                    entries.append(("Subdirectories", child.name, f"{child.name}/index.md", descriptions.get(child,"")))
            if not entries: continue
            text=_index_text(entries)
            path=directory/"index.md"; path.write_text(text, encoding="utf-8"); written.append(str(path.relative_to(root)))
            if directory != root:
                pairs=[(t,d) for _,t,_,d in entries]
                descriptions[directory] = pairs[0][1] if len(pairs)==1 and pairs[0][1] else f"Contains {len(pairs)} entries: {', '.join(t for t,_ in pairs if t)}."
        return Response(message="Written indexes:\n"+"\n".join(written), break_loop=False)

def _fm(path):
    text=path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"): return {}
    end=text.find("\n---",4)
    if end<0: return {}
    try:
        import yaml
        return yaml.safe_load(text[4:end]) or {}
    except Exception: return {}

def _index_text(entries):
    grouped=defaultdict(list)
    for typ,title,link,desc in entries: grouped[typ or "Other"].append((title,link,desc))
    sections=[]
    for typ in sorted(grouped):
        lines=[f"# {typ}",""]
        for title,link,desc in sorted(grouped[typ], key=lambda e:e[0].lower()):
            lines.append(f"* [{title}]({link})" + (f" - {desc}" if desc else ""))
        sections.append("\n".join(lines))
    return "\n\n".join(sections)+"\n"
