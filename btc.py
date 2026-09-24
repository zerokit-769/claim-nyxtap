#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import random
import hashlib
import re
import urllib.parse
import requests
from datetime import datetime, timezone

# ========== WARNA ==========
class Col:
    R    = '\033[0m'
    WHT  = '\033[97m'
    YEL  = '\033[93m'
    RED  = '\033[91m'
    GRN  = '\033[92m'
    BLU  = '\033[94m'
    CYA  = '\033[96m'
    MAG  = '\033[95m'
    DIM  = '\033[2m'
    B    = '\033[1m'
    NEON_G  = '\033[38;5;46m'
    NEON_C  = '\033[38;5;51m'
    NEON_P  = '\033[38;5;201m'
    NEON_Y  = '\033[38;5;226m'
    NEON_O  = '\033[38;5;208m'
    NEON_R  = '\033[38;5;196m'
    DIM_C   = '\033[38;5;240m'
    GOLD    = '\033[38;5;220m'

RESET = Col.R
MERAH = Col.RED
HIJAU = Col.GRN
KUNING = Col.YEL
BIRU = Col.BLU
CYAN = Col.CYA
PUTIH = Col.WHT

# ========== KONFIGURASI ==========
BASE_URL = "https://btc.tonrevenue.space"
GIGA_URL = "https://ad.gigapub.tech/v1/ad"
GIGA_PROJ = "5736"
GIGA_TOKEN = "CEEUHXgZVL184wyaDp6laEchjHQ7RNN3"
CONFIG_FILE = "btcton_config.json"

DEFAULT_UA = "Mozilla/5.0 (Linux; Android 16; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.7977.87 Mobile Safari/537.36 Telegram-Android/12.9.2 (Samsung SM-A556E; Android 16; SDK 36; HIGH)"

init_data = ""
SESSION_FINGERPRINT = ""

# ========== ANIMATIONS (REMASTERED) ==========
class Anim:
    @staticmethod
    def spinner(text, duration=2):
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        end = time.time() + duration
        i = 0
        while time.time() < end:
            sys.stdout.write(f"\r {Col.NEON_C}[{frames[i % len(frames)]}]{Col.R} {Col.DIM_C}{text}...{Col.R}\033[K")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write(f"\r {Col.NEON_G}[✓]{Col.R} {Col.WHT}{text}{Col.R}\033[K\n")

    @staticmethod
    def progress(text, duration=2, width=25):
        end = time.time() + duration
        total = duration
        while time.time() < end:
            elapsed = duration - (end - time.time())
            pct = min(1.0, elapsed / total)
            filled = int(pct * width)
            empty = width - filled
            bar = f"{Col.NEON_C}{'█' * filled}{Col.DIM_C}{'░' * empty}{Col.R}"
            sys.stdout.write(f"\r {Col.NEON_C}[>]{Col.R} {Col.WHT}{text:<20}{Col.R} [{bar}] {Col.NEON_C}{int(pct * 100):>3}%{Col.R}\033[K")
            sys.stdout.flush()
            time.sleep(0.05)
        sys.stdout.write(f"\r {Col.NEON_G}[✓]{Col.R} {Col.WHT}{text:<20}{Col.R} [{Col.NEON_G}{'█' * width}{Col.R}] {Col.NEON_G}100%{Col.R}\033[K\n")

    @staticmethod
    def scan(text, duration=2):
        frames = ['|', '/', '-', '\\']
        end = time.time() + duration
        i = 0
        while time.time() < end:
            sys.stdout.write(f"\r {Col.NEON_Y}[{frames[i % len(frames)]}]{Col.R} {Col.WHT}Simulating {text}...{Col.R}\033[K")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write(f"\r {Col.NEON_G}[✓]{Col.R} {Col.WHT}Simulation {text} complete.{Col.R}\033[K\n")

    @staticmethod
    def banner_animation():
        steps = [
            "Mounting virtual environment...",
            "Injecting stealth headers...",
            "Establishing secure handshake...",
            "Bypassing provider protections..."
        ]
        print()
        for s in steps:
            sys.stdout.write(f"  {Col.DIM_C}[~] {s}{Col.R}\r")
            sys.stdout.flush()
            time.sleep(random.uniform(0.1, 0.3))
            sys.stdout.write(f"  {Col.NEON_G}[✓] {Col.WHT}{s}{Col.R}\n")
        print(f"  {Col.NEON_C}[*] Status : {Col.NEON_G}ONLINE & SECURED{Col.R}\n")
        time.sleep(0.4)

