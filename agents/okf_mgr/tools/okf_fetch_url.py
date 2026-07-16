from __future__ import annotations

import json, re
from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen
from helpers.tool import Tool, Response

_MAX_MARKDOWN_BYTES = 40 * 1024
_HREF_RE = re.compile(r'''href\s*=\s*["']([^"'#\s]+)["']''', re.I)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I|re.S)

class OkfFetchUrl(Tool):
    """Fetch one web page as markdown plus outbound links with reference-agent-like crawl guards."""
    async def execute(self, **kwargs):
        url = self.args.get("url")
        if not url: return Response(message="url is required", break_loop=False)
        state = self.agent.get_data("okf_web_state") or {}
        if self.args.get("reset_state"):
            state = {}
        seeds = self.args.get("seeds") or state.get("seeds") or [url]
        allowed_hosts = set(self.args.get("allowed_hosts") or state.get("allowed_hosts") or [urlparse(s).netloc for s in seeds if urlparse(s).netloc])
        max_pages = int(self.args.get("max_pages") or state.get("max_pages") or 100)
        max_depth = int(self.args.get("max_depth") or state.get("max_depth") or 2)
        prefixes = tuple(self.args.get("allowed_path_prefixes") or state.get("allowed_path_prefixes") or ())
        denied = tuple(self.args.get("denied_path_substrings") or state.get("denied_path_substrings") or ())
        visited = set(state.get("visited") or [])
        depth = dict(state.get("url_depth") or {s:0 for s in seeds})
        fetched = int(state.get("fetched_count") or 0)
        parsed = urlparse(url); path = parsed.path or "/"
        def reject(reason):
            return Response(message=json.dumps({"error": reason, "url": url, "fetched_count": fetched, "max_pages_budget": max_pages}, indent=2), break_loop=False)
        if parsed.scheme not in ("http","https"): return reject(f"unsupported scheme: {parsed.scheme or '(none)'}")
        if allowed_hosts and parsed.netloc not in allowed_hosts: return reject(f"host not in allowed list: {parsed.netloc} (allowed: {sorted(allowed_hosts)})")
        if prefixes and not any(path.startswith(p) for p in prefixes): return reject(f"path not in allowed prefixes: {path} (allowed: {list(prefixes)})")
        for bad in denied:
            if bad and bad in path: return reject(f"path matches denied substring: {bad!r}")
        if url in visited: return reject("already fetched in this session")
        if fetched >= max_pages: return reject("max_pages reached")
        if url not in depth: return reject("URL not reachable from a seed within the crawl graph")
        if depth[url] > max_depth: return reject(f"depth {depth[url]} exceeds max_depth {max_depth}")
        try:
            page = _fetch(url)
        except Exception as e:
            return reject(f"fetch failed: {e}")
        visited.add(url); fetched += 1
        for link in page["links"]: depth.setdefault(link, depth[url]+1)
        state = {"seeds": seeds, "allowed_hosts": sorted(allowed_hosts), "max_pages": max_pages, "max_depth": max_depth, "allowed_path_prefixes": list(prefixes), "denied_path_substrings": list(denied), "visited": sorted(visited), "fetched_count": fetched, "url_depth": depth}
        self.agent.set_data("okf_web_state", state)
        page.update({"fetched_count": fetched, "max_pages_budget": max_pages, "depth": depth[url], "max_depth": max_depth})
        return Response(message=json.dumps(page, indent=2, ensure_ascii=False), break_loop=False)

def _fetch(url):
    req = Request(url, headers={"User-Agent":"okf_mgr/0.1 (+https://github.com/GoogleCloudPlatform/knowledge-catalog)", "Accept":"text/html,*/*;q=0.5"})
    with urlopen(req, timeout=10) as resp:
        ctype = resp.headers.get("Content-Type", "")
        final = resp.geturl() or url
        body = resp.read()
    if "html" not in ctype.lower(): raise ValueError(f"non-HTML content-type: {ctype or 'unknown'}")
    html = body.decode("utf-8", errors="replace")
    title = None
    m = _TITLE_RE.search(html)
    if m: title = re.sub(r"\s+", " ", m.group(1)).strip() or None
    links=[]; seen=set()
    for m in _HREF_RE.finditer(html):
        href=m.group(1).strip(); scheme=urlparse(href).scheme.lower()
        if scheme and scheme not in ("http","https",""): continue
        absolute,_=urldefrag(urljoin(final, href))
        if absolute not in seen: seen.add(absolute); links.append(absolute)
    try:
        from markdownify import markdownify
        markdown = markdownify(html, heading_style="ATX")
    except Exception:
        markdown = re.sub(r"<[^>]+>", " ", html)
    enc=markdown.encode("utf-8", errors="replace")
    if len(enc)>_MAX_MARKDOWN_BYTES:
        markdown=enc[:_MAX_MARKDOWN_BYTES].decode("utf-8", errors="ignore")+"\n\n[...truncated...]"
    return {"url": final, "title": title, "markdown": markdown, "links": links}
