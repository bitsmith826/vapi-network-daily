#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
           vAPI Network - All-in-One Daily Runner (VS Code)
  Reward Pool : 1,000,000 $vAPI | Network: Base Mainnet
  Tasks       : Auto Connect/Auth | vAPI ID Mint | Daily Check-in | Quests
====================================================================
"""

import os
import sys
import time
import json
import uuid
import re
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows terminal / VS Code
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from eth_account import Account
from eth_account.messages import encode_defunct

# Rich terminal formatting
try:
    import shutil
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    
    term_width = 105
    try:
        cols = shutil.get_terminal_size((105, 24)).columns
        term_width = max(cols, 105)
    except Exception:
        term_width = 105

    console = Console(width=term_width, highlight=False)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

CONFIG_FILE = "config.json"
TOKENS_FILE = "tokens.txt"
PKEYS_FILE = "private_keys.txt"
PROXIES_FILE = "proxies.txt"

DEFAULT_CONFIG = {
    "referral_code": "",
    "base_url": "https://api.vapinetwork.ai",
    "auto_mint_id": True,
    "auto_daily_checkin": True,
    "auto_complete_quests": True,
    "auto_router_key": True,
    "auto_connect_agent": True,
    "quest_delay_seconds": 1,
    "account_delay_seconds": 2
}

def log(msg, style="cyan"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if HAS_RICH:
        try:
            console.print(f"[dim]{timestamp}[/dim] {msg}", style=style)
            return
        except Exception:
            pass
    print(f"[{timestamp}] {msg}")

def log_success(msg):
    log(f"[bold green]✔[/bold green] {msg}", "white")

def log_info(msg):
    log(f"[bold cyan]ℹ[/bold cyan] {msg}", "white")

def log_step(step_name, msg):
    log(f"[bold yellow]▶ [{step_name}][/bold yellow] {msg}", "white")

def log_warn(msg):
    log(f"[bold yellow]⚠[/bold yellow] {msg}", "yellow")

def log_error(msg):
    log(f"[bold red]✖[/bold red] {msg}", "red")

def print_banner(config=None):
    cfg = config or DEFAULT_CONFIG
    ref = cfg.get("referral_code", "").strip()
    ref_line = f"\n[yellow]Referral: {ref}[/yellow]" if ref else ""
    banner_content = (
        "[bold cyan]vAPI Network[/bold cyan] [bold white]— All-in-One Daily Runner[/bold white]\n"
        "[dim]Pool: 1M $vAPI | Chain: Base Mainnet | Mode: Full Auto Daily[/dim]" + ref_line
    )
    if HAS_RICH:
        try:
            console.print(Panel(banner_content, title="[bold magenta]🚀 vAPI ALL-IN-ONE AUTOMATION[/bold magenta]", border_style="cyan", box=box.ROUNDED))
            return
        except Exception:
            pass
    print("=" * 60)
    print("      vAPI Network - All-in-One Daily Runner (Base)")
    print("=" * 60)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception as e:
        log_warn(f"Gagal membaca {CONFIG_FILE}, menggunakan default: {e}")
        return DEFAULT_CONFIG

def load_private_keys():
    if not os.path.exists(PKEYS_FILE):
        return []
    keys = []
    with open(PKEYS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if len(line.split()) >= 12:
                # Seed phrase
                try:
                    Account.enable_unaudited_hdwallet_features()
                    acc = Account.from_mnemonic(line)
                    keys.append(acc.key.hex())
                except Exception:
                    pass
            elif line.startswith("0x") or len(line) == 64:
                k = line if line.startswith("0x") else "0x" + line
                keys.append(k)
    return keys

def load_tokens():
    if not os.path.exists(TOKENS_FILE):
        return []
    with open(TOKENS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def load_proxies():
    if not os.path.exists(PROXIES_FILE):
        return []
    with open(PROXIES_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def shorten_address(addr):
    if not addr or len(addr) < 12:
        return str(addr)
    return f"{addr[:6]}...{addr[-4:]}"

def test_token_valid(cookie_str, base_url="https://api.vapinetwork.ai"):
    """Quick check if a session cookie is still valid without doing full UI"""
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"{base_url}/earn",
        "Cookie": cookie_str
    })
    try:
        r = s.get(f"{base_url}/api/account", timeout=10)
        if r.status_code == 200:
            data = r.json()
            addr = data.get("profile", {}).get("walletAddress") or data.get("walletAddress")
            return addr
        return None
    except Exception:
        return None

def auto_login_with_camoufox(private_keys, existing_tokens=None, config=None):
    """
    100% Automated, Headless Camoufox Turnstile Solver & SIWE Authenticator.
    Iterates over all private keys and captures valid session cookies.
    """
    cfg = config or DEFAULT_CONFIG
    base_url = cfg.get("base_url", "https://api.vapinetwork.ai").rstrip("/")
    ref_code = cfg.get("referral_code", "").strip()
    target_url = f"{base_url}/earn?ref={ref_code}" if ref_code else f"{base_url}/earn"

    try:
        from camoufox.sync_api import Camoufox
    except ImportError:
        log_error("Paket camoufox belum terinstall. Jalankan: pip install camoufox")
        return []

    log_step("CAMOUFOX AUTH", f"Menjalankan login otomatis 100% headless untuk {len(private_keys)} akun...")
    
    # Download Turnstile api.js once
    try:
        api_js = requests.get('https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit', timeout=15).text
    except Exception as e:
        log_error(f"Gagal mengunduh script Cloudflare Turnstile: {e}")
        return []

    # Map existing valid sessions by wallet address to avoid re-logging in
    valid_sessions = {}
    if existing_tokens:
        log_info("Memeriksa sesi login yang sudah ada di tokens.txt...")
        for tok in existing_tokens:
            addr = test_token_valid(tok)
            if addr:
                valid_sessions[addr.lower()] = tok
                log_success(f"Sesi aktif ditemukan untuk: {shorten_address(addr)}")

    final_tokens = []
    keys_to_login = []

    for idx, pkey in enumerate(private_keys, 1):
        try:
            acc = Account.from_key(pkey)
            addr_lower = acc.address.lower()
            if addr_lower in valid_sessions:
                final_tokens.append(valid_sessions[addr_lower])
            else:
                keys_to_login.append((idx, pkey, acc))
        except Exception as e:
            log_error(f"Private key #{idx} tidak valid: {e}")

    if not keys_to_login:
        log_success(f"Semua {len(final_tokens)} akun sudah memiliki sesi aktif!")
        return final_tokens

    log_info(f"Membuka browser Camoufox untuk menyelesaikan Turnstile & SIWE bagi {len(keys_to_login)} akun...")

    with Camoufox(headless=True) as browser:
        context = browser.new_context()
        
        for num, (idx, pkey, acc) in enumerate(keys_to_login, 1):
            addr = acc.address
            log_step("AUTO-LOGIN", f"[{num}/{len(keys_to_login)}] Autentikasi Akun #{idx}: [bold green]{shorten_address(addr)}[/bold green]")
            
            def sign_fn(msg_text):
                encoded = encode_defunct(text=msg_text)
                sig = acc.sign_message(encoded).signature.hex()
                return "0x" + sig if not sig.startswith("0x") else sig

            page = context.new_page()
            page.expose_function("pySignMessage", sign_fn)
            
            try:
                page.goto(target_url)
                time.sleep(2)

                # Inject Turnstile script element and evaluate api_js
                page.evaluate('''() => {
                    const s = document.createElement("script");
                    s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
                    s.async = true;
                    document.head.appendChild(s);
                }''')
                page.evaluate(api_js)

                # Solve Turnstile
                ts_res = page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        const cont = document.createElement("div");
                        cont.id = "cf-ts-" + Date.now();
                        cont.style.position = "fixed";
                        cont.style.bottom = "20px";
                        cont.style.right = "20px";
                        cont.style.width = "300px";
                        cont.style.height = "100px";
                        cont.style.zIndex = "999999";
                        document.body.appendChild(cont);
                        
                        window.turnstile.render(cont, {
                            sitekey: "0x4AAAAAAEN_PvE1iYWei9wu",
                            action: "account_creation",
                            callback: (token) => resolve({ success: true, token: token }),
                            "error-callback": (err) => resolve({ success: false, error: err }),
                            "timeout-callback": () => resolve({ success: false, error: "turnstile timeout" })
                        });
                        setTimeout(() => resolve({ success: false, error: "timeout" }), 25000);
                    });
                }
                """)
                ts_token = ts_res.get("token")
                if not ts_token:
                    log_error(f"Gagal menyelesaikan Turnstile untuk {shorten_address(addr)}: {ts_res.get('error')}")
                    page.close()
                    continue

                # Submit SIWE inside Camoufox page
                siwe_script = """
                async (args) => {
                    const resNonce = await fetch('/api/auth/siwe-nonce', { cache: 'no-store' });
                    const { nonce } = await resNonce.json();

                    const resChallenge = await fetch('/api/protection/challenge', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'auth.siwe.verify' })
                    });
                    const challenge = await resChallenge.json();

                    const now = new Date();
                    const message = [
                        `${window.location.host} wants you to sign in with your Ethereum account:`,
                        args.address,
                        "",
                        "Sign in to vAPI Network. This will not trigger a blockchain transaction.",
                        "",
                        `URI: ${window.location.href}`,
                        "Version: 1",
                        "Chain ID: 8453",
                        `Nonce: ${nonce}`,
                        `Issued At: ${now.toISOString()}`
                    ].join("\\n");

                    const signature = await window.pySignMessage(message);

                    const resSiwe = await fetch('/api/auth/siwe', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            message: message,
                            signature: signature,
                            protection: {
                                challengeToken: challenge.token,
                                elapsedMs: 2500,
                                honeypot: "",
                                bot: { status: "not_detected" }
                            },
                            turnstileToken: args.turnstileToken
                        })
                    });
                    return await resSiwe.json();
                }
                """
                auth_res = page.evaluate(siwe_script, {"turnstileToken": ts_token, "address": addr})

                if auth_res and (auth_res.get("code") == "RATE_LIMITED" or "Wait before trying again" in str(auth_res)):
                    log_warn(f"SIWE Rate limit terdeteksi pada Akun #{idx}. Menunggu 45 detik...")
                    time.sleep(45)
                    auth_res = page.evaluate(siwe_script, {"turnstileToken": ts_token, "address": addr})
                
                if auth_res.get("ok"):
                    cookies = context.cookies()
                    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies if 'sb-' in c['name'] or 'vapi' in c['name']])
                    log_success(f"Akun #{idx} ({shorten_address(addr)}) Berhasil Login via Camoufox!")
                    final_tokens.append(cookie_str)
                    # Simpan langsung ke tokens.txt agar tidak hilang jika terputus
                    with open(TOKENS_FILE, "a", encoding="utf-8") as tf:
                        tf.write(f"{cookie_str}\n")
                else:
                    log_error(f"Akun #{idx} ({shorten_address(addr)}) SIWE ditolak: {auth_res}")

            except Exception as e:
                log_error(f"Error saat login Akun #{idx}: {e}")
            finally:
                page.close()
                context.clear_cookies()
                time.sleep(3)

        browser.close()

    # Save all fresh tokens to tokens.txt
    if final_tokens:
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            for tok in final_tokens:
                f.write(f"{tok}\n")
        log_success(f"Semua {len(final_tokens)} sesi berhasil diperbarui di {TOKENS_FILE}!")

    return final_tokens

