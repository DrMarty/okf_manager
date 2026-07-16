#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

_LINK_RE = re.compile(r"\]\(([^)\s]+\.md)(?:#[A-Za-z0-9_-]*)?\)")


def doc(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = {}
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            try:
                import yaml
                parsed = yaml.safe_load(text[4:end]) or {}
                fm = parsed if isinstance(parsed, dict) else {}
                body = text[end + 4 :].lstrip("\n")
            except Exception:
                pass
    return fm, body


def build_graph(root: Path) -> dict:
    nodes = []
    ids = set()
    bodies = {}
    for md in sorted(root.rglob("*.md")):
        if md.name in {"index.md", "log.md"}:
            continue
        cid = md.relative_to(root).with_suffix("").as_posix()
        ids.add(cid)
        fm, body = doc(md)
        tags = fm.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]
        nodes.append({
            "id": cid,
            "type": str(fm.get("type") or "Unknown"),
            "title": str(fm.get("title") or cid),
            "description": str(fm.get("description") or ""),
            "resource": str(fm.get("resource") or ""),
            "tags": [str(tag) for tag in tags],
            "path": md.relative_to(root).as_posix(),
            "body": body[:1600],
        })
        bodies[cid] = body
    edges = []
    for cid, body in bodies.items():
        base = Path(cid).parent
        for match in _LINK_RE.finditer(body):
            target = match.group(1)
            if "://" in target or target.startswith("/"):
                continue
            tid = (base / target).with_suffix("").as_posix()
            tid = str(Path(tid)) if tid != "." else ""
            if tid in ids:
                edges.append({"source": cid, "target": tid})
    return {"nodes": nodes, "edges": edges}


def render(title: str, graph: dict) -> str:
    data = json.dumps(graph, ensure_ascii=False)
    safe_title = html.escape(title)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OKF Live Self-Graph — {safe_title}</title>
<style>
body {{ margin:0; font-family: system-ui, sans-serif; background:#0f172a; color:#e2e8f0; }}
header {{ padding:1rem; border-bottom:1px solid #334155; }}
main {{ display:grid; grid-template-columns: 1fr 22rem; min-height: calc(100vh - 5rem); }}
#graph {{ width:100%; height:100%; min-height:36rem; }}
aside {{ border-left:1px solid #334155; padding:1rem; overflow:auto; }}
.node {{ cursor:pointer; }}
.link {{ stroke:#64748b; stroke-width:1.4; opacity:.7; }}
.card {{ background:#111827; border:1px solid #334155; border-radius:.75rem; padding:.75rem; }}
.muted {{ color:#94a3b8; }}
</style>
</head>
<body>
<header><h1>OKF Live Self-Graph — {safe_title}</h1><div class="muted"><span id="counts"></span></div></header>
<main><svg id="graph"></svg><aside><div id="detail" class="card">Select a concept node.</div></aside></main>
<script type="application/json" id="graph-data">{html.escape(data)}</script>
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<script>
const graph = JSON.parse(document.getElementById('graph-data').textContent);
document.getElementById('counts').textContent = `${{graph.nodes.length}} concepts · ${{graph.edges.length}} links`;
const svg = d3.select('#graph');
function draw() {{
  const width = svg.node().clientWidth || 900, height = svg.node().clientHeight || 650;
  svg.attr('viewBox', [0,0,width,height]); svg.selectAll('*').remove();
  const color = d3.scaleOrdinal(d3.schemeTableau10);
  const sim = d3.forceSimulation(graph.nodes).force('link', d3.forceLink(graph.edges).id(d=>d.id).distance(110)).force('charge', d3.forceManyBody().strength(-360)).force('center', d3.forceCenter(width/2,height/2));
  const link = svg.append('g').selectAll('line').data(graph.edges).join('line').attr('class','link');
  const node = svg.append('g').selectAll('g').data(graph.nodes).join('g').attr('class','node').call(d3.drag().on('start',(e,d)=>{{if(!e.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y;}}).on('drag',(e,d)=>{{d.fx=e.x;d.fy=e.y;}}).on('end',(e,d)=>{{if(!e.active)sim.alphaTarget(0);}}));
  node.append('circle').attr('r',9).attr('fill',d=>color(d.type));
  node.append('title').text(d=>`${{d.title}}\n${{d.type}}`);
  node.append('text').attr('x',13).attr('y',4).attr('fill','#e2e8f0').attr('font-size',12).text(d=>d.title);
  node.on('click', (_, d) => {{ document.getElementById('detail').innerHTML = `<h2>${{escapeHtml(d.title)}}</h2><p class="muted">${{escapeHtml(d.type)}} · ${{escapeHtml(d.path)}}</p><p>${{escapeHtml(d.description)}}</p><p><strong>Resource:</strong> ${{escapeHtml(d.resource || '—')}}</p><pre>${{escapeHtml(d.body || '').slice(0,1200)}}</pre>`; }});
  sim.on('tick',()=>{{ link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y); node.attr('transform',d=>`translate(${{d.x}},${{d.y}})`); }});
}}
function escapeHtml(s) {{ return String(s ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
draw(); addEventListener('resize', draw);
</script>
</body></html>'''


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in {"-h", "--help"}:
        print("Usage: okf_visualize_bundle.py <bundle_root> [out_html]")
        return 2
    root = Path(argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"Bundle directory not found: {root}", file=sys.stderr)
        return 1
    out = Path(argv[2]).expanduser().resolve() if len(argv) > 2 else root / "viz.html"
    graph = build_graph(root)
    page = render(root.name, graph)
    out.write_text(page, encoding="utf-8")
    print(json.dumps({"concepts": len(graph["nodes"]), "edges": len(graph["edges"]), "path": str(out), "bytes": len(page.encode('utf-8'))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
