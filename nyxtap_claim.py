"""nyxtap.com faucet claimer that mirrors the playnxc.com HAR capture flow.

Flow:
  1. GET https://nyxtap.com/<coin>-faucet            -> nyxtap session cookies + csrf
  2. POST https://nyxtap.com/api/claim                -> {solve_url, fields} or direct payout
  3. POST solve_url (forms) -> GET playnxc captcha    -> PHPSESSID + CSRF token
  4. POST /api/captcha   action=challenge             -> tile puzzle (pick_emoji)
  5. POST /api/captcha   action=verify                -> redirect_url (nyxtap captcha-return + token)
  6. GET redirect_url                                  -> nyxtap marks verification
  7. POST /api/captcha-verify                          -> confirms the solve
  8. POST /api/captcha-claim                           -> payout to FaucetPay

The captcha tiles are emoji glyphs rendered with the Google/Noto emoji set.
Each tile is matched to the emoji named in the puzzle prompt ("Pick the X …")
by comparing binary glyph masks (IoU) against the emoji rendered from the
emoji-datasource-google package.
"""

import argparse
import base64
import io
import json
import os
import random
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

import requests

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

UA = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/137.0.0.0 Mobile Safari/537.36")

NYX = "https://nyxtap.com"
PXC = "https://playnxc.com"
EMOJI_CDN = "https://cdn.jsdelivr.net/npm/emoji-datasource-google@14.0.0/img/google/64/{name}"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "nyxtap_emojis")

EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U00002B00-\U00002BFF"
    "\U0000200D"          # ZWJ
    "\U0000FE00-\U0000FE0F"
    "\U0001F1E6-\U0001F1FF"  # regional indicators
    "]"
)

_CTX = ssl.create_default_context()


def _load_noto_table():
    NOTO_FONT = "/system/fonts/NotoColorEmoji.ttf"
    if not os.path.exists(NOTO_FONT):
        return None, None, None, None
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(NOTO_FONT)
        cmap = font.getBestCmap()
        glyph_order = font.getGlyphOrder()
        cblc = font["CBLC"]
        strike = cblc.strikes[0]
        glyph_to_png = {}
        png_counter = 0
        for sub in strike.indexSubTables:
            names = getattr(sub, "names", None)
            first, last = sub.firstGlyphIndex, sub.lastGlyphIndex
            count = last - first + 1
            if names:
                for i in range(len(names)):
                    glyph_to_png[first + i] = png_counter
                    png_counter += 1
                png_counter += count - len(names)
            else:
                for i in range(count):
                    glyph_to_png[first + i] = png_counter
                    png_counter += 1
        with open(NOTO_FONT, "rb") as f:
            raw = f.read()
        pngs = []
        i = 0
        while i < len(raw) - 8:
            if raw[i : i + 8] == b"\x89PNG\r\n\x1a\n":
                j = raw.find(b"IEND", i)
                if j >= 0:
                    pngs.append(raw[i : j + 8])
                    i = j + 8
                    continue
            i += 1
        return cmap, glyph_order, glyph_to_png, pngs
    except Exception:
        return None, None, None, None


_NOTO_TABLE = None


def _noto_table():
    global _NOTO_TABLE
    if _NOTO_TABLE is None:
        _NOTO_TABLE = _load_noto_table()
    return _NOTO_TABLE


def fetch_noto_emoji(cp):
    cmap, glyph_order, glyph_to_png, pngs = _noto_table()
    if cmap is None or cp not in cmap:
        return None
    gn = cmap[cp]
    gi = glyph_order.index(gn)
    pi = glyph_to_png.get(gi)
    if pi is None or pi >= len(pngs):
        return None
    try:
        im = Image.open(io.BytesIO(pngs[pi])).convert("RGBA")
        px = im.getpixel((0, 0))
        if px[3] == 255:
            bg = px[:3]
            data = im.tobytes()
            out = bytearray(len(data))
            for i in range(0, len(data), 4):
                r, g, b, a = data[i : i + 4]
                if (r, g, b) == bg and a == 255:
                    out[i : i + 4] = bytes([255, 255, 255, 0])
                else:
                    out[i : i + 4] = bytes([r, g, b, a])
            im = Image.frombytes("RGBA", im.size, bytes(out))
        return im
    except Exception:
        return None


