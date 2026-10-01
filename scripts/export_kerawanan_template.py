"""Convert one of our ingest workbooks into the "template_kerawanan_subsistem"
layout used by a colleague's SLD viewer (sheets Jalur_Transmisi, Gardu_Induk,
Panduan_Simbol_SLD, Tabel_Kerawanan).

The template is copied and only its data rows are replaced, so its headers and
the Panduan_Simbol_SLD sheet stay exactly as the viewer expects.

How their layout differs from ours:
* An IBT is also a ruas there ("Bay IBT", HV bus -> LV bus), and a pembangkit
  hangs on its bus through a "Bay Generator" ruas. We keep the IBT only as an
  asset row with Bus HV / Bus LV.
* One row per sirkit: a 2-sirkit ruas becomes two rows, No Sirkit 1 and 2.
* Tiers start at 0 for the 500 kV buses and generators; our first 150 kV tier
  is their tier 1. An IBT sits on its LV bus's tier.
* Status uses their vocabulary only: a pinned object is "Sangat Rawan" (our
  rule for a pinned ruas), everything else "Normal".
* Several risk numbers are joined with "&" ("1&2"), as in their example.
* Pembebanan, Panjang and Kapasitas stay blank: the book gives thresholds
  (">80%"), not measured values. ID FunctLoc follows their placeholder pattern
  FL-<KODE>-<kV>; it is not a SAP id.

Run:
    python scripts/export_kerawanan_template.py SAMPLE.xlsx TEMPLATE.xlsx OUT.xlsx
"""
from __future__ import annotations

import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl


def _rows(ws):
    head = [c.value for c in ws[1]]
    for r in ws.iter_rows(min_row=2, values_only=True):
        if any(v not in (None, "") for v in r):
            yield dict(zip(head, r))


def _nums(v) -> list[str]:
    return [p for p in re.split(r"[;,&\s]+", str(v or "")) if p]


def _amp(v) -> str:
    return "&".join(_nums(v))


def _clean(text: str, header: str) -> str:
    """Tidy one risk-table cell for display: drop our "[N-1] " category
    prefix and the column header that PDF extraction leaks in at page breaks,
    repair the commonest glued words, and put each numbered item and each
    "Jangka ..." block on its own line, as the template's example does."""
    t = re.sub(r"^\[[A-Z0-9_\-]+\]\s*", "", str(text or "")).strip()
    t = re.sub(rf"\s{re.escape(header)}\s", " ", t)
    t = re.sub(r"(?<=[a-z])(?=N-1)", " ", t)
    t = re.sub(r"%(?=[a-z])", "% ", t)
    t = re.sub(r"(?<=Tahun)(?=\d)|(?<=COD)(?=Tahun)|(?<=MW)(?=[a-z])", " ", t)
    t = re.sub(r"\s+(?=Jangka (Pendek|Menengah|Panjang))", "\n\n", t)
    t = re.sub(r"(Jangka (?:Pendek|Menengah|Panjang))\s*:\s*", r"\1 :\n", t)
    t = re.sub(r"[ \t]+(?=\d{1,2}\.\s)", "\n", t)
    return t.strip()


def _risk_cols(nums, risks):
    """Kondisi / Dampak / Mitigasi / Usulan for the risks pinned on one row.
    A single risk is copied as is; several are each prefixed with their #."""
    picked = [risks[n] for n in nums if n in risks]
    if not picked:
        return ["", "", "", ""]
    out = []
    for key in ("kondisi", "dampak", "mitigasi", "usulan"):
        if len(picked) == 1:
            out.append(picked[0][key])
        else:
            out.append("\n\n".join(f"#{r['no']}: {r[key]}" for r in picked))
    return out


def _kv_head(kv: str) -> str:
    m = re.match(r"\s*(\d+)", str(kv or ""))
    return m.group(1) if m else ""


def _fl(code: str, kv: str) -> str:
    return f"FL-{re.sub(r'[^A-Za-z0-9]', '', code).upper()}-{_kv_head(kv)}"


