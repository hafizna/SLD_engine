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

## Baseline fixture dan quality gate (11 September 2026)

Audit dapat diulang dengan `python scripts/audit_sample_workbooks.py`. Setiap
workbook masuk melalui jalur produksi parse -> validate -> publish sementara ->
render semua view -> invariant geometri. Laporan rinci ditulis ke
`.render_tmp/sample-audit/WORKBOOK_AUDIT.md`.

| Fixture | View | Status |
|---|---:|---|
| SS Balaraja-Lengkong | 1 | PASS |
| SS Cawang-Depok | 1 | PASS |
| SS Daya-Gandul | 1 | PASS |
| SS Gandul-Cilegon | 1 | **FAIL: 20 temuan geometri** |
| SS Lontar-Balaraja-Kembangan | 2 | PASS |
| SS Priok-Bekasi-Cawang | 2 | **FAIL: 1 near-continuation** |
| SS Suralaya-Cilegon | 1 | PASS |
| SS Muarakarang-Durikosambi (template final eksternal) | 2 | PASS |
| Backbone 500 kV | 1 | **FAIL: 2 near-continuation** |

Dengan demikian delapan SS memang dapat diparse dan dirender, tetapi baru enam
yang lolos quality gate geometri. Backbone 500 kV dihitung sebagai fixture
sistem tersendiri, bukan SS kedelapan. Fixture berstatus FAIL tidak boleh
dinyatakan production-ready atau dipakai sebagai bukti bahwa renderer sudah
menangani semua pola.

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
view. QA visual responsif dan data fixture lima UP2B masih perlu dilengkapi.

### B. Risk affected objects dan shadowing

- Tambahkan relasi affected-object tanpa menggandakan `RiskRecord`.
- Endpoint/UI untuk primary attachment dan affected objects.
- Selected, shadowed, dan dimmed state pada SVG/viewer.
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
