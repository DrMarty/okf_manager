### okf_visualize_bundle:
Generate a **live D3/SVG self-graph** HTML artifact for an OKF bundle. The graph data is embedded in `viz.html`, while rendering intentionally loads D3 from `https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js` for stable force-graph layout and resizing.

The output embeds bundle data and browser-side JavaScript in a single `viz.html` file. It supports an interactive force-directed canvas graph, search, type filtering, zoom/pan, draggable/pinnable nodes, clickable concept details, outgoing links, backlinks, body previews, and type legend coloring.

Args: optional `bundle_root`, optional `out` path.

Verification: after generation, parse the embedded `<script id="bundle-data" type="application/json">` payload, or use `scripts/okf_verify_graph.py`, and report exact concept, edge, and type counts. Do not treat file existence or file size alone as graph verification.

Use this after validating or indexing a bundle when the user wants to browse relationships visually without a backend service.

When the user asks to **see**, **show me**, **graph**, **visualize**, or visually inspect the knowledge catalog, generate or refresh the `viz.html` artifact with this tool and then open the generated file as a live page in the Agent Zero Browser using the `browser` tool, preferably with `action: "open"` or `action: "navigate"` and a `file://` URL for the absolute artifact path. Open or activate the Browser tab displaying the live self-view when possible, but do not claim you can definitively force or detect whether the Agent Zero Browser side panel is visible in the user's GUI. Report the full path after loading it.

In the final user-facing response, include this notice exactly or with equivalent wording: "The live self-graph has been loaded in the Agent Zero Browser. If you do not see it, please open the Browser tab/panel manually."

Do **not** satisfy visualization requests by taking or returning a screenshot, static image, or screenshot-only preview. Screenshots may be used only as optional diagnostics after the live Browser page has been opened or loaded.