def emoji_filename(emoji):
    parts = []
    for ch in emoji:
        if ord(ch) in (0xFE0F, 0xFE0E):
            continue
        parts.append("%x" % ord(ch))
    return "%s.png" % "-".join(parts)


def extract_emoji(text):
    run = []
    for ch in text:
        if EMOJI_RE.match(ch):
            run.append(ch)
        elif run:
            break
    return "".join(run) if run else None


def fetch_emoji_image(emoji):
    cp = 0
    for ch in emoji:
        o = ord(ch)
        if o > 0x2000:
            cp = o
            break
    img = fetch_noto_emoji(cp)
    if img is not None:
        return img
    os.makedirs(CACHE_DIR, exist_ok=True)
    name = emoji_filename(emoji)
    path = os.path.join(CACHE_DIR, name)
    if not os.path.exists(path):
        url = EMOJI_CDN.format(name=name)
        last = None
        for _ in range(3):
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            try:
                with urllib.request.urlopen(req, timeout=20, context=_CTX) as r:
                    data = r.read()
                if data:
                    with open(path, "wb") as f:
                        f.write(data)
                    break
            except Exception as ex:
                last = ex
                time.sleep(1)
        else:
            return None
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def glyph_data(im, size=64):
    im = im.convert("RGBA")
    if im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    px = im.tobytes()
    mask = []
    colors = []
    for i in range(size * size):
        r, g, b, a = px[4 * i:4 * i + 4]
        mx, mn = max(r, g, b), min(r, g, b)
        glyph = not (a < 40 or (mx > 232 and (mx - mn) < 40))
        mask.append(1 if glyph else 0)
        if glyph:
            colors.append((r, g, b))
    xs = [i % size for i, v in enumerate(mask) if v]
    ys = [i // size for i, v in enumerate(mask) if v]
    bbox = (min(xs), min(ys), max(xs), max(ys)) if xs else None
    return im, mask, colors, bbox


def norm_glyph_mask(im, bbox, n=44):
    x0, y0, x1, y1 = bbox
    crop = im.crop((x0, y0, x1 + 1, y1 + 1)).convert("RGBA")
    crop = crop.resize((n, n), Image.LANCZOS)
    px = crop.tobytes()
    m = []
    for i in range(n * n):
        r, g, b, a = px[4 * i:4 * i + 4]
        mx, mn = max(r, g, b), min(r, g, b)
        m.append(0 if (a < 40 or (mx > 232 and (mx - mn) < 40)) else 1)
    return m


def norm_glyph_template(im, bbox, n=44):
    x0, y0, x1, y1 = bbox
    crop = im.crop((x0, y0, x1 + 1, y1 + 1)).convert("RGBA")
    crop = crop.resize((n, n), Image.LANCZOS)
    base = Image.new("RGB", (n, n), (255, 255, 255))
    base.paste(crop, (0, 0), crop)
    gray = bytearray(base.convert("L").tobytes())
    px = crop.tobytes()
    mask = bytearray(n * n)
    for i in range(n * n):
        r, g, b, a = px[4 * i:4 * i + 4]
        mx, mn = max(r, g, b), min(r, g, b)
        if not (a < 40 or (mx > 232 and (mx - mn) < 40)):
            mask[i] = 1
    return mask, gray


def template_align(tm, tg, vm, vg, n=44, rng=6):
    best = -1.0
    for ay in range(-rng, rng + 1):
        for ax in range(-rng, rng + 1):
            s = 0
            cnt = 0
            for y in range(n):
                rv = y * n
                ty = y - ay
                if not (0 <= ty < n):
                    continue
                rt = ty * n
                for x in range(n):
                    tx = x - ax
                    if 0 <= tx < n:
                        if vm[rv + x] and tm[rt + tx]:
                            s += 1 - abs(tg[rt + tx] - vg[rv + x]) / 255.0
                            cnt += 1
                        elif vm[rv + x]:
                            s += 1 - abs(255 - vg[rv + x]) / 255.0
                            cnt += 1
                    else:
                        if vm[rv + x]:
                            s += 1 - abs(255 - vg[rv + x]) / 255.0
                            cnt += 1
            for ty in range(n):
                rt = ty * n
                by = ty + ay
                if not (0 <= by < n):
                    continue
                rv = by * n
                for tx in range(n):
                    bx = tx + ax
                    if not (0 <= bx < n) and tm[rt + tx]:
                        s += 1 - abs(tg[rt + tx] - 255) / 255.0
                        cnt += 1
            if cnt:
                score = s / cnt
                if score > best:
                    best = score
    return best


def best_iou(a, b, n=44):
    best = 0.0
    for ay in range(-7, 8):
        for ax in range(-7, 8):
            v = mask_iou(a, b, ax, ay, n)
            if v > best:
                best = v
    return best


def color_hist(colors, bins=24):
    h = [0.0] * bins
    for r, g, b in colors:
        mx, mn = max(r, g, b), min(r, g, b)
        if mx == 0:
            continue
        sat = (mx - mn) / 255.0
        if sat < 0.15:
            continue
        delta = mx - mn
        if mx == r:
            hue = ((g - b) / delta) % 6
        elif mx == g:
            hue = (b - r) / delta + 2
        else:
            hue = (r - g) / delta + 4
        hh = int(hue / 6.0 * bins) % bins
        h[hh] += sat
    return h


def color_cos(a, b):
    na = sum(v * v for v in a) ** 0.5
    nb = sum(v * v for v in b) ** 0.5
    if not na or not nb:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


class FaucetClaimer:

    def __init__(self, email=None):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA})
        self.s.headers.update(
            {"Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"})
        self.email = email
        self.coin = None
        self.csrf = None
        self.sub_id = None
        self.return_url = None
        self.last_prompt = ""

    def log(self, msg):
        print("[*] %s" % msg, flush=True)

    def err(self, msg):
        print("[!] %s" % msg, flush=True)

    # -- nyxtap faucet page -------------------------------------------------

    def visit_faucet(self, coin):
        url = "%s/%s-faucet" % (NYX, coin)
        self.log("GET %s" % url)
        r = self.s.get(url, allow_redirects=True)
        r.raise_for_status()
        html = r.text
        m = re.search(r'var\s+csrf\s*=\s*"([0-9a-fA-F]+)"', html)
        self.csrf = m.group(1) if m else None
        if not self.csrf:
            raise RuntimeError("no csrf found on faucet page")
        self.coin = coin
        return html

    # -- start claim --------------------------------------------------------

    def start_claim(self, delay=8):
        body = {
            "csrf": self.csrf,
            "coin": self.coin,
            "website": "",
        }
        if self.email:
            body["email"] = self.email
        for attempt in range(1, 6):
            self.log("POST %s/api/claim" % NYX)
            r = self.s.post("%s/api/claim" % NYX, data=body)
            j = r.json()
            if j.get("success"):
                return j
            msg = j.get("message", "")
            cooldown = (r.status_code == 429) or ("Slow down" in msg)
            too_fast = "Too fast" in msg
            if (cooldown or too_fast) and attempt < 5:
                wait = 60 if cooldown else delay * (2 ** (attempt - 1))
                self.err("%s — waiting %ds before retry" % (msg, wait))
                time.sleep(wait)
                continue
            raise RuntimeError("claim refused: %s" % msg)
        d = j.get("data") or {}
        if d.get("redirect"):
            return d.get("solve_url"), d.get("fields") or {}
        if d.get("units") is not None or d.get("coin_amount"):
            return None, d
        raise RuntimeError("claim response not understood: %s" % j)

    # -- playnxc captcha ------------------------------------------------------

    def enter_captcha(self, solve_url, fields):
        if fields and any(fields.values()):
            self.log("POST %s (fields: %s)" % (solve_url, list(fields)))
            r = self.s.post(solve_url, data=fields, allow_redirects=True)
        else:
            self.log("GET %s" % solve_url)
            r = self.s.get(solve_url, allow_redirects=True)
        html = r.text
        m = re.search(r'var\s+CSRF\s*=\s*"([0-9a-fA-F]+)"', html)
        csrf = m.group(1) if m else None
        if not csrf:
            raise RuntimeError("no CSRF token on captcha page (did we reach playnxc?)")
        return csrf

    def load_challenge(self, csrf):
        r = self.s.post(
            "%s/api/captcha" % PXC,
            data={"action": "challenge", "csrf_token": csrf},
        )
        j = r.json()
        if not j.get("success"):
            raise RuntimeError("challenge failed: %s" % j.get("message"))
        return j["data"]["challenge"]

    def score_challenge(self, challenge, emoji, target_im):
        t_im, t_mask, t_colors, t_bbox = glyph_data(target_im)
        if not t_bbox:
            return None
        t_norm_mask, t_gray = norm_glyph_template(t_im, t_bbox)
        t_hist = color_hist(t_colors)
        scored = []
        for t in challenge.get("tiles", []):
            tid = t["id"]
            b64 = t["image"].split(",", 1)[1]
            tim = Image.open(io.BytesIO(base64.b64decode(b64)))
            _, _, colors, bbox = glyph_data(tim)
            if not bbox:
                scored.append((0.0, tid, 0.0, 0.0, 0.0))
                continue
            v_norm_mask, v_gray = norm_glyph_template(tim, bbox)
            template = template_align(t_norm_mask, t_gray, v_norm_mask, v_gray)
            csim = color_cos(t_hist, color_hist(colors))
            scored.append((template + 0.8 * csim, tid, template, csim))
        scored.sort(key=lambda x: x[0], reverse=True)
        self.log("matched emoji %s (%s):" % (emoji, self.last_prompt)
                 + " ".join("%s=%.2f(t%.2f+c%.2f)" % (s[1], s[0], s[2], s[3])
                            for s in scored))
        return scored

    def solve_challenge(self, challenge):
        required = challenge.get("required", 1)
        self.last_prompt = challenge.get("prompt", "")
        target = None
        emoji = None
        if HAS_PIL:
            tgt = challenge.get("target")
            if isinstance(tgt, str) and tgt.startswith("data:image"):
                target = Image.open(io.BytesIO(base64.b64decode(tgt.split(",", 1)[1])))
                emoji = "(target image)"
            else:
                emoji = extract_emoji(self.last_prompt)
                if emoji:
                    target = fetch_emoji_image(emoji)
            if target is not None:
                scored = self.score_challenge(challenge, emoji or "", target)
                if scored:
                    return [t[1] for t in scored[:required]]
        self.log("no vision solver available, guessing randomly")
        ids = [t["id"] for t in challenge.get("tiles", [])]
        return random.sample(ids, min(required, len(ids)))

    def verify_captcha(self, csrf, challenge, chosen):
        now = int(time.time() * 1000)
        clicks = []
        for i, tid in enumerate(chosen):
            if i:
                now += random.randint(700, 1600)
            clicks.append(("antibot_order[]", tid))
            clicks.append(("antibot_click_ms[]", str(now)))
        body = [("action", "verify"), ("csrf_token", csrf)] + clicks
        r = self.s.post("%s/api/captcha" % PXC, data=body)
        j = r.json()
        if j.get("success"):
            return j["data"]["redirect_url"]
        if j.get("errors") and j["errors"].get("locked"):
            raise RuntimeError("captcha locked: too many attempts")
        return None

    # -- return + claim --------------------------------------------------------

    def confirm_and_claim(self):
        self.log("POST %s/api/captcha-verify" % NYX)
        body = {
            "csrf": self.csrf,
            "sub_id": self.sub_id,
            "token": self.return_token,
            "status": "success",
        }
        r = self.s.post("%s/api/captcha-verify" % NYX, data=body)
        vj = r.json()
        if not vj.get("success"):
            raise RuntimeError("verify failed: %s" % vj.get("message"))
        if not vj.get("data", {}).get("verified"):
            self.err("verification not confirmed server-side yet: %s" % vj)
            time.sleep(2)
            return self.confirm_and_claim()
        self.log("POST %s/api/captcha-claim" % NYX)
        r = self.s.post("%s/api/captcha-claim" % NYX, data=body)
        cj = r.json()
        if not cj.get("success"):
            raise RuntimeError("claim failed: %s" % cj)
        return cj

    # -- main ---------------------------------------------------------------------

    def run(self, coin, max_tries=10):
        self.visit_faucet(coin)
        self.log("csrf=%s coin=%s" % (self.csrf, self.coin))
        self.log("waiting a few seconds to look human before claiming")
        time.sleep(len("getting ready") + random.randint(1, 4))
        claim_j = self.start_claim()
        d = claim_j.get("data") or {}
        if not d.get("redirect"):
            if d.get("units") is not None or d.get("coin_amount"):
                return d
            raise RuntimeError("claim refused: %s" % claim_j.get("message"))
        solve_url = d["solve_url"]
        q = urllib.request.urlparse(solve_url)
        qp = urllib.parse.parse_qs(q.query)
        fields = d.get("fields") or {}
        self.return_url = fields.get("return_url") or (qp.get("return_url") or [None])[0]
        self.sub_id = fields.get("sub_id") or (qp.get("sub_id") or [None])[0]
        if not self.sub_id:
            raise RuntimeError("no sub_id returned from /api/claim: %s" % d)
        csrf = self.enter_captcha(solve_url, fields)
        last_err = None
        for attempt in range(1, max_tries + 1):
            self.log("captcha attempt %d/%d" % (attempt, max_tries))
            challenge = self.load_challenge(csrf)
            chosen = self.solve_challenge(challenge)
            redirect_url = self.verify_captcha(csrf, challenge, chosen)
            if redirect_url:
                m = re.search(r"[?&]token=([0-9a-fA-F]+)", redirect_url)
                if not m:
                    raise RuntimeError("no token in redirect_url: %s" % redirect_url)
                self.return_token = m.group(1)
                self.log("GET %s" % redirect_url.split("?")[0])
                self.s.get(redirect_url, allow_redirects=True)
                return self.confirm_and_claim()
            self.err("verify rejected, retrying with a fresh challenge")
            time.sleep(1)
        raise RuntimeError("could not pass the captcha in %d attempts" % max_tries)


