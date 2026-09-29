import requests
import json, time, re, sys, os, random
from datetime import datetime

# ==== CONFIG ====
HOST    = "https://faucetearning.com"
SESSION = "session_fe.json"
LOG     = "faucetearning.log"

# ==== AUTO-SLEEP / AUTO-STOP ====
MAX_FAIL_BEFORE_SLEEP = 3       # gagal 3x berturut → tidur panjang
LONG_SLEEP_SECONDS    = 1800    # 30 menit tidur panjang
EXIT_AFTER_LONG_SLEEP = 0       # 0 = jangan exit (loop 24/7)
                                # 3 = exit setelah 3x tidur tanpa progress

# ==== COLORS ====
BLK="\033[0;30m"; RED="\033[1;31m"; GRN="\033[1;32m"; YEL="\033[1;33m"
BLU="\033[1;34m"; MAG="\033[1;35m"; CYN="\033[1;36m"; WHT="\033[1;37m"
GRY="\033[1;90m"; RST="\033[0m"; BOLD="\033[1m"

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

# ==== BANNER BARU ====
def banner():
    clear()
    print(f"\n{WHT}  ╔════════════════════════════════════════════╗{RST}")
    print(f"{CYN}  ║             ZEINTHHUB PROJECT              ║{RST}")
    print(f"{WHT}  ║          FaucetEarning Auto Bot            ║{RST}")
    print(f"{WHT}  ╚════════════════════════════════════════════╝{RST}\n")

# ==== NOTICE / INFO ====
def notice():
    print(f"{CYN}  [+] Status  :{RST} {WHT}SYSTEM READY{RST}")
    print(f"{CYN}  [+] Target  :{RST} {WHT}FaucetEarning{RST}")
    print(f"{CYN}  [+] Link Web :{RST} {GRN}https://faucetearning.com/?r=11745{RST} (Auto Claim)\n")
    time.sleep(0.8)

# ==== MENU ====
def menu():
    print(f"{WHT}  Pilih Mode Eksekusi:{RST}")
    print(f"{CYN}  [1]{RST} {WHT}FAUCET ONLY{RST}")
    print(f"{CYN}  [2]{RST} {WHT}PTC ONLY{RST}")
    print(f"{CYN}  [3]{RST} {GRN}SMART MODE (PTC + Faucet + Anti-Ban){RST}\n")
    
    while True:
        try:
            choice = input(f"{WHT}  Masukkan Pilihan [1/2/3] : {RST}").strip()
            if choice in ("1", "2", "3"):
                print("") # Spacing
                return int(choice)
            print(f"{RED}  ⚠ Input tidak valid.{RST}")
        except KeyboardInterrupt:
            print(f"\n{YEL}Dibatalkan.{RST}")
            sys.exit(0)

def log(msg, tag="i", end="\n"):
    ts = datetime.now().strftime("%H:%M:%S")
    if tag in ["ok", "bi"]:
        line = f"{GRY}[{ts}]{RST} {GRN}└─> SUCCESS: {msg}{RST}"
    elif tag == "er":
        line = f"{GRY}[{ts}]{RST} {WHT}│    {RED}ERROR: {WHT}{msg}{RST}"
    elif tag == "wr":
        line = f"{GRY}[{ts}]{RST} {WHT}│    {YEL}WARN: {WHT}{msg}{RST}"
    elif tag == "zz":
        line = f"{GRY}[{ts}]{RST} {WHT}│    {BLU}{msg}{RST}"
    else:
        line = f"{GRY}[{ts}]{RST} {WHT}│    {msg}{RST}"
    
    print(line, end=end)
    sys.stdout.flush()
    try:
        with open(LOG, "a") as f:
            plain = re.sub(r'\033\[[0-9;]*m', '', line)
            f.write(plain + (end if end != "\r" else "\n"))
    except Exception:
        pass


def timer(seconds, prefix="Sleeping"):
    wait = int(seconds)
    while wait > 0:
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"\r\033[K{GRY}[{ts}] {YEL}[zZz] {GRY}{prefix} {wait}s before next claim...     {RST}")
        sys.stdout.flush()
        time.sleep(1)
        wait -= 1
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()

