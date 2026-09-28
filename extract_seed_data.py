#!/usr/bin/env python3
"""Extrait P (60 proprietes) et LOTS_INIT (8 lots) depuis index.html et
genere dialibatou-backend/seed_data.json au format JSON valide."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
OUT = ROOT / "dialibatou-backend" / "seed_data.json"


def extract_array(source: str, name: str) -> list:
    start = source.index(f"const {name}=[")
    i = source.index("[", start)
    depth = 0
    for j in range(i, len(source)):
        c = source[j]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                raw = source[i : j + 1]
                break
    else:
        raise ValueError(f"Array {name} non trouve")
    # Supprime les virgules finales autorisees en JS mais pas en JSON
    raw = re.sub(r",(\s*[\]\}])", r"\1", raw)
    # Guillemetage des cles d'objets non quoted en JS ({id:"p1"} -> {"id":"p1"})
    raw = re.sub(r"([{,\[]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)", r'\1"\2"\3', raw)
    return json.loads(raw)


properties = extract_array(HTML, "P")
lots = extract_array(HTML, "LOTS_INIT")
print(f"Proprietes extraites : {len(properties)}")
print(f"Lots extraits        : {len(lots)}")
assert len(properties) == 60, "Attendu 60 proprietes"
assert len(lots) == 8, "Attendu 8 lots"

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps({"properties": properties, "lots": lots}, ensure_ascii=False, indent=1),
    encoding="utf-8",
)
print(f"Ecrit : {OUT}")
