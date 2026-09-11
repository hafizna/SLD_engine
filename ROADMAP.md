# Product scope and delivery roadmap

Dokumen ini adalah brief utama untuk pekerjaan lanjutan. Codex, Claude Code, dan developer lain harus membacanya sebelum mengubah product flow, model risiko, ingest, atau viewer.

## Keputusan produk

MANTAPS saat ini adalah **dashboard peta kerawanan berbasis snapshot**. Aplikasi mendigitalisasi SLD yang diberikan P2B, menggabungkannya dengan data Buku Kerawanan, dan menghasilkan tampilan SLD yang dapat ditelusuri dan diekspor.

Scope dekat tidak mencakup kondisi jaringan real-time, SCADA, kendali operasi, atau penggantian NMM. Update mengikuti buku baru atau snapshot rekonfigurasi yang diberikan P2B.

```text
SLD/PDF terbaru P2B       Buku Kerawanan terbaru
         |                         |
         v                         v
  draft topologi Excel       draft data risiko
         |                         |
         +-----------+-------------+
                     v
          validasi dan review attachment
                     |
                     v
             publish snapshot dashboard
```

Excel adalah kontrak input deterministik. AI/CV kelak hanya menghasilkan draft Excel/JSON; AI tidak boleh langsung menulis snapshot published atau ikut dalam proses render.

## Information architecture

```text
JAMALI
|-- peta lima UP2B + populasi risiko per kategori
|-- Sistem 500 kV
|   |-- Transmisi: SLD + pin + shadowing
|   `-- IBT: SLD + pin + shadowing
`-- UP2B
    |-- populasi risiko per SS dan kategori
    `-- Subsistem
        |-- satu SLD atau multiview
        |-- pin + shadowing
        `-- detail kondisi/dampak/mitigasi/usulan
```

Kategori dibaca dari sumber dan tidak dikunci pada daftar tertentu. Kategori saat ini mencakup `N-1`, `N-2`, dan `N-1-1`. Satu risk record dihitung sekali walaupun tampil pada beberapa view atau memiliki banyak objek terdampak.

Risiko sistem 500 kV tetap berada pada scope sistem. Dampaknya pada UP2B/SS ditampilkan sebagai `terdampak risiko sistem`, terpisah dari risiko lokal agar tidak terjadi double counting.

## Pin dan shadowing

Setiap risiko memiliki satu **primary attachment** tempat pin nomor ditampilkan dan nol atau banyak **affected objects** yang disorot saat risiko dipilih. Attachment dapat menunjuk circuit, GI/GIS/GITET, IBT, atau bay. Affected scope juga dapat menunjuk SS atau wilayah.

Saat risiko dipilih, objek utama mendapat highlight kuat, affected objects mendapat shadow ringan, dan objek lain diredupkan. Mekanisme yang sama berlaku pada SLD Transmisi 500, SLD IBT, dan SLD SS.

Risiko pembangkit/peralatan yang tidak mempunyai representasi tepat pada SLD ditampilkan pada menu tersendiri. Jangan membuat pin semu.

## Tier, subsystem, dan multiview

- Batas SS berasal dari snapshot konfigurasi P2B.
- SLD sistem dapat memperlihatkan beberapa SS sekaligus. Blok ungu pada contoh sistem Jakban adalah SS Cawang-Depok.
- Multiview membagi tampilan **satu SS** yang terlalu besar menjadi dua atau tiga view. Aset fisik tidak diduplikasi.
- Tier adalah band vertikal analitis, bukan parent-child tree.
- Posisi geografis dapat menjadi constraint horizontal, terutama pada SLD sistem, tetapi tetap tunduk pada tier, konektivitas, dan keterbacaan.
- Jarak tier tumbuh per gap yang padat. Generator selalu paling atas dan penghantar tidak boleh melintasi zona generator.
- Latitude/longitude adalah metadata referensi urutan horizontal, bukan posisi
  absolut dan bukan penentu Tier. Longitude hanya dipakai sebagai soft
  tie-break apabila sedikitnya dua GI pada satu view memiliki koordinat; tanpa
  koordinat, layout lama tidak berubah. Constraint crossing, jarak busbar,
  port, dan keterbacaan tetap lebih kuat daripada urutan geografis.

