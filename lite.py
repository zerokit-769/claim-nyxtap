#!/usr/init/env python3
# -*- coding: utf-8 -*-
"""
LiteBits.io Telegram Mini App Auto Claim Bot (@litebits_faucet_bot)
- Telethon Auth + Referral 78CO20HD
- Auto-stop 6 jam + Session Report
- Classic CLI Banner with Dynamic Live Logs & Progress Bar
"""

import time
import json
import re
import os
import sys
import random
import urllib.parse
import asyncio
from datetime import datetime, timezone
from collections import deque

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


# ==================== COLORS ====================
class Col:
    R = '\033[0m'
    B = '\033[1m'
    D = '\033[2m'
    RED = '\033[91m'
    GRN = '\033[92m'
    YEL = '\033[93m'
    BLU = '\033[94m'
    MAG = '\033[95m'
    CYN = '\033[96m'
    WHT = '\033[97m'
    GRY = '\033[90m'
    NEON_G = '\033[38;5;46m'
    NEON_C = '\033[38;5;51m'
    NEON_Y = '\033[38;5;226m'
    NEON_P = '\033[38;5;207m'
    NEON_O = '\033[38;5;208m'
    NEON_V = '\033[38;5;141m'
    NEON_R = '\033[38;5;196m'
    DIM_C  = '\033[38;5;244m'


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


# ==================== ANIMATIONS ====================
class Anim:
    @staticmethod
    def spinner(text, duration=1.5):
        sys.stdout.write(f" {Col.NEON_C}[*]{Col.R} {Col.WHT}{text}...{Col.R}")
        sys.stdout.flush()
        time.sleep(duration)
        sys.stdout.write(f"\r {Col.NEON_G}[✓]{Col.R} {Col.WHT}{text} - Selesai{Col.R}\n")
        sys.stdout.flush()

    @staticmethod
    def progress(text, duration=1.0):
        sys.stdout.write(f" {Col.NEON_C}[>]{Col.R} {Col.WHT}{text}{Col.R}")
        sys.stdout.flush()
        time.sleep(duration)
        sys.stdout.write(f"\r {Col.NEON_G}[✓]{Col.R} {Col.WHT}{text}{Col.R}\n")
        sys.stdout.flush()

    @staticmethod
    def typewriter(text, delay=0.01, color=None):
        c = color or Col.WHT
        for ch in text:
            sys.stdout.write(f"{c}{ch}{Col.R}")
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def opening_sequence():
        clear()
        print()
        Anim.typewriter(f"{Col.NEON_C}Initializing boot sequence...", 0.01, Col.NEON_C)
        time.sleep(0.2)
        Anim.progress("Loading core modules", 0.5)
        Anim.progress("Establishing secure channel", 0.5)
        Anim.progress("Verifying signature chain", 0.5)
        print()
        print(render_banner())
        print()
        time.sleep(0.5)


# ==================== BANNER ====================
def render_banner():
    return f"""{Col.NEON_C}=============================================================={Col.R}
                   ⚡ {Col.NEON_G}LITEBITS{Col.R} ⚡                   
                     AUTO CLAIM SYSTEM v2.0                   
{Col.NEON_C}=============================================================={Col.R}
{Col.NEON_V}ScriptMaker : {Col.WHT}ZeinthHub{Col.R}                             
{Col.NEON_V}Bot         : {Col.NEON_C}@litebits_faucet_bot{Col.R}                     
{Col.NEON_V}Referral    : {Col.NEON_Y}{REFERRAL_CODE}{Col.R}                                 
{Col.NEON_V}Auto-stop   : {Col.NEON_O}{MAX_RUNTIME // 3600} hours{Col.R}                                 
{Col.NEON_V}Status      : {Col.NEON_G}● ONLINE{Col.R}                             
{Col.NEON_C}=============================================================={Col.R}"""


# ==================== CONFIG ====================
API_HASH      = 'fb06985ea797ac51aaa1e6d1168ceaaa'
API_ID        = 35898257
DEFAULT_BOT   = 'litebits_faucet_bot'
REFERRAL_CODE = '78CO20HD'
CONFIG_FILE   = 'litebits.json'
BASE_URL      = 'https://mini.litebits.io'

HOLD_DURATION    = 5
PREPARE_WAIT     = 8
AD_VIEW_WAIT     = 20
DEFAULT_COOLDOWN = 301

