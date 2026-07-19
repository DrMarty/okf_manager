#!/usr/bin/env python3
"""Stable OKF Manager worker runner.

Use this wrapper instead of bare `python` for OKF Manager operations. It
bootstraps/reuses the plugin-local worker venv and dispatches deterministic
scripts with explicit runtimes and compact JSON output.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def worker_python(root: Path) -> Path:
    return root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(cmd: list[str], *, cwd: Path | None = None) -> int:
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    return proc.returncode


def ensure_env(root: Path, no_bootstrap: bool) -> Path:
    py = worker_python(root)
    if no_bootstrap and not py.exists():
        raise FileNotFoundError(f"worker python not found: {py}; run scripts/okf_bootstrap_env.py")
    if not no_bootstrap:
        rc = run([sys.executable, str(root / "scripts" / "okf_bootstrap_env.py")])
        if rc != 0:
            raise RuntimeError(f"worker environment bootstrap failed with exit code {rc}")
    return py


def arg_path(args, positional: str, *option_names: str) -> str:
    for name in option_names:
        val = getattr(args, name, None)
        if val:
            return str(val)
    val = getattr(args, positional, None)
    if val:
        return str(val)
    raise SystemExit(f"missing required path; provide positional {positional!r} or one of {option_names}")


def add_catalog_arg(parser: argparse.ArgumentParser, help_text: str = "Path to <okf>/catalog") -> None:
    parser.add_argument("catalog_root", nargs="?", help=help_text)
    parser.add_argument("--catalog", dest="catalog_opt", help=help_text)


def main(argv: list[str]) -> int:
    root = plugin_root()
    parser = argparse.ArgumentParser(description="Run OKF Manager deterministic worker operations")
    parser.add_argument("--no-bootstrap", action="store_true", help="Do not create/install the plugin worker venv")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan-sources", help="Inventory an unstructured source collection without assuming concept structure")
    p.add_argument("source_root", nargs="?")
    p.add_argument("--source-root", dest="source_root_opt")
    p.add_argument("--out")
    p.add_argument("--max-preview-chars", type=int, default=600)

    p = sub.add_parser("bulk-write", help="Write a JSON concept plan and optionally retain raw evidence")
    add_catalog_arg(p)
    p.add_argument("plan_json", nargs="?")
    p.add_argument("--plan", dest="plan_opt")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--source-root")
    p.add_argument("--raw-name")

    p = sub.add_parser("clean-raw", help="Remove internal/generated artifacts from sibling raw evidence")
    p.add_argument("raw_root", nargs="?")
    p.add_argument("--raw-root", dest="raw_root_opt")
    p.add_argument("--catalog", dest="catalog_opt")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("lint", help="Lint catalog and raw evidence links")
    add_catalog_arg(p)
    p.add_argument("--non-strict", action="store_true")

    p = sub.add_parser("validate", help="Validate OKF catalog")
    add_catalog_arg(p)
    p.add_argument("--non-strict", action="store_true")

    p = sub.add_parser("index", help="Regenerate catalog indexes")
    add_catalog_arg(p)

    p = sub.add_parser("visualize", help="Generate viz.html")
    add_catalog_arg(p)

    p = sub.add_parser("verify-graph", help="Verify viz.html bundle-data payload")
    p.add_argument("path", nargs="?", help="Path to viz.html or OKF catalog directory")
    p.add_argument("--path", dest="path_opt")
    p.add_argument("--catalog", dest="catalog_opt", help="Path to <okf>/catalog containing viz.html")
    p.add_argument("--min-concepts", type=int, default=0)
    p.add_argument("--min-edges", type=int, default=0)

    p = sub.add_parser("pipeline", help="Clean raw, lint, index, visualize, verify graph")
    add_catalog_arg(p)
    p.add_argument("--min-concepts", type=int, default=0)
    p.add_argument("--min-edges", type=int, default=0)

    args = parser.parse_args(argv[1:])
    py = ensure_env(root, args.no_bootstrap)
    scripts = root / "scripts"

    if args.command == "plan-sources":
        source_root = arg_path(args, "source_root", "source_root_opt")
        cmd = [str(py), str(scripts / "okf_plan_sources.py"), source_root, "--max-preview-chars", str(args.max_preview_chars)]
        if args.out:
            cmd += ["--out", args.out]
        return run(cmd)
    if args.command == "bulk-write":
        catalog_root = arg_path(args, "catalog_root", "catalog_opt")
        plan_json = arg_path(args, "plan_json", "plan_opt")
        cmd = [str(py), str(scripts / "okf_bulk_write.py"), catalog_root, plan_json]
        if args.overwrite:
            cmd.append("--overwrite")
        if args.source_root:
            cmd += ["--source-root", args.source_root]
        if args.raw_name:
            cmd += ["--raw-name", args.raw_name]
        return run(cmd)
    if args.command == "clean-raw":
        cmd = [str(py), str(scripts / "okf_clean_raw.py")]
        if args.catalog_opt:
            cmd += ["--catalog", args.catalog_opt]
        else:
            cmd.append(arg_path(args, "raw_root", "raw_root_opt"))
        if args.dry_run:
            cmd.append("--dry-run")
        return run(cmd)
    if args.command == "lint":
        catalog_root = arg_path(args, "catalog_root", "catalog_opt")
        cmd = [str(py), str(scripts / "okf_lint_catalog.py"), catalog_root]
        if args.non_strict:
            cmd.append("--non-strict")
        return run(cmd)
    if args.command == "validate":
        catalog_root = arg_path(args, "catalog_root", "catalog_opt")
        cmd = [str(py), str(scripts / "okf_validate_bundle.py"), catalog_root]
        if args.non_strict:
            cmd.append("--non-strict")
        return run(cmd)
    if args.command == "index":
        return run([str(py), str(scripts / "okf_regenerate_indexes.py"), arg_path(args, "catalog_root", "catalog_opt")])
    if args.command == "visualize":
        return run([str(py), str(scripts / "okf_visualize_bundle.py"), arg_path(args, "catalog_root", "catalog_opt")])
    if args.command == "verify-graph":
        path = args.catalog_opt or args.path_opt or args.path
        if not path:
            raise SystemExit("missing graph path; provide path, --path, or --catalog")
        return run([str(py), str(scripts / "okf_verify_graph.py"), path, "--min-concepts", str(args.min_concepts), "--min-edges", str(args.min_edges)])
    if args.command == "pipeline":
        catalog_root = arg_path(args, "catalog_root", "catalog_opt")
        steps = [
            [str(py), str(scripts / "okf_clean_raw.py"), "--catalog", catalog_root],
            [str(py), str(scripts / "okf_lint_catalog.py"), catalog_root],
            [str(py), str(scripts / "okf_regenerate_indexes.py"), catalog_root],
            [str(py), str(scripts / "okf_visualize_bundle.py"), catalog_root],
            [str(py), str(scripts / "okf_verify_graph.py"), str(Path(catalog_root) / "viz.html"), "--min-concepts", str(args.min_concepts), "--min-edges", str(args.min_edges)],
        ]
        for step in steps:
            rc = run(step)
            if rc != 0:
                print(json.dumps({"ok": False, "failed_step": step, "exit_code": rc}, indent=2))
                return rc
        print(json.dumps({"ok": True, "pipeline": "clean-raw-lint-index-visualize-verify", "catalog_root": str(Path(catalog_root).resolve())}, indent=2))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
