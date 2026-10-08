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

## Pemetaan ulang risiko LBK dan PBRC — 24 September 2026

Workbook revisi LBK dan PBRC tidak membawa tabel risiko, sehingga dashboard
menampilkan kedua SS dengan 0 kerawanan. `_restore_risks` di
`_reviewed_jakban.py` kini memasang kembali baris Tabel 2.3 (LBK, 6 risiko) dan
Tabel 2.8 (PBRC, 7 risiko) dari SPEC historis builder ke topologi revisi, tanpa
mengubah aset atau relasi dari file pengguna. Langkah ini hanya berjalan bila
tabel risiko sumber kosong; GUCL tetap memakai 7 risiko dari file pengguna.

Pin mengikuti aturan lokasi (objek yang disebut Kondisi, `Multi Pin = Ya`),
daftar lengkapnya di `RISK_PINS`. Tiga objek tidak ada pada topologi revisi dan
diwakili objek terdekat yang tergambar:

| Risiko | Kondisi menyebut | Pin pada topologi revisi |
|---|---|---|
| LBK #1 | IBT-1,2 Kembangan | bus 150 kV `KMBGN` (GITET/IBT tidak dimodelkan) |
| LBK #5 | ruas Durikosambi–Cengkareng | GI `CNKNG` (Durikosambi milik SS Muarakarang) |
| PBRC #1 | interconnector Priok Timur Lama arah Priok Barat | ruas `PRTMR–PRTRU` (tidak ada ruas langsung Timur Lama–Barat) |

Sekaligus diperbaiki: nomor kerawanan pada baris Pembangkit dulu terbit sebagai
pin `SUBSTATION` yang membawa id GeneratingUnit, sehingga tergambar pada GI yang
kebetulan ber-id sama (PBRC #5, Ungaran 1,2 #8). Parser kini memasang pin itu
pada bus outlet pembangkit.

## Regenerasi

```powershell
python scripts/make_ss_lbk_xlsx.py
python scripts/make_ss_gucl_xlsx.py
python scripts/make_ss_prbc_xlsx.py
python -m pytest tests/test_reviewed_jakban.py tests/test_ingest.py -q
python scripts/render_one.py samples/ss_lbk_ingest.xlsx
```


## Pemulihan sumber tegangan LBK ? 8 Oktober 2026

Import reviewed LBK sebelumnya menghilangkan bus 500 kV dan IBT sumber. Builder kini menambahkan GITET_KMBGN dan GITET_NBRJA (500 kV), masing-masing dengan IBT unit 1 dan 2 menuju KMBGN/NBRJA (150 kV), berdasarkan SPEC dan workbook historis LBK. Bus ILKNG tetap 150 kV sesuai workbook reviewed. View FULL memakai sumber GITET tersebut dan ILKNG. Pin LBK #1 kini berada pada GITET_KMBGN; pemetaan ke bus 150 kV pada tabel historis di atas sudah digantikan. Boundary NCKUPA tetap mengikuti workbook reviewed; hubungan rencana historis ke JTAKE tidak digabungkan otomatis.

Regenerasi sample mengubah workbook dan preview berikutnya; snapshot website atau database yang telah dipublish perlu diperbarui menggunakan alur ingest/build yang sesuai.


## Audit ulang LBK per halaman ? 8 Oktober 2026

PDF asli diperiksa visual pada halaman buku 69-70 (halaman PDF 85-86). Dua view utama dipulihkan: KEMBANGAN dan BALARAJA; GABUNGAN adalah view tambahan. Anotasi audit sumber tetap disimpan terpisah dari kolom Sudut Pandang yang kini menentukan membership.

Koreksi transkripsi yang didukung label lama: UUMI?ULJMI, DLRA?BLRJA, SUJYA?SDJYA, ILKNG?LTKNG, DADAP?TLKNG2, CKDRU?CKBRU, SPTAR?SPTAN, SPTAN (bus Tier-5)?SPTAN2. Nama penuh dipulihkan setelah normalisasi kode, sehingga Ulujami, Balaraja, Sindang Jaya, Lontar, Teluknaga 2/Dadap, dan kedua Sepatan tidak lagi memakai hasil raster mentah.

PLTU Lontar dan outlet ke bus Lontar dipulihkan. TGBRU3 menjadi aset belum operasi pada Tier-2, dengan hubungan historis ke Lontar; bukan Bay dari Sindang Jaya. Bus hitam pada PDF berada di koridor Lontar?Sindang Jaya: titik switching/tap persisnya masih perlu konfirmasi teknis; hubungan rencana tidak dianggap energized. PLTD Senayan dipulihkan sebagai generator dengan GIS tersendiri pada cabang Senayan?Danayasa sesuai model historis dan Tabel 2.3; representasi GIS ini adalah pemodelan cabang yang pada gambar tampil sebagai tap. Jalur langsung Senayan?Danayasa tetap satu sirkit. Boundary GI dibatasi per view, termasuk DKSBI, PKTGN, SVRNA, PSKMS, JTKBR dan JTAKE. Kabel sisi Kembangan serta single-phi Pasar Kemis?Gajah Tunggal dipulihkan.

Batas audit: kode IIS?ITS (KTT ITS) dan JTKDR?JTKBR (Jatake Baru) telah dikonfirmasi pengguna. JTKBR adalah satu aset: full bus pada Balaraja dan boundary pada Kembangan. Hubungan silang Balaraja?Sindang Jaya?Suvarna mengikuti tracing reviewed; detail terminal dan jumlah sirkit perlu review manual. Lulus geometry memverifikasi gambar dapat dirender tanpa invariant error, bukan bukti seluruh topologi fisik telah benar. Workbook sumber pengguna tidak diubah.

Bug status lintas SS juga ditemukan: boundary future di SS Priok terbit lebih dulu dan menentukan status kanonik PDKLP/SKTNI/SMRCN. Loader kini menandai aset yang hanya diketahui dari boundary; data GI penuh yang datang kemudian melengkapi status/nama/tipe/simbol fisiknya, sementara status Bay tetap mengikuti view asal. Ini berlaku untuk snapshot baru; database existing tanpa penanda tersebut memerlukan rekonsiliasi eksplisit.

Konfirmasi konsistensi PLTD Senayan: kode GIS PLTD SNY dan PLTD SNY dipakai bersama workbook Muarakarang?Durikosambi. Outlet generator selalu menuju GIS tersebut. Keduanya Tier-3 pada Kembangan dan Tier-4 pada sisi Muarakarang, sesuai masing-masing sumber.
