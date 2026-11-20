#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connect Agent Quest Runner for all wallets in vAPI Network
Awards +250 PTS per wallet using 100% free pure Python OAuth linking
"""

import sys
import os
import time
from datetime import datetime, timezone
import requests
from eth_account import Account
from eth_account.messages import encode_defunct

import main

def connect_wallet_agent(client, idx):
    acc = client.get_account()
    if not acc:
        print(f"[-] Akun #{idx}: Gagal mendapatkan info akun")
        return False
    
    owner_addr = acc.get("profile", {}).get("walletAddress")
    print(f"\n[*] Akun #{idx} ({owner_addr[:6]}...{owner_addr[-4:]}) Menghubungkan agent...")

    # 1. Ephemeral agent wallet
    agent = Account.create()

    # 2. Nonce
    r_nonce = client.session.get(f"{client.base_url}/api/auth/siwe-nonce?purpose=link", timeout=15)
    if r_nonce.status_code != 200:
        print(f"[-] Akun #{idx}: Gagal mengambil link nonce: {r_nonce.status_code}")
        return False
    nonce = r_nonce.json().get("nonce")

    # 3. SIWE message
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    msg = (
        f"api.vapinetwork.ai wants you to sign in with your Ethereum account:\n"
        f"{agent.address}\n\n"
        f"Link this wallet to a vAPI account as an agent.\n\n"
        f"URI: {client.base_url}\n"
        f"Version: 1\n"
        f"Chain ID: 8453\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {now_iso}"
    )
    sig = agent.sign_message(encode_defunct(text=msg)).signature.hex()
    if not sig.startswith("0x"):
        sig = "0x" + sig

    # 4. Device authorization
    auth_payload = {
        "agent_message": msg,
        "agent_signature": sig,
        "label": "main",
        "scope": "mcp:call router.use tasks:read tasks:write",
        "router_allowance_usd": 1.0
    }
    r_auth = client.session.post(f"{client.base_url}/oauth/device_authorization", json=auth_payload, timeout=15)
    if r_auth.status_code != 200:
        print(f"[-] Akun #{idx}: Gagal device_authorization: {r_auth.status_code}")
        return False
    
    auth_data = r_auth.json()
    device_code = auth_data.get("device_code")
    user_code = auth_data.get("user_code")
    client_id = auth_data.get("client_id")

    # 5. Owner approval via logged-in session
    approve_data = {
        "code": user_code,
        "expectedOwnerWallet": owner_addr,
        "routerAllowanceUsd": "1.00",
        "intent": "approve"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"{client.base_url}/link?code={user_code}",
        "Origin": client.base_url
    }
    r_app = client.session.post(f"{client.base_url}/link?code={user_code}", data=approve_data, headers=headers, timeout=15)
    if r_app.status_code != 200:
        print(f"[-] Akun #{idx}: Gagal approval /link: {r_app.status_code}")
        return False

    # 6. Finalize token exchange
    poll_data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": device_code,
        "client_id": client_id
    }
    r_tok = requests.post(f"{client.base_url}/oauth/token", json=poll_data, timeout=15)
    if r_tok.status_code != 200:
        print(f"[-] Akun #{idx}: Gagal token exchange: {r_tok.status_code}")
        return False

    # 7. Reconcile quest board
    time.sleep(1)
    b = client.get_board(fresh=True).get("board", {})
    pts = b.get("points", {}).get("total", 0)
    print(f"[+] Akun #{idx} Agent Linked BERHASIL! Total Poin: {pts:,} PTS (+250 pts Sukses!)")
    return True

def main_connect():
    tokens = main.load_tokens()
    print("=" * 65)
    print("   vAPI Network - Connect Agent Quest Automation (+250 pts)")
    print("=" * 65)
    print(f"Memeriksa {len(tokens)} akun...")

    success_count = 0
    for idx, tok in enumerate(tokens, 1):
        try:
            client = main.VapiClient(tok)
            # Check if already completed
            b = client.get_board(fresh=True).get("board", {})
            agent_done = False
            for s in b.get("sections", []):
                for q in s.get("quests", []):
                    if "connect an agent" in q.get("title", "").lower() and q.get("state") == "completed":
                        agent_done = True
                        break
            if agent_done:
                pts = b.get("points", {}).get("total", 0)
                print(f"[+] Akun #{idx}: Connect Agent SUDAH SELESAI sebelumnya ({pts:,} pts)")
                success_count += 1
                continue

            ok = connect_wallet_agent(client, idx)
            if ok:
                success_count += 1
            time.sleep(1)
        except Exception as e:
            print(f"[-] Error pada Akun #{idx}: {e}")

    print("\n" + "=" * 65)
    print(f"Selesai! {success_count}/{len(tokens)} Akun telah menyelesaikan Connect Agent.")
    print("=" * 65)

if __name__ == "__main__":
    main_connect()