## Alur update snapshot

1. Upload SLD/Excel terbaru.
2. Parse dan tampilkan preview.
3. Tampilkan diff terhadap snapshot published.
4. Upload/parse Buku Kerawanan terbaru.
5. Review primary attachment setiap risiko.
6. Pilih affected objects untuk shadowing.
7. Validasi kelengkapan dan konflik.
8. Publish dengan effective date.
9. Pertahankan snapshot lama untuk audit.

Diff minimum mencakup node/circuit baru atau hilang, jumlah sirkit, status, tier, batas SS, view, serta attachment risiko yang tidak lagi valid.

## Roadmap sprint

## Baseline fixture dan quality gate (11 September 2026, diperbarui setelah sesi Claude Code)

Audit dapat diulang dengan `python scripts/audit_sample_workbooks.py`. Setiap
workbook masuk melalui jalur produksi parse -> validate -> publish sementara ->
render semua view -> invariant geometri. Laporan rinci ditulis ke
`.render_tmp/sample-audit/WORKBOOK_AUDIT.md` dan
`.render_tmp/sample-audit/workbook-audit.json` (generated, gitignored).

| Fixture | View | Status |
|---|---:|---|
| SS Balaraja-Lengkong | 1 | PASS |
| SS Cawang-Depok | 1 | PASS |
| SS Daya-Gandul | 1 | PASS |
| SS Gandul-Cilegon | 1 | **FAIL: 2 near-continuation** (turun dari 20 temuan) |
| SS Lontar-Balaraja-Kembangan | 2 | PASS |
| SS Priok-Bekasi-Cawang | 2 | **FAIL: 1 near-continuation** |
| SS Suralaya-Cilegon | 1 | PASS |
| SS Muarakarang-Durikosambi (template final eksternal) | 2 | PASS |
| SS Bali | 1 | PASS (setelah perbaikan soft-band router) |
| SS Pelabuhan Ratu-Salak-Cibinong 1,2-Depok 2 | 2 | **FAIL: 1 near-continuation** |
| SS Bekasi 1,3-Cibinong 3 | 1 | PASS |
| SS Gandul 2,4 | 1 | PASS |
| SS New Tambun (Jabar) | 1 | PASS |
| SS Sukatani 1,2 (Jabar) | 1 | PASS |
| SS Tasikmalaya 1,2 (Jabar) | 1 | PASS |
| SS Cibatu 1,2-Deltamas 1,2 (Jabar) | 1 | PASS |
| SS Cirata 1,2,3 (Jabar) | 1 | PASS |
| SS Pemalang 1,2 (Jateng) | 1 | PASS |
| SS Boyolali 1,2 (Jateng) | 1 | PASS |
| SS Kesugihan 1,2 (Jateng) | 1 | PASS |
| SS Krian 3,4,5,6 (Jatim) | 1 | PASS |
| SS Kediri 1,2 (Jatim) | 1 | PASS |
| SS Paiton 1,2,3 (Jatim) | 1 | PASS |
| Backbone 500 kV | 1 | **FAIL: 1 near-continuation** (turun dari 2 temuan) |

Dengan demikian dua puluh tiga SS dapat diparse dan dirender. SS GUCL, SS PRBC
dan SS Pelabuhan Ratu masih memiliki temuan near-continuation. Backbone 500 kV
dihitung sebagai fixture sistem tersendiri. Fixture berstatus FAIL tidak boleh
dinyatakan production-ready atau dipakai sebagai bukti bahwa renderer sudah
menangani semua pola.

### Perluasan ke UP2B Jawa Barat

Lima dari tujuh subsistem Jawa Barat sudah dibangkitkan; sisa dua (Cibatu 3,4 -
PLTU Indramayu - Mandirancan 1,2 dengan 19 kerawanan, dan Bandung Selatan 1,2 -
New Ujungberung 1,2 dengan 12) belum dikerjakan.

