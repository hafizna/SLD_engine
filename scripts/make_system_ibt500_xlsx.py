"""samples/system_ibt_500_ingest.xlsx -- Sistem 500 kV, view Kerawanan IBT 500/150.

Gambar 1.5 (PDF p.40) draws the SAME 500 kV network as the Transmisi view --
the same blue busbars, the same SUTET spans, the same tiers -- and adds one
thing: a small IBT stub hanging under each GITET that steps down to 150 kV.
It does NOT draw the 150 kV buses. So this view is the backbone topology plus
IBT stubs plus the Sec 1.5 risk pins, and the earlier copy of the backbone was
not wrong about the network, only missing the transformers.

The IBT rows are DERIVED from the subsystem workbooks rather than retyped:
every 500/150 kV bank already exists on an SS sheet with both endpoints, so
correcting a bank there corrects it here on the next run. That keeps one source
of truth and avoids a third registration of the same GITET.

How the stub is modelled:
    The template has no "transformer hanging off a bus with no far end", so the
    150 kV side is registered as a Bay on the GITET. A Bay draws as a short stub
    off the busbar, which is what Gambar 1.5 shows, and it keeps the view honest:
    the 150 kV network genuinely is not part of this drawing. The IBT's own
    identity (unit numbers, owning subsystem) rides on the bay name.

Risks:
    Sec 1.5, PDF p.41-64, 38 rows. That table has SEVEN columns -- it adds
    `Subsistem` between `UIT` and `Kondisi` -- and is organised by subsystem
    rather than by fault, so the subsystem column says which GITET each row is
    about. See `_kerawanan_tables.subsystem_rows`.

Run: python scripts/make_system_ibt500_xlsx.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from _kerawanan_tables import as_risk_dicts, subsystem_rows   # noqa: E402
from _ss_xlsx_common import build_workbook                    # noqa: E402

from app.services.ingest_parser import parse_upload           # noqa: E402

RISK_FROM, RISK_TO, RISK_COUNT = 41, 64, 38
BACKBONE = ROOT / "samples" / "backbone_500_ingest.xlsx"

# The same physical GITET is spelled differently on the backbone sheet and on
# the subsystem sheets, so an IBT bank cannot be matched to its 500 kV busbar by
# code alone. This is the concrete form of the "same GI registered twice"
# problem. Mapping is SS code -> backbone code; anything not listed matches
# after dropping a `GITET_` prefix and ensuring the 500 kV trailing `7`.
SS_TO_BACKBONE = {
    "GITET_KMBGN": "KMBNG7",     # Kembangan
    "GITET_NBRJA": "BLRJA7",     # New Balaraja -> Balaraja
    "GITET_CLBRU": "CLGON7",     # Cilegon Baru -> Cilegon
    "GITET_CWBRU": "CWANG7",     # Cawang Baru -> Cawang
    "GITET_LKBRU": "LNGKG7",     # Lengkong Baru -> Lengkong
    "GITET_MKBRU": "MKRNG7",     # Muarakarang Baru -> Muarakarang
    "MDRCN7": "MDCAN7",          # Mandirancan
    "UNGAR7": "UNGRN7",          # Ungaran
    "NGORO7": "KDIRI7",          # GITET Ngoro feeds the Kediri subsystem
    "TSBRU7": "TSMYA7",          # Tasikmalaya Baru -> Tasikmalaya
    "NTMBN7": "TMBUN7",          # New Tambun -> Tambun
    "NUBRG7": "UBRNG7",          # New Ujungberung -> Ujungberung
    "CBATU347": "CBATU7",        # Cibatu 3,4 shares the Cibatu busbar
    "CRAT37": "CRATA7",          # Cirata 3 shares the Cirata busbar
    "SRLYABR": "SRLYA7",         # Suralaya Baru -> Suralaya
    # NCKUPA (New Cikupa) is a planned GITET that the backbone sheet does not
    # carry yet, so its bank has no 500 kV busbar to hang from in this view.
}

# Sec 1.5 names each row's subsystem in prose, with the book's own spellings
# ("Kesuguhan", "Boyoli", "Tambun1,2"). Map each to the GITET code used by the
# backbone workbook, which is what this view draws.
RISK_GITET = {
    1: "SRLYA7", 2: "SRLYA7", 3: "CLGON7", 4: "KMBNG7", 5: "CWANG7", 6: "BKASI7",
    7: "MDCAN7", 8: "MDCAN7", 9: "CRATA7", 10: "CBATU7", 11: "CBATU7", 12: "DLTMS7",
    13: "BDSLN7", 14: "UBRNG7", 15: "TSMYA7", 16: "TMBUN7",
    17: "TJATI7", 18: "TJATI7", 19: "TJATI7", 20: "TJATI7",
    21: "UNGRN7", 22: "UNGRN7", 23: "PEDAN7", 24: "PEDAN7", 25: "PEDAN7",
    26: "KSGHN7", 27: "PMLNG7", 28: "BYOLI7", 29: "BYOLI7",
    30: "GRSIK7", 31: "GRSIK7", 32: "KRIAN7", 33: "NBANG7",
    34: "KDIRI7", 35: "KDIRI7", 36: "GRATI7", 37: "PITON7", 38: "PITON7",
}


def backbone_spec() -> tuple[list[dict], list[dict]]:
    """Read the 500 kV network this view shares with the Transmisi view."""
    parsed = parse_upload(BACKBONE.read_bytes(), BACKBONE.name)
    name = {o["external_key"]: (o.get("site_name") or o["raw_label"])
            for o in parsed["objects"]}
    tier = {o["external_key"]: o.get("tier_hint") for o in parsed["objects"]}
    outlet = {o["external_key"]: o.get("outlet_key") for o in parsed["objects"]}

    assets: list[dict] = []
    for o in parsed["objects"]:
        key = o["external_key"]
        if o["object_type"] == "GENERATING_UNIT":
            assets.append(dict(code=key, name=name[key], type="Pembangkit",
                               tier=tier[key] or 1, kv="500 kV"))
        else:
            assets.append(dict(code=key, name=name[key], type="Busbar GITET",
                               tier=tier[key] or 1, kv="500 kV"))

    lines: list[dict] = []
    for c in parsed["connections"]:
        a, b = c["from_external_key"], c["to_external_key"]
        lines.append(dict(fr=a, to=b,
                          name=f"SUTET 500 kV {name.get(a, a)} - {name.get(b, b)}",
                          kv=500, tier_fr=tier.get(a), tier_to=tier.get(b),
                          sirkit=c.get("circuit_count") or 2,
                          status="Beroperasi", koridor="Jawa-Madura-Bali"))
    # Generator outlets are carried as `outlet_key` on the unit, not as a
    # connection row, so re-create them here.
    for key, feed in outlet.items():
        if feed:
            lines.append(dict(fr=key, to=feed, name=f"Outlet {name.get(key, key)}",
                              kv=500, tier_fr=tier.get(key), tier_to=tier.get(feed),
                              sirkit=1, status="Beroperasi",
                              koridor="Jawa-Madura-Bali"))
    return assets, lines


def ibt_bays() -> list[tuple]:
    """One stub per 500/150 kV bank, read back from the subsystem workbooks."""
    banks: dict[str, list[str]] = {}
    owner: dict[str, str] = {}
    for path in sorted(ROOT.glob("samples/ss_*_ingest.xlsx")):
        parsed = parse_upload(path.read_bytes(), path.name)
        kv = {o["external_key"]: (o.get("voltage_hv_kv") or 0) for o in parsed["objects"]}
        for conn in parsed["connections"]:
            if conn["relation_type"] != "IBT_LINK":
                continue
            hv, lv = conn["from_external_key"], conn["to_external_key"]
            if kv.get(hv, 0) < 500 or kv.get(lv, 0) >= 500:
                continue
            unit = str(conn.get("unit_no") or "1")
            banks.setdefault(hv, [])
            if unit not in banks[hv]:
                banks[hv].append(unit)
            owner.setdefault(hv, parsed["subsystem"]["name"])
    return banks, owner


def main() -> None:
    assets, lines = backbone_spec()
    have = {a["code"] for a in assets}
    banks, owner = ibt_bays()

    def backbone_code(ss_code: str) -> str:
        # The backbone now marks the 500 kV side with a trailing 7, so a
        # subsystem's `GITET_XXX` or bare `XXX` resolves to `XXX7`.
        if ss_code in SS_TO_BACKBONE:
            return SS_TO_BACKBONE[ss_code]
        plain = ss_code.removeprefix("GITET_")
        if plain in have:
            return plain
        return plain if plain.endswith("7") else plain + "7"

    bays: list[tuple] = []
    risk_on: dict[str, list[str]] = {}
    skipped: list[str] = []
    merged: dict[str, list[str]] = {}
    for hv, units in sorted(banks.items()):
        code = backbone_code(hv)
        if code not in have:
            skipped.append(f"{hv} -> {code}")
            continue
        # Two SS sheets can feed the same GITET (Pedan 1,2 and Pedan 3,4), so
        # collect their units onto one stub rather than drawing two.
        # A unit list from one sheet can be "1,2" and from another "2", so split
        # to individual units before merging; otherwise BKASI reads "1,3,2,4,4".
        for group in units:
            for u in group.split(","):
                u = u.strip()
                merged.setdefault(code, [])
                if u and u not in merged[code]:
                    merged[code].append(u)
        risk_on.setdefault(code, [])
    for code, units in sorted(merged.items()):
        label = ",".join(sorted(units, key=lambda s: (len(s), s)))
        # Every stub in this view is a 500/150 kV transformer bank, not a
        # feeder, so say so rather than leaving it to the SUTT default.
        bays.append((f"IBT_{code}", f"IBT {label} {code} 500/150 kV", code, None,
                     1, "Beroperasi", "", "IBT"))

    risks = as_risk_dicts(RISK_FROM, RISK_TO, expected=RISK_COUNT)
    ss_of = dict(subsystem_rows(RISK_FROM, RISK_TO))
    unmatched: list[str] = []
    for r in risks:
        gitet = RISK_GITET.get(r["no"])
        if ss_of.get(r["no"]):
            r["kondisi"] = f"[{ss_of[r['no']]}] {r['kondisi']}"
        if gitet in risk_on:
            risk_on[gitet].append(str(r["no"]))
        else:
            unmatched.append(f"#{r['no']} -> {gitet} ({ss_of.get(r['no'])})")

    # Attach each bank's risk numbers, keeping the rest of the tuple (circuit
    # count, status, views, Jenis) rather than truncating it.
    bays = [(b[0], b[1], b[2], ";".join(risk_on.get(b[2], [])) or None, *b[4:])
            for b in bays]
    for a in assets:
        if a["code"] in risk_on and risk_on[a["code"]]:
            a["kerawanan"] = ";".join(risk_on[a["code"]])

    if skipped:
        # A bank whose GITET the backbone sheet does not carry, e.g. the planned
        # New Cikupa. Report rather than invent a 500 kV busbar for it.
        print("bank IBT tanpa busbar 500 kV di sheet backbone:")
        for line in skipped:
            print("   ", line)
    if unmatched:
        # Report rather than invent: a Sec 1.5 GITET with no IBT bank in any
        # subsystem workbook is a real gap in the fixtures.
        print("risiko Sec 1.5 tanpa bank IBT pada workbook SS:")
        for line in unmatched:
            print("   ", line)

    build_workbook(dict(
        code="SYSTEM_IBT_500",
        name="Sistem Jamali 500 kV - Kerawanan IBT 500/150 kV",
        apb="UIP2B Jamali",
        # System scope, not a UP2B subsystem: this is what puts the view on the
        # Sistem 500 kV page (IBT tile) instead of a region's map.
        rule_profile="IBT_500_150",
        wilayah="Jawa-Madura-Bali",
        source_ref="Buku Kerawanan SJB 2026 Sec 1.5, Gambar 1.5 (PDF p.40-64); "
                   "jaringan 500 kV sama dengan view Transmisi, stub IBT "
                   "diturunkan dari baris IBT pada workbook subsistem",
        assets=assets,
        lines=lines,
        bays=bays,
        risks=risks,
    ))


if __name__ == "__main__":
    main()
