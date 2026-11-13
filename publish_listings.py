#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vAPI Network - Auto Publisher for "List your API on vAPI" Quest (+500 pts per wallet)
Using official Web Provider endpoints & Pure Python Session Authentication
"""

import sys
import os
import json
import time
from datetime import datetime, timezone
import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_checksum_address

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from main import load_private_keys, load_tokens, VapiClient

BASE_URL = "https://api.vapinetwork.ai"
PAYOUT_STATEMENT = "Confirm this address as your vAPI payout wallet. This signature does not submit a transaction or use gas."
PAYOUT_URI = "https://api.vapinetwork.ai/call/register"
PAYOUT_CHAIN_ID = 8453

def build_payout_siwe(address, nonce, issued_at=None):
    if not issued_at:
        issued_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    checksum = to_checksum_address(address)
    lines = [
        "api.vapinetwork.ai wants you to sign in with your Ethereum account:",
        checksum,
        "",
        PAYOUT_STATEMENT,
        "",
        f"URI: {PAYOUT_URI}",
        "Version: 1",
        f"Chain ID: {PAYOUT_CHAIN_ID}",
        f"Nonce: {nonce}",
        f"Issued At: {issued_at}"
    ]
    return "\n".join(lines)

def publish_wallet_api(worker_base_url, private_key, token, index=1):
    acc = Account.from_key(private_key)
    checksum_addr = to_checksum_address(acc.address)
    print(f"\n=======================================================")
    print(f"[*] Processing Akun #{index} ({checksum_addr[:6]}...{checksum_addr[-4:]})")
    print(f"=======================================================")

    client = VapiClient(token)

    # Check if quest is already completed
    try:
        b_init = client.get_board(fresh=True).get("board", {})
        for s in b_init.get("sections", []):
            for q in s.get("quests", []):
                if q.get("title") == "List your API on vAPI" and q.get("state") == "completed":
                    pts = b_init.get("points", {}).get("total", 0)
                    print(f"[+] Quest 'List your API on vAPI' SUDAH SELESAI sebelumnya! Poin: {pts:,} pts")
                    return True
    except Exception:
        pass

    # Clean worker URL
    clean_worker_url = worker_base_url.rstrip("/")
    if index == 1:
        target_url = f"{clean_worker_url}/quote"
    else:
        target_url = f"{clean_worker_url}/quote/{checksum_addr}"

    # 1. Probe the endpoint via web provider API
    print(f"[*] [1/4] Memeriksa endpoint via vAPI probe: {target_url}...")
    probe_payload = {"url": target_url, "method": "GET"}
    r_probe = client.session.post(f"{BASE_URL}/api/providers/probe", json=probe_payload, timeout=25)
    if r_probe.status_code != 200:
        print(f"[-] Probe HTTP Error {r_probe.status_code}: {r_probe.text}")
        return False
    
    probe_data = r_probe.json()
    rejection = probe_data.get("diagnostics", {}).get("rejection")
    if rejection:
        print(f"[-] Probe DITOLAK: {rejection.get('code')} - {rejection.get('message')}")
        return False

    op = probe_data.get("endpoint") or probe_data.get("operations", [{}])[0]
    op_name = op.get("name", "quote")
    print(f"[+] Probe LOLOS! Operasi: {op_name}")

    # 2. Request payout nonce
    print(f"[*] [2/4] Mengambil payout nonce...")
    r_nonce = client.session.get(f"{BASE_URL}/api/providers/payout-nonce", timeout=15)
    if r_nonce.status_code != 200:
        print(f"[-] Gagal payout-nonce: {r_nonce.status_code} - {r_nonce.text}")
        return False
    
    nonce = r_nonce.json().get("nonce")
    print(f"[+] Nonce didapatkan: {nonce[:16]}...")

    # 3. Build & Sign SIWE payout message
    siwe_msg = build_payout_siwe(checksum_addr, nonce)
    signed = acc.sign_message(encode_defunct(text=siwe_msg))
    signature = "0x" + signed.signature.hex()
    print(f"[+] [3/4] SIWE Payout ditandatangani oleh {checksum_addr[:8]}...")

    # 4. Publish listing
    endpoint_item = {
        "name": op.get("name", "quote"),
        "method": (op.get("method") or "GET").upper(),
        "url": op.get("url", target_url),
        "description": op.get("description", "One random inspirational quote")
    }
    if op.get("metadataEvidence"):
        endpoint_item["metadataEvidence"] = op.get("metadataEvidence")

    publish_payload = {
        "name": f"Quote API ({checksum_addr[:6]})",
        "description": "Returns one random inspirational quote as JSON per call. Costs $0.001 USDC on Base via x402.",
        "category": "data",
        "endpoints": [endpoint_item],
        "payoutWallet": checksum_addr,
        "siweMessage": siwe_msg,
        "signature": signature
    }

    print(f"[*] [4/4] Mendaftarkan listing API ke vAPI...")
    r_pub = client.session.post(f"{BASE_URL}/api/providers/publish", json=publish_payload, timeout=20)
    if r_pub.status_code not in (200, 201):
        print(f"[-] Gagal publish: {r_pub.status_code} - {r_pub.text}")
        return False
    
    pub_data = r_pub.json()
    slug = pub_data.get("listing", {}).get("slug")
    print(f"[+] Listing berhasil dibuat! Slug: {slug}")

    # 5. Activate listing
    if slug:
        print(f"[*] Mengaktifkan listing {slug}...")
        r_act = client.session.post(f"{BASE_URL}/api/providers/{slug}/status", json={"action": "activate"}, timeout=15)
        if r_act.status_code in (200, 201):
            print(f"[+] Listing {slug} BERHASIL DIAKTIFKAN (Status: listed)!")
        else:
            print(f"[!] Warning activate: {r_act.status_code} - {r_act.text}")

    # 6. Verify Points
    time.sleep(2)
    b_final = client.get_board(fresh=True).get("board", {})
    pts = b_final.get("points", {}).get("total", 0)
    rk = b_final.get("points", {}).get("rank", "-")
    print(f"[+] Poin Akun #{index} sekarang: {pts:,} PTS │ Rank #{rk} (+500 pts SUKSES!)")
    return True

if __name__ == "__main__":
    from main import load_config
    cfg = load_config()
    
    worker_url = None
    if len(sys.argv) > 1 and sys.argv[1].strip():
        worker_url = sys.argv[1].strip()
    elif cfg.get("worker_url"):
        worker_url = cfg.get("worker_url").strip()
    
    if not worker_url:
        print("[!] Penggunaan: python publish_listings.py <WORKER_URL>")
        print("[!] Contoh: python publish_listings.py https://your-worker.workers.dev")
        print("[!] Atau isi field 'worker_url' di file config.json.")
        sys.exit(1)

    pkeys = load_private_keys()
    tokens = load_tokens()

    print(f"[*] Memulai publikasi API untuk {len(pkeys)} wallet menggunakan worker:")
    print(f"    {worker_url}\n")

    success_count = 0
    for idx, (pkey, tok) in enumerate(zip(pkeys, tokens), 1):
        try:
            ok = publish_wallet_api(worker_url, pkey, tok, idx)
            if ok:
                success_count += 1
        except Exception as e:
            print(f"[-] Exception pada Akun #{idx}: {e}")
        time.sleep(2)

    print(f"\n=======================================================")
    print(f"[+] Selesai! Berhasil mempublikasikan {success_count}/{len(pkeys)} akun.")
    print(f"=======================================================")