| Subsistem | Sec | Halaman tabel | Aset | Ruas | Kerawanan |
|---|---|---|---:|---:|---:|
| New Tambun | 3.8 | 136-137 | 10 | 7 | 2 |
| Sukatani 1,2 | 3.9 | 138-140 | 11 | 8 | 2 |
| Tasikmalaya 1,2 | 3.7 | 133-135 | 16 | 11 | 5 |
| Cibatu 1,2 - Deltamas 1,2 | 3.5 | 123-126 | 30 | 23 | 8 |
| Cirata 1,2,3 | 3.4 | 119-122 | 37 | 29 | 10 |

Rentang halaman tabel diambil dari penomoran risiko per halaman, BUKAN dari
halaman judul seksi. Tabel satu subsistem berlanjut melewati judul seksi
berikutnya, sehingga rentang berbasis judul diam-diam menarik baris tetangga --
New Tambun sempat membawa risiko #5 milik Tasikmalaya. `as_risk_dicts` sekarang
menolak rentang yang penomorannya bukan 1..N berurutan.

Kotak abu-abu dengan nama pemilik dalam kurung pada Gambar 3.4-3.12 adalah aset
subsistem tetangga, bukan GI subsistem tersebut, dan dimodelkan SOURCE_BOUNDARY.
Beberapa di antaranya sudah muncul dari sisi seberang: TMBUN pada sheet New
Tambun, BKASI/KSBRU/DWUAN pada sheet Bekasi 1,3 - Cibinong 3, dan MNANG pada
sheet Kesugihan 1,2.

### UP2B Jakarta & Banten lengkap + perbaikan renderer IBT 150/70

Tiga subsistem Jakban terakhir dibangkitkan dari Peta Kerawanan per-SS (Gambar
2.10-2.12), bukan dari Lampiran-1 -- gambar per-SS jauh lebih terbaca dan sudah
membawa pita Tier, bay stub, serta pin kerawanan.

| Subsistem | Sec / Tabel | Halaman PDF | Aset | Ruas | Kerawanan | View |
|---|---|---:|---:|---:|---:|---:|
| Pelabuhan Ratu-Salak-Cibinong 1,2-Depok 2 | 2.11 / Tabel 2.9 | 101-104 | 41 | 31 | 8 | 2 |
| Bekasi 1,3-Cibinong 3 | 2.12 / Tabel 2.10 | 104-106 | 17 | 12 | 3 | 1 |
| Gandul 2,4 | 2.13 / Tabel 2.11 | 107-110 | 8 | 5 | 1 | 1 |

Pelabuhan Ratu memakai jalur multiview: satu graf GI kanonik, dua `Sudut
Pandang` (CIBINONG dan SALAK) sesuai dua panel gambar buku. BGBRU, SNTUL dan
KTLPA muncul di kedua panel dan terekonsiliasi menjadi satu substation kanonik,
sementara kedelapan risiko tetap dihitung sekali.

Kotak abu-abu "UP2B 2 (JABAR)" pada Gambar 2.10/2.11 adalah aset UP2B Jawa Barat
yang dijangkau subsistem ini (Sukatani, New Tambun, Cugenang, Lengkong Dar),
bukan GI subsistem Jakban. Semuanya dimodelkan sebagai SOURCE_BOUNDARY.

Tiga defect renderer ditemukan dan diperbaiki saat pekerjaan ini:

1. `app/services/ingest.py` memberi label `500/150` pada SETIAP IBT dan menyimpan
   `voltage_kv=500`. Rasio sekarang diturunkan dari tegangan kedua bus, sehingga
   IBT 150/70 (Cibinong, Semen Baru, Cibadak) terlabel benar.
2. Sisi HV IBT ditentukan dari tipe aset (GITET). Untuk step-down di dalam
   jaringan 150 kV tidak ada GITET di kedua ujung, sehingga arah terbalik dan
   menghasilkan IBT "70/150". Sekarang jatuh ke perbandingan tegangan bus.
3. `app/services/sld_renderer.py` hanya menggambar rantai IBT bila sisi HV-nya
   GITET, sehingga step-down 150/70 hilang dari gambar dan jaringan 70 kV
   tampil sebagai pulau terputus. Rantai sekarang digambar untuk sisi HV mana
   pun; bus GITET tetap melayang di atas bus yang dipasoknya, sedangkan bus
   150 kV biasa mempertahankan baris Tier dan penghantarnya sendiri, dan rantai
   yang bergeser horizontal dirutekan turun-menyamping-turun.