def claim_once(email, coin, max_tries):
    claimer = FaucetClaimer(email=email)
    try:
        result = claimer.run(coin, max_tries=max_tries)
    except RuntimeError as e:
        print("[!] %s" % e, file=sys.stderr)
        return False, None
    d = result.get("data", result)
    print("\n[+] SUCCESS: %s %s (%s satoshi) sent to your FaucetPay wallet%s"
          % (d.get("coin_amount", ""), d.get("coin", ""), d.get("units", ""),
             (" [ref %s]" % d["payout_id"]) if d.get("payout_id") else ""))
    print("[+] %s" % result.get("message", ""))
    return True, result


def main():
    COINS = [
        "usdt", "eth", "usdc", "bnb", "sol", "xrp", "doge", "trx",
        "ltc", "bch", "dash", "pol", "xlm", "ada", "zec", "ton", "fey",
    ]

    ap = argparse.ArgumentParser(
        description="Claim nyxtap.com faucet rewards")
    ap.add_argument("--coin", default=None)
    ap.add_argument("--email", default=None)
    ap.add_argument("--max-tries", type=int, default=10)
    ap.add_argument("--times", type=int, default=0)
    ap.add_argument("--interval", type=int, default=110)
    args = ap.parse_args()

    email = args.email
    if not email:
        email = input("Enter your FaucetPay email: ").strip()
        if not email:
            print("Email is required.", file=sys.stderr)
            raise SystemExit(1)

    coin = args.coin
    if not coin:
        print("\nAvailable coins:")
        for i, c in enumerate(COINS, 1):
            print("  %2d. %s" % (i, c.upper()))
        while True:
            choice = input("\nSelect coin (1-%d): " % len(COINS)).strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(COINS):
                    coin = COINS[idx]
                    break
            except ValueError:
                if choice.lower() in COINS:
                    coin = choice.lower()
                    break
            print("Invalid choice, try again.")

    times = args.times
    if not times:
        t = input("How many times to claim? (0=unlimited): ").strip()
        try:
            times = int(t)
        except ValueError:
            times = 0

    print("\nStarting: email=%s coin=%s times=%s interval=%ds" % (
        email, coin.upper(), times or "unlimited", args.interval))
    print()

    remaining = times
    i = 0
    while remaining != 0:
        i += 1
        print("===== claim round %d -> %s =====" % (i, coin.upper()))
        ok, _ = claim_once(email, coin, args.max_tries)
        if ok and times:
            remaining -= 1
        if remaining == 0 and times:
            break
        wait = args.interval
        print("[*] sleeping %ds before next claim..." % wait)
        for _ in range(wait):
            time.sleep(1)


if __name__ == "__main__":
    main()