def human_delay(base_seconds, min_extra=2, max_extra=5):
    return base_seconds + random.randint(min_extra, max_extra)

# ==== SESSION ====
def make_session():
    
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    })
    
    if os.path.exists(SESSION):
        try:
            with open(SESSION) as f:
                cookies = json.load(f)
            s.cookies.update(cookies)
        except Exception as e:
            log(f"Session load failed: {e}", "wr")
    return s

def save_session(s):
    try:
        with open(SESSION, "w") as f:
            json.dump(dict(s.cookies.get_dict()), f, indent=2)
    except Exception as e:
        log(f"Session save failed: {e}", "wr")

def delete_session():
    try:
        if os.path.exists(SESSION):
            os.remove(SESSION)
            log("Old session deleted.", "wr")
    except Exception as e:
        log(f"Failed to delete session: {e}", "er")

def check_login(s):
    try:
        r = s.get(f"{HOST}/dashboard", timeout=30, allow_redirects=True)
        is_logged = "Logout" in r.text or "auth/logout" in r.text
        if not is_logged:
            try:
                with open("debug_login.html", "w") as f:
                    f.write(r.text)
            except Exception:
                pass
            log(f"Saved debug_login.html (status={r.status_code})", "wr")
        return is_logged
    except Exception as e:
        log(f"check_login error: {e}", "er")
        return False

def parse_cookie_string(cookie_str):
    cookies = {}
    for part in cookie_str.strip().split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies[name.strip()] = value.strip()
    return cookies

def load_cookies(s, cookie_str):
    cookies = parse_cookie_string(cookie_str)
    s.cookies.clear()
    s.cookies.update(cookies)
    return cookies

def prompt_cookie():
    print(f"\n{CYN}  ╭──────────────────────────────────────────────╮{RST}")
    print(f"{CYN}  │{RST} {WHT}AUTENTIKASI COOKIE DIBUTUHKAN{RST}                {CYN}│{RST}")
    print(f"{CYN}  ├──────────────────────────────────────────────┤{RST}")
    print(f"{CYN}  │{RST} {GRY}1. Login ke faucetearning.com di browser{RST}     {CYN}│{RST}")
    print(f"{CYN}  │{RST} {GRY}2. Copy Header String dari Cookie-Editor{RST}     {CYN}│{RST}")
    print(f"{CYN}  │{RST} {GRY}3. Format: fe_sess=xxx; fe_c_xxx=yyy; ...{RST}    {CYN}│{RST}")
    print(f"{CYN}  ╰──────────────────────────────────────────────╯{RST}")
    
    # Warna input dibikin Cyan biar beda dari teks prompt
    cookie_str = input(f"\n{WHT}  [>] Paste Cookie : {CYN}").strip()
    print(f"{RST}", end="") # Reset warna setelah user menekan enter
    return cookie_str

def ensure_login(s, cfg=None):
    if check_login(s):
        return True

    log("No valid session. Need fresh cookie.", "wr")
    delete_session()

    cookie_input = prompt_cookie()
    if not cookie_input:
        log("Empty cookie. Skipping.", "er")
        return False

    cd = load_cookies(s, cookie_input)
    if not cd:
        log("Invalid cookie format.", "er")
        return False

    log(f"Loaded {len(cd)} cookies, testing login...", "i")

    if check_login(s):
        save_session(s)
        log("Cookie login SUCCESS! Saved.", "ok")
        return True

    log("Cookie invalid. Check debug_login.html", "er")
    return False