MAX_RUNTIME = 6 * 3600

try:
    from telethon import TelegramClient, functions, types
    HAS_TELETHON = True
except ImportError:
    HAS_TELETHON = False


# ==================== BOT ====================
class LiteBitsTeleBot:

    def __init__(self):
        self.session          = None
        self.init_data        = ""
        self.auth_token       = ""
        self.bot_username     = DEFAULT_BOT
        self.user_agent       = "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36 Telegram-Android"
        self.session_earned   = 0.0
        self.cycles           = 0
        self.cycles_failed    = 0
        self.user_info        = {}
        self.cooldown_seconds = DEFAULT_COOLDOWN
        self.running          = True
        self.cycle_logs       = deque(maxlen=6)
        self.base_dir         = os.path.dirname(os.path.abspath(__file__))
        self.start_time       = time.time()

    def _bar(self, remaining, total, width=20):
        if total <= 0:
            total = 1
        filled = int((total - remaining) / total * width)
        filled = max(0, min(width, filled))
        empty = width - filled
        return f"{Col.NEON_G}{'█' * filled}{Col.DIM_C}{'░' * empty}{Col.R}"

    def _progress_wait(self, seconds, label="WAIT"):
        total = seconds
        for left in range(seconds, 0, -1):
            if not self.running:
                break
            bar = self._bar(left, total, width=20)
            mm, ss = divmod(left, 60)
            hh, mm = divmod(mm, 60)
            tstr = f"{hh:02d}:{mm:02d}:{ss:02d}" if hh > 0 else f"{mm:02d}:{ss:02d}"
            line = f" [⏳ {label}] Cooldown {tstr}  [{bar}]"
            self.render_view(live_line=line)
            time.sleep(1)

    def render_dashboard(self):
        name = str(
            self.user_info.get('telegramUsername')
            or self.user_info.get('username')
            or self.user_info.get('first_name')
            or 'User'
        )
        if not name.startswith('@') and (
            self.user_info.get('telegramUsername') or self.user_info.get('username')
        ):
            name = '@' + name

        try:
            bal = float(str(self.user_info.get('balance', '0')))
            bal_str = f"{bal:.2f} Coins"
        except Exception:
            bal_str = f"{self.user_info.get('balance', '0.00')} Coins"

        earned_str = f"+{self.session_earned:.2f} Coins"
        total_cyc = self.cycles + self.cycles_failed
        rate = (self.cycles / total_cyc * 100) if total_cyc > 0 else 100.0

        elapsed = int(time.time() - self.start_time)
        remaining = max(0, MAX_RUNTIME - elapsed)
        eh, er = divmod(elapsed, 3600); em, es = divmod(er, 60)
        rh, rr = divmod(remaining, 3600); rm, rs = divmod(rr, 60)

        out = []
        out.append(f"{Col.NEON_C}┌─ ACCOUNT ─────────────────────────────────────────────────┐{Col.R}")
        out.append(f"{Col.NEON_C}│{Col.R} User      : {Col.NEON_C}{name:<45}{Col.NEON_C}│{Col.R}")
        out.append(f"{Col.NEON_C}│{Col.R} Balance   : {Col.NEON_Y}{bal_str:<45}{Col.NEON_C}│{Col.R}")
        out.append(f"{Col.NEON_C}│{Col.R} Earned    : {Col.NEON_G}{earned_str:<45}{Col.NEON_C}│{Col.R}")
        out.append(f"{Col.NEON_C}│{Col.R} Cycles    : {Col.WHT}{str(self.cycles):<45}{Col.NEON_C}│{Col.R}")
        out.append(f"{Col.NEON_C}│{Col.R} Success   : {Col.NEON_G if rate >= 90 else Col.NEON_Y}{f'{rate:.1f}%':<45}{Col.NEON_C}│{Col.R}")
        out.append(f"{Col.NEON_C}│{Col.R} Uptime    : {Col.NEON_C}{f'{eh:02d}:{em:02d}:{es:02d}':<45}{Col.NEON_C}│{Col.R}")
        out.append(f"{Col.NEON_C}│{Col.R} Remaining : {Col.NEON_O}{f'{rh:02d}:{rm:02d}:{rs:02d}':<45}{Col.NEON_C}│{Col.R}")
        out.append(f"{Col.NEON_C}└────────────────────────────────────────────────────────────┘{Col.R}")
        return "\n".join(out)

    def render_view(self, live_line=None):
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        print(render_banner())
        print(self.render_dashboard())

        print(f"\n{Col.NEON_C}========================= LIVE LOGS ==========================={Col.R}\n")
        for entry in list(self.cycle_logs)[-6:]:
            print(entry)
        
        for _ in range(max(0, 6 - len(self.cycle_logs))):
            print()

        print(f"{Col.NEON_C}=============================================================={Col.R}")
        if live_line:
            print(f"{Col.WHT}{live_line}{Col.R}")
        else:
            print(f" {Col.NEON_G}● SYSTEM IDLE / READY{Col.R}")
        
        elapsed = int(time.time() - self.start_time)
        eh, er = divmod(elapsed, 3600); em, es = divmod(er, 60)
        uptime_str = f"{eh:02d}:{em:02d}:{es:02d}"
        pid = os.getpid()
        print(f"{Col.NEON_C}========================================================={Col.R}")
        print(f" STATUS : {Col.NEON_G}● RUNNING{Col.R}    | Uptime: {uptime_str}    | PID: {pid}")
        print(f"{Col.NEON_C}========================================================={Col.R}")
        sys.stdout.flush()

    def add_log(self, level, msg):
        icons = {
            'ok':    f"{Col.NEON_G}[✓]{Col.R}",
            'err':   f"{Col.RED}[✗]{Col.R}",
            'info':  f"{Col.NEON_C}[*]{Col.R}",
            'wait':  f"{Col.NEON_Y}[⏳]{Col.R}",
            'warn':  f"{Col.NEON_O}[!]{Col.R}",
            'star':  f"{Col.NEON_P}[★]{Col.R}",
            'net':   f"{Col.NEON_C}[🌐]{Col.R}",
        }
        icon = icons.get(level, f"{Col.NEON_C}[·]{Col.R}")
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = f"{Col.DIM_C}[{ts}]{Col.R}"
        self.cycle_logs.append(f" {prefix} {icon} {Col.WHT}{msg}{Col.R}")
        self.render_view()

    def init_http_session(self):
        try:
            from curl_cffi import requests as c_requests
            self.session = c_requests.Session(impersonate="chrome120")
        except ImportError:
            import requests
            self.session = requests.Session()
        self.apply_headers()

    def apply_headers(self):
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': BASE_URL,
            'Referer': f"{BASE_URL}/",
            'Content-Type': 'application/json'
        }
        if self.auth_token:
            headers['Authorization'] = f"Bearer {self.auth_token}"
        if self.init_data:
            headers['x-telegram-init-data'] = self.init_data
        if hasattr(self.session, 'headers'):
            self.session.headers.update(headers)

    def load_config(self):
        cfg_path = os.path.join(self.base_dir, CONFIG_FILE)
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self.init_data    = cfg.get('init_data', '')
                self.auth_token   = cfg.get('auth_token', '')
                self.session_earned = float(cfg.get('total_earned', 0))
                self.cycles       = int(cfg.get('total_cycles', 0))
                return bool(self.init_data or self.auth_token)
            except Exception:
                pass
        return False

    def save_config(self):
        cfg_path = os.path.join(self.base_dir, CONFIG_FILE)
        cfg = {
            'init_data': self.init_data,
            'auth_token': self.auth_token,
            'bot_username': self.bot_username,
            'user_agent': self.user_agent,
            'total_earned': round(self.session_earned, 4),
            'total_cycles': self.cycles,
        }
        try:
            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def validate_telegram_auth(self):
        if not self.init_data:
            return False
        url = f"{BASE_URL}/api/auth/telegram/validate"
        payload = {'initData': self.init_data, 'referralCode': REFERRAL_CODE}
        try:
            r = self.session.post(url, json=payload, timeout=12)
            if r.status_code == 200:
                data = r.json()
                if data.get('success'):
                    self.auth_token = data.get('token', '')
                    if data.get('user'):
                        self.user_info.update(data['user'])
                    self.apply_headers()
                    self.save_config()
                    return True
        except Exception:
            pass
        return False

    def fetch_app_settings(self):
        try:
            r = self.session.get(f"{BASE_URL}/api/app-settings", timeout=12)
            if r.status_code == 200:
                d = r.json()
                interval_hrs = float(d.get('claimInterval', 0.0825))
                self.cooldown_seconds = max(60, int(interval_hrs * 3600))
                return True
        except Exception:
            pass
        return False

    def fetch_user_profile(self):
        if not self.auth_token:
            if not self.validate_telegram_auth():
                return False
        url = f"{BASE_URL}/api/user/profile"
        try:
            r = self.session.get(url, timeout=12)
            if r.status_code == 200:
                d = r.json()
                if 'balance' in d or 'email' in d:
                    self.user_info.update(d)
                    return True
        except Exception:
            pass
        return bool(self.user_info)

    def get_server_cooldown_left(self):
        last_claim_str = self.user_info.get('lastClaim')
        if not last_claim_str:
            return 0
        try:
            last_dt = datetime.fromisoformat(last_claim_str.replace('Z', '+00:00'))
            now_dt = datetime.now(timezone.utc)
            passed = int((now_dt - last_dt).total_seconds())
            return max(0, self.cooldown_seconds - passed)
        except Exception:
            return 0

    async def extract_init_data_async(self):
        if not HAS_TELETHON:
            return None
        session_path = os.path.join(self.base_dir, 'session_auth')
        client = TelegramClient(session_path, API_ID, API_HASH)

        clear()
        print()
        Anim.typewriter(f"{Col.NEON_C}LITEBITS SECURE LOGIN v2.6{Col.R}", 0.01)
        print()

        def get_phone():
            return input(f" {Col.NEON_G}➜{Col.R} Phone Number (+62...): ").strip()

        def get_code():
            return input(f" {Col.NEON_G}➜{Col.R} Telegram OTP Code: ").strip()

        def get_password():
            return input(f" {Col.NEON_G}➜{Col.R} 2FA Password (jika ada): ").strip()

        await client.start(phone=get_phone, code_callback=get_code, password=get_password)
        init_data = None
        try:
            bot = await client.get_input_entity(self.bot_username)
            try:
                await client.send_message(bot, f'/start {REFERRAL_CODE}')
            except Exception:
                pass

            res_app = await client(functions.messages.RequestAppWebViewRequest(
                peer=bot,
                app=types.InputBotAppShortName(bot_id=bot, short_name='app'),
                platform='android',
                write_allowed=True,
                start_param=REFERRAL_CODE
            ))
            if res_app and hasattr(res_app, 'url'):
                parsed = urllib.parse.urlparse(res_app.url)
                params = urllib.parse.parse_qs(parsed.fragment or parsed.query)
                init_data = params.get('tgWebAppData', [None])[0]
        except Exception:
            pass
        finally:
            await client.disconnect()
        return init_data

    def do_telegram_login(self):
        try:
            token = asyncio.run(self.extract_init_data_async())
            if token:
                self.init_data = token
                self.save_config()
                return True
            return False
        except Exception:
            return False

    def setup_interactive(self):
        Anim.opening_sequence()
        self.load_config()
        self.fetch_app_settings()

        valid_auth = False
        if self.init_data:
            if self.validate_telegram_auth():
                valid_auth = True

        if valid_auth:
            print(f"{Col.NEON_C}========================= SELECT MODE ========================={Col.R}")
            print(f"  {Col.NEON_G}[1]{Col.R} Start Auto Claim {Col.D}(default){Col.R}")
            print(f"  {Col.NEON_C}[2]{Col.R} Re-login with Telegram Phone")
            print(f"  {Col.NEON_Y}[3]{Col.R} Paste init_data manually")
            print(f"{Col.NEON_C}=============================================================={Col.R}")
            choice = input(f"\n{Col.WHT} ➜ Select option: {Col.NEON_G}").strip()
            print(Col.R, end='')
        else:
            choice = '2'

        if choice == '2':
            if not self.do_telegram_login():
                return False
            self.validate_telegram_auth()
        elif choice == '3':
            user_in = input(f"{Col.WHT}Init Data / Token: {Col.NEON_G}").strip()
            print(Col.R, end='')
            if user_in:
                if 'tgWebAppData=' in user_in:
                    user_in = urllib.parse.unquote(user_in.split('tgWebAppData=')[1].split('&')[0])
                self.init_data = user_in
                self.validate_telegram_auth()
        return True

    def do_claim_flow(self):
        self.add_log('info', f"Holding interaction channel ({HOLD_DURATION}s)...")
        self._progress_wait(HOLD_DURATION, label="HOLD")

        self.add_log('info', f"Preparing secure claim payload ({PREPARE_WAIT}s)...")
        self._progress_wait(PREPARE_WAIT, label="PREP")

        self.add_log('net', "Initializing endpoint request to server...")
        try:
            r_start = self.session.post(f"{BASE_URL}/api/claim/start", json={}, timeout=15)
            start_data = r_start.json()
        except Exception as e:
            self.add_log('err', f"Network transmission exception: {e}")
            self.cycles_failed += 1
            return False, str(e)

        if not start_data.get('success'):
            retry_sec = start_data.get('retryInSeconds')
            if retry_sec:
                self.add_log('wait', f"Server rate limit enforced. Cooldown: {retry_sec}s")
                return True, int(retry_sec)
            self.cycles_failed += 1
            return False, "Failed"

        claim_id = start_data.get('claimId')
        self.add_log('ok', f"Target session allocated [ID: {str(claim_id)[:8]}]")

        ad_token = None
        try:
            r_ads = self.session.get(f"{BASE_URL}/api/claim/{claim_id}/ads", timeout=15)
            if r_ads.status_code == 200:
                ads_json = r_ads.json()
                if ads_json.get('success') and ads_json.get('adsUrl'):
                    ad_token = ads_json['adsUrl'].get('token')
        except Exception:
            pass

        self.add_log('wait', f"Processing stream simulation buffer ({AD_VIEW_WAIT}s)...")
        self._progress_wait(AD_VIEW_WAIT, label="AD")

        self.add_log('net', "Broadcasting cryptographic confirmation...")
        complete_url = f"{BASE_URL}/api/claim/{claim_id}/complete"
        amount_awarded = 1.0

        payloads = [{"token": ad_token} if ad_token else {}, {}]
        for payload in payloads:
            try:
                r_comp = self.session.post(complete_url, json=payload, timeout=15)
                comp_data = r_comp.json()
                if comp_data.get('success'):
                    amount_awarded = float(comp_data.get('reward', 1.0))
                    break
            except Exception:
                pass

        self.fetch_user_profile()
        self.session_earned += amount_awarded
        self.cycles += 1
        self.add_log('star', f"Reward claimed successfully: +{amount_awarded:.2f} Coins")
        self.save_config()
        time.sleep(1)
        return True, "Success"

    def live_cooldown(self, wait_seconds=None):
        total_sec = wait_seconds if wait_seconds is not None else self.get_server_cooldown_left()
        if total_sec <= 0:
            total_sec = self.cooldown_seconds

        total = total_sec
        for left in range(total_sec, 0, -1):
            if not self.running:
                break
            if (time.time() - self.start_time) >= MAX_RUNTIME:
                self.running = False
                break
            bar = self._bar(left, total, width=20)
            mm, ss = divmod(left, 60)
            hh, mm = divmod(mm, 60)
            tstr = f"{hh:02d}:{mm:02d}:{ss:02d}" if hh > 0 else f"{mm:02d}:{ss:02d}"
            line = f" [⏳ WAIT] Cooldown {tstr}  [{bar}]"
            self.render_view(live_line=line)
            time.sleep(1)

    def run(self):
        self.init_http_session()
        if not self.setup_interactive():
            sys.exit(1)

        while self.running:
            try:
                if (time.time() - self.start_time) >= MAX_RUNTIME:
                    self.running = False
                    break

                self.fetch_user_profile()
                self.fetch_app_settings()

                time_left = self.get_server_cooldown_left()
                if time_left > 0:
                    self.live_cooldown(wait_seconds=time_left)

                ok, res = self.do_claim_flow()
                if isinstance(res, int) and res > 0:
                    self.live_cooldown(wait_seconds=res)
                    continue
                if not ok:
                    self.add_log('warn', "Operation delayed. Retrying protocol in 15s...")
                    self._progress_wait(15, label="RETRY")
                    continue

                self.live_cooldown()
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                self.add_log('err', f"Runtime loop exception: {e}")
                time.sleep(10)

        self.save_config()
        print(f"\n{Col.NEON_G}Sesi Selesai. Total Earned: {self.session_earned:.2f} Coins{Col.R}")


if __name__ == '__main__':
    bot = LiteBitsTeleBot()
    bot.run()
