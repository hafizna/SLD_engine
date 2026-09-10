# Nota Konsep — Bisnis Proses Peta Kerawanan

> **Draf untuk diskusi tim.**
> Kasus uji: COD GITET New Cikupa. Basis: *Buku Kerawanan SJB 2026* §2.5.
> Slice: SS Lontar–Balaraja–Kembangan (41 GI, 49 penghantar, 6 kerawanan, 3 view).

Hari ini tidak ada basis data di belakang SLD P2B — semua digambar tangan. Repo ini
mengusulkan basis data itu: begitu topologi tersimpan terstruktur, perubahan jaringan
(GITET baru, subsistem dipecah, penghantar putus bertahun) cukup diubah lewat *register*,
dan peta, Tier, serta titik kerawanan ikut menyesuaikan. Dokumen ini menunjukkan alurnya
lewat satu kasus nyata, plus jawaban jujur atas "apakah repo ini kejauhan?".

---

## 1. Premis — masalahnya bukan menggambar, tapi tidak ada basis data di belakang gambar

SLD di Buku Kerawanan hari ini digambar tangan — Visio, Corel, atau AutoCAD — lalu
ditempel ke dokumen. **Tidak ada basis data topologi** yang jadi sumbernya. Setiap
perubahan jaringan berarti seseorang membuka file gambar, menata ulang, mengekspor lagi.
Untuk perubahan kecil merepotkan; untuk perubahan masif — satu GITET baru mengubah pola
suplai seluruh wilayah — praktis tidak akan dikerjakan, dan peta kerawanan pelan-pelan
jadi basi tanpa ada yang tahu.

Repo ini adalah usulan basis data itu — "DB Sistem" yang menyimpan topologi 500 / 150 kV
secara terstruktur, lalu **menghasilkan** SLD dan peta kerawanan dari situ. Fondasinya
sedang dibangun dengan cara reverse-engineering: SLD yang ada dibaca manual, dituangkan
ke bentuk terstruktur, sebagai benih isi DB.

Ide alternatif — "klik titik manual di atas SLD yang di-upload" — tidak menyelesaikan
masalah ini: titik kerawanan jadi terikat ke *piksel* gambar. Ganti gambar, semua titik
meleset, plot ulang dari nol.

> **Simpan satu topologi.** Titik kerawanan menempel ke *objek* — IBT Kembangan 1,
> ruas Cikupa–Jatake — bukan ke koordinat. SLD adalah hasil render posisi objek,
> bukan sumber kebenaran.

Dengan model itu, mengubah peta = mengedit beberapa baris di register. Sisanya dihitung mesin.

---

## 2. Kosakata — dua kelas perubahan, jangan dicampur

Kebanyakan kebingungan proses datang dari menyamakan dua hal yang beda pemilik, beda
frekuensi, beda sifat. *Keduanya lewat form yang sama, tapi register-nya terpisah.*

| | **Perubahan struktural** | **Pola operasi** |
|---|---|---|
| **Contoh** | GITET New Cikupa COD; SKTT Petukangan–Senayan rusak 2 tahun; IBT baru; GI baru; subsistem dipecah | Bus split; kopel dibuka; feeder dialihkan sementara saat pemeliharaan; islanding; looping |
| **Topologi fisik** | **Berubah.** Aset betul bertambah / hilang / berpindah | **Sama.** Yang berubah hanya status hubung (CB open/close) |
| **Sifat** | Permanen sampai perubahan berikutnya. Versi lama jadi *superseded*, tidak dihapus | Reversibel dan berjangka waktu. Ada tanggal mulai & berakhir |
| **Pemilik** | Perencana / P2B aset | Dispatcher / operasi |
| **Di repo** | `TopologyVersion` + `ChangeSet` (sudah ada) | `scenario_id` pada circuit & view (hook sudah ada, register belum) |

Kasus **"SKTT putus bertahun"** adalah **perubahan struktural**, bukan pola operasi: satu
perubahan yang men-set ruas itu `DE_ENERGIZED` dengan tanggal berlaku, lalu satu perubahan
lagi yang mengembalikannya saat perbaikan selesai. Buku kerawanan memang "berubah permanen"
selama periode itu — dan itu benar, karena memang begitu kondisi sistemnya.

