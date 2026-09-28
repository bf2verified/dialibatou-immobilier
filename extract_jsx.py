#!/usr/bin/env python3
"""Extrait le script babel de index.html vers _check.jsx pour validation esbuild."""
import re
from pathlib import Path

html = Path(__file__).resolve().parent / "index.html"
src = html.read_text(encoding="utf-8")
m = re.search(r'<script type="text/babel">(.*?)</script>', src, re.S)
if not m:
    raise SystemExit("script text/babel introuvable")
Path("_check.jsx").write_text(m.group(1), encoding="utf-8")
print(f"script extrait : {len(m.group(1))} caracteres")
