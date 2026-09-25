"""Put back the spaces the book's PDF tables lost in published risk text.

pdfplumber reads Buku Kerawanan's narrow justified cells at a 3 pt word gap
and glues words whose gap is narrower ("Kesugihandengan", "JangkaMenengah").
At 1.5 pt it separates them, but it also splits some words the PDF stretched
letter by letter ("pemeliha raan"). Neither read is the book.

So this re-reads each published fixture's own table at both gaps and, token
by token, adds a space only where the tighter read has one AND every piece it
leaves is a word the book itself uses standing alone (or a number, a unit, an
acronym). It only ever adds spaces between the same letters: a cell whose
letters differ from the book at all -- hand-edited, reviewed, merged -- is
left exactly as it is, so a reviewed workbook can gain spaces, never lose an
edit. Everything it declines is reported.

    python scripts/respace_risk_text.py            # dry run: what would change
    python scripts/respace_risk_text.py --write    # rewrite the fixtures
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

from _kerawanan_sections import FIXTURES, SECTIONS, SYSTEM_TABLES
from _kerawanan_tables import risk_rows

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"
TEXT_COLS = ("Kondisi / Permasalahan", "Dampak", "Mitigasi", "Usulan / Solusi")
JSON_FIELDS = ("title", "condition", "impact", "mitigation", "follow_up")
SHORT_WORDS = {"di", "ke"}          # the only 1-2 letter lowercase words trusted
_TAG = re.compile(r"^(\s*\[[^\]]*\]\s*)")
_LETTERS = re.compile(r"[A-Za-z]+")


def sources() -> dict[str, tuple[int, int]]:
    """Published fixture -> the book pages its risk table was read from."""
    pages = {sec: rng for _label, sec, _fig, rng, _n in SECTIONS}
    out = {fx: pages[sec] for sec, fx in FIXTURES.items() if not fx.startswith("seed_")}
    out.update({fx: rng for _label, rng, _n, fx in SYSTEM_TABLES
                if fx and fx.endswith((".xlsx", ".json")) and not fx.startswith("system_tables")})
    return out


def _nospace(text: str) -> tuple[str, list[int]]:
    idx = [i for i, ch in enumerate(text) if not ch.isspace()]
    return "".join(text[i] for i in idx), idx


class Respacer:
    def __init__(self, loose: list[str], tight: list[str]):
        # the book's own words: tokens the 3 pt read already stands alone
        self.vocab = Counter(w.lower() for text in loose for w in _LETTERS.findall(text))
        self.tight = tight
        self.declined: Counter = Counter()

    def piece_ok(self, piece: str) -> bool:
        core = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", piece)
        if not core or re.search(r"\d", core):
            return True                       # numbers, "1.", "(RUPTL" -> fine
        if not core.isalpha():
            return all(self.piece_ok(p) for p in re.split(r"[^A-Za-z0-9]+", core) if p)
        if core.isupper():
            return True                       # MW, GI, SUTT, N
        if core in ("kV", "kA", "MVA", "MVAR", "MVAr", "Mvar"):
            return True
        low = core.lower()
        if len(low) <= 2:
            return low in SHORT_WORDS
        return self.vocab[low] >= 2

    def token(self, tok: str, breaks: list[int]) -> str:
        """Best way to cut one glued token at some of `breaks` (offsets)."""
        options = []
        for k in range(1, len(breaks) + 1):
            for cut in itertools.combinations(breaks, k):
                bounds = [0, *cut, len(tok)]
                pieces = [tok[a:b] for a, b in zip(bounds, bounds[1:])]
                # a capital right after a lowercase letter is glue in itself
                # ("PenambahanBattery"): a real word of 3+ letters there
                # needs no second sighting in the book
                if all(self.piece_ok(p) or (a and tok[a - 1].islower() and tok[a].isupper()
                                            and p.rstrip(".,;:)").isalpha() and len(p) >= 3)
                       for a, p in zip(bounds, pieces)):
                    options.append(pieces)
        if not options:
            self.declined[tok] += 1
            return tok
        best = min(options, key=len)
        # a whole token the book uses on its own stays whole, unless the cut
        # falls on a glue signal (lower->Upper, letter<->digit)
        camel = any(re.search(r"[a-z][A-Z]|[A-Za-z]\d|\d[A-Za-z]", tok[max(0, c - 1):c + 1])
                    for c in breaks)
        if not camel and self.piece_ok(tok) and self.vocab[tok.lower()] >= 3:
            return tok
        return " ".join(best)

    def fix(self, text: str | None) -> str | None:
        if not isinstance(text, str) or not text.strip():
            return None
        m = _TAG.match(text)
        prefix = m.group(1) if m else ""
        body = text[len(prefix):]
        key, key_idx = _nospace(body)
        if len(key) < 8:
            return None
        for cand in self.tight:
            cand_ns, cand_idx = _nospace(cand)
            at = cand_ns.find(key)
            if at < 0:
                continue
            # break offsets in `body`: a space in the tight read, none in body
            breaks_at = set()
            for n in range(1, len(key)):
                bi, bj = key_idx[n - 1], key_idx[n]
                ci, cj = cand_idx[at + n - 1], cand_idx[at + n]
                if bj == bi + 1 and cj > ci + 1:
                    breaks_at.add(bj)
            if not breaks_at:
                return None
            out, pos = [], 0
            for tm in re.finditer(r"\S+", body):
                out.append(body[pos:tm.start()])
                inner = sorted(b - tm.start() for b in breaks_at if tm.start() < b < tm.end())
                out.append(self.token(tm.group(), inner) if inner else tm.group())
                pos = tm.end()
            out.append(body[pos:])
            fixed = prefix + "".join(out)
            assert _nospace(fixed)[0] == _nospace(text)[0]     # letters untouched
            return fixed if fixed != text else None
        return None


def main(write: bool) -> None:
    srcs = sources()
    read: dict[tuple[int, int], tuple[list[str], list[str]]] = {}
    for rng in sorted(set(srcs.values())):
        loose = [f for row in risk_rows(*rng, x_tolerance=3) for f in row[2:6]]
        tight = [f for row in risk_rows(*rng, x_tolerance=1.5) for f in row[2:6]]
        read[rng] = (loose, tight)
    all_loose = [t for loose, _ in read.values() for t in loose]

    total, samples = Counter(), []
    declined = Counter()
    for fx, rng in sorted(srcs.items()):
        rs = Respacer(all_loose, read[rng][1])
        path = SAMPLES / fx
        changed = 0
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            for risk in data["risks"]:
                for field in JSON_FIELDS:
                    new = rs.fix(risk.get(field))
                    if new:
                        samples.append((fx, risk.get(field), new))
                        risk[field] = new
                        changed += 1
            if write and changed:
                # the file's own layout: indent 2, UTF-8, no trailing newline
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            wb = openpyxl.load_workbook(path)
            ws = wb["Data_Kerawanan_Detail"]
            header = [c.value for c in ws[1]]
            cols = [header.index(h) + 1 for h in TEXT_COLS if h in header]
            for row in ws.iter_rows(min_row=2):
                for col in cols:
                    cell = row[col - 1]
                    new = rs.fix(cell.value)
                    if new:
                        samples.append((fx, cell.value, new))
                        cell.value = new
                        changed += 1
            if write and changed:
                wb.save(path)
        total[fx] = changed
        declined.update(rs.declined)
    for fx, n in total.most_common():
        print(f"{n:4} cells  {fx}")
    print(f"{sum(total.values())} cells respaced in {sum(1 for n in total.values() if n)} fixtures"
          f"{'' if write else ' (dry run)'}")
    print(f"{sum(declined.values())} glued tokens left as they are (no split the book's words support):")
    print("   " + ", ".join(t for t, _ in declined.most_common(40)))
    out = ROOT / "tmp" / "respace_report.txt"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for fx, old, new in samples:
            fh.write(f"## {fx}\n- {old}\n+ {new}\n\n")
        fh.write("\nDECLINED\n" + "\n".join(f"{t}\t{n}" for t, n in declined.most_common()))
    print(f"diff -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main("--write" in sys.argv)