Selain itu pita `soft_bands` router diperlebar `NEAR_CONT_GAP` melewati rentang
rute lain, karena dua penghantar horizontal panjang yang bersambung ujung ke
ujung terbaca sebagai satu konduktor walau tidak beririsan pada sumbu x. Ini
menghilangkan tiga temuan near-continuation pada SS Bali dan satu pada SS GUCL.
Ambang penalti sendiri tetap `CHANNEL_PITCH`: menaikkannya ke 40 justru membuat
SS Kesugihan yang tadinya lulus menjadi gagal.

### Perluasan ke UP2B Jateng & DIY dan UP2B Jawa Timur

Enam subsistem di luar Jakarta-Banten dibangkitkan langsung dari Buku Kerawanan
SJB 2026 memakai template ingest yang sama (`scripts/_ss_xlsx_common.py`):

| Subsistem | Sec / Tabel | Halaman PDF | Aset | Ruas | Kerawanan |
|---|---|---:|---:|---:|---:|
| Pemalang 1,2 | 4.8 / Tabel 4.6 | 173-175 | 11 | 8 | 4 |
| Boyolali 1,2 | 4.9 / Tabel 4.7 | 175-178 | 9 | 7 | 4 |
| Kesugihan 1,2 | 4.7 / Tabel 4.5 | 165-172 | 27 | 28 | 18 |
| Krian 3,4,5,6 | 5.4 | 197-201 | 16 | 12 | 8 |
| Kediri 1,2 | 5.6 | 206-208 | 14 | 10 | 6 |
| Paiton 1,2,3 | 5.9 | 228-237 | 16 | 13 | 8 |

Teks kerawanan diekstrak verbatim dari tabel PDF oleh
`scripts/_kerawanan_tables.py`, bukan diketik ulang; modul itu juga membuang
header/footer halaman yang ikut masuk ke sel saat baris terpotong antar halaman.
Topologi ditelusuri dari Lampiran-3 (Jateng & DIY, PDF p.250) dan Lampiran-4
(Jawa Timur, PDF p.251), yang mewarnai tiap subsistem sehingga keanggotaan GI
dibaca dari gambar. Ruas yang label sirkitnya tidak terbaca pasti tetap perlu
verifikasi terhadap SLD native sebelum dipakai operasional.

Catatan sumber Bali: peta kerawanan Buku Kerawanan dipakai untuk Tier, nomor,
dan konteks risiko. Daftar GI/GIS, hubungan penghantar, bus section, bay,
trafo/kapasitor, dan pembangkit harus direkonsiliasi terhadap referensi rinci
`Single Line Bali 2026`. `PESANGGARAN` (GI/AIS) dan `GIS_PESANGGARAN` adalah
dua node berbeda; keduanya sudah ada di fixture, tetapi rincian bay/asetnya
belum diaudit penuh terhadap referensi tersebut.

### Perbaikan sesi ini (11 September 2026, Claude Code)

Dua defect nyata diperbaiki di root cause, bukan dilonggarkan di checker:

1. **False positive checker "crosses its endpoint bus"** (16 dari 20 temuan
   GUCL) — `tests/test_sld_geometry.py::geometry_errors` menandai crossing
   berdasarkan y saja tanpa memverifikasi x segmen berada dalam rentang bus
   tersebut. Karena banyak bus berbagi ketinggian-y yang sama (satu tier),
   setiap segmen vertikal di titik x manapun yang kebetulan melewati y itu ikut
   tertandai. Diperbaiki dengan menambahkan syarat `l <= x <= r` (rentang bus).
2. **Overlap nyata SUTT_CLBRU_MENES/SUTT_CLBRU_ASAHI** (GUCL) —
   `OrthogonalRouter._cost` di `sld_layout.py` hanya memblokir dua segmen
   sejajar-berdekatan bila rentang-y-nya *strictly* tumpang tindih; dua segmen
   yang hanya *bersinggungan* di satu titik y lolos tanpa block, padahal
   setelah offset bundle +/-7 unit keduanya benar-benar bertabrakan. Diperbaiki
   dengan mengubah syarat overlap dari `<` ketat menjadi `<=` (inklusif
   singgung), plus melebarkan pita penalti `COLLINEAR_TOUCH_PENALTY` dari
   `< CHANNEL_PITCH` menjadi `<= CHANNEL_PITCH` supaya router tidak konvergen
   ke jarak minimum legal (32) sebagai default tanpa penalti sama sekali.

