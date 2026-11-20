# 🚀 vAPI Network - Automated Daily Runner & Web3 Agent Engine (Base Mainnet)

[![Network](https://img.shields.io/badge/Network-Base%20Mainnet%20(8453)-0052FF?style=flat&logo=ethereum)](https://base.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)
[![Reward Pool](https://img.shields.io/badge/Reward%20Pool-1%2C000%2C000%20%24vAPI-magenta?style=flat)]()

> ⚠️ **DISCLAIMER HUKUM & PANDUAN EDUKASI (RESEARCH ONLY)**
>
> Repositori ini dibuat dan didistribusikan semata-mata untuk **tujuan edukasi**, **riset arsitektur Web3**, dan pembelajaran implementasi standar kriptografi terdesentralisasi:
> 1. Standar autentikasi **Ethereum EIP-4361 / EIP-191 (Sign-In with Ethereum - SIWE)**.
> 2. Protokol otorisasi agen terdistribusi **OAuth 2.0 Device Authorization Grant (RFC 8628)**.
> 3. Standar kurasi API terdesentralisasi dan micropayment on-chain **x402 HTTP Framework**.
> 4. Ketahanan browser headless terhadap mekanisme proteksi bot (Cloudflare Turnstile).
>
> Pengembang tidak berafiliasi secara resmi dengan vAPI Network dan tidak bertanggung jawab atas tindakan pemblokiran, perubahan aturan protokol, maupun konsekuensi apa pun dari penggunaan skrip ini. Pengguna bertanggung jawab penuh atas tindakan masing-masing.

---

## 📖 Ringkasan Proyek & Konsep Edukasi

**`vAPI Network`** adalah jaringan protokol terdesentralisasi (DePIN) di atas **Base Mainnet** yang menghubungkan agen AI independen dengan penyedia API dan komputasi model bahasa (*LLM Routing*). 

Repositori **`vapi-network-daily`** adalah kerangka kerja (*framework*) otomatisasi dan interaksi cerdas multi-wallet berbasis **Python** murni yang mengimplementasikan penanganan siklus hidup akun Web3 secara lengkap:
- Autentikasi nir-kata-sandi berbasis tanda tangan kriptografi kurva elips secp256k1.
- Penerbitan identitas on-chain NFT digital ERC-721 gasless bersponsor.
- Pembentukan koneksi terautentikasi antara agen AI otonom dengan akun pemilik (*wallet pairing*).
- Publikasi listing API x402 termonetisasi menggunakan serverless edge worker multi-tenant.

---

## 🧠 Pembelajaran Protokol Teknis (Architectural Deep-Dive)

### 1. Kriptografi EIP-4361 (Sign-In with Ethereum)
Alih-alih menggunakan kombinasi username dan password terpusat, vAPI Network memanfaatkan standar **EIP-4361 / EIP-191**:
$$\text{Signature} = \text{ECDSA\_Sign}_{k_{\text{private}}}(\text{keccak256}(\text{"\x19Ethereum Signed Message:\n"} + \text{len}(m) + m))$$
Skrip ini menghitung tanda tangan secara offline di dalam RAM menggunakan modul `eth_account`, memastikan **private key tidak pernah dikirimkan melalui jaringan internet**.

### 2. Auto-Renewal Sesi Supabase (~100ms)
Sesi JWT Supabase vAPI memiliki masa berlaku 3.600 detik (1 jam). Skrip ini membedah cookie sesi `sb-*-auth-token`, mengekstrak string `refresh_token`, dan memperbarui sesi langsung ke gateway Supabase over TLS. Ini memangkas waktu login dari puluhan detik menjadi hanya **100 milidetik per akun** tanpa perlu menyelesaikan captcha berulang kali.

### 3. OAuth 2.0 Device Authorization Grant (RFC 8628)
Untuk quest *"Connect an agent"*, skrip ini menjalankan device authorization grant:
1. Menghasilkan wallet agen sementara (*ephemeral key*) di memori.
2. Meminta `device_code` dan `user_code` via `/oauth/device_authorization`.
3. Menandatangani persetujuan otorisasi dari wallet pemilik via endpoint `/link?code={userCode}` dengan parameter `expectedOwnerWallet`.
4. Menyelesaikan pertukaran token via `/oauth/token`.

### 4. Framework x402 Micropayment & EIP-712 Listing
Untuk quest *"List your API on vAPI"*, skrip berinteraksi dengan smart contract katalog Base Mainnet (`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` USDC) dan facilitator `payai.network` melalui Cloudflare Worker multi-wallet, memvalidasi handshake `HTTP 402 Payment Required` secara otomatis.

---

## ✨ Fitur Unggulan

- 🛡️ **Zero-Exposure Private Key Custody**: Private key diolah murni di lingkungan lokal, tidak pernah dicatat atau dibocorkan ke log publik.
- ⚡ **Multi-Wallet Concurrency**: Mendukung skalabilitas dari 1 hingga 50+ wallet dalam sekali jalan berurutan.
- 🤖 **100% Headless Solver (Camoufox)**: Mengintegrasikan browser engine Camoufox untuk menyelesaikan tantangan Cloudflare Turnstile secara mandiri.
- 🖥️ **Interactive Fallback Onboarder (`interactive_onboard.py`)**: Antarmuka browser tunggal yang ramah pengguna jika tantangan bot memerlukan interaksi visual klik manusia.
- 🆔 **Auto Mint vAPI ID**: Mengirimkan transaksi gasless minting ERC-721 di Base Mainnet via relayer sponsor protokol (+350 pts).
- 📅 **Daily Check-in Smart Engine**: Mengklaim poin harian (+10 pts) secara otomatis dan mendeteksi durasi cooldown jika klaim sedang aktif.
- 🎯 **100% Platform Quest Sweep**:
  - `Complete your profile` (**+500 pts**)
  - `Mint your vAPI ID` (**+350 pts**)
  - `Create your first Router key` (**+150 pts**)
  - `Connect an agent` (**+250 pts**)
  - `List your API on vAPI` (**+500 pts**)
- 📊 **Tampilan Terminal Presisi (Rich Console)**: Tabel statistik warna-warni yang merangkum alamat ter-masking (`0x1234...5678`), total poin, dan peringkat global.

---

## 📋 Prasyarat Sistem

* **Python 3.10** atau versi lebih baru.
* **Git** (untuk mengkloning repositori).
* Sistem Operasi: Windows 10/11, Ubuntu/Debian Linux, atau macOS.

---

## 🛠️ Tutorial Penggunaan (Langkah demi Langkah)

### 1. Kloning Repositori & Masuk ke Folder
```bash
git clone https://github.com/bitsmith826/vapi-network-daily.git
cd vapi-network-daily
```

### 2. Pasang Pustaka Dependensi Python
```bash
pip install -r requirements.txt
camoufox fetch
```

### 3. Konfigurasi Wallet (`private_keys.txt`)
Salin file template contoh:
```bash
# Windows (PowerShell / CMD)
copy private_keys.txt.example private_keys.txt

# Linux / macOS
cp private_keys.txt.example private_keys.txt
```
Buka file `private_keys.txt` dan masukkan Private Key EVM atau 12/24 Mnemonic Seed Phrase Anda (1 baris per akun):
```text
0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
```

> **🔒 Jaminan Privasi**: File `private_keys.txt` dan `tokens.txt` telah **100% diabaikan oleh `.gitignore`**, sehingga tidak akan pernah terunggah ke Git atau GitHub.

---

### 4. Menjalankan Bot

#### A. Eksekusi Harian Standar (Recommended)
Cukup jalankan satu perintah:
```bash
python main.py
```
Bot akan otomatis mengecek sesi login, memperbarui token via Supabase, memeriksa status vAPI ID, mengklaim check-in harian, menyelesaikan platform quest, dan menampilkan tabel peringkat akhir.

#### B. Onboarding Interaktif (Jika Turnstile Butuh Verifikasi Visual)
Jika login headless mengalami proteksi ketat dari Cloudflare, jalankan onboarder interaktif:
```bash
python interactive_onboard.py
```
Jendela browser tunggal akan terbuka dan Anda cukup mengklik kotak verifikasi Turnstile di layar untuk masing-masing wallet secara berurutan.

#### C. Menghubungkan Agen AI Mandiri (+250 Poin)
```bash
python run_agent_connect.py
```

#### D. Publikasi Listing API x402 (+500 Poin)
1. Deploy kode [`cloudflare_worker.js`](cloudflare_worker.js) ke Cloudflare Workers gratis Anda.
2. Jalankan perintah:
```bash
python publish_listings.py https://<subdomain-worker-anda>.workers.dev
```

---

## 📊 Contoh Tampilan Output Terminal

```text
                        📊 RINGKASAN HARIAN vAPI NETWORK
┏━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┓
┃ No ┃   Wallet Address   ┃     Username     ┃ vAPI ID ┃  Daily Check-in  ┃     Points ┃   Rank    ┃ Status  ┃
┣━━━━╋━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━╋━━━━━━━━━╋━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━┫
┃ 01 ┃ 0x728f...de7f      ┃ vapiuser728fde   ┃ Minted  ┃ Cooldown (21j 4m)┃  5,415 pts ┃   #349    ┃ Sukses  ┃
┃ 02 ┃ 0x86a4...5ce4      ┃ vapiuser86a45c   ┃ Minted  ┃ Cooldown (21j 4m)┃  1,905 pts ┃  #6,517   ┃ Sukses  ┃
┃ 03 ┃ 0xce7b...00ac      ┃ vapiuserce7b00   ┃ Minted  ┃ Cooldown (21j 4m)┃  1,905 pts ┃  #6,518   ┃ Sukses  ┃
┃ 11 ┃ 0xadcd...c5a6      ┃ vapiuseradcda6   ┃ Minted  ┃ Cooldown (21j 4m)┃  1,760 pts ┃  #7,594   ┃ Sukses  ┃
┃ 30 ┃ 0xef4c...ec42      ┃ vapiuseref4cec   ┃ Minted  ┃ Cooldown (21j 4m)┃  1,760 pts ┃  #7,613   ┃ Sukses  ┃
┗━━━━┻━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━┻━━━━━━━━━┻━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━┻━━━━━━━━━━━┻━━━━━━━━━┛

Total Wallets: 30  │  Total Poin: 57,760 pts  │  Top Rank: #349  │  Status: 30/30 Sukses
```

---

## 🛡️ Audit Kriptografis & Keamanan Rilis (REA Audited)

Proyek ini telah melalui audit keamanan statis dan analisis rilis menggunakan standar **Reverse-Engineer-Anything (REA)**:

```text
[✓] Text Credential Markers : NOT OBSERVED (0 Hardcoded Secrets)
[✓] Identity Masking        : PASS (Alamat dipotong menjadi 0x1234...5678)
[✓] Git Ignore Boundary     : PASS (private_keys.txt, tokens.txt, proxies.txt dilindungi)
[✓] Signature Standard      : PASS (EIP-191 & EIP-4361 compliant)
[✓] REA Exposure Severity   : NULL (0 Exposed Vulnerabilities)
```

---

## 📄 Lisensi

Didistribusikan di bawah Lisensi **MIT**. Lihat file `LICENSE` untuk informasi lebih lanjut.

---

**Dikembangkan untuk Riset & Eksplorasi Web3 oleh [bitsmith826](https://github.com/bitsmith826)**
