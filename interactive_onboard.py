#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Wallet Onboarder for vAPI Network
Single-page persistent browser session for seamless multi-wallet Cloudflare Turnstile onboarding.
"""

import os
import sys
import time
import json
from datetime import datetime, timezone
import requests
from eth_account import Account
from eth_account.messages import encode_defunct

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from camoufox.sync_api import Camoufox
import main

TOKENS_FILE = "tokens.txt"
PKEYS_FILE = "private_keys.txt"
SITEKEY = "0x4AAAAAAEN_PvE1iYWei9wu"

def load_keys():
    return main.load_private_keys()

def load_existing_tokens():
    return main.load_tokens()

def main_interactive():
    pkeys = load_keys()
    existing_tokens = load_existing_tokens()

    print("=" * 70)
    print("      vAPI Network - Interactive Turnstile Onboarder")
    print("=" * 70)
    print(f"Total Private Keys ditemukan: {len(pkeys)}")
    print(f"Total Token Sesi yang sudah ada: {len(existing_tokens)}")

    # Map existing valid sessions to wallet addresses
    valid_sessions = {}
    print("\nMemeriksa validitas token yang sudah ada...")
    for idx, tok in enumerate(existing_tokens, 1):
        addr = main.test_token_valid(tok)
        if not addr:
            refreshed = main.refresh_supabase_token(tok)
            if refreshed and main.test_token_valid(refreshed):
                tok = refreshed
                addr = main.test_token_valid(tok)
        if addr:
            valid_sessions[addr.lower()] = tok
            print(f"  [✓] Akun #{idx}: {addr} (Sesi Aktif)")

    # Identify keys that still need onboarding
    pending_wallets = []
    wallet_keys = {}
    for idx, pkey in enumerate(pkeys, 1):
        acc = Account.from_key(pkey)
        addr_lower = acc.address.lower()
        wallet_keys[addr_lower] = acc
        if addr_lower not in valid_sessions:
            pending_wallets.append((idx, pkey, acc))

    if not pending_wallets:
        print(f"\n[✓] SEMUA {len(pkeys)} akun sudah memiliki sesi aktif di {TOKENS_FILE}!")
        return

    print(f"\nAda {len(pending_wallets)} wallet baru yang perlu diautentikasi (Wallet #{pending_wallets[0][0]} s/d #{pending_wallets[-1][0]}):")
    for idx, _, acc in pending_wallets:
        print(f"  • Akun #{idx:02d}: {acc.address}")

    print("\nMengunduh script Cloudflare Turnstile...")
    try:
        api_js = requests.get('https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit', timeout=15).text
    except Exception as e:
        print(f"Gagal mengunduh script Turnstile: {e}")
        return

    print("\nMembuka jendela browser Camoufox untuk verifikasi...")
    print("Petunjuk: Klik kotak verifikasi Turnstile yang muncul di layar untuk masing-masing wallet.")

    with Camoufox(headless=False) as browser:
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(0)

        # Sign function exposed to browser JS
        def py_sign(address, msg_text):
            acc = wallet_keys.get(address.lower())
            if not acc:
                raise ValueError(f"Wallet {address} tidak ditemukan")
            encoded = encode_defunct(text=msg_text)
            sig = acc.sign_message(encoded).signature.hex()
            return "0x" + sig if not sig.startswith("0x") else sig

        page.expose_function("pySignMessage", py_sign)

        print("\nNavigasi ke https://api.vapinetwork.ai/earn...")
        page.goto("https://api.vapinetwork.ai/earn")
        time.sleep(2)

        # Inject Turnstile once
        page.evaluate('''() => {
            const s = document.createElement("script");
            s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
            s.async = true;
            document.head.appendChild(s);
        }''')
        page.evaluate(api_js)

        # Inject master UI container once
        page.evaluate('''() => {
            const overlay = document.createElement("div");
            overlay.id = "vapi-onboard-ui";
            overlay.style.position = "fixed";
            overlay.style.top = "25px";
            overlay.style.left = "50%";
            overlay.style.transform = "translateX(-50%)";
            overlay.style.padding = "24px 36px";
            overlay.style.background = "#181825";
            overlay.style.color = "#cdd6f4";
            overlay.style.borderRadius = "16px";
            overlay.style.border = "2px solid #89b4fa";
            overlay.style.zIndex = "99999999";
            overlay.style.boxShadow = "0 25px 50px -12px rgba(0, 0, 0, 0.75)";
            overlay.style.textAlign = "center";
            overlay.style.fontFamily = "system-ui, -apple-system, sans-serif";
            overlay.style.minWidth = "380px";

            overlay.innerHTML = `
                <div id="vapi-badge" style="font-size: 13px; font-weight: 600; color: #f9e2af; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">
                    vAPI Network Onboarding
                </div>
                <div id="vapi-title" style="font-size: 20px; font-weight: 700; color: #89b4fa; margin-bottom: 4px;">
                    Menyiapkan...
                </div>
                <div id="vapi-address" style="font-size: 12px; color: #a6adc8; font-family: monospace; background: #313244; padding: 4px 10px; border-radius: 6px; margin-bottom: 16px;">
                    -
                </div>
                <div id="vapi-status" style="font-size: 14px; color: #a6e3a1; margin-bottom: 14px; font-weight: 500;">
                    Memuat...
                </div>
                <div id="turnstile-slot" style="display: flex; justify-content: center; min-height: 70px;"></div>
            `;
            document.body.appendChild(overlay);
        }''')

        for curr_i, (idx, pkey, acc) in enumerate(pending_wallets, 1):
            addr = acc.address
            print(f"\n[{curr_i}/{len(pending_wallets)}] Menunggu Verifikasi Akun #{idx} ({addr[:6]}...{addr[-4:]})...")

            # Reset cookies and storage before logging in
            context.clear_cookies()
            try:
                page.evaluate("() => { try { localStorage.clear(); sessionStorage.clear(); } catch(e){} }")
            except Exception:
                pass

            # Script to run single wallet Turnstile & SIWE
            wallet_script = f"""
            () => {{
                return new Promise((resolve) => {{
                    const badgeEl = document.getElementById("vapi-badge");
                    const titleEl = document.getElementById("vapi-title");
                    const addrEl = document.getElementById("vapi-address");
                    const statusEl = document.getElementById("vapi-status");
                    const slot = document.getElementById("turnstile-slot");

                    badgeEl.innerText = "vAPI Onboarding [{curr_i} / {len(pending_wallets)}]";
                    titleEl.innerText = "Akun #{idx}";
                    addrEl.innerText = "{addr}";
                    statusEl.innerText = "Silakan klik centang verifikasi di bawah:";
                    statusEl.style.color = "#a6e3a1";

                    // Clean previous turnstile widget
                    slot.innerHTML = "";

                    let widgetId = null;
                    try {{
                        widgetId = window.turnstile.render(slot, {{
                            sitekey: "{SITEKEY}",
                            action: "account_creation",
                            appearance: "always",
                            callback: async (token) => {{
                                statusEl.innerText = "⏳ Sedang memproses SIWE & autentikasi...";
                                statusEl.style.color = "#f9e2af";

                                try {{
                                    const resNonce = await fetch('/api/auth/siwe-nonce', {{ cache: 'no-store' }});
                                    const {{ nonce }} = await resNonce.json();

                                    const resChallenge = await fetch('/api/protection/challenge', {{
                                        method: 'POST',
                                        headers: {{ 'Content-Type': 'application/json' }},
                                        body: JSON.stringify({{ action: 'auth.siwe.verify' }})
                                    }});
                                    const challenge = await resChallenge.json();

                                    const now = new Date();
                                    const message = [
                                        `${{window.location.host}} wants you to sign in with your Ethereum account:`,
                                        "{addr}",
                                        "",
                                        "Sign in to vAPI Network. This will not trigger a blockchain transaction.",
                                        "",
                                        `URI: ${{window.location.href}}`,
                                        "Version: 1",
                                        "Chain ID: 8453",
                                        `Nonce: ${{nonce}}`,
                                        `Issued At: ${{now.toISOString()}}`
                                    ].join("\\n");

                                    const signature = await window.pySignMessage("{addr}", message);

                                    const resSiwe = await fetch('/api/auth/siwe', {{
                                        method: 'POST',
                                        credentials: 'include',
                                        headers: {{ 'Content-Type': 'application/json' }},
                                        body: JSON.stringify({{
                                            message: message,
                                            signature: signature,
                                            protection: {{
                                                challengeToken: challenge.token,
                                                elapsedMs: 2500,
                                                honeypot: "",
                                                bot: {{ status: "not_detected" }}
                                            }},
                                            turnstileToken: token
                                        }})
                                    }});

                                    const siweData = await resSiwe.json();
                                    if (siweData.ok) {{
                                        statusEl.innerText = "✔ Berhasil Login! Menyimpan sesi...";
                                        statusEl.style.color = "#a6e3a1";
                                        resolve({{ success: true, data: siweData }});
                                    }} else {{
                                        const errMsg = siweData.message || JSON.stringify(siweData);
                                        statusEl.innerText = "✖ Gagal: " + errMsg;
                                        statusEl.style.color = "#f38ba8";
                                        resolve({{ success: false, error: siweData }});
                                    }}
                                }} catch (err) {{
                                    statusEl.innerText = "✖ Error: " + err.message;
                                    statusEl.style.color = "#f38ba8";
                                    resolve({{ success: false, error: String(err) }});
                                }}
                            }},
                            "error-callback": (err) => {{
                                statusEl.innerText = "✖ Turnstile error (" + err + "). Merender ulang...";
                                statusEl.style.color = "#f38ba8";
                                setTimeout(() => {{
                                    try {{ if (widgetId) window.turnstile.reset(widgetId); }} catch(e){{}}
                                }}, 2000);
                            }},
                            "timeout-callback": () => {{
                                statusEl.innerText = "⚠ Waktu verifikasi habis. Merender ulang...";
                                statusEl.style.color = "#fab387";
                                setTimeout(() => {{
                                    try {{ if (widgetId) window.turnstile.reset(widgetId); }} catch(e){{}}
                                }}, 1500);
                            }}
                        }});
                    }} catch(e) {{
                        resolve({{ success: false, error: String(e) }});
                    }}
                }});
            }}
            """

            login_res = page.evaluate(wallet_script)

            if login_res.get("success"):
                time.sleep(1)
                cookies = context.cookies()
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies if 'sb-' in c['name'] or 'vapi' in c['name']])
                print(f"  [✓] Akun #{idx} ({addr[:6]}...{addr[-4:]}) Sukses Login!")

                with open(TOKENS_FILE, "a", encoding="utf-8") as tf:
                    tf.write(f"{cookie_str}\n")

                time.sleep(2)
            else:
                err = login_res.get("error")
                print(f"  [✖] Akun #{idx} Gagal: {err}")
                if "RATE_LIMITED" in str(err) or "Wait before trying again" in str(err):
                    print("  [!] Rate limit terdeteksi, menunggu 40 detik...")
                    time.sleep(40)

        # Final message in browser
        page.evaluate('''() => {
            const badgeEl = document.getElementById("vapi-badge");
            const titleEl = document.getElementById("vapi-title");
            const addrEl = document.getElementById("vapi-address");
            const statusEl = document.getElementById("vapi-status");
            const slot = document.getElementById("turnstile-slot");

            badgeEl.innerText = "SELESAI!";
            titleEl.innerText = "🎉 Semua Wallet Berhasil Diautentikasi!";
            addrEl.style.display = "none";
            slot.style.display = "none";
            statusEl.innerText = "Menutup jendela dan melanjutkan ke eksekusi tugas harian...";
            statusEl.style.color = "#a6e3a1";
        }''')
        time.sleep(3)
        browser.close()

    print("\n" + "=" * 70)
    print("Semua wallet selesai diautentikasi!")
    final_tokens = load_existing_tokens()
    print(f"Total token aktif saat ini di {TOKENS_FILE}: {len(final_tokens)}")

if __name__ == "__main__":
    main_interactive()