class VapiClient:
    def __init__(self, raw_token, proxy=None, config=None):
        self.raw_token = raw_token.strip()
        self.proxy = proxy
        self.config = config or DEFAULT_CONFIG
        self.base_url = self.config.get("base_url", "https://api.vapinetwork.ai").rstrip("/")
        self.ref_code = self.config.get("referral_code", "").strip()
        
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        if self.proxy:
            self.session.proxies = {"http": self.proxy, "https": self.proxy}

        self._setup_auth()

    def _setup_auth(self):
        referer_url = f"{self.base_url}/earn?ref={self.ref_code}" if self.ref_code else f"{self.base_url}/earn"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": self.base_url,
            "Referer": referer_url,
            "X-Earn-View": "2",
            "Content-Type": "application/json"
        }
        self.session.headers.update(headers)
        if self.ref_code:
            self.session.cookies.set("vapi_ref", self.ref_code, domain="api.vapinetwork.ai")

        token = self.raw_token
        if "=" in token and ";" in token:
            for part in token.split(";"):
                if "=" in part:
                    k, v = part.strip().split("=", 1)
                    self.session.cookies.set(k.strip(), v.strip(), domain="api.vapinetwork.ai")
        elif "sb-" in token and "=" in token:
            k, v = token.strip().split("=", 1)
            self.session.cookies.set(k.strip(), v.strip(), domain="api.vapinetwork.ai")
        else:
            self.session.headers["Authorization"] = f"Bearer {token}"
            self.session.cookies.set("sb-uxajzjyqicllxoplzgtk-auth-token", token, domain="api.vapinetwork.ai")

    def setup_account(self, address=None):
        """
        Auto-completes initial onboarding setup when setupComplete is false or board returns 409 setup_required.
        1. complete_setup (avatarVariant, safetyWord)
        2. claim_username (username)
        3. mint_id (avatarVariant, username)
        """
        clean_addr = (address or "user").replace("0x", "").lower()
        suffix = clean_addr[-6:] if len(clean_addr) >= 6 else clean_addr
        uname = f"vapiuser{suffix}"
        
        # Step 1: complete_setup
        try:
            self.session.patch(f"{self.base_url}/api/account", json={
                "action": "complete_setup",
                "avatarVariant": 1,
                "safetyWord": uname
            }, timeout=15)
        except Exception:
            pass

        # Step 2: claim_username
        try:
            self.session.patch(f"{self.base_url}/api/account", json={
                "action": "claim_username",
                "username": uname
            }, timeout=15)
        except Exception:
            pass

        # Step 3: mint_id action
        try:
            self.session.patch(f"{self.base_url}/api/account", json={
                "action": "mint_id",
                "avatarVariant": 1,
                "username": uname
            }, timeout=15)
        except Exception:
            pass
        return uname

    def get_account(self):
        try:
            res = self.session.get(f"{self.base_url}/api/account", timeout=15)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception:
            return None

    def get_id_status(self):
        try:
            res = self.session.get(f"{self.base_url}/api/id/me", timeout=15)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception:
            return None

    def mint_id(self):
        try:
            res = self.session.post(f"{self.base_url}/api/id/mint", json={}, timeout=20)
            if res.status_code in (200, 201):
                data = res.json()
                st = data.get("state")
                if st == "failed":
                    return {"state": "queued_relayer"}
                return data
            elif res.status_code == 409:
                data = res.json()
                if data.get("error") == "id_not_issued":
                    return {"state": "deferred"}
                return {"state": "already_minted"}
            return {"state": "queued_relayer"}
        except Exception:
            return {"state": "queued_relayer"}

    def get_board(self, fresh=False):
        url = f"{self.base_url}/api/earn/board?fresh=1" if fresh else f"{self.base_url}/api/earn/board"
        try:
            res = self.session.get(url, timeout=20)
            if res.status_code == 200:
                return res.json()
            elif res.status_code == 409 and "setup_required" in res.text:
                acc = self.get_account()
                addr = None
                if acc:
                    addr = acc.get("profile", {}).get("walletAddress")
                self.setup_account(addr)
                time.sleep(1)
                res_retry = self.session.get(url, timeout=20)
                if res_retry.status_code == 200:
                    return res_retry.json()
            return None
        except Exception:
            return None

    def execute_quest_action(self, quest_id, action, inputs=None):
        url = f"{self.base_url}/api/earn/quests/{quest_id}/{action}"
        body = {"inputs": inputs or {}}
        headers = {"Idempotency-Key": str(uuid.uuid4())}
        try:
            res = self.session.post(url, json=body, headers=headers, timeout=20)
            if res.status_code in (200, 201):
                return res.json()
            try:
                return {"error": res.json().get("error") or res.text, "status": res.status_code}
            except Exception:
                return {"error": res.text, "status": res.status_code}
        except Exception as e:
            return {"error": str(e), "status": 0}

    def create_router_key(self, label="daily-bot"):
        """Creates a router key using compute source (100% free) if not already created"""
        try:
            res_get = self.session.get(f"{self.base_url}/api/router/keys", timeout=15)
            if res_get.status_code == 200:
                data = res_get.json()
                if data.get("keyCount", 0) > 0:
                    return True
            res_post = self.session.post(f"{self.base_url}/api/router/keys", json={
                "label": label,
                "source": "compute"
            }, timeout=15)
            return res_post.status_code in (200, 201)
        except Exception:
            return False

    def connect_agent(self):
        """Connects an agent to the account via OAuth device authorization in pure Python (100% free)"""
        try:
            # 1. Ephemeral agent wallet
            agent = Account.create()

            # 2. Nonce
            r_nonce = self.session.get(f"{self.base_url}/api/auth/siwe-nonce?purpose=link", timeout=15)
            if r_nonce.status_code != 200:
                return False
            nonce = r_nonce.json().get("nonce")
            if not nonce:
                return False

            # 3. SIWE message
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            msg = (
                f"api.vapinetwork.ai wants you to sign in with your Ethereum account:\n"
                f"{agent.address}\n\n"
                f"Link this wallet to a vAPI account as an agent.\n\n"
                f"URI: {self.base_url}\n"
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
            r_auth = self.session.post(f"{self.base_url}/oauth/device_authorization", json=auth_payload, timeout=15)
            if r_auth.status_code != 200:
                return False
            auth_data = r_auth.json()
            device_code = auth_data.get("device_code")
            user_code = auth_data.get("user_code")
            client_id = auth_data.get("client_id", "vapi-network")

            # 5. Owner approval via logged-in session
            approve_data = {
                "code": user_code,
                "intent": "approve",
                "routerAllowanceUsd": "1.00"
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": f"{self.base_url}/link?code={user_code}",
                "Origin": self.base_url
            }
            r_app = self.session.post(f"{self.base_url}/link", data=approve_data, headers=headers, timeout=15)
            if r_app.status_code != 200:
                return False

            # 6. Finalize token exchange
            poll_data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": client_id
            }
            requests.post(f"{self.base_url}/oauth/token", data=poll_data, timeout=15)
            return True
        except Exception:
            return False

