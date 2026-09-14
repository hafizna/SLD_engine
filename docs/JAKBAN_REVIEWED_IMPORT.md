# Revisi sample Jakarta & Banten — 15 September 2026

Tiga workbook sample digenerate ulang dari file revisi pengguna. File asli
disimpan utuh di `samples/sources/`. Excel diperlakukan sebagai data dan bukti
audit; isi workbook tidak dipakai sebagai instruksi untuk mengubah aplikasi.

| Sample | Sumber pengguna | Node lama → baru | Relasi lama → baru | Risiko lama → baru | View lama → baru |
|---|---|---:|---:|---:|---:|
| `ss_lbk_ingest.xlsx` | `JBB_SS_LBK_single_view_v1.xlsx` | 42 → 36 | 48 → 32 | 6 → 0 | 2 → 1 |
| `ss_gucl_ingest.xlsx` | `JBB_SS_GUCL_manual_audit_v2 (1).xlsx` | 59 → 60 | 49 → 43 | 7 → 7 | 1 → 1 |
| `ss_prbc_ingest.xlsx` | `JBB_SS_PBRC_single_view_v1.xlsx` | 60 → 54 | 65 → 59 | 7 → 0 | 3 → 1 |

Relasi adalah record hasil parser, termasuk `IBT_LINK`; jumlah sirkit dan
baris Bay tidak dihitung sebagai relasi tambahan.

## Penyesuaian ingest

- Kode PBRC dinormalisasi menjadi `SS_PRBC`, identitas subsistem yang sudah
  dipakai proyek. Berkas sumber tetap menggunakan kode aslinya.
- Kolom `Sudut Pandang` pada tiga sheet ingest diganti judulnya menjadi
  `Catatan Sudut Pandang Sumber`. Nilai audit tetap utuh, tetapi tidak dibaca
  sebagai ID view sehingga seluruh isi masuk ke view `FULL`.
- Manifest `Views` berisi satu view `FULL` dengan source bus eksplisit.
- Bukti boundary yang tegas dari sheet `Boundary_External` dipromosikan ke
  sheet machine-readable:
  - LBK: `NCKUPA→CKUPA`, `CKNN?→DLRA`, `TGBRU3→SUJYA`, `JTKBR→JTAKE`,
    `BSH→CKDRU` sebagai Bay/stub.
  - GUCL: rantai abu-abu `SARAN4→SRANG→RGKOT→BUNAR→KRACAK` sebagai Bay.
  - PBRC: `GITET_BKASI`, `GITET_MTWAR`, `GITET_CWBRU`, lima `IBT_LINK`
    500/150 kV, tiga KIT dengan outlet ke `MKLMA`, `PRBRT`, `PRTRU`, serta
    stub `PDKLP`, `SKTNI`, `SMRCN` ke `BKASI`.
- `Busbar GITET` 150 kV pada `BKASI`, `MTWAR`, dan `CWBRU` dikoreksi menjadi
  `Busbar GI`; GITET 500 kV dimodelkan sebagai node terpisah agar pasangan
  GITET/GI dan IBT tidak lepas.
- Label aset yang kodenya stabil dipulihkan dari workbook lama melalui
  `samples/sources/jakban_legacy_names.json`. Rekonsiliasi memakai kode dan
  tegangan; relasi, status, dan koreksi tipe dari workbook baru tetap dipakai.
- Baris KIT ke bus dibaca ingest sebagai hubungan outlet generator. Saat
  publish, hubungan ini mengisi `GeneratingUnit.outlet_substation_id` dan
  renderer menggambar jalur vertikal generator ke bus.
- CLI `make_ss_lbk_xlsx.py`, `make_ss_gucl_xlsx.py`, dan
  `make_ss_prbc_xlsx.py` menggunakan `_reviewed_jakban.py` agar regenerasi
  berikutnya tetap mengambil file revisi, bukan SPEC historis.

## Hasil pengujian

`python -m pytest tests/test_reviewed_jakban.py tests/test_ingest.py -q`

**32 passed** pada audit utama sebelumnya; setelah penambahan boundary,
`python -m pytest tests/test_reviewed_jakban.py -q` menghasilkan **6 passed**.
Validasi parser, draft, publish, dan geometry untuk ketiga workbook tetap PASS,
tanpa dropped edge atau geometry error. Naming GI yang masih berakhiran `?`
dipertahankan sebagai label sumber ketika raster PDF tidak cukup jelas.

Diff parser lengkap tersimpan di `JAKBAN_REVIEWED_COMPARISON.json`. Perubahan
dibandingkan sebagai pasangan tak berarah; unit IBT, jumlah sirkit, dan
`single_phi` tetap ikut dibandingkan.

## Batas kesimpulan

- Workbook baru merepresentasikan satu halaman SLD dan bukti audit yang tersedia;
  kebenaran terhadap master SLD belum diverifikasi.
- Data lama tidak digabungkan otomatis karena kode GI, relasi, dan lingkupnya
  berubah. Risiko yang tidak ada pada workbook baru tetap 0 pada hasil ingest.
- `KOPO` pada GUCL dan koridor abu-abu tanpa feeder tegas tetap evidence-only.
- Beberapa nama GI masih perlu rekonsiliasi manual terhadap master karena pixel
  PDF rendah, meskipun struktur jaringan satu halaman sudah terbaca.
- Sheet `Audit_Topologi`, `Boundary_External`, `POV_Tiering`, dan `Unified_View`
  dipertahankan sebagai bukti; parser tidak mengimpor seluruh isi sheet tersebut
  sebagai constraint topologi.

## Regenerasi

```powershell
python scripts/make_ss_lbk_xlsx.py
python scripts/make_ss_gucl_xlsx.py
python scripts/make_ss_prbc_xlsx.py
python -m pytest tests/test_reviewed_jakban.py tests/test_ingest.py -q
python scripts/render_one.py samples/ss_lbk_ingest.xlsx
```