def _write(ws, rows):
    if ws.max_row > 1:
        ws.delete_rows(2, ws.max_row - 1)
    for r in rows:
        ws.append(r)


def convert(sample: Path, template: Path, out: Path) -> Path:
    src = openpyxl.load_workbook(sample, data_only=True)
    info = {r["Kunci"]: r["Nilai"] for r in _rows(src["Info"])}
    assets = list(_rows(src["Gardu_Induk_dan_Aset"]))
    lines = list(_rows(src["Jalur_Transmisi"]))
    risk_rows = list(_rows(src["Data_Kerawanan_Detail"]))

    ss_name = f"Subsistem {info.get('Nama Subsistem', '')}".replace(" - ", " – ")
    uit = next((r["UIT"] for r in risk_rows if r.get("UIT")), "")
    risks = {
        str(r["No"]): dict(
            no=str(r["No"]),
            kondisi=_clean(r["Kondisi / Permasalahan"], "Kondisi / Permasalahan"),
            dampak=_clean(r["Dampak"], "Dampak"),
            mitigasi=_clean(r["Mitigasi"], "Mitigasi"),
            usulan=_clean(r["Usulan / Solusi"], "Usulan / Solusi"))
        for r in risk_rows
    }

    by_code = {a["Kode Singkatan"]: a for a in assets}
    kind = {}
    for a in assets:
        t = str(a["Tipe Asset"] or "")
        kind[a["Kode Singkatan"]] = ("IBT" if t.startswith("IBT") else
                                     "Pembangkit" if t == "Pembangkit" else "Busbar")
    gen_codes = {c for c, k in kind.items() if k == "Pembangkit"}

    # --- tiers in their numbering ------------------------------------------
    tier = {}
    for a in assets:
        c = a["Kode Singkatan"]
        if kind[c] == "Busbar":
            tier[c] = 0 if str(a["Tegangan"]).startswith("500") else int(a["Tier (Mulai 0)"] or 0) + 1
    for a in assets:
        c = a["Kode Singkatan"]
        if kind[c] == "IBT":
            tier[c] = tier.get(a["Bus LV"], int(a["Tier (Mulai 0)"] or 0) + 1)
        elif kind[c] == "Pembangkit":
            bus = next((ln["Ke GI"] if ln["Dari GI"] == c else ln["Dari GI"]
                        for ln in lines if c in (ln["Dari GI"], ln["Ke GI"])), None)
            tier[c] = max(0, tier.get(bus, 1) - 1)

    # --- Jalur_Transmisi: IBT bays, generator bays, then the ruas ----------
    jalur = []
    neighbours = defaultdict(list)
    ends = defaultdict(int)

    def add_neighbour(a, b):
        if b not in neighbours[a]:
            neighbours[a].append(b)
        if a not in neighbours[b]:
            neighbours[b].append(a)

    ibt_groups = defaultdict(list)
    for a in assets:
        if kind[a["Kode Singkatan"]] == "IBT":
            ibt_groups[(a["Bus HV"], a["Bus LV"])].append(a)
    for (hv, lv), group in ibt_groups.items():
        add_neighbour(hv, lv)
        for i, a in enumerate(group, 1):
            nums = _nums(a["No Kerawanan"])
            gi = by_code.get(hv, {}).get("Nama Asset / GI", hv).replace("GITET ", "")
            gi = re.sub(r"\s*\(bus [^)]*\)", "", gi)
            jalur.append([
                None, _amp(a["No Kerawanan"]),
                f"Bay IBT {a['No IBT']} {gi} ({a['Tegangan']})", "Bay IBT", "IBT",
                hv, "Busbar", tier[hv], lv, "Busbar", tier[lv], a["Tegangan"],
                len(group), i, a["Status Operasi"] or "Beroperasi",
                "Sangat Rawan" if nums else "Normal", None, None, None,
                a["Wilayah"], uit, *_risk_cols(nums, risks)])
            ends[hv] += 1
            ends[lv] += 1

    for ln in lines:
        fr, to = ln["Dari GI"], ln["Ke GI"]
        add_neighbour(fr, to)
        nums = _nums(ln["No Kerawanan"])
        n = int(ln["Jumlah Sirkit"] or 1)
        is_gen = fr in gen_codes or to in gen_codes
        if is_gen and to in gen_codes:
            fr, to = to, fr
        for i in range(1, n + 1):
            if is_gen:
                name = f"Bay Evakuasi {by_code[fr]['Nama Asset / GI']}"
                saluran, simbol = "Bay Generator", "Trafo Generator"
            else:
                name = ln["Nama Penghantar"] + (f" (Sirkit {i})" if n > 1 else "")
                saluran = simbol = "PHT"
            cols = _risk_cols(nums, risks)
            if is_gen and not cols[0]:
                cols[0] = f"Evakuasi daya {by_code[fr]['Nama Asset / GI']}."
            jalur.append([
                None, _amp(ln["No Kerawanan"]), name, saluran, simbol,
                fr, kind.get(fr, "Busbar"), tier[fr], to, kind.get(to, "Busbar"),
                tier[to], ln["Tegangan"], n, i,
                ln["Status Operasi"] or "Beroperasi",
                "Sangat Rawan" if nums else "Normal", None, None, None,
                ln["Koridor / Wilayah"], uit, *cols])
            ends[fr] += 1
            ends[to] += 1
    for i, r in enumerate(jalur, 1):
        r[0] = i

    # --- Gardu_Induk ---------------------------------------------------------
    gardu = []
    for i, a in enumerate(assets, 1):
        c, k = a["Kode Singkatan"], kind[a["Kode Singkatan"]]
        nm, kv = a["Nama Asset / GI"], a["Tegangan"]
        nums = _nums(a["No Kerawanan"])
        if k == "Busbar" and str(kv).startswith("500"):
            label, desc = f"{nm} (500 kV)", f"Busbar 500 kV {nm}"
        elif k == "Busbar":
            label = nm if re.match(r"(GI|GIS|GITET)\b", nm) else f"GI {nm}"
            desc = f"Gardu Induk {nm.removeprefix('GI ')}"
        elif k == "IBT":
            label, desc = nm, f"{nm}: {a['Bus HV']} -> {a['Bus LV']}"
            neighbours[c] = [a["Bus HV"], a["Bus LV"]]
        else:
            label, desc = nm, f"Bay Pembangkit {nm}: 1. Pembangkit, 2. Trafo Generator, 3. CB"
        if a.get("Catatan Simbol"):
            desc += f" ({a['Catatan Simbol']})"
        cols = _risk_cols(nums, risks)
        if not cols[0]:
            cols[0] = desc
        wide = k == "Busbar" and ends[c] >= 6
        gardu.append([
            i, label, c, k, "Panjang (Wide Busbar)" if wide else "Normal", None,
            tier[c], kv, a["No IBT"] or None,
            "Sangat Rawan" if nums else "Normal", _amp(a["No Kerawanan"]) or None,
            a["Wilayah"], uit, *cols, "; ".join(neighbours.get(c, [])) or None,
            None, _fl(c, kv)])

    # --- Tabel_Kerawanan -----------------------------------------------------
    tabel = [[i, r["no"], ss_name, uit, r["kondisi"], r["dampak"], r["mitigasi"],
              r["usulan"]] for i, r in enumerate(risks.values(), 1)]

    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, out)
    wb = openpyxl.load_workbook(out)
    _write(wb["Jalur_Transmisi"], jalur)
    _write(wb["Gardu_Induk"], gardu)
    _write(wb["Tabel_Kerawanan"], tabel)
    wb.save(out)
    print(f"wrote {out}: {len(gardu)} aset, {len(jalur)} baris jalur, "
          f"{len(tabel)} kerawanan")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    convert(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
