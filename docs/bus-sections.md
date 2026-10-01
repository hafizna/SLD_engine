# Seksi bus dan kopel pada ingest

Satu GI tetap satu `Substation`. `BusSection` mewakili seksi internal, dan
`Circuit.from_bus_section_id` / `to_bus_section_id` menentukan terminal
penghantar. Kopel adalah `Circuit` bertipe `BUS_COUPLER` atau `BUS_TIE` dalam
satu GI, dengan dua seksi berbeda dan posisi `OPEN`, `CLOSED`, atau `UNKNOWN`.
Bay terminal serta CB kopel disimpan pada tabel `Bay` dan `Device` yang sudah ada.

Status energisasi aset berbeda dari posisi CB. Kopel OPEN tidak menjadi jalur
listrik. Tidak ada penggabungan otomatis semua seksi berdasarkan ID GI.

## Excel

Kolom tambahan opsional pada `Gardu_Induk_dan_Aset`:

- `Seksi Bus`: daftar nama, misalnya `A;B`.
- `Seksi Bus HV` / `Seksi Bus LV`: terminal seksi untuk baris IBT.
- `Seksi Bus Terhubung`: terminal outlet pembangkit jika memakai outlet langsung.

Kolom tambahan pada `Jalur_Transmisi`:

- `Seksi Dari` dan `Seksi Ke`: nama seksi sesuai deklarasi GI.
- `No Sirkit`: identitas baris circuit, termasuk saat sirkit paralel menempel
  pada seksi berbeda. Jangan menebak nomor sirkit dari urutan gambar.

Sheet opsional `Kopel_Bus`:

| Kode GI | ID Kopel | Seksi Dari | Seksi Ke | Status Kopel | No Kerawanan | Catatan | Sudut Pandang |
|---|---|---|---|---|---|---|---|
| BKLAN | KOP_AB | A | B | OPEN | 21 | Tabel 5.1 #21 | |

Format lama tanpa deklarasi seksi tetap didukung. Catatan `seksi A/B` saja
tidak dijadikan pemisahan listrik oleh parser.

## JSON

Tambahkan `bus_sections: ["A", "B"]` pada objek GI. Connection biasa memakai
`from_bus_section` / `to_bus_section`. Contoh kopel:

```json
{
  "from_external_key": "BKLAN",
  "to_external_key": "BKLAN",
  "from_bus_section": "A",
  "to_bus_section": "B",
  "circuit_type_hint": "BUS_COUPLER",
  "switch_state": "OPEN",
  "unit_no": "KOP_AB",
  "circuit_count": 1,
  "confidence": 1
}
```

Pin risiko kopel: `pin_kind: "CIRCUIT"`,
`pin_key: "BKLAN-BKLAN:KOP_AB"`. Parser mempertahankan ID circuit pada pin
agar dua sirkit di seksi berbeda tidak jatuh pada satu circuit yang sama.

## Validasi, routing, dan simulasi

Nama seksi yang tidak dideklarasikan, kopel ke GI berbeda, kopel ke seksi yang
sama, atau posisi selain OPEN/CLOSED/UNKNOWN ditolak. Terminal yang belum
dipetakan dan posisi UNKNOWN menghasilkan peringatan. Gambar masih dapat
ditinjau/diingest, tetapi `connectivity.complete=false`; viewer tidak memberikan
kesimpulan dampak seolah-olah topologi sudah lengkap.

Autorouter memakai alokasi port per seksi yang berasal dari data parser.
Spans disimpan relatif terhadap pusat GI, sehingga perubahan posisi otomatis
atau posisi tersimpan tidak meninggalkan seksi/terminal pada koordinat lama.
Endpoint tanpa pemetaan muncul di jalur abu-abu `? Belum dipetakan`. Jalur
tersebut hanya alat review dan tidak menjadi sambungan listrik antar seksi.

API graph menyediakan `nodes[].bus_sections`, endpoint seksi pada edges,
`switch_state`, serta blok `connectivity` untuk graf listrik. Uji skenario
read-only melalui `POST /api/views/{id}/connectivity-scenario`:

```json
{"switch_overrides": {"123": "CLOSED"}, "removed_edges": []}
```

`123` adalah ID circuit kopel pada view. Skenario tidak menulis keadaan operasi
ke database. Di viewer, klik simbol kopel untuk memilih OPEN/CLOSED dan
`Kembalikan sumber` untuk reset. Hasil hanya keterjangkauan sumber, bukan
load flow, pembebanan, atau jaminan kriteria N-1.

Schema lama diupgrade secara aditif dan idempotent saat aplikasi mulai; kolom
baru nullable, sehingga identitas aset/data lama tidak dihapus. Ingest tetap
melarang publish ulang kode subsistem yang sudah ada. Untuk instalasi yang
sudah memuat fixture lama, gunakan proses versi/review yang berlaku; jangan
menghapus GI atau membuat duplikat untuk memaksa upgrade.

## Krian 1,2 - Gresik 1,2

Fixture memasukkan A/B Rungkut dan Bangkalan dari Gambar 5.3 serta screenshot
1 Oktober 2026. Terminal Rungkut: Karangpilang dan Surabaya Selatan ke A;
Waru, Sukolilo dan HJAYA ke B. Terminal Bangkalan: Gilitimur ke A;
Ujung dan Kedinding ke B. Dua konduktor Bangkalan-Sampang dipisah sebagai
baris A/B; itu ID menurut seksi, bukan nomor sirkit resmi.

Kopel Bangkalan OPEN sesuai #21; Rungkut OPEN sesuai splitting pada mitigasi
#3. Sawahan OPEN sesuai #9, tetapi lima terminal belum dipetakan sesuai
instruksi pengguna. Seksi Sawahan `1/2` hanya ID model. Akibatnya simulasi
seluruh fixture tetap ditandai belum lengkap. Konflik #13/#23 dan nama GI
yang belum diketahui tidak diselesaikan dengan perubahan ini.
