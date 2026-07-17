from __future__ import annotations

import html
import json
import re
from pathlib import Path
from helpers.tool import Tool, Response

_LINK_RE = re.compile(r"\]\(([^)\s]+\.md)(?:#[A-Za-z0-9_-]*)?\)")
_TYPE_COLORS = [
    "#60a5fa",
    "#34d399",
    "#f59e0b",
    "#f472b6",
    "#a78bfa",
    "#22d3ee",
    "#fb7185",
    "#84cc16",
]


class OkfVisualizeBundle(Tool):
    """Generate a self-contained live HTML graph for an OKF bundle."""

    async def execute(self, **kwargs):
        ctx = self.agent.get_data("okf_context") or {}
        root = Path(self.args.get("bundle_root") or ctx.get("bundle_root") or ".").expanduser()
        if not root.is_absolute():
            root = Path.cwd() / root
        out = Path(self.args.get("out") or root / "viz.html")
        if not out.is_absolute():
            out = Path.cwd() / out
        if not root.is_dir():
            return Response(message=f"Bundle directory not found: {root}", break_loop=False)

        graph = _build_graph(root)
        doc = _render_html(root.name, graph)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc, encoding="utf-8")
        return Response(
            message=json.dumps(
                {
                    "concepts": len(graph["nodes"]),
                    "edges": len(graph["edges"]),
                    "path": str(out),
                    "bytes": len(doc.encode("utf-8")),
                    "mode": "live-self-graph",
                },
                indent=2,
            ),
            break_loop=False,
        )


def _build_graph(root: Path) -> dict:
    concepts = []
    ids = set()
    bodies = {}
    for md in sorted(root.rglob("*.md")):
        if md.name in {"index.md", "log.md"}:
            continue
        cid = md.relative_to(root).with_suffix("").as_posix()
        ids.add(cid)
        fm, body = _doc(md)
        tags = fm.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]
        node = {
            "id": cid,
            "type": str(fm.get("type") or "Unknown"),
            "title": str(fm.get("title") or cid),
            "description": str(fm.get("description") or ""),
            "resource": str(fm.get("resource") or ""),
            "tags": [str(t) for t in tags],
            "path": md.relative_to(root).as_posix(),
            "body": body,
        }
        concepts.append(node)
        bodies[cid] = body

    edges = []
    seen = set()
    for md in sorted(root.rglob("*.md")):
        if md.name in {"index.md", "log.md"}:
            continue
        source = md.relative_to(root).with_suffix("").as_posix()
        _, body = _doc(md)
        for m in _LINK_RE.finditer(body):
            target = m.group(1)
            if "://" in target or target.startswith("/"):
                continue
            try:
                dest = (md.parent / target).resolve().relative_to(root.resolve()).with_suffix("").as_posix()
            except Exception:
                continue
            if dest in ids and dest != source and (source, dest) not in seen:
                seen.add((source, dest))
                edges.append({"source": source, "target": dest})

    type_names = sorted({n["type"] for n in concepts})
    palette = {typ: _TYPE_COLORS[i % len(_TYPE_COLORS)] for i, typ in enumerate(type_names)}
    return {
        "nodes": concepts,
        "edges": edges,
        "types": type_names,
        "palette": palette,
        "stats": {
            "concepts": len(concepts),
            "edges": len(edges),
            "types": len(type_names),
        },
    }



def _parse_simple_frontmatter(raw: str) -> dict:
    """Parse the simple YAML subset commonly used by OKF frontmatter.

    This fallback keeps the standalone helper script independent of PyYAML so
    `./scripts/okf_visualize_bundle.py` works under the system Python too.
    """
    result = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            result[key] = [item.strip().strip('"\'') for item in inner.split(",") if item.strip()]
        else:
            result[key] = value.strip('"\'')
    return result


def _load_frontmatter(raw: str) -> dict:
    try:
        import yaml

        parsed = yaml.safe_load(raw) or {}
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return _parse_simple_frontmatter(raw)


