#!/usr/bin/env python3
"""Scan the project for spec-implement: existing spec files, test runners, missing harnesses.

Usage: scan-project.py --spec PATH [--root DIR] [--require PATH ...]

  --spec     technical-spec.md; backticked file or directory paths in it are checked on disk
             (a heuristic: treat 'missing' as a hint, the phase plan is still your call)
  --root     project root, default the current directory
  --require  paths that must exist (prerequisites of a phase); status=missing if any do not

Output is one JSON object on stdout:
  {"status": "ok"|"missing", "existing": [...], "missing": [...],
   "layers": {"<dir>": {"manifest": "...", "runner": "<command>"|null}},
   "no_harness": ["<dir>", ...], "required_missing": [...]}
A layer is a directory (the root or a direct subdirectory) holding a build manifest.
Errors: status=error/message=/hint= on stdout, exit 2.
"""
import argparse
import json
import os
import re

import speclog as S

PATH_TOKEN = re.compile(r"`([^`\s]+)`")
LOOKS_LIKE_PATH = re.compile(r"(/|\.[A-Za-z0-9]{1,6}$)")
SKIP_DIRS = {"node_modules", "target", "dist", "build", "venv", "__pycache__"}


def spec_paths(text):
    seen = []
    for tok in PATH_TOKEN.findall(text):
        tok = tok.strip().rstrip(",.;:")
        if "://" in tok or tok.startswith(("-", "$", "~", "@")) or "*" in tok or "<" in tok:
            continue
        if LOOKS_LIKE_PATH.search(tok) and tok not in seen:
            seen.append(tok)
    return seen


def contains(path, needle):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return needle in f.read()
    except OSError:
        return False


def layer(d):
    """(manifest, runner) for a directory, or None if it holds no build manifest."""
    def has(name):
        return os.path.isfile(os.path.join(d, name))

    if has("package.json"):
        try:
            with open(os.path.join(d, "package.json"), encoding="utf-8") as f:
                pkg = json.load(f)
        except (OSError, json.JSONDecodeError):
            pkg = {}
        deps = {**pkg.get("devDependencies", {}), **pkg.get("dependencies", {})}
        if "vitest" in deps:
            return "package.json", "npx vitest run"
        return "package.json", "npm test" if pkg.get("scripts", {}).get("test") else None
    if has("pyproject.toml") or has("pytest.ini") or has("setup.cfg"):
        manifest = "pyproject.toml" if has("pyproject.toml") else "pytest.ini" if has("pytest.ini") else "setup.cfg"
        pytest = has("pytest.ini") or any(contains(os.path.join(d, n), "pytest") for n in ("pyproject.toml", "setup.cfg"))
        return manifest, "pytest" if pytest else None
    if has("Cargo.toml"):
        return "Cargo.toml", "cargo test"
    if has("go.mod"):
        return "go.mod", "go test ./..."
    if has("build.zig"):
        return "build.zig", "zig build test" if contains(os.path.join(d, "build.zig"), '"test"') else None
    if has("pom.xml"):
        return "pom.xml", "mvn test"
    for g in ("build.gradle", "build.gradle.kts"):
        if has(g):
            return g, "./gradlew test"
    if has("Gemfile"):
        return "Gemfile", "bundle exec rspec" if contains(os.path.join(d, "Gemfile"), "rspec") else None
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--spec", required=True)
    p.add_argument("--root", default=".")
    p.add_argument("--require", action="append", default=[])
    a = p.parse_args()

    root = os.path.abspath(a.root)
    spec_text = S.read(a.spec)
    existing, missing = [], []
    for rel in spec_paths(spec_text):
        (existing if os.path.exists(os.path.join(root, rel)) else missing).append(rel)

    layers, no_harness = {}, []
    dirs = [root] + sorted(
        os.path.join(root, n) for n in os.listdir(root)
        if os.path.isdir(os.path.join(root, n)) and not n.startswith(".") and n not in SKIP_DIRS)
    for d in dirs:
        found = layer(d)
        if found:
            name = os.path.relpath(d, root)
            layers[name] = {"manifest": found[0], "runner": found[1]}
            if found[1] is None:
                no_harness.append(name)

    required_missing = [r for r in a.require if not os.path.exists(os.path.join(root, r))]
    print(json.dumps({"status": "missing" if required_missing else "ok", "existing": existing,
                      "missing": missing, "layers": layers, "no_harness": no_harness,
                      "required_missing": required_missing}, indent=2))


if __name__ == "__main__":
    main()