**Register pola operasi belum jadi prasyarat.** Hook `scenario_id` sudah ada; tabel tipisnya
ditambah nanti saat dispatcher betul-betul butuh skenario split-bus di peta.

---

## 3. Kasus — COD GITET New Cikupa → lahir subsistem baru

Di slice sekarang, GITET New Cikupa adalah node berstatus `NEW_NOT_ENERGIZED` (busbar hitam
di SLD) — ada di peta sebagai informasi, tidak ikut hitungan Tier. Saat GITET ini benar
beroperasi, IBT 500/150-nya menyuntik bus 150 kV baru, beban GI Tangerang dan sekitarnya
berpindah ke sana, dan sebagian GI lepas dari SS Lontar–Balaraja–Kembangan membentuk
subsistem sendiri.

**Konvensi warna busbar (Buku Kerawanan SJB 2026 — sudah dipetakan ke enum status di engine):**

| Warna | Arti |
|---|---|
| merah / oranye | 150 kV energized |
| hitam | dibangun, belum energize |
| abu-abu | masih rencana |
| biru | 500 kV |

Yang **tidak** P2B kerjakan: membuka file Visio, menata ulang 40-an GI, mengekspor PDF baru,
lalu plot ulang 6 titik kerawanan. Yang P2B kerjakan ada di bawah — tiga langkah form,
masing-masing beberapa isian.

### Langkah 1 — Naikkan status GITET New Cikupa

Node sudah ada di register sejak proyek dicatat. Ini bukan "tambah objek", cuma ganti status.

| Isian | Nilai |
|---|---|
| Objek | `NCKUPA` — GITET New Cikupa (500 kV) *(terkunci)* |
| Status | `NEW_NOT_ENERGIZED` → **`ENERGIZED`** |
| Berlaku sejak | `2026-11-01` |

Peta sebelum tanggal ini tetap bisa dibuka apa adanya (versi lama = superseded).

**Efek mesin:** IBT 500/150 New Cikupa jadi seed Tier-1 baru untuk sisi Balaraja. Belum ada
GI yang tersambung ke situ — itu langkah 2.

### Langkah 2 — Sambungkan & pindahkan beban

Tabel penghantar subsistem. Tambah baris, hapus baris, ubah status. Tidak ada kanvas.

| Dari | Ke | Jenis | Sirkit | Aksi |
|---|---|---|---:|---|
| `NCKUPA` | Cikupa Baru | `IBT_LINK` | 2 | **tambah** |
| `CKBRU` | Tangerang | `SUTT` | 2 | **tambah** |
| `CKUPA` | Tangerang | `SUTT` | 1 | **putus** |
| `PSKMS` | Pasar Kemis Baru | `SUTT` | 1 | tetap |

**Pratinjau dampak — dihitung otomatis:**

