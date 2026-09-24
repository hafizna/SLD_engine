"""samples/ss_sumbagut_ingest.xlsx -- Subsistem Sumbagut (Aceh + Sumatera Utara).

Source: Kerawanan Sistem Sumatera, UIP3B Sumatera, Sep 2026 (the pptx deck),
slide 24 "Tier Jaringan Sumbagut" (raster, ppt/media/image53.png, 3871 px wide;
read at 2-4x), slide 25 "Kerawanan Sumbagut" (map with the numbered pins) and
the risk table on slides 26-28. The codes are the tier SLD's own (the deck is
the only place they are spelled, so the neighbour sheets reuse them: KTPNG,
NPSDM). Conventions as in make_ss_bengkulu_xlsx.py; the SLD is read as
make_ss_sumsel_xlsx.py describes (a straight line through a busbar is joined
to it) -- e.g. Binjai -> Pangkalan Brandan -> Tanjung Pura, which is exactly
the chain risk #1 names.

Boxes on the sheet (TBING, BTAGI, SROTN, PBUNG, SBOGA, TTKNG) are connectors to
a bus drawn elsewhere on the same sheet; a line drawn from both ends through
such boxes is ONE ruas.

Not drawn here, as in the Sumsel and Sumbagteng sheets: SUTET 275 kV between
GITETs (Ulee Kareng - Sigli - Nagan, Binjai - Galang - Simangkuk - Sarulla -
New Padang Sidempuan). A 275 kV power plant GITET is a Bay stub on the GITET
it feeds (Pangkalan Susu on Binjai, Asahan on Simangkuk), like Sumsel 5.

Pins follow the slide 25 map, cross-checked with each Kondisi (the tier SLD's
yellow numbers are another numbering). Read off the sheet, noted for review:
  * SMUT4 is the Sarulla site: slide 29 reads "GITET Simangkuk - GITET Sarulla
    - GI Sarulla - PLTP Sarulla", and SMUT4 is the bus between Simangkuk and
    the NIL / SIL units (Namora I Langit, Silangkitang).
  * The generator symbol at Kuala Tanjung is taken as Inalum (slide 25 draws
    the Inalum plant there; risk #17 is the Inalum split). Titi Kuning and
    Glugur carry a generator symbol with no plant name on either slide.
  * The map draws Tele - Dolok Sanggul and Blang Pidie - Tapak Tuan; the tier
    SLD draws Dolok Sanggul -> Tarutung / Sidikalang -> Tele (lines through the
    buses) and Meulaboh - Tapak Tuan. The SLD is followed, as everywhere else.
  * Kota Pinang has ONE arrow to Sumbagteng here (drawn as a 1-circuit ruas to
    Bagan Batu, SOURCE_BOUNDARY); the Sumbagteng sheet draws
    two conductors from Bagan Batu. Each sheet keeps its own count.
  * Risk #19 "Jalur looping 150 kV Medan-Tapanuli tidak beroperasi": slide 25
    stars Perbaungan - Tebing Tinggi (pinned) and the 275 kV Galang -
    Simangkok SUTET (backbone sheet). The SLD still draws the 150 kV ruas
    solid, so it stays in service here.
  * Peusangan sits in the Tier-1 band with no generator drawn; it is fed only
    through Bireun, so it is filed at Tier-2.
  * The deck draws Sumbagut as ONE sheet; here it is two views, Aceh and
    Sumatera Utara, joined at Binjai (see VIEWS below for why).

Run: python scripts/make_ss_sumbagut_xlsx.py
"""
from __future__ import annotations

from _kerawanan_sumatera import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Sumbagut"


def GI(code, name, tier, kv=150, **kw):
    return dict(code=code, name=name, type="Busbar GI", tier=tier, kv=kv, **kw)


def GITET(code, name, **kw):
    return dict(code=code, name=name, type="Busbar GITET", tier=1, kv="275 kV", **kw)