# ========== BANNER ==========
BANNER = f"""
{Col.NEON_C}╔════════════════════════════════════════════════════════╗
║                                                        ║
║        {Col.B}{Col.NEON_G}Z E I N T H H U B   P R O J E C T   V 1{Col.R}{Col.NEON_C}         ║
║           {Col.DIM_C}TonRevenue Ads Farm - Bypass Mode{Col.R}{Col.NEON_C}            ║
║                                                        ║
╚════════════════════════════════════════════════════════╝{Col.R}
"""


# ========== UTILITY ==========
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def timer(seconds, prefix="[⏳] Waiting"):
    if seconds < 1:
        return
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while seconds > 0:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        spinner = frames[i % len(frames)]
        sys.stdout.write(f"\r {Col.NEON_Y}{prefix} {Col.NEON_C}{time_str} {Col.DIM_C}{spinner}\033[K{Col.R}")
        sys.stdout.flush()
        time.sleep(1)
        seconds -= 1
        i += 1
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()

def fmt(n):
    if n is None:
        return "0"
    try:
        return f"{float(n):.8f}".rstrip('0').rstrip('.')
    except:
        return str(n)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"initData": ""}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def parse_init_data(raw):
    try:
        if raw.startswith('user=') or '&hash=' in raw:
            parsed = dict(urllib.parse.parse_qsl(raw))
        else:
            parsed = dict(urllib.parse.parse_qsl(urllib.parse.unquote(raw)))

        user_str = parsed.get('user', '{}')
        try:
            user = json.loads(urllib.parse.unquote(user_str))
        except:
            user = json.loads(user_str) if user_str.startswith('{') else {}

        auth_date = parsed.get('auth_date')
        auth_ts = int(auth_date) if auth_date else 0

        return {
            'raw': raw,
            'user': user,
            'language_code': user.get('language_code', 'id'),
            'auth_date': auth_ts,
            'hash': parsed.get('hash', '')
        }
    except Exception as e:
        return {'raw': raw, 'user': {}, 'language_code': 'id', 'auth_date': 0, 'hash': '', 'error': str(e)}

def validate_init_data(parsed):
    if not parsed.get('auth_date'):
        return True, "no auth_date"
    age = time.time() - parsed['auth_date']
    if age > 86400:
        return False, f"expired ({int(age/3600)}h lalu)"
    if age < 0:
        return False, "clock skew"
    return True, f"valid ({int(age/60)}m ago)"

def gen_fingerprint(seed=None):
    if seed is None:
        seed = f"{time.time()}{random.random()}{random.randint(0, 999999)}"
    return hashlib.md5(seed.encode()).hexdigest()

def get_init_data():
    global init_data
    config = load_config()
    if config.get('initData'):
        return config['initData']
    print(f" {Col.NEON_C}[➜]{Col.R} {Col.WHT}Masukkan initData: {Col.NEON_G}", end="")
    init_data = input().strip()
    print(Col.R, end="")
    if init_data:
        config['initData'] = init_data
        save_config(config)
        print(f" {Col.NEON_G}[✓]{Col.R} {Col.WHT}Data tersimpan di {Col.DIM_C}{CONFIG_FILE}{Col.R}")
        return init_data
    return None