- ✅ Tangerang, Jatake Baru, Gajah Tunggal kini bersumber dari New Cikupa — Tier dihitung ulang dari seed baru
- ⚠️ Ruas Cikupa–Jatake (Kerawanan #4) — kondisi "bay panjang" hilang; risiko ditandai *perlu dinilai ulang*
- ✅ 0 objek jadi tak-tersambung · 0 konflik penghantar

Setiap baris yang diedit dicatat sebagai satu entri `ChangeSet` — jejak perubahan otomatis,
tanpa mengisi log terpisah.

### Langkah 3 — Keanggotaan & penamaan subsistem

Ini inti yang dimaksud: seringkali cukup ubah register keanggotaan, kadang beri nama
subsistem baru.

| Isian | Nilai |
|---|---|
| Subsistem baru | SS GITET Cikupa — Tangerang – Jatake Baru |
| Kode | `SS_NCKUPA_TGR` (dibuat otomatis). Sumber: RUPTL. |

| GI | Peran | Pindah dari | Aksi |
|---|---|---|---|
| Tangerang | `CORE` | `SS_LBK` | **masuk** |
| Jatake Baru | `CORE` | `SS_LBK` | **masuk** |
| Gajah Tunggal | `CORE` | `SS_LBK` | **masuk** |
| Cikupa Baru | `SOURCE_BOUNDARY` | — | **masuk** |

**Dampak ke SS Lontar–Balaraja–Kembangan:**

- 3 GI keluar dari `SS_LBK` — objek fisiknya **tidak** dihapus, hanya keanggotaannya
- Kerawanan #4 (Cikupa–Jatake) ikut pindah konteks ke subsistem baru
- SLD kedua subsistem di-generate ulang — tidak ada yang digambar tangan

Satu GI fisik boleh jadi anggota beberapa subsistem dengan peran berbeda — disimpan sekali,
seperti Durikosambi (`BOUNDARY` di sini, `CORE` di SS Muarakarang).

---

## 4. Bisnis proses, ujung ke ujung

Nomor menandai urutan nyata — tiap langkah bergantung pada yang sebelumnya. Aktor: **P2B**
atau **Mesin**.

| # | Langkah | Aktor | Isi |
|---|---|---|---|
| 01 | **Ajukan perubahan** | P2B | Isi form: naikkan status, tambah/hapus penghantar, atur keanggotaan & nama subsistem. Beberapa baris, bukan gambar. |
| 02 | **Validasi otomatis** | Mesin | Cek: tidak ada GI jadi terisolasi tanpa alasan, seed Tier masih ada, tidak ada penghantar konflik (A bilang ke Bus X, B bilang ke Bus Y). |
| 03 | **Pratinjau dampak** | Mesin | SLD baru + Tier baru + daftar kerawanan yang berpindah Tier / berubah konteks / perlu dinilai ulang. Ini yang di-review, bukan gambarnya. |
| 04 | **Tinjau teknis** | P2B | Rekan P2B memeriksa diff. Setuju → lanjut. Perlu koreksi → kembali ke 01. (Tahap approval formal bisa ditambah belakangan — belum wajib untuk versi awal.) |
| 05 | **Terbitkan versi** | P2B | Topologi baru jadi `ACTIVE` dengan tanggal berlaku; versi lama jadi `SUPERSEDED` — tetap bisa dibuka. Peta kerawanan resmi ikut versi aktif. |
| 06 | **Peta & register menyesuaikan** | Mesin | Semua view (500 kV backbone, IBT 500/150, subsistem) yang menyentuh objek itu di-proyeksikan ulang. Ekspor tabular tinggal di-generate bila perlu. |

Beban nyata P2B ada di langkah **01** dan **04** saja — mengisi beberapa isian dan membaca
diff. Bukan menggambar ulang SLD, bukan menata ratusan objek.

---

## 5. Apakah repo sekarang kejauhan?

Sebagian ya — tapi bukan di tempat yang mungkin dikira. Yang berat adalah **bootstrap awal**:
karena belum ada DB Sistem, SLD yang ada harus dibaca manual dan dituangkan ke bentuk
terstruktur. Satu subsistem penuh makan sekitar 5 jam, dan meski sumber datanya sudah
selengkap Buku Kerawanan, hasilnya belum mulus — apalagi kalau diserahkan penuh ke konversi
otomatis. Tapi ini **kerja sekali per subsistem**. Begitu topologi masuk repo, BAU-nya cuma
update register — tidak baca ulang gambar, tidak upload ulang. Pain-nya di depan, dan sedang
dikerjakan sekarang.

| Verdikt | Bagian | Alasan |
|---|---|---|
| **Pertahankan** | Topologi relational, bukan gambar | Ini bukan over-engineering — ini satu-satunya cara "edit → peta menyesuaikan" bisa jalan. Membuangnya = kembali ke plot-titik-manual yang sudah ditolak. |
| **Pertahankan** | Kerawanan menempel ke objek; Tier dihitung | Kedua hal ini yang membuat regenerate peta otomatis mungkin. Sudah terbukti di slice SS_LBK. |
| **Pertahankan** | Bootstrap manual dari gambar, sekali per subsistem | Berat dan belum mulus — tapi kerja satu kali di depan, bukan BAU. Setelah topologi masuk repo, tidak ada baca-ulang gambar. Urutannya benar: fondasi dulu. |
| **Rampingkan** | Bentuk staging yang lebar & banyak tabel | Wajar untuk menuangkan satu subsistem pertama. Tapi jangan jadi cara BAU: update rutin lewat form web, bukan mengisi tabel lebar. Ekspor tabular cukup jadi *review / arsip*. |
| **Rampingkan** | Tabel `Bay` / `Device` / `BusSection` | Sudah nullable dan tak dipakai peta kerawanan. Biarkan di skema, tapi jangan pernah muncul di dokumen konsep atau form P2B. |
| **Nanti** | Workflow approval berjenjang | `TopologyVersion` / `ChangeSet` cukup jadi changelog dulu. Approval formal ditambah sebagai lapisan di atas endpoint tulis yang sama, saat sudah dipakai. |
| **Nanti** | Register pola operasi | Bukan prasyarat. Hook `scenario_id` sudah ada. Tambah tabel tipis saat dispatcher betul-betul butuh skenario split-bus di peta. |

### Soal NMM yang sudah berdiri

Arah ke NMM/CIM benar dan tidak perlu ditunda — justru itu alasan struktur kanonik dibuat
netral, supaya nanti tinggal ganti sumber tanpa membongkar engine, view, dan API. Yang perlu
dikonfirmasi ke tim NMM **sebelum** membaca banyak subsistem manual:

- **Apakah NMM sudah menyimpan *connectivity* antar-GI 500/150 kV** — bukan sekadar daftar
  aset, tapi relasi "GI A tersambung ke GI B lewat penghantar C"?
- Jika ya: bikin adapter baca-sekali. Tidak perlu membaca ulang 41 GI + 49 penghantar per
  subsistem dari gambar — itu datang dari NMM. Kerja P2B tinggal lapisan tipis: batas
  subsistem, peran, konteks risiko. Beban bootstrap turun drastis.
- Jika tidak (NMM cuma registri aset tanpa relasi): pembacaan manual per subsistem tetap
  perlu — dan usaha yang sudah dikeluarkan untuk SS pertama adalah investasi yang benar.

> **Rekomendasi:** sebelum membaca banyak subsistem berikutnya, klarifikasi dulu isi
> connectivity NMM. Itu menentukan apakah repo ini jadi "alat pembentuk DB dari nol" atau
> "alat proyeksi + editor tipis di atas NMM".

---

## 6. Langkah minimal — yang membuat ini nyata, bukan konsep

Untuk versi "ketik perubahan, peta menyesuaikan" — tanpa governance korporat — yang kurang
cuma ini (urutan dari yang paling menentukan):

| Bagian | Usaha | Catatan |
|---|---|---|
| Endpoint tulis | Kecil | API sekarang hanya baca. `POST/PATCH/DELETE` untuk penghantar, GI, keanggotaan SS. Ini inti yang hilang. |
| Form editor web | Sedang | Tiga langkah di dokumen ini, memanggil endpoint di atas lalu me-refresh SLD dari `/api/views/{id}/graph`. |
| Mesin diff / dampak | Sedang | Bandingkan dua versi: node / penghantar / Tier / kerawanan apa yang berubah. Ini yang membuat review cepat. |
| Siklus hidup kerawanan | Kecil | Status `OPEN` sekarang statis. Tambah: `MATERIALIZED`, `MITIGATED`, `REASSESS` saat objeknya berubah. |
| Renderer SLD teknik | Besar | Opsional. Starter renderer sudah cukup untuk membuktikan konsep; poles kualitas gambar belakangan. |

---

## Ringkasan satu paragraf

Hari ini tidak ada basis data di belakang SLD — repo ini mengusulkannya, dan begitu ada,
peta kerawanan di-update dengan mengubah register, bukan menggambar. Bagian yang berat —
membaca gambar jadi topologi terstruktur — adalah kerja sekali per subsistem, dan sedang
dikerjakan. Yang perlu diputuskan minggu ini bukan arsitektur, tapi dua hal: (1) sepakati
bahwa BAU-nya lewat form editor, bukan mengisi tabel lebar; (2) tanya tim NMM apakah
connectivity 500/150 kV sudah ada di sana — itu menentukan berapa banyak subsistem lagi
yang perlu dibaca manual.