def IBT(unit, hv, lv, name, **kw):
    return dict(code=f"IBT {unit} {hv}", name=name, type="IBT 3-Winding", tier=2,
                kv="275/150 kV", ibt=str(unit), bus_hv=hv, bus_lv=lv, trafo=1, **kw)


def KIT(code, name, kv=150):
    return dict(code=code, name=name, type="Pembangkit", tier=1, kv=f"{kv} kV")


ASSETS = [
    # ======================= 275 kV GITET + IBT =======================
    # Sigli, Ulee Kareng and Nagan run one IBT each (slides 6/9 say so too).
    GITET("ULKRG_275", "GITET Ulee Kareng (275 kV)"),
    IBT(1, "ULKRG_275", "ULKRG", "IBT Ulee Kareng 275/150 kV"),
    GITET("SIGLI_275", "GITET Sigli (275 kV)"),
    IBT(1, "SIGLI_275", "SIGLI", "IBT Sigli 275/150 kV"),
    GITET("NAGAN_275", "GITET Nagan Raya (275 kV)", kerawanan="2;3"),
    KIT("KIT_NAGAN_275", "PLTU Nagan Raya (275 kV)", kv=275),
    IBT(1, "NAGAN_275", "NAGAN", "IBT Nagan Raya 275/150 kV"),
    GITET("ARUN_275", "GITET Arun (275 kV)", kerawanan="4;6"),
    KIT("KIT_ARUN_275", "PLTMG Arun", kv=275),
    IBT(1, "ARUN_275", "ARUN", "IBT Arun 275/150 kV"),
    GITET("BNJAI_275", "GITET Binjai (275 kV)"),
    IBT(1, "BNJAI_275", "BNJAI", "IBT 1 Binjai 275/150 kV"),
    IBT(2, "BNJAI_275", "BNJAI", "IBT 2 Binjai 275/150 kV"),
    GITET("GLANG_275", "GITET Galang (275 kV)"),
    IBT(1, "GLANG_275", "GLANG", "IBT 1 Galang 275/150 kV"),
    IBT(2, "GLANG_275", "GLANG", "IBT 2 Galang 275/150 kV"),
    GITET("SMKOK_275", "GITET Simangkuk (275 kV)"),
    IBT(1, "SMKOK_275", "SMKOK", "IBT 1 Simangkuk 275/150 kV"),
    IBT(2, "SMKOK_275", "SMKOK", "IBT 2 Simangkuk 275/150 kV"),
    GITET("SMUT4_275", "GITET Sarulla (275 kV, label SMUT4)"),
    IBT(1, "SMUT4_275", "SMUT4", "IBT 1 Sarulla 275/150 kV"),
    IBT(2, "SMUT4_275", "SMUT4", "IBT 2 Sarulla 275/150 kV"),
    GITET("NPSDM_275", "GITET New Padang Sidempuan (275 kV)"),
    IBT(1, "NPSDM_275", "NPSDM", "IBT 1 New Padang Sidempuan 275/150 kV"),
    IBT(2, "NPSDM_275", "NPSDM", "IBT 2 New Padang Sidempuan 275/150 kV"),
    # ======================= Tier-1, 150 kV =======================
    KIT("KIT_BACEH", "PLTD Lueng Bata"),
    GI("BACEH", "Banda Aceh", 1, trafo=1),
    KIT("KIT_NAGAN", "PLTU Nagan Raya (150 kV)"),
    GI("NAGAN", "Nagan Raya (bus 150 kV)", 1),
    GI("ARUN", "Arun (bus 150 kV)", 1, trafo=1),
    GI("LNGSA", "Langsa", 1, trafo=1),
    GI("BNJAI", "Binjai (bus 150 kV)", 1, trafo=1),
    KIT("KIT_BLWCC", "PLTGU Belawan"),
    GI("BLWCC", "Belawan CC", 1, kerawanan="5;6;7"),
    KIT("KIT_PPSIR", "PLTG Paya Pasir"),
    GI("PPSIR", "Paya Pasir", 1, trafo=1),
    KIT("KIT_BLWTU", "PLTU Belawan"),
    GI("BLWTU", "Belawan PLTU", 1, kerawanan="7"),
    GI("SROTN", "Sei Rotan", 1, trafo=1),
    GI("GLANG", "Galang (bus 150 kV)", 1, trafo=1),
    GI("SMKOK", "Simangkuk (bus 150 kV)", 1),
    KIT("KIT_RENUN", "PLTA Renun"),
    GI("RENUN", "PLTA Renun", 1),
    KIT("KIT_WAMPU", "PLTA Wampu"),
    GI("WAMPU", "PLTA Wampu", 1),
    GI("SMUT4", "Sarulla (bus 150 kV, label SMUT4)", 1),
    KIT("KIT_NIL", "PLTP Sarulla - Namora I Langit"),
    GI("NIL", "PLTP Sarulla NIL", 1, kerawanan="11"),
    KIT("KIT_SIL", "PLTP Sarulla - Silangkitang"),
    GI("SIL", "PLTP Sarulla SIL", 1, kerawanan="11"),
    KIT("KIT_KTJUG", "Inalum (Kuala Tanjung)"),
    GI("KTJUG", "Kuala Tanjung", 1, trafo=1, kerawanan="17",
       simbol="simbol pembangkit di Kuala Tanjung = Inalum (peta slide 25)"),
    KIT("KIT_HSANG", "PLTA Hasang"),
    GI("HSANG", "PLTA Hasang", 1),
    GI("RTPAT", "Rantau Prapat", 1, trafo=1),
    GI("KTPNG", "Kota Pinang", 1, trafo=1),
    KIT("KIT_SIPAN1", "PLTA Sipan 1"),
    GI("SIPAN1", "PLTA Sipan 1", 1),
    KIT("KIT_SIPAN2", "PLTA Sipan 2"),
    GI("SIPAN2", "PLTA Sipan 2", 1),
    KIT("KIT_LBAGN", "PLTU Labuhan Angin"),
    GI("LBAGN", "PLTU Labuhan Angin", 1),
    GI("NPSDM", "New Padang Sidempuan (bus 150 kV)", 1, trafo=1),
    KIT("KIT_SMGP", "PLTP Sorik Marapi"),
    GI("SMGP", "PLTP Sorik Marapi", 1),
    # ======================= Tier-2 =======================
    GI("ULKRG", "Ulee Kareng (bus 150 kV)", 2, trafo=1),
    GI("SIGLI", "Sigli (bus 150 kV)", 2, trafo=1),
    GI("PSNGN", "Peusangan", 2, trafo=1,
       simbol="digambar di pita Tier-1 tanpa pembangkit; hanya lewat Bireun"),
    GI("BIRUN", "Bireun", 2, trafo=1),
    GI("LSMWE", "Lhokseumawe", 2, trafo=1),
    GI("PBDAN", "Pangkalan Brandan", 2, trafo=1),
    GI("PGELI", "Paya Geli", 2, trafo=1),
    GI("GIKIM", "KIM", 2, trafo=1, kerawanan="10"),
    KIT("KIT_TTKNG", "Pembangkit di Titi Kuning (nama tidak tertulis)"),
    GI("TTKNG", "Titi Kuning", 2, trafo=1),
    GI("GISLS", "GIS Listrik", 2, trafo=1),
    GI("KLNMU", "Kualanamu", 2, trafo=1),
    GI("NRMBE", "Namorambe", 2, trafo=1),
    GI("TMORA", "Tamora", 2, trafo=1),
    GI("PORSA", "Porsea", 2, trafo=1),
    GI("PSTAR", "Pematang Siantar", 2, trafo=1),
    GI("DSGUL", "Dolok Sanggul", 2, trafo=1),
    GI("BTAGI", "Brastagi", 2, trafo=1),
    GI("TBING", "Tebing Tinggi", 2, trafo=1),
    GI("SMKEI", "Sei Mangke", 2, trafo=1),
    GI("KSRAN", "Kisaran", 2, trafo=1),
    GI("PSDEM", "Padang Sidempuan", 2, trafo=1),
    GI("SBOGA", "Sibolga", 2, trafo=1),
    # ======================= Tier-3 =======================
    GI("KRAYA", "Krueng Raya", 3, trafo=1),
    GI("MLBOH", "Meulaboh", 3, trafo=1),
    GI("BLPDI", "Blang Pidie", 3, trafo=1),
    GI("SMLGA", "Samalanga", 3, trafo=1),
    GI("PLABU", "Panton Labu", 3, trafo=1),
    GI("GIDIE", "Idie", 3, trafo=1),
    KIT("KIT_GLGUR", "Pembangkit di Glugur (nama tidak tertulis)"),
    GI("GLGUR", "Glugur", 3, trafo=1),
    GI("MABAR", "Mabar", 3, trafo=1),
    GI("LBHAN", "Labuhan", 3, trafo=1),
    GI("LMHTA", "Lamhotma", 3, trafo=1),
    GI("DENAI", "Denai", 3, trafo=1),
    GI("PBUNG", "Perbaungan", 3, trafo=1),
    GI("NDLOK", "Negeri Dolok", 3, trafo=1),
    GI("TRTUG", "Tarutung", 3, trafo=1),
    GI("SDKAL", "Sidikalang", 3, trafo=1),
    GI("KTCNE", "Kutacane", 3, trafo=1),
    GI("SBSLM", "Subulussalam", 3, trafo=1, kerawanan="13"),
    GI("SNGKL", "Singkil", 3, trafo=1, kerawanan="13"),
    GI("AKNPN", "Aek Kanopan", 3, trafo=1),
    GI("GNTUA", "Gunung Tua", 3, trafo=1),
    GI("MRTBE", "Martabe", 3, trafo=1),
    GI("PYBGN", "Panyabungan", 3, trafo=1),
    # ======================= Tier-4 / 5 =======================
    GI("JNTHO", "Jantho", 4, trafo=1),
    GI("TTUAN", "Tapak Tuan", 4, trafo=1),
    GI("TKGON", "Takengon", 4, trafo=1),
    GI("TLCUT", "Tualang Cut", 4, trafo=1),
    GI("TJPRA", "Tanjung Pura", 4, trafo=1),
    GI("SLYNG", "Selayang", 4, trafo=1),
    GI("TJAWA", "Tanah Jawa", 4, trafo=1),
    GI("TELE", "Tele", 4, trafo=1),
    GI("SRUBE", "Siempat Rube", 4, trafo=1),
    GI("TJBLI", "Tanjung Balai", 4, trafo=1),
    GI("LBLIK", "Labuhan Bilik", 4, trafo=1),
    GI("SBHAN", "Sibuhuan", 4, trafo=1),
    GI("GPARA", "Gunung Para", 5, trafo=1, kerawanan="12",
       simbol="GI taping pada SUTT Pematang Siantar - Tebing Tinggi (risiko #12)"),
    GI("PGRUN", "Pangururan", 5, trafo=1),
    # ============ batas subsistem ============
    # Kota Pinang has only this one ruas, so a Bay on it had no busbar to hang
    # from; the neighbour GI is drawn whole instead (the Jakban convention).
    GI("BGBTU", "Bagan Batu (Subsistem Sumbagteng)", 2, role="SOURCE_BOUNDARY",
       simbol="batas ke Subsistem Sumbagteng"),
]

