# vAPI Network - Automated Daily Runner 🚀

Script bot otomatisasi garap Airdrop **vAPI Network** (Reward Pool: **1,000,000 $vAPI** di Base Mainnet).

Bot ini didesain **All-in-One**, 100% headless (di latar belakang), tanpa perlu klik browser manual, dengan tabel ringkasan presisi berwarna (*Rich Table*).

---

## 🌟 Fitur Utama

- 🤖 **100% Headless Auto-Login (Camoufox)**: Menyelesaikan Cloudflare Turnstile & SIWE (*Sign-In with Ethereum*) otomatis menggunakan private key tanpa membuka antarmuka browser.
- ⚡ **Auto Onboarding Profil**: Otomatis mengatur avatar & username akun baru serta langsung mengklaim **+500 Poin bonus**.
- 🆔 **Auto Mint vAPI ID**: Mengirimkan transaksi minting identitas digital vAPI di Base Network via sponsor relayer.
- 📅 **Daily Check-in**: Otomatis mengklaim poin harian (+10 pts) atau mendeteksi waktu cooldown jika sudah diklaim.
- 🎯 **Quests Automation**: Otomatis menyelesaikan quest yang tersedia secara cepat dan efisien.
- 📊 **Tampilan Terminal Presisi Berwarna**: Menampilkan ringkasan seluruh wallet, poin, dan rank global secara rapi.

---

## 📦 Instalasi & Persiapan

### 1. Clone Repository & Masuk ke Folder
```bash
git clone https://github.com/bitsmith826/vapi-network-daily.git
cd vapi-network-daily
```

### 2. Install Dependensi Python
Pastikan Anda menggunakan Python 3.10+:
```bash
pip install -r requirements.txt
camoufox fetch
```

### 3. Konfigurasi Wallet
Salin file template `private_keys.txt.example` menjadi `private_keys.txt`:
```bash
cp private_keys.txt.example private_keys.txt
```
Lalu masukkan Private Key EVM atau 12/24 Seed Phrase Anda ke dalam `private_keys.txt` (1 baris per wallet).

*(Opsional)* Jika menggunakan Proxy, salin `proxies.txt.example` menjadi `proxies.txt` dan isi proxy Anda.

---

## 🚀 Cara Menjalankan

Cukup jalankan satu perintah:

```bash
python main.py
```

*(Di Windows, Anda juga bisa langsung klik dua kali file **`run_daily.bat`**)*

---

## ⏰ Otomatisasi Jadwal Harian (Windows Task Scheduler)

Jika Anda ingin bot berjalan otomatis setiap hari pada jam 08:00 Pagi tanpa harus membuka terminal:
1. Klik kanan pada file **`setup_windows_task.bat`**.
2. Pilih **Run as Administrator**.
3. Bot akan otomatis didaftarkan ke Windows Task Scheduler.

---

## 🔒 Keamanan & Privasi

- File `private_keys.txt`, `tokens.txt`, dan `proxies.txt` sudah terdaftar di `.gitignore`.
- Jangan pernah mengunggah atau membagikan file `private_keys.txt` atau `tokens.txt` ke publik.

---

## ⚠️ Disclaimer

Script ini dibuat untuk tujuan edukasi dan otomatisasi pribadi. Gunakan dengan bijak dan atas tanggung jawab Anda sendiri.
