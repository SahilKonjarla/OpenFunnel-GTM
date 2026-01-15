from __future__ import annotations
import re
from rapidfuzz import process, fuzz

CANON = {
    "node": "nodejs",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "react.js": "react",
    "reactjs": "react",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "js": "javascript",
    "ts": "typescript",
}
KNOWN = sorted(set(CANON.values()) | set(CANON.keys()))

def normalize_token(t: str) -> str:
    t = t.strip().lower()
    t = re.sub(r"[^a-z0-9.+#-]+", " ", t).strip()
    if t in CANON:
        return CANON[t]
    m = process.extractOne(t, KNOWN, scorer=fuzz.WRatio)
    if m and m[1] >= 92:
        return CANON.get(m[0], m[0])
    return t

def canonicalize(skills: list[str]) -> list[str]:
    out, seen = [], set()
    for s in skills:
        n = normalize_token(s)
        if not n or len(n) < 2:
            continue
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out