L = lambda fr, to, nm, tf, tt, kno=None, sirkit=2, st="Beroperasi": dict(
    fr=fr, to=to, name=f"SUTT 150 kV {nm}", kv=150, tier_fr=tf, tier_to=tt,
    kerawanan=kno, sirkit=sirkit, status=st, koridor=WIL)


def OUT(kit, bus, name, kv=150):
    return dict(fr=kit, to=bus, name=f"Outlet {name}", kv=kv, tier_fr=1, tier_to=1,
                sirkit=1, koridor=WIL)


LINES = [
    OUT("KIT_NAGAN_275", "NAGAN_275", "PLTU Nagan Raya (275 kV)", kv=275),
    OUT("KIT_ARUN_275", "ARUN_275", "PLTMG Arun", kv=275),
    OUT("KIT_BACEH", "BACEH", "PLTD Lueng Bata"),
    OUT("KIT_NAGAN", "NAGAN", "PLTU Nagan Raya (150 kV)"),
    OUT("KIT_BLWCC", "BLWCC", "PLTGU Belawan"),
    OUT("KIT_PPSIR", "PPSIR", "PLTG Paya Pasir"),
    OUT("KIT_BLWTU", "BLWTU", "PLTU Belawan"),
    OUT("KIT_RENUN", "RENUN", "PLTA Renun"),
    OUT("KIT_WAMPU", "WAMPU", "PLTA Wampu"),
    OUT("KIT_NIL", "NIL", "PLTP Sarulla NIL"),
    OUT("KIT_SIL", "SIL", "PLTP Sarulla SIL"),
    OUT("KIT_KTJUG", "KTJUG", "Inalum"),
    OUT("KIT_HSANG", "HSANG", "PLTA Hasang"),
    OUT("KIT_SIPAN1", "SIPAN1", "PLTA Sipan 1"),
    OUT("KIT_SIPAN2", "SIPAN2", "PLTA Sipan 2"),
    OUT("KIT_LBAGN", "LBAGN", "PLTU Labuhan Angin"),
    OUT("KIT_SMGP", "SMGP", "PLTP Sorik Marapi"),
    OUT("KIT_TTKNG", "TTKNG", "pembangkit Titi Kuning"),
    OUT("KIT_GLGUR", "GLGUR", "pembangkit Glugur"),
    # ======================= Aceh =======================
    L("BACEH", "ULKRG", "Banda Aceh - Ulee Kareng", 1, 2),
    L("ULKRG", "KRAYA", "Ulee Kareng - Krueng Raya", 2, 3),
    L("BACEH", "JNTHO", "Banda Aceh - Jantho", 1, 4, sirkit=1),
    L("BACEH", "SIGLI", "Banda Aceh - Sigli", 1, 2, sirkit=1),
    L("SIGLI", "JNTHO", "Sigli - Jantho", 2, 4, sirkit=1),
    L("NAGAN", "MLBOH", "Nagan Raya - Meulaboh", 1, 3),
    L("MLBOH", "TTUAN", "Meulaboh - Tapak Tuan", 3, 4),
    L("NAGAN", "BLPDI", "Nagan Raya - Blang Pidie", 1, 3),
    L("SIGLI", "SMLGA", "Sigli - Samalanga", 2, 3, kno="1;2;3", sirkit=1),
    L("SMLGA", "BIRUN", "Samalanga - Bireun", 3, 2, kno="1;2;3", sirkit=1),
    L("SIGLI", "BIRUN", "Sigli - Bireun", 2, 2, kno="1;2;3", sirkit=1),
    L("ARUN", "BIRUN", "Arun - Bireun", 1, 2, kno="1;2;3"),
    L("PSNGN", "BIRUN", "Peusangan - Bireun", 2, 2),
    L("PSNGN", "TKGON", "Peusangan - Takengon", 2, 4),
    L("ARUN", "LSMWE", "Arun - Lhokseumawe", 1, 2, kno="1"),
    L("LSMWE", "PLABU", "Lhokseumawe - Panton Labu", 2, 3, kno="1", sirkit=1),
    L("PLABU", "GIDIE", "Panton Labu - Idie", 3, 3, kno="1", sirkit=1),
    L("GIDIE", "LNGSA", "Idie - Langsa", 3, 1, kno="1", sirkit=1),
    L("LNGSA", "LSMWE", "Langsa - Lhokseumawe", 1, 2, kno="1", sirkit=1),
    L("LNGSA", "TLCUT", "Langsa - Tualang Cut", 1, 4),
    L("LNGSA", "PBDAN", "Langsa - Pangkalan Brandan", 1, 2, kno="1"),
    L("BNJAI", "PBDAN", "Binjai - Pangkalan Brandan", 1, 2, kno="1", sirkit=1),
    L("PBDAN", "TJPRA", "Pangkalan Brandan - Tanjung Pura", 2, 4, sirkit=1),
    L("BNJAI", "TJPRA", "Binjai - Tanjung Pura", 1, 4, sirkit=1),
    # ======================= Medan =======================
    L("BNJAI", "PGELI", "Binjai - Paya Geli", 1, 2),
    L("BNJAI", "BLWCC", "Binjai - Belawan CC", 1, 1),
    L("BLWCC", "SROTN", "Belawan CC - Sei Rotan", 1, 1),
    L("SROTN", "TTKNG", "Sei Rotan - Titi Kuning", 1, 2),
    L("TTKNG", "BTAGI", "Titi Kuning - Brastagi", 2, 2),
    L("PPSIR", "PGELI", "Paya Pasir - Paya Geli", 1, 2),
    L("PPSIR", "MABAR", "Paya Pasir - Mabar", 1, 3, kno="18"),
    L("PPSIR", "BLWTU", "Paya Pasir - Belawan PLTU", 1, 1),
    L("PPSIR", "SROTN", "Paya Pasir - Sei Rotan", 1, 1),
    L("SROTN", "GIKIM", "Sei Rotan - KIM", 1, 2, kno="18"),
    L("SROTN", "DENAI", "Sei Rotan - Denai", 1, 3, sirkit=1),
    L("DENAI", "TMORA", "Denai - Tamora", 3, 2, sirkit=1),
    L("TMORA", "KLNMU", "Tamora - Kualanamu", 2, 2),
    L("SROTN", "TMORA", "Sei Rotan - Tamora", 1, 2, sirkit=1),
    L("SROTN", "PBUNG", "Sei Rotan - Perbaungan", 1, 3, sirkit=1),
    L("PBUNG", "TBING", "Perbaungan - Tebing Tinggi", 3, 2, kno="19", sirkit=1),
    L("SROTN", "TBING", "Sei Rotan - Tebing Tinggi", 1, 2, sirkit=1),
    L("PBUNG", "KLNMU", "Perbaungan - Kualanamu", 3, 2),
    L("BLWTU", "LBHAN", "Belawan PLTU - Labuhan", 1, 3, sirkit=1),
    L("LBHAN", "LMHTA", "Labuhan - Lamhotma", 3, 3, sirkit=1),
    L("LMHTA", "BLWTU", "Lamhotma - Belawan PLTU", 3, 1, sirkit=1),
    L("PGELI", "GLGUR", "Paya Geli - Glugur", 2, 3, kno="9"),
    L("PGELI", "SLYNG", "Paya Geli - Selayang", 2, 4),
    L("SLYNG", "NRMBE", "Selayang - Namorambe", 4, 2),
    L("TTKNG", "NRMBE", "Titi Kuning - Namorambe", 2, 2),
    L("TTKNG", "GISLS", "Titi Kuning - GIS Listrik", 2, 2, kno="8"),
    L("NRMBE", "GLANG", "Namorambe - Galang", 2, 1),
    L("GLANG", "TMORA", "Galang - Tamora", 1, 2),
    L("TMORA", "NDLOK", "Tamora - Negeri Dolok", 2, 3, sirkit=1),
    L("GLANG", "NDLOK", "Galang - Negeri Dolok", 1, 3, sirkit=1),
    # ======================= Toba / Tapanuli =======================
    L("SMKOK", "PORSA", "Simangkuk - Porsea", 1, 2),
    L("PORSA", "TRTUG", "Porsea - Tarutung", 2, 3),
    L("TRTUG", "SBOGA", "Tarutung - Sibolga", 3, 2),
    L("PORSA", "PSTAR", "Porsea - Pematang Siantar", 2, 2),
    L("PSTAR", "TJAWA", "Pematang Siantar - Tanah Jawa", 2, 4),
    L("PSTAR", "TBING", "Pematang Siantar - Tebing Tinggi", 2, 2, sirkit=1),
    L("PSTAR", "GPARA", "T-connection Gunung Para (dari Pematang Siantar - Tebing Tinggi)",
      2, 5, kno="12", sirkit=1),
    L("DSGUL", "TRTUG", "Dolok Sanggul - Tarutung", 2, 3, sirkit=1),
    L("TRTUG", "TELE", "Tarutung - Tele", 3, 4, sirkit=1),
    L("DSGUL", "SDKAL", "Dolok Sanggul - Sidikalang", 2, 3, sirkit=1),
    L("SDKAL", "TELE", "Sidikalang - Tele", 3, 4, sirkit=1),
    L("TELE", "PGRUN", "Tele - Pangururan", 4, 5),
    L("RENUN", "SDKAL", "PLTA Renun - Sidikalang", 1, 3),
    L("SDKAL", "SRUBE", "Sidikalang - Siempat Rube", 3, 4),
    L("SDKAL", "SBSLM", "Sidikalang - Subulussalam", 3, 3, kno="13"),
    L("SBSLM", "SNGKL", "Subulussalam - Singkil", 3, 3, kno="13"),
    L("WAMPU", "BTAGI", "PLTA Wampu - Brastagi", 1, 2),
    L("BTAGI", "KTCNE", "Brastagi - Kutacane", 2, 3),
    L("SMUT4", "NIL", "Sarulla - PLTP NIL", 1, 1),
    L("SMUT4", "SIL", "Sarulla - PLTP SIL", 1, 1),
    # ======================= Asahan / Labuhanbatu =======================
    L("KTJUG", "TBING", "Kuala Tanjung - Tebing Tinggi", 1, 2),
    L("KTJUG", "SMKEI", "Kuala Tanjung - Sei Mangke", 1, 2),
    L("SMKEI", "KSRAN", "Sei Mangke - Kisaran", 2, 2),
    L("KSRAN", "TJBLI", "Kisaran - Tanjung Balai", 2, 4),
    L("KSRAN", "AKNPN", "Kisaran - Aek Kanopan", 2, 3, sirkit=1),
    L("AKNPN", "HSANG", "Aek Kanopan - PLTA Hasang", 3, 1, sirkit=1),
    L("HSANG", "RTPAT", "PLTA Hasang - Rantau Prapat", 1, 1, sirkit=1),
    L("KSRAN", "RTPAT", "Kisaran - Rantau Prapat", 2, 1, sirkit=1),
    L("RTPAT", "LBLIK", "Rantau Prapat - Labuhan Bilik", 1, 4),
    L("RTPAT", "GNTUA", "Rantau Prapat - Gunung Tua", 1, 3, sirkit=1),
    L("RTPAT", "PSDEM", "Rantau Prapat - Padang Sidempuan", 1, 2, sirkit=1),
    L("PSDEM", "GNTUA", "Padang Sidempuan - Gunung Tua", 2, 3, sirkit=1),
    L("RTPAT", "KTPNG", "Rantau Prapat - Kota Pinang", 1, 1, sirkit=1),
    L("KTPNG", "BGBTU", "Kota Pinang - Bagan Batu (arah Sumbagteng)", 1, 2, sirkit=1),
    L("GNTUA", "SBHAN", "Gunung Tua - Sibuhuan", 3, 4),
    # ======================= Sibolga / Padang Sidempuan =======================
    L("SIPAN1", "SBOGA", "PLTA Sipan 1 - Sibolga", 1, 2, kno="14", sirkit=1),
    L("SIPAN1", "SIPAN2", "PLTA Sipan 1 - PLTA Sipan 2", 1, 1, kno="14", sirkit=1),
    L("SIPAN2", "SBOGA", "PLTA Sipan 2 - Sibolga", 1, 2, kno="14", sirkit=1),
    L("LBAGN", "SBOGA", "PLTU Labuhan Angin - Sibolga", 1, 2, kno="14"),
    L("SBOGA", "MRTBE", "Sibolga - Martabe", 2, 3),
    L("PSDEM", "MRTBE", "Padang Sidempuan - Martabe", 2, 3),
    L("NPSDM", "PSDEM", "New Padang Sidempuan - Padang Sidempuan", 1, 2),
    L("NPSDM", "PYBGN", "New Padang Sidempuan - Panyabungan", 1, 3, kno="15;16"),
    L("SMGP", "PYBGN", "PLTP Sorik Marapi - Panyabungan", 1, 3),
]

