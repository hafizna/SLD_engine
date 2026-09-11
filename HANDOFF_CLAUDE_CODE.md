# Handover prompt untuk Claude Code

Lanjutkan pekerjaan pada repository `mantaps-topology-engine` dari working tree
saat ini. Jangan reset atau checkout file karena working tree berisi perubahan
renderer, ingest, fixture, dokumentasi, dan Sprint A yang belum di-commit.

## Objective

1. Selesaikan quality gate geometri untuk seluruh fixture XLSX tanpa merusak
   fixture yang sudah PASS.
2. Selesaikan QA visual Sprint A dashboard Jamali dan perbaiki masalah UI yang
   nyata, tanpa mengubah algoritma SLD dalam pekerjaan shell/navigation.

## Baseline yang sudah diverifikasi

- `python -m pytest -q`: 63 test harus lulus setelah test baru ikut dihitung.
- `python scripts/audit_sample_workbooks.py` menjalankan parse, validate,
  publish ke DB sementara, render semua view, dan `geometry_errors`.
- PASS: SS_BLL, SS_CWD, SS_DKGD, SS_LBK (2 view), SS_SLCG, dan template final
  eksternal `~/Downloads/ss_muarakarang_durikosambi_ingest.xlsx` (2 view).
- FAIL yang harus diselesaikan:
  - `SS_GUCL_FULL`: 20 laporan. Mayoritas endpoint-bus crossing pada
    ANYER-KSTEL, ASAHI-POLMA, SRANG-GORDA; satu unrelated overlap
    CLBRU-MENES/CLBRU-ASAHI; tiga near-continuation.
  - `SS_PRBC_PRIOK`: PLPNG20-PKRNG / PLPRU-MGBSR near-continuation
    (spacing 14, gap 38.6).
  - `BACKBONE_500_JB_BACKBONE500`: dua near-continuation:
    IDMYU-MDCAN / CWANG-GNDUL dan GNDUL-DEPOK / KMBNG-DKSBI.
- Laporan lengkap: `.render_tmp/sample-audit/workbook-audit.json` dan
  `.render_tmp/sample-audit/WORKBOOK_AUDIT.md` (generated, gitignored).

Periksa apakah laporan endpoint-bus pada GUCL adalah defect renderer atau
false positive invariant sebelum mengubah routing. Jangan melonggarkan invariant
untuk menyembunyikan collision yang benar. Semua pasangan dua sirkit harus tetap
paralel, crossing penghantar lain memakai hop-arc, generator tetap di atas Tier-1,
dan warna tegangan tidak boleh berubah.

## Sprint A yang sudah dibuat

- `GET /api/dashboard/summary` di `app/api/routes.py` mengagregasi risk record
  secara deduplicated untuk Jamali, lima UP2B, SS, serta Sistem 500 Transmisi/IBT.
- `app/static/index.html` sekarang membuka landing Jamali dan masuk ke viewer
  lewat pin UP2B, kartu SS, atau kartu Sistem 500.
- `scripts/build_static_site.py` memakai shell UI yang sama dan menulis
  `data/dashboard-summary.json`; file duplikat `scripts/static_index.html`
  dihapus.
- Test API memastikan enam risiko SS_LBK tidak menjadi dua kali karena dua view.
- Static build sekarang memuat tujuh SS repo (LBK, BLL, CWD, DKGD, GUCL,
  PRBC, SLCG) dan backbone 500. Navigasi viewer Sistem 500 dipisahkan dari
  pohon UP2B/SS.
- Jalur metadata `Latitude`/`Longitude` sudah tersedia dari parser -> draft ->
  canonical Substation -> graph API. Longitude menjadi soft ordering hint hanya
  bila minimal dua node pada view memiliki data; workbook lama tidak berubah.

## Langkah berikutnya

1. Jalankan aplikasi, lakukan QA visual desktop dan mobile pada `/`, klik kelima
   pin, kartu SS, Sistem 500 Transmisi, tombol kembali `Peta Jamali`, lalu viewer.
   Browser visual belum tersedia pada sesi Codex terakhir, jadi ini wajib.
2. Perbaiki empty state IBT dan region kosong bila ada masalah UX. Jangan membuat
   angka atau fixture palsu untuk empat UP2B yang datanya belum tersedia.
3. Jalankan `python scripts/build_static_site.py .render_tmp/revamp-site` dan uji
   hasil statis melalui HTTP server (jangan membuka `file://`).
4. Tangani defect geometri per fixture secara bertahap; jalankan audit setelah
   setiap perubahan routing.
5. Perbarui tabel baseline di `ROADMAP.md` hanya dari output audit terbaru.

## Acceptance criteria

- Semua test lulus.
- Audit workbook keluar exit code 0, atau sisa kegagalan dijelaskan sebagai
  blocker spesifik dengan SVG dan root cause, bukan disebut lulus.
- Landing dan viewer tidak memiliki dead end pada server maupun build statis.
- Hitungan Jamali/UP2B/SS dapat direkonsiliasi ke risk record yang sama.
- Tidak ada regresi double-line, busbar collision, hop-arc, warna tegangan,
  posisi generator, bay stub, multiview, atau attachment risiko.

File dominan: `app/services/sld_layout.py`, `app/services/sld_renderer.py`,
`tests/test_sld_geometry.py` untuk quality gate; `app/static/index.html`,
`app/api/routes.py`, `scripts/build_static_site.py`, `tests/test_api.py` untuk
Sprint A. Hindari mengerjakan renderer dan shell dalam satu perubahan campuran.
