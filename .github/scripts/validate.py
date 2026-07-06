#!/usr/bin/env python3
"""Site validation: JSON-LD syntax, internal links, sitemap consistency,
and service-worker precache list. Run from the repo root."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://bros-ai.github.io/pdf-text-extractor/"
errors = []

html_files = sorted(ROOT.glob("*.html"))

# 1. Every JSON-LD block must parse
for f in html_files:
    html = f.read_text(encoding="utf8")
    for i, block in enumerate(re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S)):
        try:
            json.loads(block)
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: JSON-LD block {i} invalid: {e}")

# 2. Internal links and asset references must resolve to real files
for f in html_files:
    html = f.read_text(encoding="utf8")
    for target in re.findall(r'(?:href|src)="([^"]+)"', html):
        if target.startswith(("http://", "https://", "data:", "mailto:", "#", "//")):
            continue
        path = target.split("#")[0].split("?")[0]
        # Site-absolute paths resolve against the GitHub Pages base path
        if path.startswith("/pdf-text-extractor/"):
            path = path[len("/pdf-text-extractor/"):]
        if not path or path == "./":
            continue
        if not (ROOT / path).exists():
            errors.append(f"{f.name}: broken internal reference: {target}")

# 3. Every sitemap URL must map to an existing file
sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf8")
for loc in re.findall(r"<loc>(.*?)</loc>", sitemap):
    if not loc.startswith(BASE_URL):
        errors.append(f"sitemap.xml: URL outside site: {loc}")
        continue
    rel = loc[len(BASE_URL):]
    if rel and not (ROOT / rel).exists():
        errors.append(f"sitemap.xml: URL has no matching file: {loc}")

# 4. Every service-worker precache entry must exist
sw = (ROOT / "sw.js").read_text(encoding="utf8")
precache_block = re.search(r"const PRECACHE = \[(.*?)\];", sw, re.S)
if precache_block:
    for entry in re.findall(r'"([^"]+)"', precache_block.group(1)):
        if entry != "./" and not (ROOT / entry).exists():
            errors.append(f"sw.js: precache entry missing on disk: {entry}")
else:
    errors.append("sw.js: PRECACHE list not found")

if errors:
    print(f"FAILED — {len(errors)} problem(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"OK — {len(html_files)} HTML files validated (JSON-LD, links, sitemap, SW precache)")
