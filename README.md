# Threads MAT — Most Active Times Dashboard

Dashboard untuk melihat **kapan audiens Threads kamu paling aktif** (peak hours / prime time posting).
Berjalan 100% gratis di GitHub: **GitHub Actions** menarik data dari Threads API tiap 6 jam, **GitHub Pages** menampilkan dashboard-nya.

![alur](https://img.shields.io/badge/Threads_API-→_GitHub_Actions_→_data%2Fthreads.json_→_GitHub_Pages-2a78d6)

## Cara MAT dihitung

Threads API **tidak** menyediakan data "jam online follower" (beda dengan Instagram). Jadi dashboard ini menghitungnya dari dua sumber:

| Sumber | Yang dilihat | Artinya |
|---|---|---|
| **Timestamp reply audiens** | Jumlah reply per hari × jam | Jam audiens *benar-benar aktif* membaca & membalas → inti MAT |
| **Insights per post** | Rata-rata views & engagement rate per jam posting | Jam posting yang menghasilkan performa terbaik |

Isi dashboard: heatmap 7 hari × 24 jam, waktu prime (2 jam teraktif), saran jam posting, hari teraktif, grafik per jam/hari, dan tabel post. Filter periode (7–90 hari) dan zona waktu (WIB/WITA/WIT).

> Makin banyak post & reply, makin akurat. Idealnya minimal ±30 post dan ratusan reply.

## Struktur

```
index.html                         dashboard (tanpa library eksternal)
data/threads.json                  data (awalnya DATA CONTOH)
scripts/fetch_threads.py           penarik data Threads API (Python standar, tanpa pip)
scripts/make_demo.py               pembuat data contoh
.github/workflows/update-data.yml  jalan tiap 6 jam → update data/threads.json
.github/workflows/refresh-token.yml perpanjang token tiap minggu (opsional)
```

---

## Langkah 1 — Buat Meta App & ambil access token

1. Buka **https://developers.facebook.com/apps** → login → **Create App**.
2. Pilih use case **"Access the Threads API"** → beri nama app (mis. `Threads MAT`) → selesai.
3. Masuk **Use cases → Access the Threads API → Customize**. Di tab **Permissions**, pastikan aktif:
   - `threads_basic`
   - `threads_manage_insights`
   - `threads_read_replies`
4. Di tab **Settings** pada halaman yang sama, isi **Redirect Callback URLs** dengan URL apa saja yang valid, mis. `https://<username-github>.github.io/` (wajib diisi, walau tidak dipakai).
5. Tambahkan akun Threads kamu sebagai tester: **App roles → Roles → Add People → Threads Tester** → masukkan username Threads kamu.
6. Terima undangannya: di **threads.net** (web) → **Settings → Account → Website permissions → Invites** → **Accept**.
7. Kembali ke **Use cases → Access the Threads API → Customize → Settings**, scroll ke paling bawah ke **User Token Generator** → klik **Generate Access Token** di akun kamu → login & setujui → salin token (diawali `TH…`).
8. Cek masa berlakunya di **https://developers.facebook.com/tools/debug/accesstoken/**.
   - Jika masih **short-lived (1 jam)**, tukar jadi long-lived (60 hari):
     ```bash
     curl -G "https://graph.threads.net/access_token" \
       -d grant_type=th_exchange_token \
       -d client_secret=APP_SECRET_KAMU \
       -d access_token=TOKEN_PENDEK
     ```
     *(App Secret ada di App settings → Basic → Threads App Secret.)*

> Karena kamu memakai akun sendiri sebagai **Threads Tester**, app **tidak perlu App Review** dan tetap dalam mode Development.

## Langkah 2 — Upload ke GitHub

1. Buat repo baru, mis. `matthreads`. **Public** (GitHub Pages gratis hanya untuk repo public) — lihat catatan privasi di bawah.
2. Upload semua file di folder ini (termasuk folder `.github` dan file `.nojekyll`).
   ```bash
   git init && git add . && git commit -m "Threads MAT dashboard"
   git branch -M main
   git remote add origin https://github.com/<username>/matthreads.git
   git push -u origin main
   ```

## Langkah 3 — Simpan token sebagai Secret

Repo → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `THREADS_ACCESS_TOKEN` | token long-lived dari Langkah 1 |

Opsional di tab **Variables**: `LOOKBACK_DAYS` (default `90`), `MAX_POSTS` (default `300`).

## Langkah 4 — Izinkan Actions menulis & aktifkan Pages

1. **Settings → Actions → General → Workflow permissions** → pilih **Read and write permissions** → Save.
2. **Settings → Pages** → Source: **Deploy from a branch** → Branch `main` / folder `/ (root)` → Save.
3. **Actions → Update data Threads → Run workflow** untuk menarik data pertama kali.
4. Buka `https://<username>.github.io/matthreads/` — banner "data contoh" hilang setelah data asli masuk.

Setelah itu data diperbarui otomatis tiap 6 jam.

## Langkah 5 (disarankan) — Perpanjang token otomatis

Token long-lived kedaluwarsa setelah **60 hari** jika tidak diperpanjang. Workflow `refresh-token.yml` memperpanjangnya tiap Senin, tapi butuh izin untuk mengubah secret:

1. GitHub → **Settings (akun) → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. Repository access: **Only select repositories** → pilih repo ini.
3. Permissions → Repository → **Secrets: Read and write**.
4. Simpan token itu sebagai secret repo bernama **`GH_PAT`**.

Tanpa `GH_PAT`, perpanjang manual sebelum 60 hari:
```bash
curl -G "https://graph.threads.net/refresh_access_token" \
  -d grant_type=th_refresh_token -d access_token=TOKEN_KAMU
```
lalu ganti isi secret `THREADS_ACCESS_TOKEN`. (Token harus berumur minimal 24 jam untuk bisa di-refresh.)

## Catatan privasi

- Token **tidak pernah** masuk ke repo — hanya tersimpan sebagai GitHub Secret.
- `data/threads.json` di repo public bisa dilihat siapa saja. Isinya: potongan teks post (sudah publik di Threads), angka views/likes/replies per post, dan **hanya timestamp** reply (tanpa username atau isi reply).
- Kalau tidak ingin angka views terlihat publik: pakai repo **private** (GitHub Pages untuk repo private butuh GitHub Pro), atau jalankan lokal saja.

## Coba di komputer sendiri

```bash
python3 -m http.server 8000          # buka http://localhost:8000
THREADS_ACCESS_TOKEN=TH... python3 scripts/fetch_threads.py   # tarik data asli
python3 scripts/make_demo.py         # kembalikan ke data contoh
```

## Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| Workflow gagal `HTTP 190` / `Invalid OAuth access token` | Token kedaluwarsa → buat token baru (Langkah 1) dan update secret |
| `HTTP 10` / permission error | Permission `threads_manage_insights` atau `threads_read_replies` belum aktif saat token dibuat → aktifkan lalu generate ulang token |
| Push gagal `403` di Actions | Workflow permissions belum **Read and write** (Langkah 4) |
| Heatmap masih kosong | Belum ada reply dalam periode terpilih → perbesar periode ke 90 hari |
| `followers_count` kosong | Insights akun butuh minimal 100 follower |
