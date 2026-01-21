from __future__ import annotations
import re
from rapidfuzz import fuzz, process

# Canonical mapping for common aliases / misspellings -> normalized skill name.
# This helps deduplicate skill lists and improve downstream filtering/search.
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

# Candidate vocabulary for fuzzy matching:
# - keys: raw aliases
# - values: canonical outputs
KNOWN = sorted(set(CANON.values()) | set(CANON.keys()))

def normalize_token(t: str) -> str:
    """
    Normalize a single skill token into a canonical form.

    Steps:
    1) Lowercase + trim whitespace
    2) Remove unwanted characters (keep letters, digits, + . # -)
    3) Apply exact canonical mapping (CANON)
    4) Otherwise use fuzzy matching against known tokens and canonical forms

    Args:
        t: Raw skill token (e.g. "Node.js", "Amazon Web Services", "K8S").

    Returns:
        Canonicalized token (e.g. "nodejs", "aws", "kubernetes").
        If no confident match exists, returns the cleaned token as-is.
    """
    # Normalize casing + whitespace.
    t = t.strip().lower()

    # Replace non-allowed characters with spaces to reduce noise.
    # Keeps common tech chars like: c++, node.js, c#, etc.
    t = re.sub(r"[^a-z0-9.+#-]+", " ", t).strip()

    # Exact canonical mapping.
    if t in CANON:
        return CANON[t]

    # Fuzzy match against known tokens.
    # extractOne returns (match, score, index) or None.
    m = process.extractOne(t, KNOWN, scorer=fuzz.WRatio)

    # Only accept high-confidence fuzzy matches to avoid bad merges.
    if m and m[1] >= 92:
        # If the matched token is an alias, map it to canonical form.
        # If it's already canonical, return it directly.
        return CANON.get(m[0], m[0])

    # No match: return cleaned token.
    return t

def canonicalize(skills: list[str]) -> list[str]:
    """
    Canonicalize and deduplicate a list of skills.

    - Normalizes each token
    - Drops empty / too-short tokens
    - Preserves original order (first occurrence wins)
    - Removes duplicates

    Args:
        skills: List of raw skill tokens.

    Returns:
        A cleaned, canonicalized, deduplicated list of skills.
    """
    out: list[str] = []
    seen: set[str] = set()

    for s in skills:
        n = normalize_token(s)

        # Skip empty or extremely short tokens (noise).
        if not n or len(n) < 2:
            continue

        # Deduplicate while preserving order.
        if n not in seen:
            seen.add(n)
            out.append(n)

    return out