# Arrows to a neighbouring subsystem or a 275 kV plant GITET: (gi, name,
# feeder, kerawanan, sirkit, status, views, jenis, kv)
BAYS = [
    ("PSUSU_275", "PLTU Pangkalan Susu (275 kV)", "BNJAI_275", "5;11", 2, "Beroperasi", None, "SUTT", "275 kV"),
    ("ASAHN_275", "PLTA Asahan (275 kV)", "SMKOK_275", None, 2, "Beroperasi", None, "SUTT", "275 kV"),
    ("PYBUH_275", "Payakumbuh (Subsistem Sumbagteng, 275 kV)", "NPSDM_275", None, 2,
     "Beroperasi", None, "SUTT", "275 kV"),
]

# Two views over the one sheet. Drawn whole, ~80 GIs took the router 16 minutes
# and came out as one tangle; split, the two render in about two minutes. The
# cut is the deck's own: risk #1 calls Binjai - P. Brandan - ... - Sigli the
# "Subsistem Aceh". Binjai (and its GITET) sits on both, as the joint.
ACEH_CODES = {
    "BACEH", "ULKRG", "ULKRG_275", "KRAYA", "JNTHO", "SIGLI", "SIGLI_275", "NAGAN",
    "NAGAN_275", "MLBOH", "BLPDI", "TTUAN", "ARUN", "ARUN_275", "BIRUN", "SMLGA",
    "PSNGN", "TKGON", "LSMWE", "PLABU", "GIDIE", "LNGSA", "TLCUT", "PBDAN", "TJPRA"}