def _doc(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    normalized = text.replace("\r\n", "\n")
    if normalized.startswith("---\n"):
        end = normalized.find("\n---", 4)
        if end >= 0:
            fm = _load_frontmatter(normalized[4:end])
            body = normalized[end + 4 :].lstrip("\n")
            return fm, body
    return {}, normalized

def _render_html(bundle_name: str, graph: dict) -> str:
    data = json.dumps(graph, ensure_ascii=False)
    title = html.escape(bundle_name)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OKF Live Self-Graph — {title}</title>
<style>
:root {{ color-scheme: dark; --bg:#0f172a; --panel:#111827; --muted:#94a3b8; --text:#e5e7eb; --accent:#38bdf8; --line:#334155; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif; background:var(--bg); color:var(--text); overflow:hidden; }}
header {{ height:58px; display:flex; align-items:center; gap:16px; padding:10px 16px; border-bottom:1px solid var(--line); background:#020617; }}
header h1 {{ margin:0; font-size:18px; white-space:nowrap; }}
header .stats {{ color:var(--muted); font-size:13px; }}
main {{ display:grid; grid-template-columns: 280px 1fr 360px; height:calc(100vh - 58px); }}
aside, section {{ min-height:0; }}
.sidebar, .detail {{ background:var(--panel); border-right:1px solid var(--line); overflow:auto; padding:14px; }}
.detail {{ border-right:0; border-left:1px solid var(--line); }}
.graph-wrap {{ position:relative; min-width:0; min-height:0; }}
#graph {{ width:100%; height:100%; display:block; background:radial-gradient(circle at 50% 40%, #172554 0%, #0f172a 48%, #020617 100%); cursor:grab; }}
#graph:active {{ cursor:grabbing; }}
input, select, button {{ width:100%; border:1px solid #334155; border-radius:8px; background:#020617; color:var(--text); padding:8px 10px; margin:6px 0 12px; }}
button {{ cursor:pointer; background:#0f172a; }}
button:hover {{ border-color:var(--accent); }}
.legend-item {{ display:flex; align-items:center; gap:8px; margin:6px 0; color:#cbd5e1; }}
.swatch {{ width:11px; height:11px; border-radius:50%; flex:none; }}
.node-list {{ margin-top:12px; border-top:1px solid var(--line); padding-top:8px; }}
.node-row {{ padding:7px; border-radius:7px; cursor:pointer; color:#cbd5e1; }}
.node-row:hover, .node-row.active {{ background:#1e293b; color:white; }}
.badge {{ display:inline-block; padding:2px 6px; border:1px solid #334155; border-radius:999px; color:#cbd5e1; font-size:11px; margin:2px 4px 2px 0; }}
.detail h2 {{ margin:0 0 4px; font-size:19px; }}
.detail .id {{ color:var(--muted); font-family:ui-monospace,monospace; font-size:12px; word-break:break-all; }}
.detail pre {{ white-space:pre-wrap; background:#020617; padding:10px; border-radius:8px; max-height:280px; overflow:auto; border:1px solid #334155; }}
.detail a {{ color:#7dd3fc; }}
.empty {{ color:var(--muted); }}
.toolbar {{ position:absolute; top:12px; right:12px; display:flex; gap:8px; }}
.toolbar button {{ width:auto; margin:0; opacity:.9; }}
.tooltip {{ position:absolute; pointer-events:none; background:#020617; border:1px solid #334155; padding:6px 8px; border-radius:7px; color:#e5e7eb; max-width:300px; display:none; }}
@media (max-width: 1000px) {{ main {{ grid-template-columns: 240px 1fr; }} .detail {{ position:absolute; right:0; top:58px; bottom:0; width:min(360px, 90vw); z-index:5; }} }}
</style>
</head>
<body>
<header>
  <h1>OKF Live Self-Graph — {title}</h1>
  <div class="stats" id="stats"></div>
</header>
<main>
  <aside class="sidebar">
    <label>Search concepts</label>
    <input id="search" placeholder="title, id, tag, description">
    <label>Filter by type</label>
    <select id="typeFilter"><option value="">All types</option></select>
    <button id="fitBtn">Fit graph</button>
    <button id="pinBtn">Unpin all nodes</button>
    <p class="empty">Live self-graph: nodes are draggable and pinnable. Double-click a node to unpin it; use the mouse wheel to zoom and drag empty space to pan.</p>
    <h3>Types</h3>
    <div id="legend"></div>
    <div class="node-list" id="nodeList"></div>
  </aside>
  <section class="graph-wrap">
    <canvas id="graph"></canvas>
    <div class="toolbar"><button id="zoomIn">+</button><button id="zoomOut">−</button><button id="resetZoom">Reset</button></div>
    <div class="tooltip" id="tooltip"></div>
  </section>
  <aside class="detail" id="detail"><p class="empty">Select a concept node to inspect frontmatter, body preview, outgoing links, and backlinks.</p></aside>
</main>
<script id="bundle-data" type="application/json">{data.replace('</', '<\\/')}</script>
<script>
(() => {{
const bundle = JSON.parse(document.getElementById('bundle-data').textContent);
const nodes = bundle.nodes.map((n, i) => ({{...n, x: 0, y: 0, vx: 0, vy: 0, pinned: false, visible: true, r: 9 + Math.min(18, Math.sqrt((n.body||'').length)/9), idx: i}}));
const byId = new Map(nodes.map(n => [n.id, n]));
const edges = bundle.edges.map(e => ({{source: byId.get(e.source), target: byId.get(e.target)}})).filter(e => e.source && e.target);
const palette = bundle.palette || {{}};
const canvas = document.getElementById('graph');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');
let width=0, height=0, dpr=1, scale=1, ox=0, oy=0, selected=null, hover=null, dragging=null, panning=false, last={{x:0,y:0}};

function resize() {{
  const rect = canvas.getBoundingClientRect(); dpr = window.devicePixelRatio || 1; width = rect.width; height = rect.height;
  canvas.width = Math.max(1, Math.floor(width*dpr)); canvas.height = Math.max(1, Math.floor(height*dpr)); ctx.setTransform(dpr,0,0,dpr,0,0);
  if (!nodes.some(n => n.x || n.y)) initPositions();
}}
function initPositions() {{
  const radius = Math.max(80, Math.min(width, height) * 0.35); const cx = width/2; const cy = height/2;
  nodes.forEach((n,i) => {{ const a = (Math.PI*2*i)/Math.max(1,nodes.length); n.x = cx + radius*Math.cos(a); n.y = cy + radius*Math.sin(a); }});
}}
function screen(n) {{ return {{x:n.x*scale+ox, y:n.y*scale+oy}}; }}
function world(x,y) {{ return {{x:(x-ox)/scale, y:(y-oy)/scale}}; }}
function visibleNodes() {{ return nodes.filter(n => n.visible); }}
function visibleEdges() {{ return edges.filter(e => e.source.visible && e.target.visible); }}
function tick() {{
  const vs = visibleNodes(); if (!vs.length) return;
  for (const n of vs) {{ if (!n.pinned) {{ n.vx *= .86; n.vy *= .86; }} }}
  for (let i=0;i<vs.length;i++) for (let j=i+1;j<vs.length;j++) {{
    const a=vs[i], b=vs[j]; let dx=a.x-b.x, dy=a.y-b.y; let d2=dx*dx+dy*dy || .01; let f=Math.min(600, 4800/d2);
    let d=Math.sqrt(d2); dx/=d; dy/=d; if(!a.pinned){{a.vx+=dx*f; a.vy+=dy*f;}} if(!b.pinned){{b.vx-=dx*f; b.vy-=dy*f;}}
  }}
  for (const e of visibleEdges()) {{
    const a=e.source,b=e.target; let dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1; let target=120, f=(d-target)*0.008; dx/=d; dy/=d;
    if(!a.pinned){{a.vx+=dx*f; a.vy+=dy*f;}} if(!b.pinned){{b.vx-=dx*f; b.vy-=dy*f;}}
  }}
  const cx=(width/2-ox)/scale, cy=(height/2-oy)/scale;
  for (const n of vs) {{ if(!n.pinned){{ n.vx += (cx-n.x)*0.002; n.vy += (cy-n.y)*0.002; n.x += n.vx; n.y += n.vy; }} }}
}}
function drawArrow(a,b,color) {{
  const sa=screen(a), sb=screen(b); const dx=sb.x-sa.x, dy=sb.y-sa.y, d=Math.sqrt(dx*dx+dy*dy)||1; const ux=dx/d, uy=dy/d;
  const endX=sb.x-ux*(b.r*scale+4), endY=sb.y-uy*(b.r*scale+4);
  ctx.strokeStyle=color; ctx.lineWidth=1; ctx.beginPath(); ctx.moveTo(sa.x,sa.y); ctx.lineTo(endX,endY); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(endX,endY); ctx.lineTo(endX-ux*9-uy*5,endY-uy*9+ux*5); ctx.lineTo(endX-ux*9+uy*5,endY-uy*9-ux*5); ctx.closePath(); ctx.fillStyle=color; ctx.fill();
}}
function draw() {{
  ctx.clearRect(0,0,width,height);
  for (const e of visibleEdges()) drawArrow(e.source,e.target, selected && (e.source===selected||e.target===selected) ? '#7dd3fc' : 'rgba(148,163,184,.45)');
  for (const n of visibleNodes()) {{
    const p=screen(n); const color=palette[n.type]||'#94a3b8';
    ctx.beginPath(); ctx.arc(p.x,p.y,Math.max(4,n.r*scale),0,Math.PI*2); ctx.fillStyle=color; ctx.fill();
    ctx.lineWidth = n===selected ? 4 : n===hover ? 3 : 1.5; ctx.strokeStyle = n===selected ? '#fff' : n===hover ? '#bae6fd' : '#020617'; ctx.stroke();
    if (scale > .55 || n===selected || n===hover) {{ ctx.fillStyle='#e5e7eb'; ctx.font='12px system-ui'; ctx.fillText(n.title || n.id, p.x + n.r*scale + 5, p.y + 4); }}
  }}
}}
function loop() {{ tick(); draw(); requestAnimationFrame(loop); }}
function fit() {{
  const vs=visibleNodes(); if(!vs.length) return; let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
  for(const n of vs){{minX=Math.min(minX,n.x);minY=Math.min(minY,n.y);maxX=Math.max(maxX,n.x);maxY=Math.max(maxY,n.y);}}
  const gw=Math.max(1,maxX-minX), gh=Math.max(1,maxY-minY); scale=Math.min(2.2, Math.max(.25, .82*Math.min(width/gw,height/gh))); ox=width/2-((minX+maxX)/2)*scale; oy=height/2-((minY+maxY)/2)*scale;
}}
function pick(x,y) {{
  for(const n of visibleNodes().slice().reverse()) {{ const p=screen(n), r=Math.max(6,n.r*scale); if((p.x-x)**2+(p.y-y)**2 <= r*r) return n; }} return null;
}}
function applyFilters() {{
  const q=document.getElementById('search').value.trim().toLowerCase(); const typ=document.getElementById('typeFilter').value;
  for(const n of nodes) {{ const hay=[n.id,n.title,n.description,n.type,(n.tags||[]).join(' ')].join(' ').toLowerCase(); n.visible=(!q||hay.includes(q))&&(!typ||n.type===typ); }}
  renderList(); updateStats(); if(selected && !selected.visible) select(null);
}}
function select(n) {{ selected=n; renderDetail(); renderList(); }}
function escape(s) {{ return String(s||'').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function mdLinksToHtml(text) {{ return escape(text).replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2">$1</a>'); }}
function renderDetail() {{
  const el=document.getElementById('detail'); if(!selected) {{ el.innerHTML='<p class="empty">Select a concept node to inspect frontmatter, body preview, outgoing links, and backlinks.</p>'; return; }}
  const outgoing=edges.filter(e=>e.source===selected).map(e=>e.target); const incoming=edges.filter(e=>e.target===selected).map(e=>e.source);
  el.innerHTML=`<h2>${{escape(selected.title)}}</h2><div class="id">${{escape(selected.id)}}</div><p>${{escape(selected.description)}}</p><p><span class="badge">${{escape(selected.type)}}</span>${{(selected.tags||[]).map(t=>`<span class="badge">${{escape(t)}}</span>`).join('')}}</p>${{selected.resource?`<p><strong>Resource:</strong><br><span class="id">${{escape(selected.resource)}}</span></p>`:''}}<h3>Outgoing links</h3>${{outgoing.length?'<ul>'+outgoing.map(n=>`<li><a href="#" data-id="${{escape(n.id)}}">${{escape(n.title||n.id)}}</a></li>`).join('')+'</ul>':'<p class="empty">None</p>'}}<h3>Backlinks</h3>${{incoming.length?'<ul>'+incoming.map(n=>`<li><a href="#" data-id="${{escape(n.id)}}">${{escape(n.title||n.id)}}</a></li>`).join('')+'</ul>':'<p class="empty">None</p>'}}<h3>Body preview</h3><pre>${{escape((selected.body||'').slice(0,2500))}}</pre>`;
  el.querySelectorAll('a[data-id]').forEach(a=>a.addEventListener('click', ev=>{{ ev.preventDefault(); const n=byId.get(a.dataset.id); if(n) select(n); }}));
}}
function renderList() {{
  const el=document.getElementById('nodeList'); const vs=visibleNodes();
  el.innerHTML = `<strong>${{vs.length}} visible concepts</strong>` + vs.slice(0,300).map(n=>`<div class="node-row ${{n===selected?'active':''}}" data-id="${{escape(n.id)}}">${{escape(n.title||n.id)}}<br><small>${{escape(n.type)}}</small></div>`).join('');
  el.querySelectorAll('.node-row').forEach(row=>row.addEventListener('click',()=>{{ const n=byId.get(row.dataset.id); if(n) select(n); }}));
}}
function updateStats() {{ document.getElementById('stats').textContent = `${{visibleNodes().length}}/${{nodes.length}} concepts · ${{visibleEdges().length}}/${{edges.length}} links · ${{bundle.types.length}} types`; }}
function initUi() {{
  document.getElementById('stats').textContent='';
  const typeFilter=document.getElementById('typeFilter'); for(const t of bundle.types) typeFilter.insertAdjacentHTML('beforeend', `<option value="${{escape(t)}}">${{escape(t)}}</option>`);
  document.getElementById('legend').innerHTML=bundle.types.map(t=>`<div class="legend-item"><span class="swatch" style="background:${{palette[t]||'#94a3b8'}}"></span>${{escape(t)}}</div>`).join('');
  document.getElementById('search').addEventListener('input', applyFilters); typeFilter.addEventListener('change', applyFilters);
  document.getElementById('fitBtn').onclick=fit; document.getElementById('pinBtn').onclick=()=>nodes.forEach(n=>n.pinned=false);
  document.getElementById('zoomIn').onclick=()=>{{scale*=1.2;}}; document.getElementById('zoomOut').onclick=()=>{{scale/=1.2;}}; document.getElementById('resetZoom').onclick=()=>{{scale=1;ox=0;oy=0;fit();}};
  canvas.addEventListener('mousedown', e=>{{ last={{x:e.clientX,y:e.clientY}}; const n=pick(e.offsetX,e.offsetY); if(n){{dragging=n;n.pinned=true;select(n);}} else panning=true; }});
  window.addEventListener('mousemove', e=>{{ const rect=canvas.getBoundingClientRect(); const x=e.clientX-rect.left, y=e.clientY-rect.top; hover=pick(x,y); if(dragging){{ const w=world(x,y); dragging.x=w.x; dragging.y=w.y; dragging.vx=dragging.vy=0; }} else if(panning){{ ox+=e.clientX-last.x; oy+=e.clientY-last.y; last={{x:e.clientX,y:e.clientY}}; }} tooltip.style.display=hover?'block':'none'; if(hover){{tooltip.style.left=(e.clientX+12)+'px';tooltip.style.top=(e.clientY+12)+'px';tooltip.textContent=hover.title+' · '+hover.type;}} }});
  window.addEventListener('mouseup',()=>{{dragging=null;panning=false;}});
  canvas.addEventListener('dblclick', e=>{{ const n=pick(e.offsetX,e.offsetY); if(n){{n.pinned=false;}} }});
  canvas.addEventListener('wheel', e=>{{ e.preventDefault(); const before=world(e.offsetX,e.offsetY); const factor=e.deltaY<0?1.12:.89; scale=Math.max(.1,Math.min(5,scale*factor)); const after=world(e.offsetX,e.offsetY); ox+=(after.x-before.x)*scale; oy+=(after.y-before.y)*scale; }}, {{passive:false}});
  applyFilters(); fit();
}}
window.addEventListener('resize',()=>{{resize();fit();}}); resize(); initUi(); loop();
}})();
</script>
</body>
</html>
"""