def format_countdown(iso_str):
    if not iso_str:
        return "Siap"
    try:
        target = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = target - now
        secs = int(diff.total_seconds())
        if secs <= 0:
            return "Siap"
        hours, remainder = divmod(secs, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"Cooldown ({hours}j {minutes}m)"
    except Exception:
        return "Cooldown"

def process_single_account(idx, total, raw_token, proxy, config):
    client = VapiClient(raw_token, proxy, config)

    # 1. Account Info
    account = client.get_account()
    if not account:
        log_error(f"Akun #{idx}: Sesi autentikasi gagal / kadaluarsa (401).")
        return {
            "idx": idx,
            "address": "Invalid Session",
            "username": "-",
            "id_status": "Failed",
            "checkin": "Failed",
            "quests": "0",
            "points": "0 pts",
            "rank": "-",
            "status": "[bold red]Error[/bold red]"
        }

    profile = account.get("profile", {})
    wallet_address = profile.get("walletAddress") or account.get("walletAddress") or account.get("address") or "Unknown"

    # Auto-onboarding if new account
    if not profile.get("setupComplete", False):
        new_uname = client.setup_account(wallet_address)
        time.sleep(1)
        account = client.get_account() or account
        profile = account.get("profile", {})
        username = profile.get("username") or new_uname
    else:
        username = profile.get("username") or profile.get("safetyWord") or ""

    if HAS_RICH:
        console.print(f"\n[bold cyan]────────────────────────────────────────────────────────────────────────────[/bold cyan]")
        console.print(f"[bold white]▶ AKUN [{idx}/{total}][/bold white] │ [cyan]{wallet_address}[/cyan]" + (f" [dim]({username})[/dim]" if username else ""))
    else:
        print(f"\n--- AKUN [{idx}/{total}] --- {wallet_address} ({username})")

    # 2. Check / Mint ID (Base Network)
    id_status_str = "Belum"
    if config.get("auto_mint_id", True):
        id_info = client.get_id_status()
        if id_info and id_info.get("hasId"):
            tok_id = id_info.get("tokenId")
            id_status_str = "Minted"
            log(f"  [dim]•[/dim] [cyan]vAPI ID (Base)[/cyan]  : [bold green]Minted[/bold green] [dim]({shorten_address(tok_id)})[/dim]")
        else:
            mint_res = client.mint_id()
            st = mint_res.get("state") if mint_res else "Proses"
            if st in ("confirmed", "submitted", "pending", "already_minted"):
                id_status_str = "Minted"
                log(f"  [dim]•[/dim] [cyan]vAPI ID (Base)[/cyan]  : [bold green]Minted ({st})[/bold green]")
            elif st in ("deferred", "queued_relayer"):
                id_status_str = "Relayer Queue"
                log(f"  [dim]•[/dim] [cyan]vAPI ID (Base)[/cyan]  : [yellow]Relayer Queue[/yellow]")
            else:
                id_status_str = st.capitalize() if st else "Proses"
                log(f"  [dim]•[/dim] [cyan]vAPI ID (Base)[/cyan]  : [cyan]{id_status_str}[/cyan]")

    # 3. Quest Board & Daily Check-in
    checkin_str = "Skip"
    board_data = client.get_board(fresh=True)
    if not board_data or "board" not in board_data:
        log_error(f"  [dim]•[/dim] [red]Gagal mengambil data quest board.[/red]")
        return {
            "idx": idx,
            "address": shorten_address(wallet_address),
            "username": username or "-",
            "id_status": id_status_str,
            "checkin": "Error",
            "quests": "0",
            "points": "0 pts",
            "rank": "-",
            "status": "[yellow]Board Error[/yellow]"
        }

    board = board_data["board"]
    sections = board.get("sections", [])
    
    current_points = board.get("points", {}).get("total", 0) if isinstance(board.get("points"), dict) else 0
    user_rank = board.get("points", {}).get("rank", "-") if isinstance(board.get("points"), dict) else "-"

    daily_quest = None
    for sec in sections:
        for q in sec.get("quests", []):
            if sec.get("key") == "daily" or q.get("questType") == "daily" or q.get("kind") == "checkin" or "check-in" in q.get("title", "").lower():
                daily_quest = q
                break
        if daily_quest:
            break

    if daily_quest and config.get("auto_daily_checkin", True):
        q_id = daily_quest.get("id")
        q_title = daily_quest.get("title", "Daily Check-in")
        next_at = daily_quest.get("nextAvailableAt")
        q_state = daily_quest.get("state")

        is_ready = True
        if q_state == "cooldown" or next_at:
            if next_at:
                try:
                    target_dt = datetime.fromisoformat(next_at.replace("Z", "+00:00"))
                    if target_dt > datetime.now(timezone.utc):
                        is_ready = False
                        cd_text = format_countdown(next_at)
                        checkin_str = cd_text
                        log(f"  [dim]•[/dim] [cyan]Daily Check-in[/cyan]  : [yellow]{cd_text}[/yellow]")
                except Exception:
                    pass
            if is_ready and q_state == "cooldown":
                is_ready = False
                checkin_str = "Cooldown"
                log(f"  [dim]•[/dim] [cyan]Daily Check-in[/cyan]  : [yellow]Cooldown[/yellow]")

        if is_ready:
            claim_res = client.execute_quest_action(q_id, "claim")
            outcome = claim_res.get("outcome", {})
            if outcome.get("kind") == "completed":
                pts = outcome.get("pointsAwarded", 10)
                checkin_str = f"Claimed (+{pts})"
                log(f"  [dim]•[/dim] [cyan]Daily Check-in[/cyan]  : [bold green]Claimed (+{pts} pts)[/bold green]")
            else:
                checkin_str = outcome.get("kind", "Sudah")
                log(f"  [dim]•[/dim] [cyan]Daily Check-in[/cyan]  : [dim cyan]{checkin_str}[/dim cyan]")

    # 4. Quests Automation (Clean, Fast & Platform Tasks)
    quests_done_count = 0
    total_quests = 0

    if config.get("auto_complete_quests", True):
        # Auto platform quests: Router Key & Connect Agent
        router_q = None
        agent_q = None
        for sec in sections:
            for q in sec.get("quests", []):
                t_lower = q.get("title", "").lower()
                if "router key" in t_lower:
                    router_q = q
                elif "connect an agent" in t_lower or ("connect" in t_lower and "agent" in t_lower):
                    agent_q = q

        if config.get("auto_router_key", True) and router_q and router_q.get("state") != "completed":
            if client.create_router_key():
                log(f"  [dim]•[/dim] [cyan]Router Key[/cyan]      : [bold green]Created (+150 pts)[/bold green]")
                time.sleep(1)

        if config.get("auto_connect_agent", True) and agent_q and agent_q.get("state") != "completed":
            if client.connect_agent():
                log(f"  [dim]•[/dim] [cyan]Connect Agent[/cyan]   : [bold green]Linked (+250 pts)[/bold green]")
                time.sleep(1)

        # Standard quest loop
        for sec in sections:
            for q in sec.get("quests", []):
                q_id = q.get("id")
                q_title = q.get("title", q_id)
                q_action = q.get("action", "verify")
                q_state = q.get("state")
                q_points = q.get("points", 0)
                inputs = q.get("inputs", [])

                if daily_quest and q_id == daily_quest.get("id"):
                    continue

                total_quests += 1
                if q_state == "completed":
                    quests_done_count += 1
                    continue

                if inputs and len(inputs) > 0:
                    continue

                # Skip platform quests from manual button attempt since they reconcile automatically
                if "router key" in q_title.lower() or "connect an agent" in q_title.lower():
                    continue

                # Only attempt available quests
                if q_state in ("available", None):
                    act = "verify" if q_action == "verify" else "claim"
                    action_res = client.execute_quest_action(q_id, act)
                    outcome = action_res.get("outcome", {})

                    if outcome.get("kind") == "completed":
                        pts = outcome.get("pointsAwarded", q_points)
                        log(f"  [dim]•[/dim] [cyan]Quest Selesai[/cyan]   : [bold green]{q_title} (+{pts} pts)[/bold green]")
                        quests_done_count += 1
                        time.sleep(1)

    # 5. Final Points & Rank
    final_board = client.get_board(fresh=True)
    if final_board and "board" in final_board:
        b_sub = final_board["board"]
        if isinstance(b_sub.get("points"), dict):
            current_points = b_sub["points"].get("total", current_points)
            user_rank = b_sub["points"].get("rank", user_rank)
        # Recount completed quests after potential platform quest updates
        f_sections = b_sub.get("sections", [])
        q_done_fresh = 0
        q_tot_fresh = 0
        for s in f_sections:
            for q in s.get("quests", []):
                if daily_quest and q.get("id") == daily_quest.get("id"):
                    continue
                q_tot_fresh += 1
                if q.get("state") == "completed":
                    q_done_fresh += 1
        quests_done_count = max(quests_done_count, q_done_fresh)
        total_quests = max(total_quests, q_tot_fresh)

    log(f"  [dim]•[/dim] [cyan]Board Quests[/cyan]    : [bold magenta]{quests_done_count}/{total_quests} Selesai[/bold magenta]")

    rank_str = f"#{user_rank:,}" if (user_rank and isinstance(user_rank, int)) else (f"#{user_rank}" if (user_rank and str(user_rank).strip() not in ("None", "-", "")) else "Active")
    log(f"  [dim]•[/dim] [cyan]Poin & Rank[/cyan]     : [bold green]{current_points:,} pts[/bold green] │ [bold yellow]Rank {rank_str}[/bold yellow]")

    return {
        "idx": idx,
        "address": shorten_address(wallet_address),
        "username": username or "-",
        "id_status": id_status_str,
        "checkin": checkin_str,
        "quests": f"{quests_done_count}/{total_quests}",
        "points": f"{current_points:,} pts",
        "rank": rank_str,
        "status": "[bold green]Sukses[/bold green]"
    }

def print_summary_table(results):
    if not results:
        return

    total_points_all = 0
    top_rank = None

    for r in results:
        try:
            pts_int = int(r["points"].replace(" pts", "").replace(",", "").strip())
            total_points_all += pts_int
        except Exception:
            pass
        rk = r.get("rank", "")
        if rk.startswith("#"):
            try:
                rk_num = int(rk.replace("#", "").replace(",", "").strip())
                if top_rank is None or rk_num < top_rank:
                    top_rank = rk_num
            except Exception:
                pass

    if HAS_RICH:
        try:
            table = Table(
                title="[bold magenta]📊 RINGKASAN HARIAN vAPI NETWORK[/bold magenta]",
                box=box.ROUNDED,
                header_style="bold cyan",
                border_style="bright_blue"
            )
            table.add_column("No", justify="center", style="bold yellow", no_wrap=True)
            table.add_column("Wallet Address", justify="center", style="cyan", no_wrap=True)
            table.add_column("Username", justify="left", style="white", no_wrap=True)
            table.add_column("vAPI ID", justify="center", no_wrap=True)
            table.add_column("Daily Check-in", justify="center", no_wrap=True)
            table.add_column("Points", justify="right", style="bold green", no_wrap=True)
            table.add_column("Rank", justify="center", style="bold yellow", no_wrap=True)
            table.add_column("Status", justify="center", no_wrap=True)

            for r in results:
                ck = r["checkin"]
                if "Claimed" in ck:
                    ck_colored = f"[bold green]{ck}[/bold green]"
                elif "Cooldown" in ck:
                    ck_colored = f"[bold yellow]{ck}[/bold yellow]"
                else:
                    ck_colored = f"[cyan]{ck}[/cyan]"

                id_st = r["id_status"]
                id_colored = f"[bold green]{id_st}[/bold green]" if "Minted" in id_st else f"[yellow]{id_st}[/yellow]"

                table.add_row(
                    str(r["idx"]),
                    r["address"],
                    r["username"],
                    id_colored,
                    ck_colored,
                    r["points"],
                    r["rank"],
                    r["status"]
                )

            console.print()
            console.print(table)
            
            top_rank_str = f"#{top_rank:,}" if top_rank else "-"
            summary_bar = (
                f"\n[bold cyan]Total Wallets:[/bold cyan] {len(results)}  │  "
                f"[bold green]Total Poin:[/bold green] {total_points_all:,} pts  │  "
                f"[bold yellow]Top Rank:[/bold yellow] {top_rank_str}  │  "
                f"[bold green]Status: {len(results)}/{len(results)} Sukses[/bold green]\n"
            )
            console.print(summary_bar)
            return
        except Exception:
            pass

    print("\n" + "=" * 90)
    print("                         RINGKASAN HARIAN vAPI NETWORK")
    print("=" * 90)
    print(f"{'No':<4} {'Wallet Address':<18} {'Username':<16} {'vAPI ID':<12} {'Daily Check-in':<20} {'Points':<12} {'Rank':<10} {'Status'}")
    print("-" * 90)
    for r in results:
        clean_status = r['status'].replace('[bold green]', '').replace('[/bold green]', '').replace('[red]', '').replace('[/red]', '').replace('[yellow]', '').replace('[/yellow]', '')
        print(f"#{r['idx']:<3} {r['address']:<18} {r['username']:<16} {r['id_status']:<12} {r['checkin']:<20} {r['points']:<12} {r['rank']:<10} {clean_status}")
    print("=" * 90)
    print(f"Total Wallets: {len(results)} | Total Poin: {total_points_all:,} pts | Status: {len(results)}/{len(results)} Sukses\n")

def main():
    config = load_config()
    print_banner(config)

    pkeys = load_private_keys()
    existing_tokens = load_tokens()
    proxies = load_proxies()

    start_time = time.time()

    if not pkeys:
        log_error(f"Tidak ada private key di file {PKEYS_FILE}. Silakan isi private key.")
        return

    log_info(f"Ditemukan [bold cyan]{len(pkeys)} Wallet[/bold cyan] di {PKEYS_FILE}.")

    # If tokens are fewer than private keys or missing, auto-authenticate with Camoufox!
    if len(existing_tokens) < len(pkeys):
        tokens = auto_login_with_camoufox(pkeys, existing_tokens, config)
    else:
        # Check if first token is valid, if not refresh all
        first_valid = test_token_valid(existing_tokens[0]) if existing_tokens else None
        if not first_valid:
            log_warn("Sesi yang tersimpan kadaluarsa. Memperbarui otomatis via Camoufox...")
            tokens = auto_login_with_camoufox(pkeys, None, config)
        else:
            tokens = existing_tokens

    if not tokens:
        log_error("Gagal mendapatkan sesi autentikasi.")
        return

    active_tokens = tokens[:len(pkeys)]
    log_info(f"\nMemulai Eksekusi Tugas Harian untuk [bold cyan]{len(active_tokens)} Akun[/bold cyan]...")

    results = []
    for idx, acc in enumerate(active_tokens, 1):
        proxy = proxies[(idx - 1) % len(proxies)] if proxies else None
        res = process_single_account(idx, len(active_tokens), acc, proxy, config)
        results.append(res)

        if idx < len(active_tokens):
            delay = config.get("account_delay_seconds", 3)
            time.sleep(delay)

    # Print Precision Summary Table
    print_summary_table(results)

    elapsed = int(time.time() - start_time)
    mins, secs = divmod(elapsed, 60)
    if HAS_RICH:
        console.print(f"\n[bold green]✔ Selesai dalam {mins}m {secs}s! Siap dijalankan kembali besok jam 8 pagi.[/bold green]\n")
    else:
        print(f"\nSelesai dalam {mins}m {secs}s! Siap dijalankan kembali besok jam 8 pagi.\n")

if __name__ == "__main__":
    main()
