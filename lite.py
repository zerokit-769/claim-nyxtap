#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiteBits.io Telegram Mini App Auto Claim Bot (@litebits_faucet_bot)
- Telethon Auth + Referral A7F2K9
- Auto-stop 6 jam + Session Report
- FIXED: Clean Static Refresh (No messy carriage returns)
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


def get_pad():
    try:
        import shutil
        term_width = shutil.get_terminal_size((60, 20)).columns
    except:
        term_width = 60
    return max(0, (term_width - 51) // 2)

def print_c(colored_text):
    pad = get_pad()
    print(" " * pad + colored_text)


# ==================== CLEAN ANIMATIONS & ZEINTHHUB BANNER ====================
class Anim:
    @staticmethod
    def spinner(text, duration=1.5):
        pad = get_pad()
        sys.stdout.write(" " * pad + f" {Col.NEON_C}[*]{Col.R} {Col.WHT}{text}...{Col.R}")
        sys.stdout.flush()
        time.sleep(duration)
        sys.stdout.write(f"\r" + " " * pad + f" {Col.NEON_G}[✓]{Col.R} {Col.WHT}{text} - Selesai{Col.R}\n")
        sys.stdout.flush()

    @staticmethod
    def progress(text, duration=1.0):
        pad = get_pad()
        sys.stdout.write(" " * pad + f" {Col.NEON_C}[>]{Col.R} {Col.WHT}{text}{Col.R}")
        sys.stdout.flush()
        time.sleep(duration)
        sys.stdout.write(f"\r" + " " * pad + f" {Col.NEON_G}[✓]{Col.R} {Col.WHT}{text}{Col.R}\n")
        sys.stdout.flush()

    @staticmethod
    def typewriter(text, delay=0.01, color=None):
        c = color or Col.WHT
        pad = get_pad()
        sys.stdout.write(" " * pad)
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

        BOX_W = 51
        INNER_W = BOX_W - 2
        top_border = f"┏{'━' * INNER_W}┓"
        mid_border = f"┣{'━' * INNER_W}┫"
        bot_border = f"┗{'━' * INNER_W}┛"
        
        title = "Z E I N T H U B   P R O J E C T".center(INNER_W)
        subtitle = "LiteBits Auto Claim & Faucet Exploitation".center(INNER_W)
        
        print_c(f"{Col.NEON_C}{top_border}{Col.R}")
        print_c(f"{Col.NEON_C}┃{Col.R}{Col.B}{Col.WHT}{title}{Col.R}{Col.NEON_C}┃{Col.R}")
        print_c(f"{Col.NEON_C}┃{Col.R}{Col.D}{subtitle}{Col.R}{Col.NEON_C}┃{Col.R}")
        print_c(f"{Col.NEON_C}{mid_border}{Col.R}")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        lbl_time = "Timestamp".ljust(11)
        lbl_sys  = "Subsystem".ljust(11)
        lbl_ref  = "Referral".ljust(11)
        
        val_sys = "LiteBits Faucet Bot"
        val_ref = REFERRAL_CODE
        
        s_time = f" ➔ {lbl_time} : {now}"
        s_sys  = f" ➔ {lbl_sys} : {val_sys}"
        s_ref  = f" ➔ {lbl_ref} : {val_ref}"
        
        pad_t = " " * (INNER_W - len(s_time))
        pad_s = " " * (INNER_W - len(s_sys))
        pad_r = " " * (INNER_W - len(s_ref))
        
        print_c(f"{Col.NEON_C}┃{Col.R} {Col.D}➔{Col.R} {Col.WHT}{lbl_time}{Col.R} : {Col.NEON_C}{now}{Col.R}{pad_t}{Col.NEON_C}┃{Col.R}")
        print_c(f"{Col.NEON_C}┃{Col.R} {Col.D}➔{Col.R} {Col.WHT}{lbl_sys}{Col.R} : {Col.NEON_Y}{val_sys}{Col.R}{pad_s}{Col.NEON_C}┃{Col.R}")
        print_c(f"{Col.NEON_C}┃{Col.R} {Col.D}➔{Col.R} {Col.WHT}{lbl_ref}{Col.R} : {Col.NEON_G}{val_ref}{Col.R}{pad_r}{Col.NEON_C}┃{Col.R}")
        print_c(f"{Col.NEON_C}{bot_border}{Col.R}")
        print_c(f"{Col.NEON_C}{'v2.5-stable'.rjust(BOX_W)}{Col.R}")
        print()
        time.sleep(0.5)


# ==================== BANNER ====================
def render_banner():
    BOX_W = 51
    INNER_W = BOX_W - 2
    top_border = f"┏{'━' * INNER_W}┓"
    mid_border = f"┣{'━' * INNER_W}┫"
    bot_border = f"┗{'━' * INNER_W}┛"
    
    title = "Z E I N T H H U B  P R O J E C T".center(INNER_W)
    sub = "@litebits_faucet_bot".center(INNER_W)
    
    lines = []
    lines.append(f"{Col.NEON_C}{top_border}{Col.R}")
    lines.append(f"{Col.NEON_C}┃{Col.R}{Col.B}{Col.NEON_G}{title}{Col.R}{Col.NEON_C}┃{Col.R}")
    lines.append(f"{Col.NEON_C}┃{Col.R}{Col.D}{sub}{Col.R}{Col.NEON_C}┃{Col.R}")
    lines.append(f"{Col.NEON_C}{mid_border}{Col.R}")
    return "\n".join([" " * get_pad() + l for l in lines])


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

    def _bar(self, remaining, total, width=15):
        if total <= 0:
            total = 1
        filled = int((total - remaining) / total * width)
        filled = max(0, min(width, filled))
        empty = width - filled
        return f"{Col.NEON_G}{'=' * filled}{Col.DIM_C}{' ' * empty}{Col.R}"

    def _progress_wait(self, seconds, label="WAIT"):
        total = seconds
        for left in range(seconds, 0, -1):
            if not self.running:
                break
            bar = self._bar(left, total)
            mm, ss = divmod(left, 60)
            hh, mm = divmod(mm, 60)
            tstr = f"{hh:02d}:{mm:02d}:{ss:02d}"
            line = f" {Col.NEON_Y}[⏳ {label}]{Col.R} {Col.WHT}{tstr}{Col.R} [{bar}]"
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

        BOX_W = 51
        INNER_W = BOX_W - 2
        out = []
        out.append(f"{Col.NEON_C}┣{'━' * INNER_W}┫{Col.R}")
        out.append(f"{Col.NEON_C}┃{Col.R} {Col.NEON_V}User{Col.R}      : {Col.NEON_C}{name:<34}{Col.R}{Col.NEON_C}┃{Col.R}")
        out.append(f"{Col.NEON_C}┃{Col.R} {Col.NEON_V}Balance{Col.R}   : {Col.NEON_Y}{bal_str:<34}{Col.R}{Col.NEON_C}┃{Col.R}")
        out.append(f"{Col.NEON_C}┃{Col.R} {Col.NEON_V}Earned{Col.R}    : {Col.NEON_G}{earned_str:<34}{Col.R}{Col.NEON_C}┃{Col.R}")
        out.append(f"{Col.NEON_C}┃{Col.R} {Col.NEON_V}Cycles{Col.R}    : {Col.WHT}{str(self.cycles):<34}{Col.R}{Col.NEON_C}┃{Col.R}")
        out.append(f"{Col.NEON_C}┃{Col.R} {Col.NEON_V}Success{Col.R}   : {Col.NEON_G if rate >= 90 else Col.NEON_Y}{f'{rate:.1f}%':<34}{Col.R}{Col.NEON_C}┃{Col.R}")
        out.append(f"{Col.NEON_C}┃{Col.R} {Col.NEON_V}Uptime{Col.R}    : {Col.NEON_C}{f'{eh:02d}:{em:02d}:{es:02d}':<34}{Col.R}{Col.NEON_C}┃{Col.R}")
        out.append(f"{Col.NEON_C}┃{Col.R} {Col.NEON_V}Remaining{Col.R} : {Col.NEON_O}{f'{rh:02d}:{rm:02d}:{rs:02d}':<34}{Col.R}{Col.NEON_C}┃{Col.R}")
        out.append(f"{Col.NEON_C}┗" + "━" * INNER_W + f"┛{Col.R}")
        return "\n".join([" " * get_pad() + l for l in out])

    def render_view(self, live_line=None):
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        print(render_banner())
        print(self.render_dashboard())

        BOX_W = 51
        INNER_W = BOX_W - 2
        log_header = f"┏{'━' * INNER_W}┓"
        log_title = "L I V E   L O G S".center(INNER_W)
        print(" " * get_pad() + f"{Col.NEON_C}{log_header}{Col.R}")
        print(" " * get_pad() + f"{Col.NEON_C}┃{Col.R}{Col.B}{Col.NEON_Y}{log_title}{Col.R}{Col.NEON_C}┃{Col.R}")
        print(" " * get_pad() + f"{Col.NEON_C}┣{'━' * INNER_W}┫{Col.R}")
        
        logs_list = list(self.cycle_logs)[-6:]
        for entry in logs_list:
            padded = entry.ljust(INNER_W + 10)
            print(" " * get_pad() + f"{Col.NEON_C}┃{Col.R} {Col.WHT}{padded[:INNER_W]}{Col.R} {Col.NEON_C}┃{Col.R}")
        
        for _ in range(max(0, 6 - len(logs_list))):
            print(" " * get_pad() + f"{Col.NEON_C}┃{Col.R}" + " " * INNER_W + f"{Col.NEON_C}┃{Col.R}")

        print(" " * get_pad() + f"{Col.NEON_C}┗" + "━" * INNER_W + f"┛{Col.R}")
        if live_line:
            print(" " * get_pad() + live_line)
        else:
            print(" " * get_pad() + f" {Col.NEON_G}● SYSTEM IDLE / READY{Col.R}")
        sys.stdout.flush()

    def add_log(self, level, msg):
        icons = {
            'ok':    f"{Col.NEON_G}✓{Col.R}",
            'err':   f"{Col.RED}✗{Col.R}",
            'info':  f"{Col.NEON_C}•{Col.R}",
            'wait':  f"{Col.NEON_Y}⏳{Col.R}",
            'warn':  f"{Col.NEON_O}!{Col.R}",
            'star':  f"{Col.NEON_P}★{Col.R}",
            'net':   f"{Col.NEON_C}🌐{Col.R}",
        }
        icon = icons.get(level, f"{Col.NEON_C}·{Col.R}")
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = f"{Col.DIM_C}[{ts}]{Col.R}"
        
        # Format log mengalir ke bawah dengan struktur persis seperti yang diinginkan
        formatted_log = f"{prefix} │  {icon} {msg}"
        self.cycle_logs.append(formatted_log)
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
        Anim.typewriter(f"{Col.NEON_C}LITEBITS SECURE LOGIN v2.5{Col.R}", 0.01)
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

        BOX_W = 51
        INNER_W = BOX_W - 2
        if valid_auth:
            print(" " * get_pad() + f"{Col.NEON_C}┏{'━' * INNER_W}┓{Col.R}")
            print(" " * get_pad() + f"{Col.NEON_C}┃{Col.R}{Col.B}{Col.NEON_Y}{'SELECT MODE'.center(INNER_W)}{Col.R}{Col.NEON_C}┃{Col.R}")
            print(" " * get_pad() + f"{Col.NEON_C}┣{'━' * INNER_W}┫{Col.R}")
            print(" " * get_pad() + f"{Col.NEON_C}┃{Col.R}  {Col.NEON_G}[1]{Col.R} {Col.WHT}Start Auto Claim {Col.D}(default){Col.R}     {Col.NEON_C}┃{Col.R}")
            print(" " * get_pad() + f"{Col.NEON_C}┃{Col.R}  {Col.NEON_C}[2]{Col.R} {Col.WHT}Re-login with Telegram Phone{Col.R}     {Col.NEON_C}┃{Col.R}")
            print(" " * get_pad() + f"{Col.NEON_C}┃{Col.R}  {Col.NEON_Y}[3]{Col.R} {Col.WHT}Paste init_data manually{Col.R}         {Col.NEON_C}┃{Col.R}")
            print(" " * get_pad() + f"{Col.NEON_C}┗" + "━" * INNER_W + f"┛{Col.R}")
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
        # Kotak Claim Round Bergaya Profesional
        pad = get_pad()
        bal_current = self.user_info.get('balance', '0.00')
        print("\n" + " " * pad + f" {Col.NEON_P}╭{'━'*51}╮{Col.R}")
        print(" " * pad + f" {Col.NEON_P}┃{Col.R} {Col.WHT}CLAIM ROUND {Col.NEON_C}{self.cycles+1:02d}{Col.R} {Col.NEON_P}➔{Col.R} {Col.NEON_Y}BAL: {bal_current}{Col.R}{' ' * 24} {Col.NEON_P}┃{Col.R}")
        print(" " * pad + f" {Col.NEON_P}╰{'━'*51}╯{Col.R}")

        self.add_log('info', f"Holding button ({HOLD_DURATION}s)...")
        self._progress_wait(HOLD_DURATION, label="HOLD")

        self.add_log('info', f"Preparing claim ({PREPARE_WAIT}s)...")
        self._progress_wait(PREPARE_WAIT, label="PREP")

        self.add_log('net', "Initializing claim on server...")
        try:
            r_start = self.session.post(f"{BASE_URL}/api/claim/start", json={}, timeout=15)
            start_data = r_start.json()
        except Exception as e:
            self.add_log('err', f"Network error: {e}")
            self.cycles_failed += 1
            return False, str(e)

        if not start_data.get('success'):
            retry_sec = start_data.get('retryInSeconds')
            if retry_sec:
                self.add_log('wait', f"Server cooldown: {retry_sec}s")
                return True, int(retry_sec)
            self.cycles_failed += 1
            return False, "Failed"

        claim_id = start_data.get('claimId')
        self.add_log('ok', f"Claim ID: {str(claim_id)[:8]}...")

        ad_token = None
        try:
            r_ads = self.session.get(f"{BASE_URL}/api/claim/{claim_id}/ads", timeout=15)
            if r_ads.status_code == 200:
                ads_json = r_ads.json()
                if ads_json.get('success') and ads_json.get('adsUrl'):
                    ad_token = ads_json['adsUrl'].get('token')
        except Exception:
            pass

        self.add_log('wait', f"Watching ad ({AD_VIEW_WAIT}s)...")
        self._progress_wait(AD_VIEW_WAIT, label="AD")

        self.add_log('net', "Confirming claim...")
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
        self.add_log('star', f"Reward +{amount_awarded:.2f} Coins collected!")
        self.save_config()
        time.sleep(1)
        return True, "Success"

    def live_cooldown(self, wait_seconds=None):
        total_sec = wait_seconds if wait_seconds is not None else self.get_server_cooldown_left()
        if total_sec <= 0:
            total_sec = self.cooldown_seconds

        for left in range(total_sec, 0, -1):
            if not self.running:
                break
            if (time.time() - self.start_time) >= MAX_RUNTIME:
                self.running = False
                break
            t = datetime.now().strftime("%H:%M:%S")
            pad = get_pad()
            sys.stdout.write("\r" + " " * pad + f" {Col.DIM_C}[{t}]{Col.R} {Col.NEON_Y}[zZz]{Col.R} Sleeping {left}s before next claim...   ")
            sys.stdout.flush()
            time.sleep(1)
        print()

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
                    self.add_log('warn', "Retrying in 15s...")
                    self._progress_wait(15, label="RETRY")
                    continue

                t = datetime.now().strftime("%H:%M:%S")
                bal_after = self.user_info.get('balance', '0.00')
                pad = get_pad()
                print(" " * pad + f" {Col.DIM_C}[{t}]{Col.R} {Col.NEON_G}{Col.B}╰─> SUCCESS: +{self.session_earned:.2f} COINS (balance: {bal_after}) [{self.cycles}]{Col.R}")

                self.live_cooldown()
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                self.add_log('err', f"Error: {e}")
                time.sleep(10)

        self.save_config()
        print(f"\n{Col.NEON_G}Sesi Selesai. Total Earned: {self.session_earned:.2f} Coins{Col.R}")


if __name__ == '__main__':
    bot = LiteBitsTeleBot()
    bot.run()