# ==== USER INFO ====
def _clean_text(t):
    if not t:
        return ""
    t = re.sub(r'&nbsp;', ' ', t)
    t = re.sub(r'&amp;', '&', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def get_crypto_balances(html):
    balances = {}
    for m in re.finditer(
        r'<option\s+value=["\'](\w+)["\'][^>]*>\s*([\d\.]+\s*\w+)\s*</option>',
        html
    ):
        code = m.group(1)
        amt  = m.group(2).strip()
        if not amt.startswith("0 ") or "." in amt:
            balances[code] = amt
    return balances

def get_user_info(s):
    info = {"username": "?", "balance": "?", "crypto": {}}
    try:
        r = s.get(f"{HOST}/dashboard", timeout=30)
        html = r.text

        m = re.search(r'Main\s+Balance\s*</p>\s*<h6[^>]*>\s*([^<\n]+?)\s*</h6>', html, re.I | re.S)
        if m:
            info["balance"] = _clean_text(m.group(1))
        else:
            m = re.search(r'Total\s+Earned\s*</p>\s*<h6[^>]*>\s*([^<\n]+?)\s*</h6>', html, re.I | re.S)
            if m:
                info["balance"] = _clean_text(m.group(1))

        if info["balance"] == "?":
            m = re.search(r'<h6[^>]*>\s*([\d,\.]+\s*Tokens?)\s*</h6>', html, re.I)
            if m:
                info["balance"] = _clean_text(m.group(1))

        info["crypto"] = get_crypto_balances(html)

        ra = s.get(f"{HOST}/account", timeout=30)
        html_a = ra.text

        for pat in [
            r'id=["\']username["\'][^>]*value=["\']([^"\']+)["\']',
            r'name=["\']username["\'][^>]*value=["\']([^"\']+)["\']',
            r'value=["\']([^"\']+)["\'][^>]*(?:id|name)=["\']username["\']',
            r'name=["\']name["\'][^>]*value=["\']([^"\']+)["\']',
            r'<span[^>]*class=["\'][^"\']*user[^"\']*["\'][^>]*>\s*([A-Za-z0-9_\.\-]{3,30})',
            r'(?:Hi|Hello|Welcome)[^\w]{0,5}([A-Za-z0-9_\.\-]{3,30})',
            r'data-username=["\']([^"\']+)["\']',
        ]:
            m = re.search(pat, html_a, re.I)
            if m:
                v = _clean_text(m.group(1))
                if v and len(v) < 50 and " " not in v:
                    info["username"] = v
                    break
    except Exception as e:
        log(f"get_user_info error: {e}", "er")
    return info

def show_user_info(s):
    info = get_user_info(s)
    uname = info.get("username", "?")
    bal   = info.get("balance", "?")

    log(f"Account: {uname}", "i")
    log(f"Balance: {bal}", "i")
    
    cryptos = info.get("crypto", {})
    if cryptos:
        for k, v in list(cryptos.items())[:4]:
            log(f"{k:<6}: {v}", "i")
    print("")
    return info

def refresh_balance(s):
    info = get_user_info(s)
    return info.get("balance", "?")

# ==== HTML PARSERS ====
def extract_slide_token(html):
    m = re.search(r'tokenInput\.value\s*=\s*["\']([a-f0-9]{16,})["\']', html)
    if m: return m.group(1)
    m = re.search(r'name=["\']slidecaptcha_token["\'][^>]*value=["\']([^"\']+)["\']', html, re.I)
    if m and m.group(1): return m.group(1)
    m = re.search(r'slidecaptcha_token["\']?\s*[:=]\s*["\']([a-f0-9]{16,})["\']', html)
    if m: return m.group(1)
    return None

def extract_fe_field(html):
    m = re.search(r'name=["\'](fe_[a-f0-9]+)["\'][^>]*value=["\']([^"\']+)["\']', html, re.I)
    if m: return m.group(1), m.group(2)
    return None, None

def extract_timer(html, default=10):
    m = re.search(r'var\s+timer\s*=\s*(\d+)', html)
    return int(m.group(1)) if m else default

def extract_verify_url(html, ad_id=None):
    m = re.search(r'<form[^>]+action=["\']([^"\']*verify[^"\']*)["\']', html, re.I)
    if m:
        url = m.group(1)
        if url.startswith("http"): return url
        return HOST + "/" + url.lstrip("/")
    if ad_id:
        return f"{HOST}/ptc/verify/{ad_id}"
    return None

def parse_ptc_list(html):
    ads = []
    seen = set()
    for m in re.finditer(r'/ptc/window/(\d+)', html):
        ad_id = m.group(1)
        if ad_id in seen: continue
        seen.add(ad_id)
        start = m.start()
        context = html[start:start + 1200]
        t_match = re.search(r'(\d+)\s*sec', context, re.I)
        timer_val = int(t_match.group(1)) if t_match else 10
        r_match = re.search(r'(\d+)\s*Token', context, re.I)
        reward = int(r_match.group(1)) if r_match else None
        title_match = re.search(r'<h[45][^>]*>([^<]+)</h[45]>', context)
        title = title_match.group(1).strip() if title_match else f"PTC #{ad_id}"
        ads.append({"id": ad_id, "timer": timer_val, "reward": reward, "title": title})
    return ads

def parse_block_timer(html):
    m = re.search(r'let\s+ban_wait\s*=\s*(\d+)', html)
    if m: return int(m.group(1)), "block"
    m = re.search(r'var\s+wait\s*=\s*(\d+)', html)
    if m: return int(m.group(1)), "wait"
    return None, None

def is_claim_ready(html):
    return "btn-collect-reward" in html

def is_ptc_required(html):
    low = html.lower()
    return any(p in low for p in [
        "complete at least 1 ptc", "your exp is 0",
        "complete a ptc", "exp: 0",
    ])

def has_ptc_available(s):
    try:
        html = s.get(f"{HOST}/ptc", timeout=20).text
        ads = parse_ptc_list(html)
        return len(ads) > 0
    except Exception:
        return False

# ==== PTC ====
def auto_ptc(s, cfg, max_ads=5):
    log("Scanning PTC zone...", "i")
    try:
        html = s.get(f"{HOST}/ptc", timeout=30).text
    except Exception as e:
        log(f"PTC fetch failed: {e}", "er"); return False

    if "Logout" not in html and "dashboard" not in html.lower():
        log("PTC session looks dead", "er"); return False

    ads = parse_ptc_list(html)
    if not ads:
        log("No PTC available", "wr"); return False

    total = min(len(ads), max_ads)
    log(f"Found {total} PTC ads ready", "i")

    done = 0
    for idx, ad in enumerate(ads[:total]):
        ad_id  = ad["id"]
        t_base = ad["timer"]
        reward = ad["reward"]
        title  = ad["title"][:30]
        reward_str = f"+{reward} Token" if reward else "?"

        log(f"Ad #{ad_id} [{idx+1}/{total}] | {t_base}s | {reward_str}", "i")

        try:
            wr = s.get(f"{HOST}/ptc/window/{ad_id}", timeout=30, headers={"Referer": f"{HOST}/ptc"})
        except Exception as e:
            log(f"Window error: {e}", "er"); continue

        slide_token = extract_slide_token(wr.text)
        fe_name, fe_value = extract_fe_field(wr.text)
        verify_url = extract_verify_url(wr.text, ad_id)

        if not slide_token:
            log(f"No token in window {ad_id}", "er")
            continue

        actual_wait = human_delay(t_base, 2, 5)
        if actual_wait > 0:
            timer(actual_wait, "Viewing Ad")

        payload = {"captcha": "slidecaptcha", "slidecaptcha_token": slide_token}
        if fe_name and fe_value:
            payload[fe_name] = fe_value

        try:
            vr = s.post(verify_url, data=payload, timeout=30,
                        headers={
                            "Referer": f"{HOST}/ptc/window/{ad_id}",
                            "Origin": HOST,
                            "Content-Type": "application/x-www-form-urlencoded",
                        })
        except Exception as e:
            log(f"Verify error: {e}", "er"); continue

        if "Good job" in vr.text or "has been added" in vr.text:
            m = re.search(r'(\d+)\s*Tokens', vr.text)
            amt = m.group(1) if m else "?"
            log(f"PTC #{ad_id} Reward +{amt} Tokens", "ok")
            done += 1
            time.sleep(random.randint(4, 8))
        else:
            log(f"PTC #{ad_id} failed verification", "wr")
            time.sleep(random.randint(3, 6))

    return done > 0

def ptc_until_unblocked(s, cfg, ban_seconds):
    expire_at = time.time() + ban_seconds
    total_ptc = 0
    empty_rounds = 0

    log(f"PTC-ONLY MODE active (Block Duration: {ban_seconds}s)", "wr")

    while time.time() < expire_at:
        sisa = int(expire_at - time.time())
        h = sisa // 3600; m = (sisa % 3600) // 60; s_ = sisa % 60
        log(f"PTC Round #{empty_rounds+1} | Block left: {h:02d}:{m:02d}:{s_:02d}", "i")

        try:
            result = auto_ptc(s, cfg, max_ads=5)
        except Exception as e:
            log(f"PTC error: {e}", "er")
            result = False

        if result:
            total_ptc += 1
            empty_rounds = 0
            time.sleep(random.randint(35, 60))
        else:
            empty_rounds += 1
            log(f"PTC empty/failed (Round #{empty_rounds})", "wr")
            if empty_rounds >= 3:
                log("PTC empty, resting...", "wr")
                remaining = int(expire_at - time.time())
                wait_time = min(120, max(remaining, 0))
                if wait_time > 0:
                    timer(wait_time, "Cooldown")
                empty_rounds = 0
            else:
                time.sleep(random.randint(15, 25))

    log(f"Block expired! Total PTC done: {total_ptc}", "ok")
    return True

# ==== FAUCET ====
def faucet_claim(s, cfg, retry=0):
    log("Processing Faucet claim...", "i")
    try:
        r = s.get(f"{HOST}/faucet", timeout=30)
        html = r.text
    except Exception as e:
        log(f"Faucet fetch failed: {e}", "er"); return False

    wait_sec, wait_type = parse_block_timer(html)

    if wait_type == "block":
        h = wait_sec // 3600
        m = (wait_sec % 3600) // 60
        s_ = wait_sec % 60
        log(f"SOFT-BAN detected! Cooldown: {h:02d}:{m:02d}:{s_:02d}", "er")
        log("Switching to PTC-ONLY mode during block...", "wr")
        ptc_until_unblocked(s, cfg, wait_sec)
        log("Block expired, retrying faucet!", "ok")
        time.sleep(3)
        return faucet_claim(s, cfg, retry)

    if wait_type == "wait" and wait_sec > 0:
        extra = random.randint(10, 20)
        actual_wait = wait_sec + extra
        log(f"Cooldown active: {wait_sec}s + {extra}s = {actual_wait}s", "wr")
        timer(actual_wait, "Wait")
        return faucet_claim(s, cfg, retry)

    if is_ptc_required(html):
        log("Requirement: Need to complete PTC first", "wr")
        if auto_ptc(s, cfg):
            time.sleep(random.randint(5, 8))
            return faucet_claim(s, cfg, retry)
        log("PTC failed, faucet claim cancelled", "er")
        return False

    if not is_claim_ready(html):
        log("Claim form not ready. Trying PTC instead...", "wr")
        if auto_ptc(s, cfg):
            time.sleep(random.randint(5, 8))
            return faucet_claim(s, cfg, retry)
        return False

    slide_token = extract_slide_token(html)
    fe_name, fe_value = extract_fe_field(html)
    verify_url = extract_verify_url(html) or f"{HOST}/faucet/verify"

    if not slide_token:
        log("Slide token missing on faucet page", "er")
        return False

    unlock_wait = human_delay(6, 2, 4)
    timer(unlock_wait, "Unlock Delay")
    log("Sending claim payload...", "i")

    payload = {
        "fe_a5e43568": fe_value or "",
        "captcha": "slidecaptcha",
        "slidecaptcha_token": slide_token,
        "user_nickname": "",
    }

    try:
        vr = s.post(verify_url, data=payload, timeout=30,
                    headers={
                        "Referer": f"{HOST}/faucet",
                        "Origin": HOST,
                        "Content-Type": "application/x-www-form-urlencoded",
                    }, allow_redirects=True)
    except Exception as e:
        log(f"POST request failed: {e}", "er"); return False

    has_303 = any(h.status_code == 303 for h in vr.history)
    m = re.search(r"Swal\.fire\s*\(\s*['\"]Good job!['\"]\s*,\s*['\"](\d+)\s*Tokens", vr.text)
    body_success = bool(m)

    if has_303 or body_success:
        amt = m.group(1) if m else "?"
        log(f"Faucet claimed! Reward +{amt} Tokens", "ok")
        return True

    vr_low = vr.text.lower()

    if "access is blocked" in vr_low or "bot behavior" in vr_low:
        blk_sec, _ = parse_block_timer(vr.text)
        if not blk_sec: blk_sec = 1800
        log(f"Blocked by server! {blk_sec}s", "er")
        ptc_until_unblocked(s, cfg, blk_sec)
        return False

    if is_ptc_required(vr.text):
        log("Needs PTC (Server Response), grinding...", "wr")
        if auto_ptc(s, cfg):
            time.sleep(random.randint(5, 8))
            return faucet_claim(s, cfg, retry)
        return False

    if "invalid" in vr_low and retry < 3:
        log(f"Invalid claim, retry ({retry+1}/3)", "wr")
        time.sleep(random.randint(5, 10))
        return faucet_claim(s, cfg, retry + 1)

    m = re.search(r'class="alert[^"]*alert-danger"[^>]*>\s*(?:<i[^>]*></i>)?\s*([^<]+)', vr.text)
    msg = m.group(1).strip()[:70] if m else f'Unknown Error (Status: {vr.status_code})'
    log(f"Server rejection: {msg}", "er")
    return False

# ==== AUTO SLEEP HELPER ====
def check_and_sleep_if_idle(s, fail_count, long_sleep_count):
    if fail_count < MAX_FAIL_BEFORE_SLEEP:
        return fail_count, long_sleep_count, False

    ptc_left = has_ptc_available(s)
    if ptc_left:
        log("Faucet error but PTC available. Continuing...", "wr")
        return 0, long_sleep_count, False

    log(f"ZONA IDLE | Failed {fail_count}x | Sleeping {LONG_SLEEP_SECONDS//60} mins", "zz")
    timer(LONG_SLEEP_SECONDS, "Idle Sleep")

    long_sleep_count += 1
    if EXIT_AFTER_LONG_SLEEP > 0 and long_sleep_count >= EXIT_AFTER_LONG_SLEEP:
        log(f"Max idle reached ({long_sleep_count}x). Exiting process.", "er")
        return 0, long_sleep_count, True

    log("Waking up, resuming tasks...", "ok")
    return 0, long_sleep_count, False

# ==== MODE 1: FAUCET ONLY ====
def mode_faucet_only(s, cfg):
    log("Mode: FAUCET ONLY active", "i")
    time.sleep(1.5)
    loop_count = 0
    fail_count = 0
    long_sleep_count = 0

    while True:
        loop_count += 1
        try:
            print(f"\n{CYN}  [ Loop #{loop_count} ]{RST}")
            if not ensure_login(s, cfg):
                log("Session invalid, waiting 60s...", "er")
                time.sleep(60); continue

            bal = refresh_balance(s)
            log(f"Current Balance: {bal}", "bi")
            
            result = faucet_claim(s, cfg)
            if result:
                fail_count = 0
                long_sleep_count = 0
                extra = random.randint(10, 20)
                timer(60 + extra, "Cooldown")
            else:
                fail_count += 1
                log(f"Claim failed (Attempt {fail_count})", "wr")
                fail_count, long_sleep_count, should_exit = check_and_sleep_if_idle(s, fail_count, long_sleep_count)
                if should_exit:
                    save_session(s)
                    return
                if fail_count > 0:
                    timer(random.randint(60, 90), "Retry Delay")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log(f"FATAL EXCEPTION: {e}", "er")
            time.sleep(30)

# ==== MODE 2: PTC ONLY ====
def mode_ptc_only(s, cfg):
    log("Mode: PTC ONLY active", "i")
    time.sleep(1.5)
    round_num = 0
    total_done = 0
    long_sleep_count = 0

    while True:
        round_num += 1
        print(f"\n{CYN}  [ PTC Round #{round_num} ]{RST}")
        if not ensure_login(s, cfg):
            log("Session invalid, waiting 60s...", "er")
            time.sleep(60); continue

        bal = refresh_balance(s)
        log(f"Current Balance: {bal}", "bi")

        try:
            result = auto_ptc(s, cfg, max_ads=10)
        except Exception as e:
            log(f"PTC runtime error: {e}", "er")
            result = False

        if result:
            total_done += 1
            long_sleep_count = 0
            log(f"PTC round completed", "ok")
            time.sleep(random.randint(20, 35))
        else:
            log("PTC queue seems dry, checking availability...", "wr")
            if not has_ptc_available(s):
                log(f"PTC empty. Initiating long sleep.", "zz")
                timer(LONG_SLEEP_SECONDS, "Idle Sleep")
                long_sleep_count += 1
                if EXIT_AFTER_LONG_SLEEP > 0 and long_sleep_count >= EXIT_AFTER_LONG_SLEEP:
                    log(f"Max idle reached. Exiting.", "er")
                    save_session(s)
                    return
            else:
                log("PTC failed to complete, retrying shortly.", "wr")
                timer(random.randint(170, 200), "Retry Delay")

# ==== MODE 3: SMART ====
def mode_smart(s, cfg):
    log("Mode: SMART (PTC + Faucet + Anti-Ban) active", "i")
    time.sleep(1.5)
    loop_count = 0
    fail_count = 0
    long_sleep_count = 0

    while True:
        loop_count += 1
        try:
            print(f"\n{CYN}  [ Smart Loop #{loop_count} ]{RST}")
            if not ensure_login(s, cfg):
                log("Session invalid, waiting 60s...", "er")
                time.sleep(60); continue

            bal = refresh_balance(s)
            log(f"Current Balance: {bal}", "bi")

            log("Step 1: Executing PTC...", "i")
            try:
                if auto_ptc(s, cfg, max_ads=5):
                    log("PTC tasks done", "ok")
                else:
                    log("PTC dry or failed, proceeding to Faucet...", "wr")
            except Exception as e:
                log(f"PTC skipped due to error: {e}", "er")

            step_delay = random.randint(5, 10)
            timer(step_delay, "Transition")

            log("Step 2: Executing Faucet...", "i")
            result = faucet_claim(s, cfg)

            if result:
                fail_count = 0
                long_sleep_count = 0
                extra = random.randint(10, 20)
                timer(60 + extra, "Cooldown")
            else:
                fail_count += 1
                log(f"Faucet failed (Attempt {fail_count})", "wr")
                fail_count, long_sleep_count, should_exit = check_and_sleep_if_idle(s, fail_count, long_sleep_count)
                if should_exit:
                    save_session(s)
                    return
                if fail_count > 0:
                    timer(random.randint(60, 90), "Retry Delay")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log(f"FATAL EXCEPTION: {e}", "er")
            time.sleep(30)

# ==== MAIN ====
def main():
    banner()
    notice()
    log("Initializing system session...", "i")
    session = make_session()

    attempts = 0
    while not ensure_login(session):
        attempts += 1
        if attempts >= 3:
            log("Failed to authenticate 3 times. Exiting process.", "er")
            sys.exit(1)
        log(f"Retrying authentication ({attempts}/3)...", "wr")
        time.sleep(2)

    log("Authentication Success!", "ok")
    show_user_info(session)
    
    mode = menu()
    cfg = {}

    try:
        if mode == 1:
            mode_faucet_only(session, cfg)
        elif mode == 2:
            mode_ptc_only(session, cfg)
        else:
            mode_smart(session, cfg)
    except KeyboardInterrupt:
        print(f"\n{YEL}Proses dihentikan pengguna. Session disave.{RST}")
        save_session(session)
    except Exception as e:
        log(f"FATAL ERROR: {e}", "er")
        save_session(session)

if __name__ == "__main__":
    main()