def refresh_initdata():
    global init_data
    print(f" {Col.NEON_C}[➜]{Col.R} {Col.WHT}Input initData baru: {Col.NEON_G}", end="")
    new = input().strip()
    print(Col.R, end="")
    if not new:
        return False
    config = load_config()
    config['initData'] = new
    save_config(config)
    init_data = new
    parsed = parse_init_data(new)
    ok, msg = validate_init_data(parsed)
    if ok:
        print(f" {Col.NEON_G}[✓]{Col.R} {Col.WHT}InitData Update ({msg}){Col.R}")
    else:
        print(f" {Col.NEON_Y}[!]{Col.R} {Col.WHT}Peringatan: {msg}{Col.R}")
    return True

def tg_headers(init_user_agent=None, extra=None):
    ua = init_user_agent or DEFAULT_UA
    headers = {
        'user-agent': ua,
        'content-type': 'application/json',
        'x-requested-with': 'org.telegram.messenger.web',
        'origin': BASE_URL,
        'referer': BASE_URL + '/',
        'sec-ch-ua': '"Chromium";v="152", "Not?A_Brand";v="24", "Android WebView";v="152"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept': '*/*',
        'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    if extra:
        headers.update(extra)
    return headers

def build_init_payload():
    parsed = parse_init_data(init_data)
    lang = parsed.get('language_code', 'id')
    return {
        "initData": init_data,
        "start_param": None,
        "fingerprint": SESSION_FINGERPRINT,
        "ua": DEFAULT_UA,
        "screen": "384x832",
        "lang": f"{lang}-{lang.upper()}" if lang else "id-ID",
        "tz": "Asia/Jakarta",
        "platform": "Linux aarch64",
        "tg_platform": "android",
        "viewport_width": 384,
        "viewport_height": 696,
        "max_touch_points": 5,
        "device_pixel_ratio": 2.8125
    }

def http_json(url, payload, headers, timeout=20):
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        try:
            data = resp.json()
            if isinstance(data, dict):
                data['_status_code'] = resp.status_code
            return data
        except:
            return {"error": "non_json", "_status_code": resp.status_code, "_text": resp.text[:200]}
    except requests.exceptions.Timeout:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": "connection_failed", "_detail": str(e)}

def is_init_error(j):
    msg = str(j.get('detail', '')) + ' ' + str(j.get('message', '')) + ' ' + str(j.get('error', ''))
    return ('InitData' in msg
            or 'initdata' in msg.lower()
            or 'session expired' in msg.lower()
            or 'invalid' in msg.lower()
            or 'auth' in msg.lower())

def api(path, extra=None):
    global init_data
    for attempt in range(2):
        payload = {"initData": init_data}
        if extra:
            payload.update(extra)
        r = http_json(BASE_URL + path, payload, tg_headers())
        if attempt == 0 and is_init_error(r):
            if refresh_initdata():
                continue
        return r
    return r

def giga_call(body):
    headers = tg_headers(extra={
        'authorization': f'Bearer {GIGA_TOKEN}',
        'project-id': GIGA_PROJ
    })
    return http_json(GIGA_URL, body, headers)

def giga_user():
    parsed = parse_init_data(init_data)
    return {'user': parsed.get('user', {}), 'platform': 'android', 'version': '9.6', 'start_param': None}

def get_state():
    r = api("/api/tasks/ads/state")
    return r.get('tasks', [])

def get_init():
    global init_data
    for attempt in range(2):
        payload = build_init_payload()
        r = http_json(BASE_URL + "/api/init", payload, tg_headers())
        if isinstance(r, dict):
            if 'user' not in r or not isinstance(r.get('user'), dict):
                r['user'] = {}
            if 'balance' in r and 'balance' not in r['user']:
                r['user']['balance'] = r['balance']
        if attempt == 0 and is_init_error(r):
            if refresh_initdata():
                continue
        return r
    return r

def captcha_answer(ch):
    prompt = re.sub(r'[^a-zA-Z ]', '', ch.get('prompt', '')).strip().lower()
    want = None
    m = re.search(r'the (\w+)', prompt)
    if m:
        want = m.group(1)
    else:
        want = re.sub(r'tap ', '', prompt).strip()
    for opt in ch.get('options', []):
        if opt.get('id', '').lower() == want or opt.get('label', '').lower() == want:
            return opt['id']
    return ''

def ensure_captcha():
    for _ in range(3):
        j = get_init()
        ch = j.get('user', {}).get('captcha_challenge')
        if not ch:
            return True
        ans = captcha_answer(ch)
        if not ans:
            return False
        Anim.spinner(f"Solving Captcha", 1.5)
        r = api("/api/captcha/verify", {"challenge_id": ch['challenge_id'], "answer": ans})
        if r.get('status') == 'success':
            return True
        time.sleep(2)
    return False

def do_farm():
    notified_limit = {}
    max_cycles = 100
    cycle = 0
    while cycle < max_cycles:
        cycle += 1
        tasks = get_state()
        if not tasks:
            ensure_captcha()
            tasks = get_state()
            if not tasks:
                timer(60, "[⏳] Retrying in")
                continue

        busy = 0
        tried_any = False
        claimed = False
        
        target_tasks = [t for t in tasks if t.get('provider', '') in ['adexium', 'gigapubs']]
        if target_tasks and all(int(t.get('remaining_today', 0)) <= 0 for t in target_tasks):
            print(f"\n {Col.NEON_R}[!] Seluruh provider telah mencapai limit harian.{Col.R}")
            break

        for t in tasks:
            prov = t.get('provider', '')
            if prov not in ['adexium', 'gigapubs']:
                continue
            rem = int(t.get('remaining_today', 0))
            cdl = int(t.get('cooldown_left', 0))
            cds = int(t.get('cooldown_seconds', 300))
            if rem <= 0:
                if prov not in notified_limit:
                    print(f" {Col.NEON_Y}[!] Provider [{prov}] kehabisan kuota hari ini.{Col.R}")
                    notified_limit[prov] = True
                continue
            if cdl > 0:
                busy = max(busy, cdl)
                continue

            tried_any = True
            Anim.progress(f"Running {prov.capitalize()}", 1.5)
            st = api("/api/tasks/ads/start", {"provider": prov, "interaction": None})
            sid = st.get('session_uid', '')
            if not sid:
                continue

            if prov == 'gigapubs':
                Anim.scan("gigapubs_payload", 2)
                tg = giga_user()
                giga_call({'method': 'init', 'args': {'user': tg}, 'version': 'v85', 'seconds': 9.9})
                uniq = f"{random.randint(100000000, 999999999)}.{random.randint(100000, 999999)}"
                any_data = {
                    'showDone': True,
                    'fallPriorityList': ['rich','rD','t','d','monetag','m1','o1','rB'],
                    'fallRotationType': 'priority',
                    'showCounter': 0,
                    'showTryCounter': 0,
                    'uniqShowId': uniq,
                    'readyNetsCount': 4,
                    'showTag': None
                }
                base = {'user': tg, 'placementId': 'main', 'transactionId': None, 'version': 'v85'}
                giga_call({'method': 'adShowTryStart', 'args': {**base, 'network': 't', 'rotationType': 'priority', 'showCounter': 0, 'anyData': any_data}})
                time.sleep(4)
                any2 = dict(any_data); any2['showDone'] = False; any2['showTryCounter'] = 1
                giga_call({'method': 'adShowed', 'args': {**base, 'network': 't', 'rotationType': 'priority', 'showCounter': 0, 'seconds': 18.7, 'anyData': any2}})
                any3 = dict(any_data); any3['showCounter'] = 1; any3['showTryCounter'] = 2
                giga_call({'method': 'adShowTryStart', 'args': {**base, 'network': 'd', 'rotationType': 'priority', 'showCounter': 1, 'anyData': any3}})
                time.sleep(4)
                any4 = dict(any3); any4['showDone'] = True
                giga_call({'method': 'adShowedX', 'args': {**base, 'network': 'd', 'rotationType': 'priority', 'showCounter': 2, 'seconds': 32.8, 'anyData': any4}})

            Anim.progress("Confirming Reward", 1.5)
            cf = api("/api/tasks/ads/confirm", {"session_uid": sid})
            status = cf.get('status', '')
            if status in ['success', 'already_confirmed']:
                amt = cf.get('reward_sats', 0.2)
                nb = cf.get('new_balance', '?')
                used = int(cf.get('used_today', 0))
                rem2 = int(cf.get('remaining_today', rem))
                c = int(cf.get('cooldown', cds))
                
                print(f" {Col.NEON_G}[+]{Col.R} {Col.WHT}Reward    : {Col.NEON_G}{fmt(amt)}{Col.WHT} satoshi{Col.R}")
                print(f" {Col.NEON_C}[#]{Col.R} {Col.WHT}Ads Limit : {Col.NEON_C}{used}/{used+rem2}{Col.R}")
                print(f" {Col.NEON_C}[$]{Col.R} {Col.WHT}Balance   : {Col.NEON_G}{fmt(nb)}{Col.WHT} satoshi{Col.R}")
                print(f" {Col.DIM_C}────────────────────────────────────────────────────────{Col.R}")
                
                busy = max(busy, c)
                claimed = True
                timer(random.randint(8, 10), "[⏳] Cooling down")
            elif status == 'pending_postback':
                busy = max(busy, cds)

        if busy > 0:
            timer(busy, "[⏳] Next cycle in")
            continue
        if not tried_any:
            return
        if claimed:
            timer(5, "[⏳] Preparing")
            continue
        timer(20, "[⏳] Retrying in")

def main():
    global init_data, SESSION_FINGERPRINT
    SESSION_FINGERPRINT = gen_fingerprint()

    clear()
    Anim.banner_animation()
    clear()
    print(BANNER)
    print(f"  {Col.DIM_C}Session Hash : {Col.WHT}{SESSION_FINGERPRINT[:24]}...{Col.R}\n")

    init_data = get_init_data()
    if not init_data:
        sys.exit(1)

    parsed = parse_init_data(init_data)
    ok, msg = validate_init_data(parsed)
    if ok:
        print(f" {Col.NEON_G}[✓]{Col.R} {Col.WHT}Koneksi Valid ({msg}){Col.R}")
    else:
        if not refresh_initdata():
            sys.exit(1)

    print()
    Anim.progress("Establishing Session", 1.5)
    
  
    Anim.spinner("Fetching Account & Task Data", 1.5)
    print()

    while True:
        ensure_captcha()
        ib = get_init()
        tasks = get_state()
        
        
        user_name = parsed['user'].get('username', '?')
        bal_str = "Failed to fetch"
        wd_str = "Failed to fetch"
        status_str = "UNKNOWN"
        
        if ib.get('user'):
            u = ib['user']
            acc = ib.get('access', {})
            bal_str = f"{fmt(u.get('balance', 0))} satoshi"
            wd_str = f"{fmt(ib.get('withdraw_available_sats', 0))} satoshi"
            
            if acc.get('mobile_only_blocked'):
                status_str = f"{Col.RED}MOBILE ONLY BLOCKED{Col.R}"
            elif u.get('is_blocked'):
                status_str = f"{Col.RED}BLOCKED{Col.R}"
            else:
                status_str = f"{Col.NEON_G}SECURED{Col.R}"

        
        print(f" {Col.DIM_C}┌─[ {Col.NEON_C}ACCOUNT DASHBOARD{Col.DIM_C} ]─────────────────────────────────{Col.R}")
        print(f" {Col.DIM_C}│{Col.R} {Col.WHT}Account User : {Col.NEON_C}@{user_name}{Col.R}")
        print(f" {Col.DIM_C}│{Col.R} {Col.WHT}Balance      : {Col.NEON_G}{bal_str}{Col.R}")
        print(f" {Col.DIM_C}│{Col.R} {Col.WHT}Available WD : {Col.NEON_Y}{wd_str}{Col.R}")
        print(f" {Col.DIM_C}│{Col.R} {Col.WHT}Status       : {status_str}")
        print(f" {Col.DIM_C}├─[ {Col.NEON_C}TASK STATUS{Col.DIM_C} ]───────────────────────────────────────{Col.R}")
        
        if tasks:
            for t in tasks:
                prov = t.get('provider', '')
                if prov not in ['adexium', 'gigapubs']:
                    continue
                used = int(t.get('daily_cap', 0)) - int(t.get('remaining_today', 0))
                print(f" {Col.DIM_C}│{Col.R} {Col.WHT}{prov.capitalize():<12} : {Col.NEON_C}{used}/{t.get('daily_cap', '?')}{Col.DIM_C} | {Col.WHT}Reward: {Col.NEON_Y}{t.get('reward_sats', '?')}{Col.DIM_C} | {Col.WHT}CD: {Col.NEON_Y}{t.get('cooldown_left', '?')}s{Col.R}")
        else:
            print(f" {Col.DIM_C}│{Col.R} {Col.RED}Tasks fetch error / empty{Col.R}")
            
        print(f" {Col.DIM_C}└────────────────────────────────────────────────────────{Col.R}")
        print()

        
        print(f"{Col.NEON_C}┌────────────────────────────────────────────────────────┐{Col.R}")
        print(f"{Col.NEON_C}│                 {Col.B}{Col.NEON_G}TONREVENUE MAIN MENU{Col.R}{Col.NEON_C}                   │{Col.R}")
        print(f"{Col.NEON_C}├────────────────────────────────────────────────────────┤{Col.R}")
        print(f"{Col.NEON_C}│ {Col.WHT} {Col.NEON_G}[1]{Col.R} Start Farm (Adexium + GigaPubs)                   {Col.NEON_C}│{Col.R}")
        print(f"{Col.NEON_C}│ {Col.WHT} {Col.NEON_Y}[2]{Col.R} Refresh InitData                                  {Col.NEON_C}│{Col.R}")
        print(f"{Col.NEON_C}│ {Col.WHT} {Col.NEON_C}[3]{Col.R} Ganti Session Fingerprint                         {Col.NEON_C}│{Col.R}")
        print(f"{Col.NEON_C}│ {Col.WHT} {Col.RED}[0]{Col.R} Terminate Script                                  {Col.NEON_C}│{Col.R}")
        print(f"{Col.NEON_C}└────────────────────────────────────────────────────────┘{Col.R}")
        print()
        
        print(f" {Col.NEON_C}[➜]{Col.R} {Col.WHT}Pilih Eksekusi: {Col.NEON_Y}", end="")
        opt = input().strip()
        print(Col.R, end="")

        if opt == '1':
            print()
            do_farm()
            input(f"\n {Col.DIM_C}Tekan [ENTER] untuk kembali ke menu utama...{Col.R}")
            clear() 
        elif opt == '2':
            print()
            refresh_initdata()
            parsed = parse_init_data(init_data) 
            input(f"\n {Col.DIM_C}Tekan [ENTER] untuk kembali ke menu utama...{Col.R}")
            clear()
        elif opt == '3':
            SESSION_FINGERPRINT = gen_fingerprint()
            print()
            Anim.spinner("Rotating Fingerprint", 1.5)
            print(f" {Col.NEON_C}[*]{Col.R} {Col.WHT}New Hash: {Col.NEON_G}{SESSION_FINGERPRINT}{Col.R}")
            input(f"\n {Col.DIM_C}Tekan [ENTER] untuk kembali ke menu utama...{Col.R}")
            clear()
        elif opt == '0':
            print()
            Anim.spinner("Shutting Down Systems", 1)
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n {Col.RED}[!] Dihentikan paksa oleh pengguna.{Col.R}")
        sys.exit(0)
