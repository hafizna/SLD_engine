"""Which GIs a kerawanan's own text names -- the book-side of its scope.

A risk's pin marks where the finding sits. What it puts at risk comes from two
places, and the viewer shows both, styled apart:
  * the topology (computed in the viewer, N-1 terms), and
  * the GIs the book's Dampak text names, found here.

Matching is on names, conservatively: a name must stand as whole words, the
longest name wins where two overlap ("Priok Timur Baru" is not also "Priok
Timur"), and subsystem names are cut out first so "Subsistem Bekasi 2,4-Cawang
1-Priok" does not light up three GIs that are merely in the subsystem's title.
"""
from __future__ import annotations

import re

# Words that describe a node rather than name it.
_TYPE_WORDS = r"(?:gitet|gis|gi|gardu induk|pltu/g|pltu|plta|pltg|pltgu|pltp|pltmg|pltd|plts|pltmg/g|pltg/mg)"
_PAREN = re.compile(r"\([^)]*\)")
_SPACE = re.compile(r"[\s\-_/]+")
# "Subsistem X", "Sub Sistem X", "SS X": the run of capitalised words, digit
# groups and joining hyphens/commas that make up a subsystem's title.
_SUBSYSTEM = re.compile(
    r"(?:(?i:\bsub\s*sistem)|\bSS)\s+"
    r"(?:(?:[A-Z][\w.&']*|\d+(?:\s*,\s*\d+)*)(?:\s*-\s*|\s+|$))+")


def _norm(s: str) -> str:
    return _SPACE.sub(" ", s.lower()).strip()


def name_variants(name: str | None, code: str | None = None) -> set[str]:
    """The spellings a GI goes by in running text: its name without the
    bracketed qualifier, and without a leading type word."""
    out: set[str] = set()
    if name:
        base = _norm(_PAREN.sub(" ", name))
        if base:
            out.add(base)
            bare = re.sub(rf"^{_TYPE_WORDS}\s+", "", base)
            if bare:
                out.add(bare)
    # the display code, when it is a real word-length token (ARUN, NADRI)
    if code:
        c = re.sub(r"(?:_\d+|@[A-Z]+)$", "", code).lower()
        if len(c) >= 4 and c.isalpha():
            out.add(c)
    return {v for v in out if len(v) >= 4}


def named_substations(text: str | None, candidates) -> list[int]:
    """ids among `candidates` ((id, code, name) tuples) whose name the text uses."""
    if not text:
        return []
    body = _norm(_SUBSYSTEM.sub(" ", text))
    by_variant: dict[str, list[int]] = {}
    for sid, code, name in candidates:
        for v in name_variants(name, code):
            by_variant.setdefault(v, []).append(sid)
    spans: list[tuple[int, int, str]] = []
    for v in by_variant:
        for m in re.finditer(rf"(?<![a-z0-9]){re.escape(v)}(?![a-z0-9])", body):
            spans.append((m.start(), m.end(), v))
    # longest first; a shorter name inside an accepted span is part of it
    spans.sort(key=lambda s: (-(s[1] - s[0]), s[0]))
    taken: list[tuple[int, int]] = []
    hits: list[int] = []
    for a, b, v in spans:
        if any(a < tb and ta < b for ta, tb in taken):
            continue
        taken.append((a, b))
        for sid in by_variant[v]:
            if sid not in hits:
                hits.append(sid)
    return hits