Satu defect data/warna tegangan yang **tidak berkaitan dengan geometri**
ditemukan dan diperbaiki di sesi yang sama: `app/services/ingest_parser.py`'s
`_kv()` kehilangan badan fungsinya (ke-orphan di bawah `return` milik
`_coordinate()`, kemungkinan tabrakan edit bersamaan saat fitur
Latitude/Longitude ditambahkan), sehingga SEMUA `voltage_hv_kv` terparse
sebagai `None` dan setiap sirkit/bus jatuh ke warna fallback merah `#C00000`
(warna 150 kV), termasuk sirkit 500 kV dan bus GITET. Diverifikasi setelah
perbaikan: bus 150 kV pada GUCL tetap merah, hanya `GITET_CLBRU` (sisi 500 kV)
yang biru; backbone 500 kV seluruhnya biru `#0047AB`, bukan lagi campuran
merah. Tidak ada override warna manual — hanya memulihkan parsing input.

### Blocker near-continuation yang tersisa (4 temuan, 3 fixture)

Root cause sudah diverifikasi: keempatnya adalah **pasangan dua sirkit yang
TIDAK berbagi bus** (dikonfirmasi lewat endpoint check), jalurnya kebetulan
sejajar-berdekatan (jarak 14-39 unit; ambang checker `spacing<40 and gap<40`)
di diagram padat. Tidak ada overlap kabel nyata (checker "unrelated wires
overlap" dan "conductors intersect" tidak ikut menyala untuk keempatnya) —
murni heuristik visual "berpotensi dibaca sebagai satu garis lurus".

- `SS_GUCL_FULL`: `SUTT_ASAHI_POLMA`/`SUTT_CLBRU_MENES` (spacing=39.0, gap=39.0)
- `SS_GUCL_FULL`: `SUTT_MNA_KRWTU`/`SUTT_CLGON_MITSUI` (spacing=25.0, gap=35.2)
- `SS_PRBC_PRIOK`: `SUTT_PLPNG20_PKRNG`/`SUTT_PLPRU_MGBSR` (spacing=14.0, gap=38.6)
- `BACKBONE_500_JB_BACKBONE500`: `SUTT_GNDUL_DEPOK`/`SUTT_KMBNG_DKSBI` (spacing=32.0, gap=15.3)
Root cause arsitektural: grid `OrthogonalRouter` (`sld_layout.py`) memakai
`CHANNEL_PITCH = 32` sebagai jarak antar-lane, sementara checker menandai
"near-continuation" untuk jarak `<40`. Grid tidak dapat menjamin hasil >=40
tanpa lompat ke lane berikutnya (+32 lagi), yang membuat banyak rute lain
berpotensi infeasible pada diagram sepadat GUCL/PRBC/backbone. Percobaan
menaikkan `COLLINEAR_TOUCH_PENALTY` (22 -> 60) hanya memindahkan pasangan mana
yang kena, bukan menghilangkan totalnya — bukan solusi.

Opsi yang dipertimbangkan dan sengaja ditunda (keputusan user, 11 September
2026): melonggarkan ambang checker dari `<40` ke `<=32` (samakan dengan grid
pitch asli), atau memperhalus grid router. Keduanya butuh keputusan desain,
bukan tuning coba-coba, dan disimpan sebagai pekerjaan lanjutan eksplisit
alih-alih diputuskan sepihak oleh agent.

### A. Shell produk dan navigasi

- Landing page peta Jawa-Madura-Bali.
- Lima UP2B dengan badge populasi dan filter kategori.
- Navigasi Jamali -> UP2B -> SS.
- Navigasi Jamali -> Sistem 500 -> Transmisi/IBT.

Selesai bila tidak ada dead end dan seluruh halaman memakai data fixture yang sama. Sprint ini tidak mengubah algoritma SLD.

Status: **in progress**. Shell FastAPI dan snapshot statis sekarang memakai
satu `app/static/index.html`, memiliki landing Jamali, lima titik UP2B, populasi
risiko per kategori, kartu Sistem 500 kV Transmisi/IBT, daftar SS, serta jalur
kembali dari viewer. API agregasi menghitung `RiskRecord`, bukan kemunculan per
view. Snapshot statis memuat sembilan SS dari fixture repo dan satu backbone 500
kV. Workspace Sistem 500 dipisahkan dari navigasi SS agar backbone tidak tampil
sebagai subsistem. QA visual responsif dan data fixture lima UP2B masih perlu
dilengkapi.

### B. Risk affected objects dan shadowing

- Tambahkan relasi affected-object tanpa menggandakan `RiskRecord`.
- Endpoint/UI untuk primary attachment dan affected objects.
- Selected, shadowed, dan dimmed state pada SVG/viewer.
- Gambar satu bidang transparan di belakang gabungan objek terdampak. Gunakan
  padding yang cukup, sudut membulat, dan opacity rendah agar warna tegangan
  serta status aset tetap terbaca dan tidak berubah.
- Untuk dampak yang terpisah secara geografis, gambar beberapa bidang per
  kelompok terhubung, bukan satu kotak besar yang menutupi area aman di
  antaranya. Risiko berscope `SUBSYSTEM` boleh menaungi seluruh area SLD.
- Daftar affected objects wajib berasal dari data risiko yang direview; viewer
  tidak boleh menebak cakupan hanya dari posisi visual atau kedekatan node.
- Terapkan pada Transmisi 500, IBT, dan SS.

Selesai bila satu risiko dapat menyorot banyak objek dengan hitungan tetap satu.

### C. Halaman UP2B dan SS

- Agregasi kategori per SS.
- Kartu SS berisi total, kategori, prioritas, dan tanggal snapshot.
- Hubungkan seluruh SLD/multiview yang tersedia.
- Samakan filter dan panel detail risiko pada semua level.

Selesai bila angka Jamali, UP2B, dan SS dapat direkonsiliasi ke risk record yang sama.

### D. Workflow update snapshot

- Draft topologi dan risiko untuk versi baru.
- Diff terhadap versi published.
- Queue attachment yang harus dipetakan ulang.
- Review dan publish dengan effective date.
- Riwayat snapshot tidak ditimpa.

### E. Adapter AI/CV

- Schema output terstruktur dan confidence.
- Integrasi provider di service terpisah.
- Output selalu draft Excel/JSON.
- Evaluasi terhadap SLD yang sudah dimodelkan.

Jangka panjang, adapter NMM/CIM dapat menghasilkan kontrak ingest yang sama tanpa mengubah topology engine dan renderer.

## Handoff Codex dan Claude Code

Gunakan satu sprint dan satu acceptance criterion per branch/PR. Jangan menjalankan dua agen pada `sld_renderer.py`, `ingest.py`, atau satu file UI yang sama secara bersamaan.

| Workstream | File dominan | Catatan |
|---|---|---|
| Shell/navigation | `app/static/index.html`, static-site template | Pisahkan dari perubahan renderer |
| Risk model/API | `app/models.py`, routes, service risiko | Satu pemilik perubahan schema |
| SVG shadowing | `sld_renderer.py`, viewer CSS/JS | Jangan paralel dengan routing |
| Snapshot/diff | `ingest.py`, version model, ingest UI | Jangan paralel dengan ingest schema |
| AI adapter | module adapter baru | Tidak perlu mengubah renderer |
| Fixture SLD | `samples/`, workbook builders | Satu workbook per task |

Setiap handoff wajib menyebutkan objective dan acceptance criteria, file yang diubah, perubahan schema/data, perintah test dan hasilnya, artefak SVG/screenshot, asumsi domain yang belum dikonfirmasi, serta pekerjaan yang sengaja tidak disentuh.

## Di luar scope dekat

- status dan operasi real-time;
- simulasi atau kendali jaringan;
- kesimpulan state coupler tanpa pola operasi;
- penggantian NMM;
- approval korporat berjenjang;
- publish otomatis dari hasil AI tanpa review.