JOINT = {"BNJAI", "BNJAI_275"}
VIEWS = [
    ("ACEH", "Aceh", "BACEH;NAGAN_275;ARUN_275;ULKRG_275;SIGLI_275;BNJAI_275", 24),
    ("SUMUT", "Sumatera Utara", "BNJAI_275;GLANG_275;SMKOK_275;SMUT4_275;NPSDM_275", 24),
]


def _side(code):
    code = code.split(" ")[-1] if code.startswith("IBT ") else code
    code = code.removeprefix("KIT_")
    if code in JOINT:
        return ["ACEH", "SUMUT"]
    return ["ACEH"] if code in ACEH_CODES else ["SUMUT"]


for _a in ASSETS:
    _a["views"] = _side(_a["code"])
for _l in LINES:
    _both = [v for v in _side(_l["fr"]) if v in _side(_l["to"])]
    _l["views"] = _both or _side(_l["fr"])
BAYS = [b[:6] + (_side(b[2]),) + b[7:] for b in BAYS]

SPEC = dict(
    code="SS_SUMBAGUT",
    name="Sumbagut",
    apb="Sumbagut",
    wilayah=WIL,
    multi_pin=True,
    views=VIEWS,
    source_ref="Kerawanan Sistem Sumatera Sep 2026 (UIP3B Sumatera), slide 24 Tier Jaringan "
               "Sumbagut; pin dari peta slide 25; tabel risiko slide 26-28",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts("SUMBAGUT"),
)

if __name__ == "__main__":
    build_workbook(SPEC)
