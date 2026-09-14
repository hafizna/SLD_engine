# Revisi sample Jakarta & Banten — 15 September 2026

Tiga workbook sample digenerate ulang dari file revisi pengguna. File asli
disimpan utuh di `samples/sources/`. File Excel diperlakukan sebagai data dan
bukti audit, bukan instruksi untuk mengubah aplikasi atau menerbitkan database.

| Sample | Sumber pengguna | Node lama → baru | Relasi lama → baru | Risiko lama → baru | View lama → baru |
|---|---|---:|---:|---:|---:|
| `ss_lbk_ingest.xlsx` | `JBB_SS_LBK_single_view_v1.xlsx` | 42 → 31 | 48 → 32 | 6 → 0 | 2 → 1 |
| `ss_gucl_ingest.xlsx` | `JBB_SS_GUCL_manual_audit_v2 (1).xlsx` | 59 → 56 | 49 → 43 | 7 → 7 | 1 → 1 |
| `ss_prbc_ingest.xlsx` | `JBB_SS_PBRC_single_view_v1.xlsx` | 60 → 45 | 65 → 51 | 7 → 0 | 3 → 1 |

Relasi adalah record hasil parser, termasuk IBT_LINK; bukan jumlah konduktor
atau seluruh feeder Bay. Bay ikut dihitung pada pemeriksaan keterhubungan.

## Penyesuaian ingest

- Kode PBRC dinormalisasi menjadi `SS_PRBC`, identitas subsistem yang sudah
  dipakai proyek. Berkas sumber tetap menggunakan kode aslinya.
- Kolom `Sudut Pandang` pada tiga sheet ingest diganti judulnya menjadi
  `Catatan Sudut Pandang Sumber`. Nilai aslinya tetap utuh. Isinya merupakan
  catatan seperti `Priok:Core T1`, bukan ID view. Memasukkannya ke parser tanpa
  adaptasi membuat filter FULL mengecualikan node/relasi dari gambar.
- Manifest `Views` berisi satu view `FULL` dengan source bus eksplisit.
  Tier dan relasi dari sumber dipertahankan, termasuk same-tier/reverse-tier.
- Tidak ada perubahan pada parser atau renderer untuk impor ini.
- CLI `make_ss_lbk_xlsx.py`, `make_ss_gucl_xlsx.py`, dan
  `make_ss_prbc_xlsx.py` kini menggunakan `_reviewed_jakban.py` agar regenerasi
  berikutnya tetap mengambil file revisi, bukan SPEC historis di modul tersebut.

## Hasil pengujian

`python -m pytest tests/test_reviewed_jakban.py tests/test_ingest.py -q`

**32 passed.** Peringatan yang muncul adalah deprecation `datetime.utcnow()`.
Pengujian baru membandingkan hasil regenerasi dengan sample tersimpan,
memastikan topologi/risiko sumber tidak berubah karena adaptasi view, memeriksa
seluruh substation dan generator menjadi anggota FULL, serta mengunci koreksi
suplai GUCL. Dua fixture multi-view lama disimpan di
`tests/fixtures/jakban_legacy/` agar regresi dukungan multi-view tetap diuji.

Ketiga sample lama dan baru diuji melalui `audit_one`: parse → draft → validate
→ publish pada SQLite sementara → render → geometry checks. Seluruhnya PASS,
tanpa dropped edge atau geometry error. Pemeriksaan graph baru termasuk Bay
menemukan satu connected component per SS, tanpa node terisolasi (31/56/45).
Artinya baseline lama juga valid secara teknis; PASS sendiri bukan bukti bahwa
relasi lama benar secara fisik.

Contoh perbaikan GUCL yang terkonfirmasi terhadap revisi pengguna:
`LBUAN–MENES`, `SKETI–RKBRU`, `KRWTU–SRANG` menggantikan relasi lama;
`CLBRU–LBUAN` dan `MENES–SKETI` tidak lagi ada. MITSUI/MCOIS menjadi Bay/load.
PBRC menyatukan sambungan antar-PoV seperti PLPNG40–HNDAH/KDSPI dan
GDPLA–MGRAI/GMLMA. LBK menyatukan core Kembangan–Balaraja melalui GI overlap.

Diff lengkap tersimpan di `JAKBAN_REVIEWED_COMPARISON.json`. Diff memperlakukan
arah pasangan sebagai tak berarah agar pembalikan penulisan endpoint tidak
dianggap perubahan topologi; unit IBT, jumlah sirkit, dan single_phi tetap
dibandingkan. Angka tambah/hapus dapat mencakup perubahan atribut atau alias.

## Batas kesimpulan

- Lebih sesuai terhadap **file revisi pengguna** dan dapat di-ingest secara
  utuh sebagai single view. Kebenaran terhadap master SLD belum diverifikasi.
- LBK dan PBRC kehilangan cakupan detail IBT/pembangkit serta seluruh tabel
  kerawanan karena sumber baru memang tidak memuatnya. Data lama tidak
  digabungkan otomatis karena kode GI/relasi dan lingkupnya telah berubah.
- Beberapa identitas berubah (misalnya LTKNG/ILKNG dan ULJMI/UUMI); masih perlu
  rekonsiliasi master GI sebelum dipakai lintas subsistem.
- Flag Single Phi LBK/PBRC berubah mengikuti file baru; jumlah sirkit saja
  tidak membuktikan konfigurasi single phi. Jangan menganggap perubahan itu
  telah diverifikasi secara fisik.
- Sheet `Audit_Topologi`, `Boundary_External`, `POV_Tiering`, dan `Unified_View`
  dipertahankan sebagai bukti; parser tidak mengimpor sheet tersebut sebagai
  topologi/constraint atau confidence per-edge. Catatan medium/verify masih
  memerlukan audit, misalnya ANYER–MENES, CASRI–ANYER, SUJYA–SVRNA,
  PSKMS–GJTGL, dan rute BKASI–HNDAH/KDSPI.
- Preview SVG/HTML tersedia di `tmp/jakban-revision-20260915/render-*/`.
  PNG dari PyMuPDF tidak menampilkan semua label HTML foreignObject SVG;
  gunakan HTML/SVG di browser untuk membaca nama GI.
- Database aplikasi, seed, dan snapshot website tidak diperbarui. Seluruh
  publish pengujian memakai database sementara.

## Regenerasi

```powershell
python scripts/make_ss_lbk_xlsx.py
python scripts/make_ss_gucl_xlsx.py
python scripts/make_ss_prbc_xlsx.py
python -m pytest tests/test_reviewed_jakban.py tests/test_ingest.py -q
python scripts/render_one.py samples/ss_lbk_ingest.xlsx
```
